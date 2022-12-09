import json
from collections import defaultdict
from math import log
from sqlalchemy import desc, func, asc
from operator import or_

from sqlalchemy import desc
from flask import Blueprint, jsonify, request
from marshmallow import validates, ValidationError, pre_dump
from werkzeug.exceptions import BadRequest
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from werkzeug.exceptions import NotFound
from database import db
from sqlalchemy.orm.util import has_identity, aliased

from models.contracted_service import ContractedService
from models.service import Service
from models.search import term_frequency
from models.user import auth, User
from routes.users import get_user
from flask import g
from utils.custom_exceptions import PrivilegeException
from utils.privilegies import access

# Todas las url de servicios empiezan por esto
services_bp = Blueprint("services", __name__, url_prefix="/services")


# Validación y serialización de servicios
class ServiceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Service
        include_relationships = True  # Incluir relaciones como la de user
        load_instance = True  # Para que se puedan crear los objetos

    @validates("user")
    def validates_user(self, value):
        """
        Validates that the user of the service exists
        :param value: user mail
        :return: None. Raises an Exception
        """
        if not has_identity(value):
            raise NotFound("Usuario con id " + str(value.email) + " no encontrado!")

    @validates("price")
    def validates_price(self, value):
        """
        Validates that the price of the service is not negative
        :param value: the price of the service
        :return: None. Raises an Exception
        """
        if value < 0:
            raise ValidationError("Price can't be negative!")


# Para crear servicio
service_schema_all = ServiceSchema(exclude=['search_coincidences', 'contracts'])


def filter_query(q, ser_table, filters):
    for filter_name in filters:

        if filter_name == 'price':
            filter_quantity = ser_table.price
        elif filter_name == 'creation_date':
            filter_quantity = ser_table.created_at
        elif filter_name == 'popularity':

            """

            cs = aliased(ContractedService)
            s2 = aliased(Service)
    
            filter_quantity = func.count(cs.id)
            q = q.add_column(filter_quantity)

            q = q.join(s2, ser_table.masterID == s2.masterID).join(cs, cs.service_id == s2.id).group_by(s2.id)
            filter_quantity = ser_table.price
            """
            raise NotImplementedError


        elif filter_name == 'rating':
            raise BadRequest('filter by rating not implemented yet')
        else:
            raise BadRequest('filter ' + filter_name + ' not yet implemented')

        if 'min' in filters[filter_name] and filters[filter_name]['min'] != -1:
            q = q.filter(filter_quantity >= filters[filter_name]['min'])

        if 'max' in filters[filter_name] and filters[filter_name]['max'] != -1:
            q = q.filter(filter_quantity <= filters[filter_name]['max'])

    return q


def sort_query_services(q, ser_table, passed_arguments):
    if 'by' not in passed_arguments:
        raise BadRequest('Specify what to sort by!')

    if passed_arguments['by'] == 'price':
        sort_criterion = ser_table.price

    elif passed_arguments['by'] == 'creation_date':
        sort_criterion = ser_table.created_at

    elif passed_arguments['by'] == 'rating':
        raise NotImplementedError('This sorting method is not supported!')

    elif passed_arguments['by'] == 'popularity':
        raise NotImplementedError('This sorting method is not supported!')

        # q = q.join(ContractedService).group_by(Service.masterID)
        # sort_criterion = func.count(ContractedService.id)

    else:
        raise NotImplementedError('This sorting method is not supported!')

    if 'reverse' in passed_arguments:
        reverse = passed_arguments['reverse']

        if reverse not in [True, False]:
            raise BadRequest('reverse parameter must be True or False!')

    else:
        reverse = False

    if reverse:
        return q.order_by(desc(sort_criterion))
    else:
        return q.order_by(asc(sort_criterion))


