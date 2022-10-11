from flask import Blueprint, jsonify, request, Response
from marshmallow import validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from werkzeug.exceptions import NotFound, Conflict
from database import db

from entities.service import Service
from entities.user import User

# Todas las url de servicios empiezan por esto
services_bp = Blueprint("services", __name__, url_prefix="/services")


# Validación y serialización de servicios
class ServiceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Service
        include_relationships = True # Incluir relaciones como la de user
        load_instance = True # Para que se puedan crear los objetos


# Para crear servicio
service_schema_all = ServiceSchema()


@services_bp.route("", methods=["GET"])
def get_all_services():
    all_services = Service.query.all()
    return jsonify(service_schema_all.dump(all_services, many=True)), 200


@services_bp.route("/<string:id>", methods=["GET"])
def get_user(id):
    service = Service.query.get(id)
    if not service:
        raise NotFound
    return jsonify(service_schema_all.dump(service, many=False)), 200


@services_bp.route("", methods=["POST"])
def create_service():
    info = request.json
    new_user = service_schema_all.load(info, session=db.session)

    db.session.add(new_user)
    db.session.commit()
    return Response(status=204)
