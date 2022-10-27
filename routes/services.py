from flask import Blueprint, jsonify, request, Response
from marshmallow import validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from werkzeug.exceptions import NotFound, Conflict
from database import db
from sqlalchemy.orm.util import has_identity
from models.service import Service
from routes.users import get_user

# Todas las url de servicios empiezan por esto
services_bp = Blueprint("services", __name__, url_prefix="/services")


# Validación y serialización de servicios
class ServiceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Service
        include_relationships = True  # Incluir relaciones como la de user
        load_instance = True  # Para que se puedan crear los objetos

    @validates("user")
    def validates_user(self, value):
        if not has_identity(value):
            raise NotFound("Usuario con id " + str(value.email) + " no encontrado!")

    @validates("price")
    def validates_price(self, value):
        if value < 0:
            raise ValidationError("Price can't be negative!")


# Para crear servicio
service_schema_all = ServiceSchema()


@services_bp.route("", methods=["GET"])
def get_all_services():
    all_services = Service.get_all()
    return jsonify(service_schema_all.dump(all_services, many=True)), 200


@services_bp.route("/<int:service_id>", methods=["GET", "PUT", "DELETE"])
def interact_concrete_service(service_id):
    service = Service.get_by_id(service_id)
    # En caso de no encontrar el servicio retornamos un mensaje de error.
    if not service:
        raise NotFound
    if request.method == "GET":
        return jsonify(service_schema_all.dump(service, many=False)), 200
    # TODO una vez haya autentificación que solo pueda acceder el usuario o admins posteriormente.
    elif request.method == "DELETE":
        service.delete_from_db()
        return Response("Se ha eliminado correctamente el servicio con identificador: " + str(service_id), status=200)
    elif request.method == "PUT":
        info = request.json
        iterator = iter(service.__dict__.items())
        next(iterator)  # Metadata
        for attr, value in iterator:
            if attr == "user_email": attr = "user"
            if attr not in info.keys():
                info[attr] = value
        n_service = service_schema_all.load(info, session=db.session)  # De esta forma pasamos todos los constrains.
        n_service.save_to_db()
        return Response("Servicio modificado correctamente", status=200)


@services_bp.route("/<int:service_id>/user", methods=["GET"])
def get_service_user(service_id):
    service = Service.get_by_id(service_id)

    # En caso de no encontrar el servicio retornamos un mensaje de error.
    if not service:
        raise NotFound

    return get_user(service.user.email)


@services_bp.route("/<string:email>/ownservices", methods=["GET"])
def get_user_services(email):
    services = Service.query.filter_by(user_email=email)
    return jsonify(service_schema_all.dump(services, many=True)), 200


@services_bp.route("", methods=["POST"])
def create_service():
    info = request.json  # Leer la info del json
    new_service = service_schema_all.load(info, session=db.session)  # Crear el objeto mediante el schema
    new_service.save_to_db()  # Actualizamos la BD

    return Response("Servicio añadido correctamente con el identificador: " + str(new_service.id), status=200)
