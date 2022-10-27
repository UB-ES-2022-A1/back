from flask import Blueprint, jsonify, request
from marshmallow import Schema, fields
from werkzeug.exceptions import NotFound
from models.user import User
from marshmallow import ValidationError

login_bp = Blueprint("login", __name__, url_prefix="/login")


class LoginSchema(Schema):
    email = fields.Str()
    pwd = fields.Str()


# Para crear usuario
login_schema = LoginSchema()


@login_bp.route("", methods=["POST"])
def login():
    data = login_schema.load(request.json)
    user = User.get_by_id(data['email'])
    if not user:
        raise NotFound("User not found")
    elif not user.verify_password(data['pwd']):
        return ValidationError("Incorrect password")
    else:
        return {'token': user.generate_auth_token()}, 200
