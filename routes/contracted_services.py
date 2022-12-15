import json

from flask import Blueprint, jsonify, request
from marshmallow import validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, fields
from werkzeug.exceptions import NotFound, BadRequest, Conflict
from database import db
from sqlalchemy.orm.util import has_identity
from models.contracted_service import ContractedService
from models.service import Service
from models.user import User
from models.user import auth
from routes.chat_rooms import chat_room_schema_load
from routes.users import get_user
from flask import g
from utils.custom_exceptions import PrivilegeException, SelfBuyException
from utils.privilegies import access
from routes.services import service_schema_all
from models.transactions import Transaction
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
            raise NotFound("User with id " + str(value.email) + " not found!")




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

    info = contracted_service_schema_all.dump(Cservice, many=False)
    info2 = service_schema_all.dump(Service.get_by_id(info['service']))

    info["title"] = info2["title"]
    info["description"] = info2["description"]
    info["price"] = info2["price"]
    info["user_buyer_email"] = info["user"]
    info["user_seller_email"] = info2["user"]
    info["user_buyer_name"] = User.get_by_id(info["user_buyer_email"]).name
    info["user_seller_name"] = User.get_by_id(info["user_seller_email"]).name
    info["contract_id"] = info["id"]
    info["service_id"] = info["service"]
    info.pop("service")
    info.pop("id")
    info.pop("user")

    return jsonify(info), 200

@contracted_services_bp.route("/<int:contracted_service_id>/user", methods=["GET"])
@auth.login_required(role=[access[1], access[8], access[9]])
def get_contracted_service_user(contracted_service_id):
    """
    This method returns the user of a contract. It requires to be admin or be a part of the contract
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
    Return all the services that a user has contracted
    :param email: the email of the client
    :return: all the contracts the client has ordered
    """

    if email != g.user.email and g.user.access < 8:
        raise PrivilegeException("Not enough privileges to access other users' contracts.")

    contracts = contracted_service_schema_all.dump(ContractedService.query.filter_by(user_email=email).all(), many=True)
    for id_c, contract in enumerate(contracts):
        contracts[id_c] = json.loads(get_contracted_service(contract["id"])[0].get_data().decode("utf-8"))

    return jsonify(contracts), 200


@contracted_services_bp.route("/contractor/<string:email>", methods=["GET"])
@auth.login_required(role=[access[1], access[8], access[9]])
def get_contractor_offered_contracts(email):
    """
    :param email: the email of the contractor
    :return: all the contracts the contractor has been offered, regardless of wether they have accepted
    """
    if email != g.user.email and g.user.access < 8:
        raise PrivilegeException("Not enough privileges to access other users' contracts.")

    contracts = contracted_service_schema_all.dump(ContractedService.query.filter(ContractedService.service.has(user_email=email)).all(), many=True)
    for id_c, contract in enumerate(contracts):
        contracts[id_c] = json.loads(get_contracted_service(contract["id"])[0].get_data().decode("utf-8"))

    return jsonify(contracts), 200


@contracted_services_bp.route("", methods=["POST"])
@auth.login_required(role=[access[1], access[8], access[9]])
def contract_service():
    """
    This method contracts a new service. Requires a token of a user to do the post.
    :return: Response
    """
    info = request.json  # Leer la info del json
    info["user"] = g.user.email
    if 'service' not in info:
        raise ValidationError({'service': ['Missing data for required field.']})
    if Service.get_by_id(info['service']).user_email == g.user.email:
        raise SelfBuyException("Cannot buy your own product.")
    new_contracted_service = contracted_service_schema_all.load(info, session=db.session)
    p = new_contracted_service.service.price
    w = g.user.wallet
    updated_w = w - p
    if updated_w < 0:
        return {'reason': 'Not enough funds'}, 400
    usr = User.query.get(g.user.email)
    usr.wallet = updated_w
    usr.save_to_db()
    new_contracted_service.save_to_db()
    transaction = Transaction(user_email=g.user.email, description="Service bought: " + new_contracted_service.service.title,
                              number=g.user.number_transactions, quantity=-p, wallet=g.user.wallet)
    transaction.save_to_db()
    g.user.number_transactions += 1
    g.user.save_to_db()

    new_room = chat_room_schema_load.load({'contracted_service':new_contracted_service.id}, session=db.session)
    new_room.save_to_db()

    return {'request_id': new_contracted_service.id}, 201


