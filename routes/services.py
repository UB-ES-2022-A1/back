from flask import Blueprint, jsonify, request, Response
from marshmallow import validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from werkzeug.exceptions import NotFound, Conflict
from database import db

from sqlalchemy.orm.util import has_identity
from entities.service import Service

# Todas las url de servicios empiezan por esto
services_bp = Blueprint("services", __name__, url_prefix="/services")


# Validación y serialización de servicios
class ServiceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Service
        include_relationships = True  # Incluir relaciones como la de user
        load_instance = True  # Para que se puedan crear los objetos

    @validates("user")
    def validates_pwd(self, value):
        if not has_identity(value):
            raise NotFound("Usuario con id " + str(value.email) + " no encontrado!")


# Para crear servicio
service_schema_all = ServiceSchema()


@services_bp.route("", methods=["GET"])
def get_all_services():
    all_services = Service.get_all()
    return jsonify(service_schema_all.dump(all_services, many=True)), 200


@services_bp.route("/<int:service_id>", methods=["GET"])
def get_service(service_id):
    service = Service.get_by_id(service_id)

    # En caso de no encontrar el servicio retornamos un mensaje de error.
    if not service:
        raise NotFound

    return jsonify(service_schema_all.dump(service, many=False)), 200


@services_bp.route("", methods=["POST"])
def create_service():
    info = request.json  # Leer la info del json
    new_service = service_schema_all.load(info, session=db.session)  # Crear el objeto mediante el schema
    new_service.save_to_db()  # Actualizamos la BD

    return Response("Servicio añadido correctamente con el identificador: " + str(new_service.id), status=200)
