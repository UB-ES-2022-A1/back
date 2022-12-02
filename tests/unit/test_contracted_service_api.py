from init_app import init_app
import pytest

from utils.secure_request import request_with_login

app, db = init_app("sqlite:///data_test.db")


@pytest.fixture(scope='function', autouse=True)
def client():
    with app.test_request_context():
        db.drop_all()
        db.create_all()
        db.session.commit()
        yield app.test_client()


def test_empty_db_contracted_services(client):
    # check empty database to start
    r = client.get("contracted_services")
    assert r.status_code == 200
    assert len(r.get_json()) == 0


def test_post_get_contracted_service(client):

    # Credentials for user
    email1 = 'pepito@gmail.com'
    pwd1 = '12345678'

    # Only required
    user1_dict = {'email': email1, 'pwd': pwd1, 'name': 'Pepito', 'access': 1}
    r = client.post("users", json=user1_dict)
    assert r.status_code == 201
    service1_dict = {'title': 'titleT2', 'description': 'description', 'price': 1}
    r = request_with_login(login=client.post, request=client.post, url="services", json_r=service1_dict, email=email1, pwd=pwd1)
    assert r.status_code == 200
    c_service1_dict = {'service': 1, 'state': 'active', 'price': 1}
    r = request_with_login(login=client.post, request=client.post, url="contracted_services", json_r=c_service1_dict, email=email1, pwd=pwd1)
    assert r.status_code == 200

    # Check service has been added correctly
    r = client.get("contracted_services")
    assert r.status_code == 200
    services = r.get_json()
    assert len(services) == 1

    # Check we cannot contract without login
    c_service1_dict = {'state': 'active', 'price': 1}
    r = client.post("contracted_services", json=c_service1_dict)
    assert r.status_code == 403


def test_service_post_missing_fields(client):

    # Credentials for user
    email1 = 'pepito@gmail.com'
    pwd1 = '12345678'

    user1_dict = {'email': email1, 'pwd': pwd1, 'name': 'Pepito', 'access': 1}
    r = client.post("users", json=user1_dict)
    assert r.status_code == 201
    service1_dict = {'title': 'titleT2', 'description': 'description', 'price': 1}
    r = request_with_login(login=client.post, request=client.post, url="services", json_r=service1_dict, email=email1,
                           pwd=pwd1)
    assert r.status_code == 200

    # Missing all
    r = request_with_login(login=client.post, request=client.post, url="contracted_services", json_r={}, email=email1, pwd=pwd1)
    assert r.status_code == 400
    j = r.get_json()
    print(j)
    assert j['message'] == 'Datos incorrectos'
    assert j['campos']['state'] == ['Missing data for required field.']

    # check no contracted services have been created
    r = client.get("contracted_services")
    assert r.status_code == 200
    assert len(r.get_json()) == 0
