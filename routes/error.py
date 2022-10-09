from flask import Blueprint, jsonify
from marshmallow import ValidationError
from werkzeug.exceptions import NotFound, Conflict

error_bp = Blueprint("errors", __name__)


@error_bp.app_errorhandler(Conflict)
def handle_validation(err):
    return jsonify({"message": "el recurso ya existe"}), 409


@error_bp.app_errorhandler(ValidationError)
def handle_validation(err):
    return jsonify({"message": "Datos incorrectos", "campos": err.messages_dict}), 400


# 404 not found
@error_bp.app_errorhandler(NotFound)
def handle_notfound(err):
    return jsonify({"message": "No se ha encontrado el recurso"}), 404


# error genérico. Poner excepciones más concretas por encima de esta.
@error_bp.app_errorhandler(Exception)
def handle_generic_exception(err):
    return jsonify({"message": "error: " + str(err)}), 500
