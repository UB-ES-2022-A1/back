from flask import Blueprint, jsonify, request
from marshmallow import validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field
from werkzeug.exceptions import NotFound, BadRequest, Conflict
from database import db
from sqlalchemy.orm.util import has_identity
from sqlalchemy.orm import join
from sqlalchemy import and_, or_, not_, desc
from models.contracted_service import ContractedService
from models.service import Service
from models.user import User
from models.chat_room import ChatRoom
from models.user import auth
from routes.users import get_user
from flask import g
from utils.custom_exceptions import PrivilegeException
from utils.privilegies import access
from database import db
from marshmallow_sqlalchemy.fields import Nested

# Todas las url de servicios contratados empiezan por esto
chat_rooms_bp = Blueprint("chat_room", __name__, url_prefix="/chats")


class ServiceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Service
        load_instance = True


class ContractedServiceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ChatRoom
        load_instance = True

    service = Nested(ServiceSchema(only=('id', 'title')), dump_only=True)


class ChatRoomSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ChatRoom
        include_relationships = True  # Incluir relaciones como la de user
        load_instance = True  # Para que se puedan crear los objetos

    contracted_service = Nested(ContractedServiceSchema(), dump_only=True)


chat_room_schema_all = ChatRoomSchema()
service_schema_all = ServiceSchema()


@chat_rooms_bp.route("/new", methods=["POST"])
@auth.login_required(role=[access[1], access[8], access[9]])
def post_new_chat():
    """
    """
    info = request.json
    seller_email = Service.get_by_id(ContractedService.get_by_id(info['contracted_service']).service_id).user_email
    client_email = ContractedService.get_by_id(info['contracted_service']).user_email
    # info = {'contracted_service':info['contract_id']}
    info['seller'] = seller_email
    info['client'] = client_email

    same_chat = ChatRoom.get_by_id(info['contracted_service'])

    if same_chat:
        return jsonify({'message': 'error: chat already exists'}), 409

    new_room = chat_room_schema_all.load(info, session=db.session)
    new_room.save_to_db()

    return jsonify({'request_id': new_room.id}), 201


@chat_rooms_bp.route("/rooms", methods=["GET"])
@auth.login_required(role=[access[1], access[8], access[9]])
def get_user_chats():
    """
    """
    resultado = ChatRoom.query.filter(
        or_(ChatRoom.seller_email == g.user.email, ChatRoom.client_email == g.user.email)
    ).order_by(desc(ChatRoom.update)).all()
    """resultado = db.session.query(
        Service.title).join(
        ContractedService, Service.id == ContractedService.service_id).join(
        ChatRoom, ChatRoom.id == ContractedService.id
    ).filter(
            or_(ChatRoom.seller_email == g.user.email, ChatRoom.client_email == g.user.email)
        ).order_by(desc(ChatRoom.update)).all()"""

    """resultado = db.session.query(
        ChatRoom).join(ContractedService, ChatRoom.id == ContractedService.id).filter(
            or_(ChatRoom.seller_email == g.user.email, ChatRoom.client_email == g.user.email)
        ).order_by(desc(ChatRoom.update)).all()

    return jsonify([str(type(x.ContractedService.id)) for x in resultado]), 200

    return jsonify(service_schema_all.dump(resultado, many=True)), 200
    #Estoy intentando hacer joins, por eso tengo esto aqui
    """

    return jsonify(chat_room_schema_all.dump(resultado, many=True)), 200
