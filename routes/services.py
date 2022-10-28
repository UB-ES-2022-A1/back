from flask import Blueprint, jsonify, request, Response
from marshmallow import validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from werkzeug.exceptions import NotFound
from database import db
from sqlalchemy.orm.util import has_identity
from models.service import Service
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
service_schema_all = ServiceSchema()


@services_bp.route("", methods=["GET"])
@auth.login_required(role=[access[0], access[1], access[8], access[9]])
def get_all_services():
    """
    This method returns all the services. It doesn't require privileges
    :return: Response with all the services
    """
    all_services = Service.get_all()
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
