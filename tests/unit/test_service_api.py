from init_app import init_app
import pytest

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
    # only required
    user1_dict = {'email': 'pepito@gmail.com', 'pwd': '12345678', 'name': 'Pepito'}
    r = client.post("users", json=user1_dict)
    service1_dict = {'title': 'titleT2', 'user': 'pepito@gmail.com', 'description': 'description'}
    r = client.post("services", json=service1_dict)
    assert r.status_code == 200

    # check service has been added correctly
    r = client.get("services")
    assert r.status_code == 200
    services = r.get_json()
    assert len(services) == 1

    # let's check the fields match
    service1_response = services[0]
    assert service1_response['title'] == service1_dict['title']
    assert service1_response['user'] == service1_dict['user']
    assert service1_response['description'] == service1_dict['description']

    # check we can not add service with non existant user
    service1_dict = {'id': 1, 'title': 'titleT2', 'user': 'pepito', 'description': 'descriptionT2', 'price': '10'}
    r = client.post("services", json=service1_dict)
    assert r.status_code == 404

    # check service has not been added
    r = client.get("services")
    assert r.status_code == 200
    services = r.get_json()
    assert len(services) == 1


def test_service_post_missing_fields(client):
    # missing all
    r = client.post("services", json={})
    assert r.status_code == 400
    j = r.get_json()
    assert j['message'] == 'Datos incorrectos'
    assert j['campos']['title'] == ['Missing data for required field.']
    assert j['campos']['description'] == ['Missing data for required field.']

    # missing title
    user1_dict = {'email': 'pepito@gmail.com', 'pwd': '12345678', 'name': 'Pepito'}
    r = client.post("users", json=user1_dict)
    assert r.status_code == 201
    r = client.post("services", json={'user': 'pepito@gmail.com', 'description': 'descriptionT', 'price': '0'})
    assert r.status_code == 400
    j = r.get_json()
    assert j['message'] == 'Datos incorrectos'
    assert 'user' not in j['campos']
    assert 'description' not in j['campos']
    assert 'price' not in j['campos']
    assert j['campos']['title'] == ['Missing data for required field.']

    # missing description
    r = client.post("services", json={'title': 'titleT', 'user': 'pepito@gmail.com', 'price': '0'})
    assert r.status_code == 400
    j = r.get_json()
    assert j['message'] == 'Datos incorrectos'
    assert 'title' not in j['campos']
    assert 'user' not in j['campos']
    assert 'price' not in j['campos']
    assert j['campos']['description'] == ['Missing data for required field.']

    # check no services have been created
    r = client.get("services")
    assert r.status_code == 200
    assert len(r.get_json()) == 0
