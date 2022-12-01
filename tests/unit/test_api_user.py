from models.user import User
from utils.secure_request import request_with_login
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


def test_empty_db_users(client):
    # check empty database to start
    r = client.get("users")
    assert r.status_code == 200
    assert len(r.get_json()) == 0


def test_post_get_user(client):
    # only required
    user1_dict = {'email': 'pepito@gmail.com', 'pwd': '12345678', 'name': 'Pepito'}
    r = client.post("users", json=user1_dict)
    assert r.status_code == 201

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
    assert r.status_code == 201

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

def test_get_one_user(client):

    r = client.get("users/pepito@gmail.com")
    assert r.status_code == 404

    user1_dict = {'email': 'pepito@gmail.com', 'pwd': '12345678', 'name': 'Pepito'}
    r = client.post("users", json=user1_dict)
    assert r.status_code == 201

    r = request_with_login(login=client.post, request=client.get, url="users/pepito@gmail.com", json_r={}, email='pepito@gmail.com', pwd='12345678')
    assert r.status_code == 200
    assert 'wallet' in r.get_json()
    assert 'wallet' not in client.get("users/pepito@gmail.com").get_json()


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
    assert j['campos']['pwd'] == ['Missing data for required field.']
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


def test_post_bad_privilege_user(client):
    # only required
    user1_dict = {'email': 'pepito@gmail.com', 'pwd': '12345678', 'name': 'Pepito', 'access': 9}
    r = client.post("users", json=user1_dict)
    assert r.status_code == 403


def test_delete_user(client):
    """
    This method tests if a user can delete itself and not other users
    :param client: used for requests.
    """
    email1 = 'pepito1@gmail.com'
    email2 = 'pepito2@gmail.com'
    pwd1 = '12345678'
    pwd2 = 'qqweas'

    # Post of the users.
    user1_dict = {'email': email1, 'pwd': pwd1, 'name': 'Pepito1', 'access': 1}
    r = client.post("users", json=user1_dict)
    assert r.status_code == 201
    user2_dict = {'email': email2, 'pwd': pwd2, 'name': 'Pepito2', 'access': 1}
    r = client.post("users", json=user2_dict)
    assert r.status_code == 201

    # A user only can delete itself
    r = request_with_login(login=client.post, request=client.delete, url="users/"+email1, json_r={}, email=email2, pwd=pwd2)
    assert r.status_code == 403
    r = request_with_login(login=client.post, request=client.delete, url="users/"+email1, json_r={}, email=email1, pwd=pwd1)
    assert r.status_code == 200


def test_admin_delete_user(client):
    """
    This method checks if an admin can delete a user
    :param client: used for requests.
    """
    email_u = 'pepito1@gmail.com'
    email_a = 'admin@gmail.com'
    pwd_u = '12345678'
    pwd_a = 'qqweas'

    # We can create by this way a max admin user
    user_a = User(email=email_a, pwd=User.hash_password(pwd_a), name="MaxAdm", access=9, verified_email=True)
    user_a.save_to_db()

    # Post of the user
    user_dict = {'email': email_u, 'pwd': pwd_u, 'name': 'Pepito1', 'access': 1}
    r = client.post("users", json=user_dict)
    assert r.status_code == 201

    # Then we can do the request with admin privileges.
    r = request_with_login(login=client.post, request=client.delete, url="users/"+email_u, json_r={}, email=email_a, pwd=pwd_a)
    assert r.status_code == 200


def test_admin_privileges_user(client):
    """
    This method tests the correct privilege modification
    :param client: used for requests.
    """
    email_u = 'pepito1@gmail.com'
    email_a = 'admin@gmail.com'
    pwd_u = '12345678'
    pwd_a = 'qqweas'

    # We can create by this way a max admin user
    user_a = User(email=email_a, pwd=User.hash_password(pwd_a), name="MaxAdm", access=9, verified_email=True)
    user_a.save_to_db()

    # Post of the user
    user_dict = {'email': email_u, 'pwd': pwd_u, 'name': 'Pepito1', 'access': 1}
    r = client.post("users", json=user_dict)
    assert r.status_code == 201

    # Normal user can't modify privileges.
    r = request_with_login(login=client.post, request=client.put, url="users/"+email_u+"/privileges/5", json_r={}, email=email_u, pwd=pwd_u)
    assert r.status_code == 403

    # MaxAdmin can modify privileges.
    r = request_with_login(login=client.post, request=client.put, url="users/"+email_u+"/privileges/5", json_r={}, email=email_a, pwd=pwd_a)
    assert r.status_code == 200

    # Bad privilege assignation
    r = request_with_login(login=client.post, request=client.put, url="users/"+email_u+"/privileges/21", json_r={}, email=email_a, pwd=pwd_a)
    assert r.status_code == 400


