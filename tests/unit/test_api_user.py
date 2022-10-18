from app import app, db
import pytest


@pytest.fixture(scope='function', autouse=True)
def client():
    with app.test_request_context():
        db.drop_all()
        db.create_all()
        db.session.commit()
        yield app.test_client()


def test_empty_db_users(client):
    # check empty database to start
    r = client.get("users")
    assert r.status_code == 200
    assert len(r.get_json()) == 0


def test_post_get_user(client):
    # only required
    user1_dict = {'email': 'pepito@gmail.com', 'pwd': '12345678', 'name': 'Pepito'}
    r = client.post("users", json=user1_dict)
    assert r.status_code == 204

    # check user has been added correctly
    r = client.get("users")
    assert r.status_code == 200
    users = r.get_json()
    assert len(users) == 1

    # let's check the fields match
    user1_response = users[0]

    # displayed fields
    assert user1_response['email'] == user1_dict['email']
    assert user1_response['name'] == user1_dict['name']
    assert user1_response['birthday'] is None

    # sensitive information is not present
    assert 'pwd' not in user1_response
    assert 'address' not in user1_response
    assert 'phone' not in user1_response

    # check we can add user with different email
    user1_dict = {'email': 'pepito2@gmail.com', 'pwd': '12345678', 'name': 'Pepito'}
    r = client.post("users", json=user1_dict)
    assert r.status_code == 204

    # check user has been added correctly
    r = client.get("users")
    assert r.status_code == 200
    users = r.get_json()
    assert len(users) == 2

    # check we can not add user with same email
    user1_dict = {'email': 'pepito@gmail.com', 'pwd': 'aaaaaaaa', 'name': 'La madre de Pepito'}
    r = client.post("users", json=user1_dict)
    assert r.status_code == 409

    # check user has not been added
    r = client.get("users")
    assert r.status_code == 200
    users = r.get_json()
    assert len(users) == 2


def test_user_post_missing_fields(client):
    # missing all
    r = client.post("users", json={})
    assert r.status_code == 400
    j = r.get_json()
    assert j['message'] == 'Datos incorrectos'
    assert j['campos']['pwd'] == ['Missing data for required field.']
    assert j['campos']['email'] == ['Missing data for required field.']
    assert j['campos']['name'] == ['Missing data for required field.']
    assert 'phone' not in j['campos']
    assert 'birthday' not in j['campos']
    assert 'address' not in j['campos']

    # missing name
    r = client.post("users", json={'email': 'pepito@gmail.com', 'pwd': '12345678'})
    assert r.status_code == 400
    j = r.get_json()
    assert j['message'] == 'Datos incorrectos'
    assert 'pwd' not in j['campos']
    assert 'email' not in j['campos']
    assert j['campos']['name'] == ['Missing data for required field.']
    assert 'phone' not in j['campos']
    assert 'birthday' not in j['campos']
    assert 'address' not in j['campos']

    # missing email
    r = client.post("users", json={'pwd': '12345678', 'name': 'pepito'})
    assert r.status_code == 400
    j = r.get_json()
    assert j['message'] == 'Datos incorrectos'
    assert 'pwd' not in j['campos']
    assert j['campos']['email'] == ['Missing data for required field.']
    assert 'name' not in j['campos']
    assert 'phone' not in j['campos']
    assert 'birthday' not in j['campos']
    assert 'address' not in j['campos']

    # missing pwd
    r = client.post("users", json={'email': 'pepito@gmail.com', 'name': 'pepito'})
    assert r.status_code == 400
    j = r.get_json()
    assert j['message'] == 'Datos incorrectos'
    j['campos']['pwd'] == ['Missing data for required field.']
    assert 'email' not in j['campos']
    assert 'name' not in j['campos']
    assert 'phone' not in j['campos']
    assert 'birthday' not in j['campos']
    assert 'address' not in j['campos']

    # check no users have been created
    r = client.get("users")
    assert r.status_code == 200
    assert len(r.get_json()) == 0


def test_user_missing_fields(client):
    # missing all
    r = client.post("users", json={})
    assert r.status_code == 400
    j = r.get_json()
    assert j['message'] == 'Datos incorrectos'

    # missing name
    r = client.post("users", json={'email': 'pepito@gmail.com', 'pwd': '12345678'})
    assert r.status_code == 400

    # missing email
    r = client.post("users", json={'pwd': '12345678', 'name': 'pepito'})
    assert r.status_code == 400

    # missing pwd
    r = client.post("users", json={'email': 'pepito@gmail.com', 'name': 'pepito'})
    assert r.status_code == 400

    # check no users have been created
    r = client.get("users")
    assert r.status_code == 200
    assert len(r.get_json()) == 0


def test_user_post_wrong_fields(client):
    # wrong all
    r = client.post("users", json={'email': 'abduzcan', 'pwd': '1', 'phone': 'aaa', 'name': 'Pepito'})
    assert r.status_code == 400
    j = r.get_json()
    assert j['message'] == 'Datos incorrectos'
    assert 'pwd' in j['campos']
    assert 'email' in j['campos']
    assert 'phone' in j['campos']

    # wrong email
    r = client.post("users", json={'email': 'abduzcan', 'pwd': '12345678', 'phone': '600600600', 'name': 'Pepito'})
    assert r.status_code == 400
    j = r.get_json()
    assert j['message'] == 'Datos incorrectos'
    assert 'pwd' not in j['campos']
    assert 'email' in j['campos']
    assert 'phone' not in j['campos']

    # wrong pwd
    r = client.post("users", json={'email': 'pepito@gmail.com', 'pwd': 'aa', 'phone': '600600600', 'name': 'Pepito'})
    assert r.status_code == 400
    j = r.get_json()
    assert j['message'] == 'Datos incorrectos'
    assert 'pwd' in j['campos']
    assert 'email' not in j['campos']
    assert 'phone' not in j['campos']

    # wrong phone
    r = client.post("users",
                    json={'email': 'pepito@gmail.com', 'pwd': 'aaaaaaaa', 'phone': 'aaaaaaaaa', 'name': 'Pepito'})
    assert r.status_code == 400
    j = r.get_json()
    assert j['message'] == 'Datos incorrectos'
    assert 'pwd' not in j['campos']
    assert 'email' not in j['campos']
    assert 'phone' in j['campos']

    # check no users have been created
    r = client.get("users")
    assert r.status_code == 200
    assert len(r.get_json()) == 0