@contracted_services_bp.route("/<int:contract_id>/accept", methods=["POST"])
@auth.login_required(role=[access[1], access[8], access[9]])
def accept(contract_id):
    """
    This method is used to accept a contract. Must be used by the seller
    :param contract_id:
    :return:
    """
    contract, service, user_client, user_seller= check(contract_id)
    if not contract.state == 0:
        raise Conflict("contract is not acceptable because it already was accepted or canceled!")

    if service.user_email != g.user.email and g.user.access < 8:
        raise PrivilegeException("Not enough privileges to modify other resources.")

    contract.state = 1
    contract.save_to_db()
    return {'status': 'State updated successfully'}, 200

@contracted_services_bp.route("/<int:contract_id>/validate", methods=["POST"])
@auth.login_required(role=[access[1], access[8], access[9]])
def validate_contract(contract_id):
    """
    THis method validates the contract. If the contract has been validated by both client and seller it updates the state.
    Can be used by the seller or the client
    :param contract_id: Contract id
    :return: Response
    """
    contract, service, user_client, user_seller = check(contract_id)
    if not contract.state == 1:
        raise Conflict('The contract cannot be validated as it was not accepted or was cancelled')
    email = g.user.email
    if email == service.user_email:
        contract.validate_s = True
    elif email == contract.user_email:
        contract.validate_c = True
    elif g.user.acces >= 8:
        contract.validate_s = True
        contract.validate_c = True
    else:
        raise PrivilegeException("Not enough privileges to modify other resources.")
    if contract.validate_s and contract.validate_c:
        contract.state = 2
        user_seller.wallet += service.price
        user_seller.save_to_db()
        transaction = Transaction(user_email=user_seller.email,
                                  description="Service sold: " + contract.service.title,
                                  number=user_seller.number_transactions, quantity=service.price, wallet=user_seller.wallet)
        transaction.save_to_db()
        user_seller.number_transactions += 1
        user_seller.save_to_db()
    contract.save_to_db()
    return {'status': 'State updated successfully'}, 200


@contracted_services_bp.route("/<int:contract_id>", methods=["DELETE"])
@auth.login_required(role=[access[1], access[8], access[9]])
def delete_contracted_service(contract_id):
    """
    This method is used to cancel a contract
    :param contract_id: The service that is going to be treated
    :return: Response
    """
    contract, service, user_client, user_seller = check(contract_id)
    # No privileges
    if service.user_email != g.user.email and g.user.access < 8 and contract.user_email != g.user.email:
        raise PrivilegeException("Not enough privileges to modify other resources.")
    if contract.state == 2:
        raise Conflict('The contract cannot be cancelled as it was already completed')
    contract.state = 3
    contract.save_to_db()
    user_client.wallet += service.price
    user_client.save_to_db()
    return_cancelled_service(contract.service.title, contract.service.price, user_seller)
    return {'cancelled_contract': contract_id}, 200


def check(contract_id):
    """
    Support method used to check the database and the security
    :param contract_id: the id of the contract that is going to be accessed.
    :return: the contract and the service if all is correct.
    """

    contract = ContractedService.get_by_id(contract_id)
    service = Service.get_by_id(contract.service_id)

    # No contract
    if not contract:
        raise NotFound("Contract not found.")

    # No service
    if not service:
        contract.state = 3
        contract.save_to_db()
        raise NotFound("Service not found. Contract cancelled.")

    user_seller = User.get_by_id(service.user_email)
    user_client = User.get_by_id(contract.user_email)

    if not user_client and not user_seller:
        contract.state = 3
        contract.save_to_db()
        raise NotFound("Both users of the contract have been deleted. Contract cancelled.")

    if not user_seller:
        user_client.wallet += service.price
        user_client.save_to_db()
        contract.state = 3
        contract.save_to_db()
        return_cancelled_service(contract.service.title, contract.service.price, user_client)
        raise NotFound("Seller has been deleted. Contract cancelled.")

    if not user_client:
        user_seller.wallet += service.price
        user_seller.save_to_db()
        contract.state = 3
        contract.save_to_db()
        return_cancelled_service(contract.service.title, contract.service.price, user_seller)
        raise NotFound("Client has been deleted. Contract cancelled.")

    return contract, service, user_client, user_seller


def return_cancelled_service(name, price, user_client):
    transaction = Transaction(user_email=user_client.email, description="Service cancelled: " + name,
                              number=user_client.number_transactions, quantity=price, wallet=user_client.wallet)
    transaction.save_to_db()
    user_client.number_transactions += 1
    user_client.save_to_db()