def sort_services(list_to_sort, passed_arguments):
    if 'by' not in passed_arguments:
        raise BadRequest('Specify what to sort by!')

    if passed_arguments['by'] == 'price':
        def sort_criterion(s: Service):
            return s.price

    elif passed_arguments['by'] == 'creation_date':
        def sort_criterion(s: Service):
            return s.created_at

    elif passed_arguments['by'] == 'rating':
        raise NotImplementedError('This sorting method is not supported!')

    elif passed_arguments['by'] == 'popularity':
        raise NotImplementedError('This sorting method is not supported!')
    else:
        raise NotImplementedError('This sorting method is not supported!')

    if 'reverse' in passed_arguments:
        reverse = passed_arguments['reverse']

        if reverse not in [True, False]:
            raise BadRequest('reverse parameter must be True or False!')

    else:
        reverse = False

    list_to_sort.sort(key=sort_criterion, reverse=reverse)


def get_matches_text(q, ser_table, search_text, search_order, threshold=0.9):
    scores = defaultdict(float)

    total_documents = Service.get_count()

    coincidences_queries = term_frequency.search_text(search_text)

    for word, coincidences_query in coincidences_queries:

        coincidences_word = coincidences_query.subquery().join(q.subquery()).all()

        if len(coincidences_word) > 0:

            idf = log(1 + total_documents / len(coincidences_word))
            partial_counts = defaultdict(float)

            for coincidence in coincidences_word:
                count = int.from_bytes(coincidence.count, "little")
                partial_counts[coincidence.service] += \
                    count / (len(coincidence.service.description) + len(coincidence.service.title)) * \
                    len(word) / len(coincidence.word)

            for service, total_count in partial_counts.items():

                if search_order:
                    tf = log(1 + total_count)
                    scores[service] += tf * idf

                else:
                    scores[service] += idf

    all_scored = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    if not search_order:

        if len(all_scored) == 0:
            return []

        n = 0
        while n < len(all_scored) and all_scored[n][1] >= all_scored[0][1] * threshold:
            n += 1

        return [scored[0] for scored in all_scored[:n]]

    else:
        return [scored[0] for scored in all_scored]


def filter_email_state(q, ser_table, user_email=None):
    q_final = q

    if user_email:

        user = User.get_by_id(user_email)
        if not user:
            raise NotFound('User not found')

        q_final = q_final.filter(ser_table.user == user)

        if g.user.email == user_email and not g.user.access >= 8:
            q_final = q_final.filter(or_(Service.state == 0, Service.state == 1))
        elif not g.user.access >= 8:
            q_final = q_final.filter(Service.state == 0)
    else:
        if not g.user.access >= 8:
            q_final = q_final.filter(Service.state == 0)

    return q_final


@services_bp.route("", methods=["GET"])
@auth.login_required(role=[access[0], access[1], access[8], access[9]])
def get_all_services():
    all_services = Service.get_all()
    return jsonify(service_schema_all.dump(all_services, many=True)), 200


@services_bp.route("/search", methods=["GET", "POST"])
@auth.login_required(role=[access[0], access[1], access[8], access[9]])
def get_many_services(user_email=None):
    """
    This method returns a list of services. It doesn't require privileges.
    :return: Response with all the services
    """

    s1 = Service
    q = s1.query

    q = filter_email_state(q, s1, user_email=user_email)

    if not request.headers.get('content-type') == 'application/json':
        services = service_schema_all.dump(q, many=True)
        for id_c, service in enumerate(services):
            services[id_c] = json.loads(get_service(service["id"])[0].get_data().decode("utf-8"))
        return jsonify(services), 200

    info = request.json

    if 'filters' in info:
        filters = info['filters']
    else:
        filters = ()

    q = filter_query(q, s1, filters=filters)

    if 'search_text' in info:
        all_services = get_matches_text(q, s1, info['search_text'], search_order='sort' not in info, threshold=0.9)
        if 'sort' in info:
            sort_services(all_services, info['sort'])
    else:

        if 'sort' in info:
            q = sort_query_services(q, s1, info['sort'])
        all_services = q.all()

    services = service_schema_all.dump(all_services, many=True)
    for id_c, service in enumerate(services):
        services[id_c] = json.loads(get_service(service["id"])[0].get_data().decode("utf-8"))
    return jsonify(services), 200


