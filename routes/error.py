from sqlite3 import IntegrityError
from flask import Blueprint, jsonify
from marshmallow import ValidationError
from werkzeug.exceptions import NotFound, Conflict, BadRequest
from sqlalchemy.exc import IntegrityError
from utils.custom_exceptions import PrivilegeException, NotAcceptedPrivilege, EmailNotVerified

error_bp = Blueprint("errors", __name__)


@error_bp.app_errorhandler(Conflict)
def handle_conflict(err):
    return jsonify({"message": "El recurso ya existe" + str(err)}), 409


@error_bp.app_errorhandler(ValidationError)
def handle_validation(err):
    return jsonify({"message": "Datos incorrectos", "campos": err.messages}), 400


# 404 not found
@error_bp.app_errorhandler(NotFound)
def handle_notfound(err):
    return jsonify({"message": err.description}), 404


@error_bp.app_errorhandler(BadRequest)
def handle_notfound(err):
    return jsonify({"message": err.description}), 400


# Error de integridad de la base de datos
@error_bp.app_errorhandler(IntegrityError)
def handle_integrity_exception(err):
    atributes = err.args[0].split("failed:")[1]
    return jsonify({"message": "Duplicated instance found, change one of the following atributs: " + atributes}), 409


# Error de privilegios
@error_bp.app_errorhandler(PrivilegeException)
def handle_privilege_exception(err):
    return jsonify({"message": str(err)}), 403


# Error al dar privilegios no acceptados.
@error_bp.app_errorhandler(NotAcceptedPrivilege)
def handle_not_accepted_privilege_exception(err):
    return jsonify({"message": str(err)}), 400


# Error al acceder sin tener el mail verificado.
@error_bp.app_errorhandler(EmailNotVerified)
def handle_email_not_verified(err):
    return jsonify({"message": str(err)}), 400


# Error genérico. Poner excepciones más concretas por encima de esta.
@error_bp.app_errorhandler(Exception)
def handle_generic_exception(err):
    return jsonify({"message": "error: " + str(err)}), 500
