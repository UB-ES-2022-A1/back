from flask import Blueprint, jsonify, request
from marshmallow import validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from werkzeug.exceptions import NotFound, BadRequest, Conflict
from database import db
from sqlalchemy.orm.util import has_identity
from sqlalchemy import and_, or_, not_, desc, asc
from models.contracted_service import ContractedService
from models.service import Service
from models.user import User
from models.chat_room import ChatRoom
from models.chat_message import ChatMessage
from models.user import auth
from routes.users import get_user
from flask import g
from utils.custom_exceptions import PrivilegeException
from utils.privilegies import access

# Todas las url de servicios contratados empiezan por esto
chat_message_bp = Blueprint("chat_message", __name__, url_prefix="/messages")

class ChatMessageSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ChatMessage
        include_relationships = True  # Incluir relaciones como la de user
        load_instance = True  # Para que se puedan crear los objetos

chat_message_schema_all = ChatMessageSchema()

@chat_message_bp.route("/new", methods=["POST"])
@auth.login_required(role=[access[1], access[8], access[9]])
def post_new_message():
    """
    """
    info = request.json
    info['user'] = g.user.email

    room = ChatRoom.get_by_id(info['chat_room'])

    if not room:
        return jsonify({'message': 'error: chat room not found'}), 404

    new_message = chat_message_schema_all.load(info, session=db.session)
    new_message.save_to_db()

    room.update = new_message.time
    room.save_to_db()

    return jsonify({'request_id': new_message.id}), 201

@chat_message_bp.route("/get", methods=["GET"])
@auth.login_required(role=[access[1], access[8], access[9]])
def get_chat_messages():
    """
    room_id:int, page:int, pagesize:int
    """
    info = request.json
    room_id, page, pagesize = info['room_id'], info['page'], info['pagesize']

    resultado = ChatMessage.query.filter(
        ChatMessage.room_id == info['room_id']
    ).order_by(desc(ChatMessage.time)).limit(pagesize).offset(page * pagesize)

    return jsonify(chat_message_schema_all.dump(resultado, many=True)), 200