@services_bp.route("/<int:service_id>", methods=["GET"])
@auth.login_required(role=[access[0], access[1], access[8], access[9]])
def get_service(service_id):
    """
    This method returns a concrete service. It doesn't require privileges
    :param service_id:
    :return: Response including the service
    """
    service = Service.get_by_id(service_id)
    # En caso de no encontrar el servicio retornamos un mensaje de error.
    if not service:
        raise NotFound
    info = service_schema_all.dump(service, many=False)
    user = User.get_by_id(info["user"])
    info["user_name"] = user.name
    info["user_email"] = info["user"]
    info["user_grade"] = user.user_grade
    info.pop("user")
    return jsonify(info), 200


@services_bp.route("/<int:service_id>/user", methods=["GET"])
@auth.login_required(role=[access[0], access[1], access[8], access[9]])
def get_service_user(service_id):
    """
    This method returns the user of a service. It doesn't require privileges.
    :param service_id:
    :return:
    """
    service = Service.get_by_id(service_id)
    # En caso de no encontrar el servicio retornamos un mensaje de error.
    if not service:
        raise NotFound
    return get_user(service.user.email)


@services_bp.route("/<string:email>/service", methods=["GET", "POST"])
@auth.login_required(role=[access[0], access[1], access[8], access[9]])
def get_user_services(email):
    """
    This method returns a user services. It doesn't require privileges
    :param email: the user mail that we want to obtain services
    :return: Response
    """
    return get_many_services(user_email=email)


@services_bp.route("", methods=["POST"])
@auth.login_required(role=[access[1], access[8], access[9]])
def create_service():
    """
    This method creates a new service. Requires a token of a user to do the post.
    :return: Response
    """
    info = request.json  # Leer la info del json
    info["user"] = g.user.email
    new_service = service_schema_all.load(info, session=db.session)  # Crear el objeto mediante el schema
    new_service.save_to_db()  # Actualizamos la BD

    return {'added_service_id': new_service.id}, 200


@services_bp.route("/<int:service_id>", methods=["POST", "PUT", "DELETE"])
@auth.login_required(role=[access[1], access[8], access[9]])
def interact_service(service_id):
    """
    Method used to delete or modify services. Requires a token. The token
    user musts coincide with the service user or be an admin
    :param service_id: The service that is going to be treated
    :return: Response
    """
    service = Service.get_by_id(service_id)
    # En caso de no encontrar el servicio retornamos un mensaje de error.
    if not service:
        raise NotFound

    if service.user_email != g.user.email and g.user.access < 8:
        raise PrivilegeException("Not enough privileges to modify other resources.")

    # Disables the service (only changes the state)
    elif request.method == "POST":
        if service.state == 2:
            raise NotFound
        if service.state == 1:
            service.state = 0
            service.save_to_db()
            return {'service_enabled_id': service_id}, 200
        elif service.state == 0:
            service.state = 1
            service.save_to_db()
            return {'service_disabled_id': service_id}, 200


    # Eliminates the service (only changes the state)
    elif request.method == "DELETE":
        service.state = 2
        service.save_to_db()
        return {'service_deleted_id': service_id}, 200

    # Modifies the service by changing the state and creating a new one with the same parameters except the changed ones
    elif request.method == "PUT":

        if service.state == 2:
            raise NotFound
        # All this code is to be able to use all the checks of the marshmallow schema.
        info = request.json
        iterator = iter(service.__dict__.items())
        next(iterator)  # Metadata
        for attr, value in iterator:
            if attr in ['title', 'description', 'user_email', 'price', 'cooldown', 'begin', 'end', 'requiresPlace']:
                if attr == "user_email": attr = "user"
                if attr not in info.keys():
                    info[attr] = value

        service.state = 2
        service.save_to_db()
        n_service = service_schema_all.load(info, session=db.session)  # De esta forma pasamos todos los constrains.
        n_service.masterID = service.masterID
        n_service.save_to_db()
        return {'modified_service_id': n_service.id}, 200
