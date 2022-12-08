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


def test_empty_db_services(client):
    # check empty database to start
    r = client.get("services")
    assert r.status_code == 200
    assert len(r.get_json()) == 0


def test_post_get_service(client):

    # Credentials for user
    email1 = 'pepito@gmail.com'
    pwd1 = '12345678'

    # only required
    user1_dict = {'email': email1, 'pwd': pwd1, 'name': 'Pepito', 'access': 1}
    r = client.post("users", json=user1_dict)
    assert r.status_code == 201
    service1_dict = {'title': 'titleT2', 'description': 'description', 'price': 1}
    r = request_with_login(login=client.post, request=client.post, url="services", json_r=service1_dict, email=email1, pwd=pwd1)
    assert r.status_code == 200

    # check service has been added correctly
    r = client.get("services")
    assert r.status_code == 200
    services = r.get_json()
    assert len(services) == 1

    # let's check the fields match
    service1_response = services[0]
    assert service1_response['title'] == service1_dict['title']
    assert service1_response['description'] == service1_dict['description']

    # check service has not been added
    r = request_with_login(login=client.post, request=client.get, url="services", json_r={}, email=email1, pwd=pwd1)
    assert r.status_code == 200
    services = r.get_json()
    assert len(services) == 1

    # Check we cannot add service without login
    service1_dict = {'title': 'titleT2', 'description': 'descriptionT2', 'price': '10'}
    r = client.post("services", json=service1_dict)
    assert r.status_code == 403


def test_service_post_missing_fields(client):

    # Credentials for user
    email1 = 'pepito@gmail.com'
    pwd1 = '12345678'

    user1_dict = {'email': email1, 'pwd': pwd1, 'name': 'Pepito', 'access': 1}
    r = client.post("users", json=user1_dict)
    assert r.status_code == 201

    # Missing all
    r = request_with_login(login=client.post, request=client.post, url="services", json_r={}, email=email1, pwd=pwd1)
    assert r.status_code == 400
    j = r.get_json()
    assert j['message'] == 'Datos incorrectos'
    assert j['campos']['title'] == ['Missing data for required field.']
    assert j['campos']['description'] == ['Missing data for required field.']

    # Missing title
    r = request_with_login(login=client.post, request=client.post, url="services", json_r={'description': 'descriptionT', 'price': '0'}, email=email1, pwd=pwd1)
    assert r.status_code == 400
    j = r.get_json()
    assert j['message'] == 'Datos incorrectos'
    assert 'description' not in j['campos']
    assert 'price' not in j['campos']
    assert j['campos']['title'] == ['Missing data for required field.']

    # missing description
    r = request_with_login(login=client.post, request=client.post, url="services", json_r={'title': 'titleT', 'price': '0'}, email=email1, pwd=pwd1)
    assert r.status_code == 400
    j = r.get_json()
    assert j['message'] == 'Datos incorrectos'
    assert 'title' not in j['campos']
    assert 'price' not in j['campos']
    assert j['campos']['description'] == ['Missing data for required field.']

    # check no services have been created
    r = client.get("services")
    assert r.status_code == 200
    assert len(r.get_json()) == 0


def test_edit_services(client):

    # Credentials for user
    email1 = 'pepito@gmail.com'
    pwd1 = '12345678'

    user1_dict = {'email': email1, 'pwd': pwd1, 'name': 'Pepito', 'access': 1}
    r = client.post("users", json=user1_dict)
    assert r.status_code == 201

    service1_dict = {'title': 'title 1', 'description': 'description', 'price': 1}
    r = request_with_login(login=client.post, request=client.post, url="services", json_r=service1_dict, email=email1,
                           pwd=pwd1)
    assert r.status_code == 200

    r = client.get("services")
    services = r.get_json()
    response = services[0]
    id = str(response['id'])

    r = client.get("services/search")
    assert r.status_code == 200
    services = r.get_json()
    assert len(services) == 1

    r = request_with_login(login=client.post, request=client.put, url="services/" + id, json_r={'title': 'title 3'},
                           email=email1,
                           pwd=pwd1)
    assert r.status_code == 200


