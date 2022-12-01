from marshmallow import ValidationError

from init_app import init_app
from models.service import Service
from models.user import User
from models.contracted_service import ContractedService
from routes.contracted_services import contracted_service_schema_all
from sqlalchemy.exc import IntegrityError
import json

app, db = init_app("sqlite:///data_test.db")

def test_new_contract():
    """
    This method tests if a contracted service is added properly to the database
    """
    with app.app_context():
        db.create_all()
        User.query.delete()
        Service.query.delete()

        user_t = User(email="emailT", pwd="passwordT", name="name")
        service_t = Service(title="titleT", user=user_t, description="descriptionT")
        contract_t = ContractedService(user=user_t, service=service_t, state="active")
        user_t.save_to_db()
        service_t.save_to_db()

        assert contract_t.user_email == "emailT"
        assert contract_t.state == "active"
        assert contract_t.service_id == 1


def test_non_existing_user():
    """
    This method check if a contracted service can be added to non existing user
    """
    with app.app_context():
        db.create_all()
        User.query.delete()
        Service.query.delete()
        ContractedService.query.delete()

        user_t = User(email="emailT", pwd="password", name="name")
        user_t.save_to_db()
        serviceT = Service(title="titleT", user=user_t, description="descriptionT")
        serviceT.save_to_db()
        user_t.delete_from_db()
        serviceT.delete_from_db()

        try:
            request_data = json.loads('{"user":"emailT", "service":"1","state":"active"}')
            contract_t = contracted_service_schema_all.load(request_data, session=db.session)
            contract_t.save_to_db()
            assert False
        except:
            assert True


def test_schema():
    """
    THis method checks if the marshmallow schema works well.
    """
    with app.app_context():
        db.create_all()
        User.query.delete()
        Service.query.delete()
        ContractedService.query.delete()

        user_t = User(email="emailT", pwd="password", name="name")
        user_t.save_to_db()
        serviceT = Service(title="titleT", user=user_t, description="descriptionT",)
        serviceT.save_to_db()
        request_data = json.loads('{"user":"emailT", "service":"1"}')
        contract_t = contracted_service_schema_all.load(request_data, session=db.session)
        contract_t.save_to_db()

        assert contract_t.state == "on process"


def test_delete_cascade():
    """
    This method checks if the cascade deletions work well.
    """
    with app.app_context():
        db.create_all()
        User.query.delete()
        Service.query.delete()
        ContractedService.query.delete()
        user_t = User(email="emailT", pwd="password", name="name")
        user_t.save_to_db()
        service_t = Service(title="titleT", user=user_t, description="descriptionT")
        service_t.save_to_db()
        contract_t = ContractedService(user=user_t, service=service_t, state="active")

        contract_t.save_to_db()
        contract_t.delete_from_db()

        # Comprovamos que al borrar el contrato y el servicio siguen existiendo
        assert User.query.all()[0].email == "emailT"

        assert Service.query.all()[0].title == "titleT"

        contract_t = ContractedService(user=user_t, service=service_t, state="active")
        user_t.delete_from_db()
        service_t.delete_from_db()

        # Comprovamos que al borrarse un usuario y un servicio se borren sus servicios contratados
        assert len(User.query.all()) == 0
        assert len(Service.query.all()) == 0
        assert len(ContractedService.query.all()) == 0
