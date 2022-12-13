from marshmallow import ValidationError

from init_app import init_app
from models.user import User
from routes.users import user_schema_create
from sqlalchemy.exc import IntegrityError
import json

app, db = init_app("sqlite:///data_test.db")


def test_new_user():
    with app.app_context():
        db.create_all()
        User.query.delete()

        user_t = User(email="emailT", pwd="passwordT", name="name")
        user_t.save_to_db()

        assert user_t.email == "emailT"
        assert user_t.name == "name"
        assert user_t.pwd == "passwordT"

def test_get_one_user():
    with app.app_context():
        db.create_all()
        User.query.delete()

        user_t = User(email="emailT", pwd="passwordT", name="name")
        user_t.save_to_db()

        assert user_t.email == "emailT"
        assert user_t.name == "name"
        assert user_t.pwd == "passwordT"

        found = User.get_by_id("emailT")

        assert found.email == "emailT"
        assert found.name == "name"
        assert found.pwd == "passwordT"


def test_existing_user():
    with app.app_context():
        db.create_all()
        User.query.delete()

        user_t = User(email="emailT", pwd="password", name="name")
        user_t2 = User(email="emailT", pwd="password", name="name")

        try:
            user_t.save_to_db()
            user_t2.save_to_db()
            assert False
        except IntegrityError:
            assert True


def test_user_schema():
    with app.app_context():
        db.create_all()
        User.query.delete()

        user_t = User(email="emailT", pwd="abc", name="name")
        user_t.save_to_db()
        request_data = json.loads('{"email":"emailT", "pwd":"password","name":"name"}')

        try:
            user_t2 = user_schema_create.load(request_data, session=db.session)
            assert False
        except ValidationError:
            assert True


def test_delete_user():
    with app.app_context():
        db.create_all()
        User.query.delete()

        user_t = User(email="emailT", pwd="password", name="name")
        user_t.save_to_db()
        user_t.delete_from_db()

        assert len(User.get_all()) == 1
        assert User.get_all()[0].state == 1


def test_hashed_pwd():
    with app.app_context():
        db.create_all()
        User.query.delete()
        user_t = User(email="emailT", pwd=User.hash_password("SUU"), name="name")
        assert user_t.verify_password("SUU")

def test_wallet_user():
    with app.app_context():
        db.create_all()
        User.query.delete()

        user_t = User(email="emailT", pwd="password", name="name")
        if user_t.wallet is None:
            user_t.wallet=0
        user_t.wallet += 2.13
        user_t.save_to_db()