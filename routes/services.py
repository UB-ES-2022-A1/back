import json
from flask import Blueprint, jsonify, request
from marshmallow import validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from werkzeug.exceptions import NotFound
from database import db
from sqlalchemy.orm.util import has_identity
from models.service import Service
from models.user import auth, User
from routes.users import get_user
from flask import g
from utils.custom_exceptions import PrivilegeException
from utils.privilegies import access
from utils.search_utils import filter_query, sort_services, get_matches_text, sort_query_services, filter_email_state

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
                if attr == "user_email":
                    attr = "user"
                if attr not in info.keys():
                    info[attr] = value

        service.state = 2
        service.save_to_db()
        n_service = service_schema_all.load(info, session=db.session)  # De esta forma pasamos todos los constrains.
        n_service.masterID = service.masterID
        n_service.save_to_db()
        return {'modified_service_id': n_service.id}, 200
