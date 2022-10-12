from flask import jsonify
from marshmallow import ValidationError
from models.service import Service
from models.user import User
from routes.services import service_schema_all
from app import app
from database import db
from sqlalchemy.exc import IntegrityError
import json


def test_new_service():
    with app.app_context():
        db.create_all()
        User.query.delete()
        Service.query.delete()

        user_t = User(email="emailT", pwd="passwordT", name="name")
        service_t = Service(title="titleT", user=user_t, description="descriptionT", price=0)
        user_t.save_to_db()
        service_t.save_to_db()

        assert service_t.user_email == "emailT"
        assert service_t.price == 0
        assert service_t.title == "titleT"
        assert service_t.description == "descriptionT"


def test_existing_service():
    with app.app_context():
        db.create_all()
        User.query.delete()
        Service.query.delete()

        user_t = User(email="emailT", pwd="password", name="name")
        service_t = Service(title="titleT", user=user_t, description="descriptionT", price=0)
        service_t2 = Service(title="titleT", user=user_t, description="descriptionT", price=0)
        try:
            user_t.save_to_db()
            service_t.save_to_db()
            service_t2.save_to_db()
            assert False
        except IntegrityError:
            assert True


def test_non_existing_user():
    with app.app_context():
        db.create_all()
        User.query.delete()
        Service.query.delete()

        user_t = User(email="emailT", pwd="password", name="name")
        user_t.save_to_db()
        user_t.delete_from_db()  # No se puede añadir un servicio si no existe el usuario.

        try:
            request_data = json.loads('{"title":"titleT", "user":"emailT","description":"descriptionT", "price":"0"}')
            service_t = service_schema_all.load(request_data, session=db.session)
            service_t.save_to_db()
            assert False
        except:
            assert True


def test_schema():
    with app.app_context():
        db.create_all()
        User.query.delete()
        Service.query.delete()

        user_t = User(email="emailT", pwd="password", name="name")
        user_t.save_to_db()
        request_data = json.loads('{"title":"titleT", "user":"emailT","description":"descriptionT", "price":"0"}')
        serviceT = service_schema_all.load(request_data, session=db.session)
        serviceT.save_to_db()
        assert serviceT.title == "titleT"

        request_data2 = json.loads('{"title":"titleT2", "user":"emailT","description":"descriptionT", "price":"-10"}')
        # No debería de funcionar ya que el precio es negativo
        try:
            service_t2 = service_schema_all.load(request_data2, session=db.session)
            assert False
        except ValidationError:
            assert True


def test_delete_cascade():
    with app.app_context():
        db.create_all()
        User.query.delete()
        Service.query.delete()
        user_t = User(email="emailT", pwd="password", name="name")
        service_t = Service(title="titleT", user=user_t, description="descriptionT", price=0)
        service_t.save_to_db()
        service_t.delete_from_db()

        # Comprovamos que al borrar el servicio el usuario sigue existiendo
        assert User.query.all()[0].email == "emailT"

        service_t = Service(title="titleT", user=user_t, description="descriptionT", price=0)
        user_t.delete_from_db()

        # Comprovamos que al borrarse un usuario se borren sus servicios
        assert len(User.query.all()) == 0