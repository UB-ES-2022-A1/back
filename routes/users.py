from flask import Blueprint, jsonify, request, Response
from marshmallow import validates, ValidationError, validate
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from werkzeug.exceptions import NotFound, Conflict
from database import db
from utils.custom_exceptions import PrivilegeException
from models.user import User

# Todas las url de users empiezan por esto
users_bp = Blueprint("users", __name__, url_prefix="/users")


# Validación y serialización de usuarios
class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True

    @validates("phone")
    def validates_phone(self, value):
        if len(str(value)) != 9:
            raise ValidationError("El teléfono tiene que tener 9 dígitos.")

    @validates("pwd")
    def validates_pwd(self, value):
        if len(value) < 5:
            raise ValidationError("Al menos 5 carácteres de contraseña.")

    @validates("email")
    def validates_email(self, value):
        validator = validate.Email()
        return validator(value)

    # TODO remove para crear el admin maximo. Se quita esta función se crea el admin y se vuelve a añadir la función.
    @validates("acces")
    def validates_acces(self, value):
        if value > 5:
            raise PrivilegeException("No se pude crear un usuario con estos privilegios.")


# Para representar usuario sin exponer info sensible
user_schema_repr = UserSchema(only=("name", "email", "birthday"))

# Para crear usuario
user_schema_create = UserSchema()

user_schema_profile = UserSchema(exclude=['pwd'])


@users_bp.route("", methods=["GET"])
def get_all_users():
    all_users = User.query.all()
    return jsonify(user_schema_repr.dump(all_users, many=True)), 200


@users_bp.route("/<string:email>", methods=["GET", "DELETE"])
def get_user(email):
    usr = User.query.get(email)
    if not usr:
        raise NotFound
    if request.method == "DELETE":
        usr.delete_from_db()
        return Response("Se ha eliminado correctamente el usuario con identificador: " + str(email), status=200)

    return jsonify(user_schema_repr.dump(usr, many=False)), 200


@users_bp.route("", methods=["POST"])
def create_user():
    d = request.json
    new_user = user_schema_create.load(d, session=db.session)
    # si ya existe no se puede
    if User.query.get(new_user.email) is not None:
        raise Conflict

    new_user.pwd = User.hash_password(new_user.pwd)
    new_user.save_to_db()
    return jsonify(user_schema_profile.dump(new_user, many=False)), 201


