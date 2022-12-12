from flask import Blueprint, jsonify, request
from marshmallow import validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from werkzeug.exceptions import NotFound, BadRequest, Conflict
from database import db
from sqlalchemy.orm.util import has_identity
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
    print("1")
    info = request.json
    print("2")
    seller_email = Service.get_by_id(ContractedService.get_by_id(info['contracted_service']).service_id).user_email
    print("3")
    client_email = ContractedService.get_by_id(info['contracted_service']).user_email
    #info = {'contracted_service':info['contract_id']}
    print("4")
    info['seller'] = seller_email
    info['client'] = client_email
    print("5")
    same_chat = ChatRoom.get_by_id(info['contracted_service'])

    if same_chat:
        return jsonify({'message': 'error: chat already exists'}), 409
    info['id'] = info['contracted_service']
    info.pop('contracted_service')
    print("HJ")
    try:
        new_room = chat_room_schema_all.load(info, session=db.session)
        print("XA")
        new_room.save_to_db()
        print("XS")
    except Exception as e: print(e)
    return jsonify({'request_id': new_room.id}), 201

@chat_rooms_bp.route("/rooms", methods=["GET"])
@auth.login_required(role=[access[1], access[8], access[9]])
def get_user_chats():
    """
    """
    info = request.json

    resultado = ChatRoom.query.filter(
            or_(ChatRoom.seller_email == g.user.email, ChatRoom.client_email == g.user.email)
        ).order_by(desc(ChatRoom.update)).all()

    return jsonify(chat_room_schema_all.dump(resultado, many=True)), 200