from collections import defaultdict
from math import log
from sqlalchemy import desc
from flask import Blueprint, jsonify, request, Response
from marshmallow import validates, ValidationError
from werkzeug.exceptions import BadRequest
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from werkzeug.exceptions import NotFound
from database import db
from sqlalchemy.orm.util import has_identity
from models.service import Service
from models.search import term_frequency
from models.user import auth
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
service_schema_all = ServiceSchema(exclude=['search_coincidences'])


def filter_query(q, filters, coincidence=False):
    if coincidence:
        q = q.join(Service, aliased=True).filter_by(state=0)

    for filter_name in filters:

        if filter_name == 'price':
            filter_quantity = Service.price
        elif filter_name == 'rating':
            raise BadRequest('filter by rating not implemented yet')
        else:
            raise BadRequest('filter ' + filter_name + ' not yet implemented')

        if 'min' in filters[filter_name]:
            q = q.filter(filter_quantity >= filters[filter_name]['min'])

        if 'max' in filters[filter_name]:
            q = q.filter(filter_quantity <= filters[filter_name]['max'])

    return q


def sort_query_services(q, passed_arguments):
    if 'by' not in passed_arguments:
        raise BadRequest('Specify what to sort by!')

    if passed_arguments['by'] == 'price':
        sort_criterion = Service.price

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

    if reverse:
        return q.order_by(desc(sort_criterion))
    else:
        return q.order_by(sort_criterion)


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


def get_matches_text(search_text, search_order, filters=(), threshold=0.9, user_email=None):
    scores = defaultdict(float)

    total_documents = Service.get_count()

    coincidences_queries = term_frequency.search_text(search_text)

    for coincidences_query in coincidences_queries:
        if user_email is not None:
            coincidences_query = coincidences_query.join(Service, aliased=True).filter_by(user_email=user_email, state=0)
        coincidences_query = filter_query(coincidences_query, filters=filters, coincidence=True)
        coincidences_word = coincidences_query.all()

        if len(coincidences_word) > 0:

            idf = log(1 + total_documents / len(coincidences_word))
            for coincidence in coincidences_word:

                if search_order:
                    count = int.from_bytes(coincidence.count, "little")
                    tf = log(1 + count / (len(coincidence.service.description) + len(coincidence.service.title)))
                    scores[coincidence.service] += tf * idf

                else:
                    scores[coincidence.service] += idf

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

    all_services = Service.query.filter(Service.state == 0)


    if not request.headers.get('content-type') == 'application/json':
        return jsonify(service_schema_all.dump(all_services, many=True)), 200

    info = request.json

    if 'filters' in info:
        filters = info['filters']
    else:
        filters = ()

    if 'search_text' in info:
        all_services = get_matches_text(info['search_text'], search_order='sort' not in info, filters=filters,
                                        threshold=0.9, user_email=user_email)
        if 'sort' in info:
            sort_services(all_services, info['sort'])
    else:
        services_query = Service.query.filter(Service.state == 0)
        if user_email is not None:
            services_query = services_query.filter_by(user_email=user_email, state=0)
        services_query = filter_query(services_query, filters=filters, coincidence=False)
        if 'sort' in info:
            services_query = sort_query_services(services_query, info['sort'])
        all_services = services_query.all()

    return jsonify(service_schema_all.dump(all_services, many=True)), 200


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
    if request.method == "GET":
        return jsonify(service_schema_all.dump(service, many=False)), 200


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

    return Response("Servicio añadido correctamente con el identificador: " + str(new_service.id), status=200)


@services_bp.route("/<int:service_id>", methods=["PUT", "DELETE"])
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

    elif request.method == "DELETE":
        service.state = 2
        return Response("Se ha eliminado correctamente el servicio con identificador: " + str(service_id), status=200)

    elif request.method == "PUT":
        # All this code is to be able to use all the checks of the marshmallow schema.
        info = request.json
        iterator = iter(service.__dict__.items())
        next(iterator)  # Metadata
        for attr, value in iterator:
            if attr != "id" and attr != "created_at":
                if attr == "user_email": attr = "user"
                if attr not in info.keys():
                    info[attr] = value

        service.state = 2
        service.save_to_db()
        n_service = service_schema_all.load(info, session=db.session)  # De esta forma pasamos todos los constrains.
        n_service.save_to_db()
        return Response("Servicio modificado correctamente", status=200)
