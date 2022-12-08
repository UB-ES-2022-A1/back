from flask import Blueprint, jsonify, request
from marshmallow import validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from werkzeug.exceptions import NotFound, BadRequest, Conflict
from database import db
from sqlalchemy.orm.util import has_identity
from models.contracted_service import ContractedService
from models.service import Service
from models.user import User
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


# Para crear servicio
contracted_service_schema_all = ContractedServiceSchema(dump_only=['state'])


@contracted_services_bp.route("", methods=["GET"])
@auth.login_required(role=[access[8], access[9]])
def get_all_contracted_services():
    """
    This method returns all the services. It requires admin privileges
    """
    all_contracted = ContractedService.get_all()
    return jsonify(contracted_service_schema_all.dump(all_contracted, many=True)), 200


@contracted_services_bp.route("/<int:contracted_service_id>", methods=["GET"])
@auth.login_required(role=[access[1], access[8], access[9]])
def get_contracted_service(contracted_service_id):
    """
    This method returns a concrete service. It requires to be admin or be a part of the contract
    :param contracted_service_id: id of the contract
    :return: Response including the service
    """
    Cservice = ContractedService.get_by_id(contracted_service_id)
    # En caso de no encontrar el servicio retornamos un mensaje de error.
    if not Cservice:
        raise NotFound

    if Cservice.user_email != g.user.email and Cservice.service.user_email != g.user.email and g.user.access < 8:
        raise PrivilegeException("Not enough privileges to access other users' contracts.")

    return jsonify(contracted_service_schema_all.dump(Cservice, many=False)), 200


@contracted_services_bp.route("/<int:contracted_service_id>/user", methods=["GET"])
@auth.login_required(role=[access[1], access[8], access[9]])
def get_contracted_service_user(contracted_service_id):
    """
    This method returns the user of a service. It requires to be admin or be a part of the contract
    :param contracted_service_id: id of the contract
    :return:
    """
    Cservice = ContractedService.get_by_id(contracted_service_id)
    # En caso de no encontrar el servicio retornamos un mensaje de error.
    if not Cservice:
        raise NotFound

    if Cservice.user_email != g.user.email and Cservice.service.user_email != g.user.email and g.user.access < 8:
        raise PrivilegeException("Not enough privileges to access other users' contracts.")

    return get_user(Cservice.user_email)


@contracted_services_bp.route("/client/<string:email>", methods=["GET"])
@auth.login_required(role=[access[1], access[8], access[9]])
def get_user_contracted_services(email):
    """
    :param email: the email of the client
    :return: all the contracts the client has ordered
    """

    if email != g.user.email and g.user.access < 8:
        raise PrivilegeException("Not enough privileges to access other users' contracts.")

    contracts = ContractedService.query.filter_by(user_email=email).all()
    return jsonify(contracted_service_schema_all.dump(contracts, many=True)), 200


@contracted_services_bp.route("/contractor/<string:email>", methods=["GET"])
@auth.login_required(role=[access[1], access[8], access[9]])
def get_contractor_offered_contracts(email):
    """
    :param email: the email of the contractor
    :return: all the contracts the contractor has been offered, regardless of wether they have accepted
    """
    if email != g.user.email and g.user.access < 8:
        raise PrivilegeException("Not enough privileges to access other users' contracts.")

    contracts = ContractedService.query.filter(ContractedService.service.has(user_email=email)).all()
    return jsonify(contracted_service_schema_all.dump(contracts, many=True)), 200


@contracted_services_bp.route("", methods=["POST"])
@auth.login_required(role=[access[1], access[8], access[9]])
def contract_service():
    """
    This method contracts a new service. Requires a token of a user to do the post.
    :return: Response
    """
    info = request.json  # Leer la info del json
    if 'service' not in info:
        raise ValidationError({'service': ['Missing data for required field.']})

    info["user"] = g.user.email
    new_contracted_service = contracted_service_schema_all.load(info, session=db.session)
    p = new_contracted_service.service.price
    w = g.user.wallet
    updated_w = w - p

    if updated_w < 0:
        return {'reason': 'Not enough funds'}, 400

    g.user.wallet = updated_w
    g.user.save_to_db()
    new_contracted_service.save_to_db()

    return {'request_id': new_contracted_service.id}, 201


@contracted_services_bp.route("/<int:id>/done", methods=["PUT"])
@auth.login_required(role=[access[1], access[8], access[9]])
def mark_as_done(id):
    contract = ContractedService.get_by_id(id)
    service = Service.get_by_id(contract.service_id)

    # En caso de no encontrar el servicio retornamos un mensaje de error.
    if not contract:
        raise NotFound

    if not service:
        raise NotFound

    if contract.state == 0:
        raise Conflict('Must accept service before doing it!')

    if service.user_email != g.user.email and g.user.access < 8:
        raise PrivilegeException("Not enough privileges to modify other resources.")

    contracted = User.get_by_id(service.user_email)
    if not contracted:
        raise NotFound

    contract.state = 3
    contracted.wallet = str(float(contracted.wallet) + float(service.price))
    contract.save_to_db()
    contracted.save_to_db()
    return {'status': 'State updated successfully'}, 200


@contracted_services_bp.route("/<int:id>/accept", methods=["PUT"])
@auth.login_required(role=[access[1], access[8], access[9]])
def mark_as_accepted(id):
    contract = ContractedService.get_by_id(id)
    service = Service.get_by_id(contract.service_id)

    # En caso de no encontrar el servicio retornamos un mensaje de error.
    if not contract:
        raise NotFound

    if not service:
        raise NotFound

    if not contract.state == 0:
        raise Conflict("contract is not acceptable because it already was accepted or canceled!")

    if service.user_email != g.user.email and g.user.access < 8:
        raise PrivilegeException("Not enough privileges to modify other resources.")

    contract.state = 1
    contract.save_to_db()
    return {'status': 'State updated successfully'}, 200


@contracted_services_bp.route("/<int:contracted_service_id>", methods=["PUT", "DELETE"])
@auth.login_required(role=[access[1], access[8], access[9]])
def delete_contracted_service(contracted_service_id):
    """
    Method used to delete or modify services. Requires a token. The token
    user musts coincide with the service user or be an admin
    :param contracted_service_id: The service that is going to be treated
    :return: Response
    """
    service = ContractedService.get_by_id(contracted_service_id)
    # En caso de no encontrar el servicio retornamos un mensaje de error.
    if not service:
        raise NotFound

    if service.user_email != g.user.email and g.user.access < 8:
        raise PrivilegeException("Not enough privileges to modify other resources.")

    if service.state == 0:
        g.user.wallet += service.price
    else:
        raise BadRequest("Can't cancel or edit an ordered which has been accepted or delivered!")

    if request.method == "DELETE":
        service.delete_from_db()
        return {'deleted_request': contracted_service_id}, 200

    elif request.method == "PUT":
        # All this code is to be able to use all the checks of the marshmallow schema.
        info = request.json
        iterator = iter(service.__dict__.items())
        next(iterator)  # Metadata
        for attr, value in iterator:
            if attr == "user_email":
                attr = "user"
            if attr not in info.keys():
                info[attr] = value

        n_contracted_service = contracted_service_schema_all.load(info, session=db.session)
        n_contracted_service.save_to_db()
        return {'modified_contract': n_contracted_service.id}, 200
