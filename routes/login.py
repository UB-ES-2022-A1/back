from flask import Blueprint, request
from marshmallow import Schema, fields
from werkzeug.exceptions import NotFound
from models.user import User
from marshmallow import ValidationError
from utils.custom_exceptions import EmailNotVerified
from utils.privilegies import access
login_bp = Blueprint("login", __name__, url_prefix="/login")


class LoginSchema(Schema):
    email = fields.Str()
    pwd = fields.Str()


# Para crear usuario
login_schema = LoginSchema()


@login_bp.route("", methods=["POST"])
def login():
    """
    This method logs the user in returning a token.
    """
    data = login_schema.load(request.json)
    user = User.get_by_id(data['email'])
    try:
        if not user:
            raise NotFound("User not found")
        elif not user.verify_password(data['pwd']):
            raise ValidationError("Incorrect email or password")
        elif not user.verified_email:
            raise EmailNotVerified("Verifica tu correo antes!")
        else:
            return {'token': user.generate_auth_token(), 'username': user.name, 'email': user.email, 'rol': access[user.access]}, 200
    except:
        raise ValidationError("Incorrect email or password")