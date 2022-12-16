from sqlalchemy.orm.util import has_identity
from flask import Blueprint, jsonify, request
from marshmallow import validates
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from werkzeug.exceptions import NotFound

from database import db
from sqlalchemy import desc
from models.chat_message import ChatMessage
from models.chat_room import ChatRoom
from models.user import auth
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

    @validates("chat_room")
    def validates_chat_room(self, chat_room):
        """
        Validates that the user of the service exists
        :param Cservice: service associated with chat
        :return: None. Raises an Exception
        """
        if not has_identity(chat_room):
            raise NotFound(f'Chat room {chat_room.id} does not exist!')

        Cservice = chat_room.contracted_service

        if Cservice.user_email != g.user.email and Cservice.service.user_email != g.user.email and g.user.access < 8:
            raise PrivilegeException("Not enough privileges to post message.")


chat_message_schema_all = ChatMessageSchema()


@chat_message_bp.route("/new", methods=["POST"])
@auth.login_required(role=[access[1], access[8], access[9]])
def post_new_message():
    """
    """
    info = request.json
    info['user'] = g.user.email

    new_message = chat_message_schema_all.load(info, session=db.session)
    new_message.save_to_db()

    room = new_message.chat_room

    room.update = new_message.time
    room.save_to_db()

    return jsonify({'request_id': new_message.id}), 201


@chat_message_bp.route("/get", methods=["GET", "POST"])
@auth.login_required(role=[access[1], access[8], access[9]])
def get_chat_messages():
    """
    room_id:int, page:int, pagesize:int
    """
    info = request.json
    room_id, page, pagesize = info['room_id'], info['page'], info['pagesize']

    room = ChatRoom.get_by_id(room_id)
    if not room:
        raise NotFound(f'room with id {room_id} not found')

    Cservice = room.contracted_service

    if Cservice.user_email != g.user.email and Cservice.service.user_email != g.user.email and g.user.access < 8:
        raise PrivilegeException("Not enough privileges to post message.")

    resultado = ChatMessage.query.filter(
        ChatMessage.room_id == info['room_id']
    ).order_by(desc(ChatMessage.time)).limit(pagesize).offset(page * pagesize)

    return jsonify(chat_message_schema_all.dump(resultado, many=True)), 200