def test_admin_display_privilege(client):
    """
    This method checks whether admin sees the access and the normal users not
    :param client: used for requests.
    """

    email_a = 'admin@gmail.com'
    pwd_a = 'qqweas'
    email1 = 'pepito1@gmail.com'
    email2 = 'pepito2@gmail.com'
    pwd1 = '12345678'
    pwd2 = 'qqweas'

    # Post of the users.
    user1_dict = {'email': email1, 'pwd': pwd1, 'name': 'Pepito1', 'access': 1}
    r = client.post("users", json=user1_dict)
    assert r.status_code == 201
    user2_dict = {'email': email2, 'pwd': pwd2, 'name': 'Pepito2', 'access': 1}
    r = client.post("users", json=user2_dict)
    assert r.status_code == 201

    # We can create by this way a max admin user
    user_a = User(email=email_a, pwd=User.hash_password(pwd_a), name="MaxAdm", access=9, verified_email=True)
    user_a.save_to_db()

    # Admin can see the access privileges of the user
    r = request_with_login(login=client.post, request=client.get, url="users/"+email1, json_r={}, email=email_a, pwd=pwd_a)
    assert "access" in r.get_json()

    # Normal user cannot see the privileges
    r = request_with_login(login=client.post, request=client.get, url="users/"+email1, json_r={}, email=email1, pwd=pwd1)
    assert "access" not in r.get_json()


def test_put_user(client):

    # only required
    user1_dict = {'email': 'pepito@gmail.com', 'pwd': '12345678', 'name': 'Pepito'}
    r = client.post("users", json=user1_dict)
    assert r.status_code == 201

    # check user has been added correctly
    r = client.get("users")
    assert r.status_code == 200
    users = r.get_json()
    assert len(users) == 1

    # let's check the fields match
    user1_response = users[0]

    # admin datta
    email_a = 'admin@gmail.com'
    pwd_a = 'qqweas'

    # We can create by this way a max admin user
    user_a = User(email=email_a, pwd=User.hash_password(pwd_a), name="MaxAdm", access=9, verified_email=True)
    user_a.save_to_db()

    # displayed fields
    assert user1_response['email'] == user1_dict['email']
    assert user1_response['name'] == user1_dict['name']
    assert user1_response['birthday'] is None

    # Then we can do the request with admin privileges.
    r = request_with_login(login=client.post, request=client.put, url="users/pepito@gmail.com", json_r={'name': 'Pepito2'}, email=email_a, pwd=pwd_a)
    assert r.status_code == 200
    r = client.get("users")
    users = r.get_json()
    user1_response = users[0]
    assert user1_response['name'] == 'Pepito2'

    # user can edit itself
    r = request_with_login(login=client.post, request=client.put, url="users/pepito@gmail.com", json_r={'name': 'Pepito3'}, email='pepito@gmail.com', pwd='12345678')
    assert r.status_code == 200
    r = client.get("users")
    users = r.get_json()
    user1_response = users[0]
    assert user1_response['name'] == 'Pepito3'

    # user can't edit other users
    user1_dict = {'email': 'pepitofalso@gmail.com', 'pwd': '12345678', 'name': 'Pepito'}
    r = client.post("users", json=user1_dict)
    r = request_with_login(login=client.post, request=client.put, url="users/pepito@gmail.com", json_r={'name': 'Pepito3'}, email='pepitofalso@gmail.com', pwd='12345678')
    assert r.status_code == 403

def test_edit_wallet(client):

    # only required
    user1_dict = {'email': 'pepito@gmail.com', 'pwd': '12345678', 'name': 'Pepito'}
    r = client.post("users", json=user1_dict)
    assert r.status_code == 201

    # check user has been added correctly
    r = client.get("users")
    assert r.status_code == 200

    # admin datta
    email_a = 'admin@gmail.com'
    pwd_a = 'qqweas'

    # We can create by this way a max admin user
    user_a = User(email=email_a, pwd=User.hash_password(pwd_a), name="MaxAdm", access=9, verified_email=True)
    user_a.save_to_db()
    users = r.get_json()
    assert len(users) == 1

    # user has 0.00 money by default
    r = request_with_login(login=client.post, request=client.get, url="users/pepito@gmail.com", json_r={}, email=email_a, pwd=pwd_a)
    assert r.status_code == 200
    assert r.get_json()['wallet'] == '0.00'

    # Then we can do the request to add money with admin privileges.
    r = request_with_login(login=client.post, request=client.put, url="users/pepito@gmail.com/wallet", json_r={'money':'20.13'}, email=email_a, pwd=pwd_a)
    assert r.status_code == 200

    r = request_with_login(login=client.post, request=client.get, url="users/pepito@gmail.com", json_r={}, email=email_a, pwd=pwd_a)
    assert r.status_code == 200
    assert r.get_json()['wallet'] == '20.13'

    # Then we can do the request to remove money with admin privileges.
    r = request_with_login(login=client.post, request=client.put, url="users/pepito@gmail.com/wallet", json_r={'money':'-10.13'}, email=email_a, pwd=pwd_a)
    assert r.status_code == 200

    r = request_with_login(login=client.post, request=client.get, url="users/pepito@gmail.com", json_r={}, email=email_a, pwd=pwd_a)
    assert r.status_code == 200
    assert r.get_json()['wallet'] == '10.00'