def test_get_many_services(client):

    # Credentials for user
    email1 = 'pepito@gmail.com'
    pwd1 = '12345678'

    user1_dict = {'email': email1, 'pwd': pwd1, 'name': 'Pepito', 'access': 1}
    r = client.post("users", json=user1_dict)
    assert r.status_code == 201

    service1_dict = {'title': 'title 1', 'description': 'description', 'price': 1}
    r = request_with_login(login=client.post, request=client.post, url="services", json_r=service1_dict, email=email1,
                           pwd=pwd1)
    assert r.status_code == 200

    r = client.get("services")
    services = r.get_json()
    response = services[0]
    id = str(response['id'])

    r = client.get("services/search")
    assert r.status_code == 200
    services = r.get_json()
    assert len(services) == 1
    r = request_with_login(login=client.post, request=client.put, url="services/" + id, json_r={'title': 'title 3'}, email=email1,
                           pwd=pwd1)
    assert r.status_code == 200

    service1_dict = {'title': 'title 2', 'description': 'description2', 'price': 1}
    r = request_with_login(login=client.post, request=client.post, url="services", json_r=service1_dict, email=email1,
                           pwd=pwd1)
    assert r.status_code == 200

    search_request = {"search_text": "title", "sort": {"by": "price", "reverse": False}, "filters": {"price": {"min": 0, "max": 200}}}

    r = request_with_login(login=client.post, request=client.get, url="services/search", json_r=search_request, email=email1,
                           pwd=pwd1)
    assert len(r.get_json()) == 2

    r = client.get("services/search")
    assert r.status_code == 200
    services = r.get_json()
    assert len(services) == 2

def test_delete_services(client):

    # Credentials for user
    email1 = 'pepito@gmail.com'
    pwd1 = '12345678'

    user1_dict = {'email': email1, 'pwd': pwd1, 'name': 'Pepito', 'access': 1}
    r = client.post("users", json=user1_dict)
    assert r.status_code == 201

    service1_dict = {'title': 'title 1', 'description': 'description', 'price': 1}
    r = request_with_login(login=client.post, request=client.post, url="services", json_r=service1_dict, email=email1,
                           pwd=pwd1)
    assert r.status_code == 200

    r = client.get("services")
    services = r.get_json()
    response = services[0]
    id = str(response['id'])

    r = request_with_login(login=client.post, request=client.delete, url="services/" + id, json_r={},
                           email=email1,
                           pwd=pwd1)
    assert r.status_code == 200

    r = client.get("services")
    assert r.status_code == 200
    services = r.get_json()
    assert len(services) == 1
    assert services[0]['state'] == 2

    r = client.get("services/search")
    assert r.status_code == 200
    services = r.get_json()
    assert len(services) == 0

def test_disable_services(client):

    # Credentials for user
    email1 = 'pepito@gmail.com'
    pwd1 = '12345678'

    user1_dict = {'email': email1, 'pwd': pwd1, 'name': 'Pepito', 'access': 1}
    r = client.post("users", json=user1_dict)
    assert r.status_code == 201

    service1_dict = {'title': 'title 1', 'description': 'description', 'price': 1}
    r = request_with_login(login=client.post, request=client.post, url="services", json_r=service1_dict, email=email1,
                           pwd=pwd1)
    assert r.status_code == 200

    r = client.get("services")
    services = r.get_json()
    response = services[0]
    id = str(response['id'])

    r = request_with_login(login=client.post, request=client.post, url="services/" + id, json_r={},
                           email=email1,
                           pwd=pwd1)
    assert r.status_code == 200

    r = client.get("services")
    assert r.status_code == 200
    services = r.get_json()
    assert len(services) == 1
    assert services[0]['state'] == 1

    r = client.get("services/search")
    assert r.status_code == 200
    services = r.get_json()
    assert len(services) == 0
