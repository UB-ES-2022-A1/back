from flask import Blueprint, jsonify, request, Response
from marshmallow import validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from werkzeug.exceptions import NotFound
from database import db
from sqlalchemy.orm.util import has_identity
from models.contracted_service import ContractedService
from models.user import auth
from routes.users import get_user
from flask import g
from utils.custom_exceptions import PrivilegeException
from utils.privilegies import access

# Todas las url de servicios contratados empiezan por esto
contracted_services_bp = Blueprint("contracted_services", __name__, url_prefix="/contracted_services")


# Validación y serialización de servicios
class ContractedServiceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ContractedService
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

    @validates("service")
    def validates_service(self, value):
        """
        Validates that the service exists
        :param value: service id
        :return: None. Raises an Exception
        """
        if not has_identity(value):
            raise NotFound("Servicio con id " + str(value.email) + " no encontrado!")
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
contracted_service_schema_all = ContractedServiceSchema()


@contracted_services_bp.route("", methods=["GET"])
@auth.login_required(role=[access[0], access[1], access[8], access[9]])
def get_all_contracted_services():
    """
    This method returns all the services. It doesn't require privileges
    :return: Response with all the services
    """
    all_contracted = ContractedService.get_all()
    return jsonify(contracted_service_schema_all.dump(all_contracted, many=True)), 200


@contracted_services_bp.route("/<int:contracted_service_id>", methods=["GET"])
@auth.login_required(role=[access[0], access[1], access[8], access[9]])
def get_contracted_service(contracted_service_id):
    """
    This method returns a concrete service. It doesn't require privileges
    :param service_id:
    :return: Response including the service
    """
    service = ContractedService.get_by_id(contracted_service_id)
    # En caso de no encontrar el servicio retornamos un mensaje de error.
    if not service:
        raise NotFound
    if request.method == "GET":
        return jsonify(contracted_service_schema_all.dump(service, many=False)), 200


@contracted_services_bp.route("/<int:contracted_service_id>/user", methods=["GET"])
@auth.login_required(role=[access[0], access[1], access[8], access[9]])
def get_contracted_service_user(contracted_service_id):
    """
    This method returns the user of a service. It doesn't require privileges.
    :param service_id:
    :return:
    """
    service = ContractedService.get_by_id(contracted_service_id)
    # En caso de no encontrar el servicio retornamos un mensaje de error.
    if not service:
        raise NotFound
    return get_user(service.user_email)


@contracted_services_bp.route("/<string:email>/contracted_service", methods=["GET"])
@auth.login_required(role=[access[0], access[1], access[8], access[0]])
def get_user_contracted_services(email):
    """
    This method returns a user services. It doesn't require privileges
    :param email: the user mail that we want to obtain services
    :return: Response
    """
    services = ContractedService.query.filter_by(user_email=email)
    return jsonify(contracted_service_schema_all.dump(services, many=True)), 200


@contracted_services_bp.route("", methods=["POST"])
@auth.login_required(role=[access[1], access[8], access[9]])
def contract_service():
    """
    This method contracts a new service. Requires a token of a user to do the post.
    :return: Response
    """
    info = request.json  # Leer la info del json
    info["user"] = g.user.email
    new_contracted_service = contracted_service_schema_all.load(info, session=db.session)  # Crear el objeto mediante el schema
    new_contracted_service.save_to_db()  # Actualizamos la BD

    return Response("Servicio contratado correctamente con el identificador: " + str(new_contracted_service.id), status=200)


@contracted_services_bp.route("/<int:contracted_service_id>", methods=["PUT", "DELETE"])
@auth.login_required(role=[access[1], access[8], access[9]])
def interact_contracted_service(contracted_service_id):
    """
    Method used to delete or modify services. Requires a token. The token
    user musts coincide with the service user or be an admin
    :param service_id: The service that is going to be treated
    :return: Response
    """
    service = ContractedService.get_by_id(contracted_service_id)
    # En caso de no encontrar el servicio retornamos un mensaje de error.
    if not service:
        raise NotFound

    if service.user_email != g.user.email and g.user.access < 8:
        raise PrivilegeException("Not enough privileges to modify other resources.")

    elif request.method == "DELETE":
        service.delete_from_db()
        return Response("Se ha eliminado correctamente el servicio con identificador: " + str(contracted_service_id), status=200)

    elif request.method == "PUT":
        # All this code is to be able to use all the checks of the marshmallow schema.
        info = request.json
        iterator = iter(service.__dict__.items())
        next(iterator)  # Metadata
        for attr, value in iterator:
            if attr == "user_email": attr = "user"
            if attr not in info.keys():
                info[attr] = value
        n_contracted_service = contracted_service_schema_all.load(info, session=db.session)  # De esta forma pasamos todos los constrains.
        n_contracted_service.save_to_db()
        return Response("Contrato modificado correctamente", status=200)