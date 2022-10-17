from flask import Blueprint, jsonify, request
from marshmallow import Schema, fields
from werkzeug.exceptions import NotFound
from models.user import User

login_bp = Blueprint("login", __name__, url_prefix="/login")

class Login_Schema(Schema):
    email = fields.Str()
    pwd = fields.Str()
    pass

# Para crear usuario
login_schema = Login_Schema()

@login_bp.route("", methods=["GET"])
def login():
    data = login_schema.load(request.json)
    usr = User.query.get(data['email'])
    if not usr:
        raise NotFound
    if usr.pwd==data['pwd']:
        return jsonify({'User exists:':usr.email==data['email'],'Password Match:':usr.pwd==data['pwd'],'Name':usr.name})
    else:
        return jsonify({'User exists:':usr.email==data['email'],'Password Match:':usr.pwd==data['pwd']})