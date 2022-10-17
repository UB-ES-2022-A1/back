from app import app, db
import pytest

from models.service import Service
from models.user import User


@pytest.fixture
def client():

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            User.query.delete()
            Service.query.delete()
        yield client

def test_user_create(client):

    r1 = client.get("users")
    assert len(r1.get_json()) == 0

    r2 = client.post("users", json={})
    assert  r2.status_code == 400


