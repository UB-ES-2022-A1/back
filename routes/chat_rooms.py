from flask import Blueprint, jsonify, request
from marshmallow import validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from werkzeug.exceptions import NotFound, BadRequest, Conflict
from database import db
from sqlalchemy.orm.util import has_identity
from sqlalchemy import and_, or_, not_
from models.contracted_service import ContractedService
from models.service import Service
from models.user import User
from models.chat_room import ChatRoom
from models.user import auth
from routes.users import get_user
from flask import g
from utils.custom_exceptions import PrivilegeException
from utils.privilegies import access

# Todas las url de servicios contratados empiezan por esto
chat_rooms_bp = Blueprint("chat_room", __name__, url_prefix="/chats")

class ChatRoomSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ChatRoom
        include_relationships = True  # Incluir relaciones como la de user
        load_instance = True  # Para que se puedan crear los objetos

chat_room_schema_all = ChatRoomSchema()

@chat_rooms_bp.route("/new", methods=["POST"])
@auth.login_required(role=[access[1], access[8], access[9]])
def post_new_chat():
    """
    """
    info = request.json
    seller_email = Service.get_by_id(ContractedService.get_by_id(info['contract_id']).service_id).user_email
    client_email = ContractedService.get_by_id(info['contract_id']).user_email
    info = {'contracted_service':info['contract_id']}
    info['seller'] = seller_email
    info['client'] = client_email

    same_chat = ChatRoom.get_by_id(info['contract_id'])

    if same_chat:
        return jsonify({'message': 'error: chat already exists'}), 409

    new_room = chat_room_schema_all.load(info, session=db.session)
    new_room.save_to_db()

    return jsonify({'message': 'ChatRoom created correctly',
            'request_id': new_room.id}), 201

@chat_rooms_bp.route("/rooms", methods=["GET"])
@auth.login_required(role=[access[1], access[8], access[9]])
def get_user_chats():
    """
    """
    info = request.json

    resultado = (
        ChatRoom.query.filter(
            or_(ChatRoom.seller_email == g.user.email, ChatRoom.client_email == g.user.email)
        )
    ).all()

    return jsonify(resultado), 200