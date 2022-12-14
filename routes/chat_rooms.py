from flask import Blueprint, jsonify, request
from marshmallow import validates
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field
from sqlalchemy import or_, desc
from werkzeug.exceptions import NotFound

from models.contracted_service import ContractedService
from models.service import Service
from models.chat_room import ChatRoom
from models.user import auth
from flask import g

from utils.custom_exceptions import PrivilegeException
from utils.privilegies import access
from database import db
from marshmallow_sqlalchemy.fields import Nested
from sqlalchemy.orm.util import has_identity

# Todas las url de servicios contratados empiezan por esto
chat_rooms_bp = Blueprint("chat_room", __name__, url_prefix="/chats")


class ServiceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Service
        load_instance = True

    user = auto_field()


class ContractedServiceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ContractedService
        load_instance = True

    service = Nested(ServiceSchema(only=('id', 'title', 'user')), dump_only=True)
    user = auto_field()


class ChatRoomSchema_dump(SQLAlchemyAutoSchema):
    class Meta:
        model = ChatRoom
        include_relationships = True  # Incluir relaciones como la de user
        load_instance = True  # Para que se puedan crear los objetos

    contracted_service = Nested(ContractedServiceSchema())


class ChatRoomSchema_load(SQLAlchemyAutoSchema):
    class Meta:
        model = ChatRoom
        include_relationships = True  # Incluir relaciones como la de user
        load_instance = True  # Para que se puedan crear los objetos

    @validates("contracted_service")
    def validates_contracted_service(self, Cservice):
        """
        Validates that the user of the service exists
        :param Cservice: service associated with chat
        :return: None. Raises an Exception
        """
        if not has_identity(Cservice):
            raise NotFound(f"Contrato con id {Cservice.id} no encontrado!")

        if Cservice.user_email != g.user.email and Cservice.service.user_email != g.user.email and g.user.access < 8:
            raise PrivilegeException("Not enough privileges to create chats for other user's contracts.")


chat_room_schema_dump = ChatRoomSchema_dump()
chat_room_schema_load = ChatRoomSchema_load()

service_schema_all = ServiceSchema()


@chat_rooms_bp.route("/new", methods=["POST"])
@auth.login_required(role=[access[1], access[8], access[9]])
def post_new_chat():
    """
    """
    info = request.json
    same_chat = ChatRoom.get_by_id(info['contracted_service'])

    if same_chat:
        return jsonify({'message': 'error: chat already exists'}), 409

    new_room = chat_room_schema_load.load(info, session=db.session)
    new_room.save_to_db()
    return jsonify({'request_id': new_room.id}), 201


@chat_rooms_bp.route("/rooms", methods=["GET"])
@auth.login_required(role=[access[1], access[8], access[9]])
def get_user_chats():
    resultado = ChatRoom.query.join(ContractedService).join(Service).filter(
        or_(
            ContractedService.user_email == g.user.email,
            Service.user_email == g.user.email
        )
    ).order_by(desc(ChatRoom.update)).all()

    return jsonify(chat_room_schema_dump.dump(resultado, many=True)), 200
