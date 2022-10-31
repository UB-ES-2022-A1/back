from collections import defaultdict
from math import log

from flask import Blueprint, jsonify, request, Response
from marshmallow import validates
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
            raise BadRequest("Price can't be negative!")


# Para crear servicio
service_schema_all = ServiceSchema(exclude=['search_coincidences'])


def passes_filters(s, filters):

    for filter_name in filters:

        if filter_name == 'price':
            filter_quantity = s.price
        elif filter_name == 'rating':
            raise BadRequest('filter by rating not implemented yet')
        else:
            raise BadRequest('filter ' + filter_name + ' not yet implemented')

        if 'min' in filters[filter_name]:
            if filter_quantity < filters[filter_name]['min']:
                return False

        if 'max' in filters[filter_name]:
            if filter_quantity > filters[filter_name]['max']:
                return False

    return True


@services_bp.route("", methods=["GET"])
@auth.login_required(role=[access[0], access[1], access[8], access[9]])
def get_many_services():
    """
    This method returns a list of services. It doesn't require privileges.
    :return: Response with all the services
    """

    if not request.headers.get('content-type') == 'application/json':
        all_services = Service.get_all()
        return jsonify(service_schema_all.dump(all_services, many=True)), 200

    info = request.json

    if 'search_text' in info:

        scores = defaultdict(float)

        total_documents = Service.get_count()
        coincidences = term_frequency.search_text(info['search_text'])

        for coincidences_word in coincidences:

            if len(coincidences_word) > 0:

                idf = log(1 + total_documents / len(coincidences_word))
                for coincidence in coincidences_word:

                    if 'sort' in info:
                        scores[coincidence.service] += idf
                    else:
                        count = int.from_bytes(coincidence.count, "little")
                        tf = log(1 + count / (len(coincidence.service.description) + len(coincidence.service.title)))
                        scores[coincidence.service] += tf * idf

        all_scored = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if 'filters' in info:
            all_scored = [scored for scored in all_scored if passes_filters(scored[0], info['filters'])]

        if 'sort' in info:

            if len(all_scored) == 0:
                return jsonify(service_schema_all.dump([], many=True)), 200

            threshold = 0.9
            n = 0
            while n < len(all_scored) and all_scored[n][1] >= all_scored[0][1] * threshold:
                n += 1

            all_services = [all_scored[i][0] for i in range(n)]

        else:
            all_services = [scored[0] for scored in all_scored]

    else:
        all_services = Service.get_all()
        if 'filters' in info:
            all_scored = [s for s in all_services if passes_filters(s, info['filters'])]

    if 'sort' in info:

        if 'by' not in info['sort']:
            raise BadRequest('Specify what to sort by!')

        if info['sort']['by'] == 'price':
            def reverse_criterion(s: Service):
                return s.price

        elif info['sort']['by'] == 'rating':
            raise NotImplementedError('This sorting method is not supported!')

        elif info['sort']['by'] == 'popularity':
            raise NotImplementedError('This sorting method is not supported!')
        else:
            raise NotImplementedError('This sorting method is not supported!')

        if 'reverse' in info['sort']:
            if not info['sort']['reverse'] in [True, False]:
                raise BadRequest('reverse parameter must be True or False!')

            all_services.sort(key=reverse_criterion, reverse=info['sort']['reverse'])

    """

    if 'filters' in info:


        for filter_name in info['filters']:

            if not filter_name in ['price', 'rating']:
                raise NotImplementedError('This filtering method is not supported!')

            if 'min' in info['filters']['filter_name']:
                min_value = info
                pass

            if 'max' in info['filters']['filter_name']:
                max_value = info
                pass
                
    """

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


@services_bp.route("/<string:email>/service", methods=["GET"])
@auth.login_required(role=[access[0], access[1], access[8], access[0]])
def get_user_services(email):
    """
    This method returns a user services. It doesn't require privileges
    :param email: the user mail that we want to obtain services
    :return: Response
    """
    services = Service.query.filter_by(user_email=email)
    return jsonify(service_schema_all.dump(services, many=True)), 200


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
        service.delete_from_db()
        return Response("Se ha eliminado correctamente el servicio con identificador: " + str(service_id), status=200)

    elif request.method == "PUT":
        # All this code is to be able to use all the checks of the marshmallow schema.
        info = request.json
        iterator = iter(service.__dict__.items())
        next(iterator)  # Metadata
        for attr, value in iterator:
            if attr == "user_email": attr = "user"
            if attr not in info.keys():
                info[attr] = value
        n_service = service_schema_all.load(info, session=db.session)  # De esta forma pasamos todos los constrains.
        n_service.save_to_db()
        return Response("Servicio modificado correctamente", status=200)
