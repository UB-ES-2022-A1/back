from flask import Blueprint, jsonify, request, Response
from marshmallow import validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from werkzeug.exceptions import NotFound, Conflict
from database import db

from entities.user import User

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


# Para representar usuario sin exponer info sensible
user_schema_repr = UserSchema(only=("name", "email", "birthday"))

# Para crear usuario
user_schema_create = UserSchema()


@users_bp.route("", methods=["GET"])
def get_all_users():
    all_users = User.query.all()
    return jsonify(user_schema_repr.dump(all_users, many=True)), 200


@users_bp.route("/<string:email>", methods=["GET"])
def get_user(email):
    usr = User.query.get(email)
    if not usr:
        raise NotFound
    return jsonify(user_schema_repr.dump(usr, many=False)), 200


@users_bp.route("", methods=["POST"])
def create_user():
    d = request.json
    new_user = user_schema_create.load(d, session=db.session)

    # si ya existe no se puede
    if User.query.get(new_user.email) is not None:
        raise Conflict

    db.session.add(new_user)
    db.session.commit()
    return Response(status=204)
