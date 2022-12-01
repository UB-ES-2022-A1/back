import populate_db
from init_app import init_app
import pytest

from utils.secure_request import request_with_login

app, db = init_app("sqlite:///data_test.db")


@pytest.fixture(scope='function', autouse=True)
def client():
    with app.test_request_context():
        db.drop_all()
        db.create_all()
        populate_db.populate(db)
        db.session.commit()
        yield app.test_client()


def test_empty_db_contracted_services(client):
    # check empty database to start
    r = request_with_login(login=client.post, request=client.get, url="contracted_services", json_r={},
                           email="madmin@gmail.com", pwd="password")
    assert r.status_code == 200
    assert len(r.get_json()) == 0


def test_post_get_contracted_service(client):
    # Credentials for contractor
    email1 = 'pepito@gmail.com'
    pwd1 = '12345678'
    user1_dict = {'email': email1, 'pwd': pwd1, 'name': 'Pepito', 'access': 1}
    r = client.post("users", json=user1_dict)
    assert r.status_code == 201

    # Credentials for client
    email2 = 'pepita@gmail.com'
    pwd2 = '12345678'
    user2_dict = {'email': email2, 'pwd': pwd2, 'name': 'Pepita', 'access': 1}
    r = client.post("users", json=user2_dict)
    assert r.status_code == 201

    # Post a service
    service1_dict = {'title': 'titleT2', 'description': 'description', 'price': 1}
    r = request_with_login(login=client.post, request=client.post, url="services", json_r=service1_dict, email=email1,
                           pwd=pwd1)
    assert r.status_code == 200

    service_id = int(r.text.split()[-1])

    # User2 requests the service
    c_service1_dict = {'service': service_id, 'state': 'active', 'price': 1}
    r = request_with_login(login=client.post, request=client.post, url="contracted_services", json_r=c_service1_dict,
                           email=email2, pwd=pwd2)
    assert r.status_code == 201

    # Check the client can see the service
    r = request_with_login(login=client.post, request=client.get, url=f"contracted_services/client/{email2}",
                           json_r={}, email=email2, pwd=pwd2)

    assert r.status_code == 200
    contracts = r.get_json()
    assert len(contracts) == 1

    # Check the contractor can see the service
    r = request_with_login(login=client.post, request=client.get, url=f"contracted_services/contractor/{email1}",
                           json_r={}, email=email1, pwd=pwd1)
    assert r.status_code == 200
    contracts = r.get_json()
    assert len(contracts) == 1

    # Check we can't see others' contracts
    r = request_with_login(login=client.post, request=client.get, url=f"contracted_services/contractor/{email1}",
                           json_r={}, email=email2, pwd=pwd2)
    assert r.status_code == 403

    # Check the client can see the service
    r = request_with_login(login=client.post, request=client.get, url=f"contracted_services/client/{email2}",
                           json_r={}, email=email1, pwd=pwd1)

    assert r.status_code == 403

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
    r = request_with_login(login=client.post, request=client.post, url="contracted_services", json_r={}, email=email1,
                           pwd=pwd1)
    assert r.status_code == 400
    j = r.get_json()
    print(j)
    assert j['message'] == 'Datos incorrectos'
    assert j['campos']['service'] == ['Missing data for required field.']

    # check no contracted services have been created
    r = request_with_login(login=client.post, request=client.get, url=f"contracted_services/client/{email1}",
                           json_r={}, email=email1, pwd=pwd1)
    assert r.status_code == 200
    assert len(r.get_json()) == 0


def test_service_mark_done(client):
    # Credentials for contractor
    email1 = 'pepito@gmail.com'
    pwd1 = '12345678'
    user1_dict = {'email': email1, 'pwd': pwd1, 'name': 'Pepito', 'access': 1}
    r = client.post("users", json=user1_dict)
    assert r.status_code == 201

    # Credentials for client
    email2 = 'pepita@gmail.com'
    pwd2 = '12345678'
    user2_dict = {'email': email2, 'pwd': pwd2, 'name': 'Pepita', 'access': 1}
    r = client.post("users", json=user2_dict)
    assert r.status_code == 201

    # Post a service
    service1_dict = {'title': 'titleT2', 'description': 'description', 'price': 1}
    r = request_with_login(login=client.post, request=client.post, url="services", json_r=service1_dict, email=email1,
                           pwd=pwd1)
    assert r.status_code == 200

    service_id = int(r.text.split()[-1])


    # User2 requests the service
    c_service1_dict = {'service': service_id, 'state': 'active', 'price': 1}
    r = request_with_login(login=client.post, request=client.post, url="contracted_services", json_r=c_service1_dict,
                           email=email2, pwd=pwd2)
    assert r.status_code == 201

    # Check the client can see the service
    r = request_with_login(login=client.post, request=client.get, url=f"contracted_services/client/{email2}",
                           json_r={}, email=email2, pwd=pwd2)

    assert r.status_code == 200
    contracts = r.get_json()
    assert len(contracts) == 1

    # Check the contractor can see the service
    r = request_with_login(login=client.post, request=client.get, url=f"contracted_services/contractor/{email1}",
                           json_r={}, email=email1, pwd=pwd1)
    assert r.status_code == 200
    contracts = r.get_json()
    assert len(contracts) == 1
    cstate = contracts[0]['state']
    cid = contracts[0]['id']
    assert cstate == 'active'

    # Check the contractor cant mark the contract as done
    r = request_with_login(login=client.post, request=client.put, url=f"contracted_services/{cid}/done",
                           json_r={}, email=email2, pwd=pwd2)
    assert r.status_code != 200

    # Check the contracted can mark the contract as done
    r = request_with_login(login=client.post, request=client.put, url=f"contracted_services/{cid}/done",
                           json_r={}, email=email1, pwd=pwd1)
    assert r.status_code == 200


    # Check the contractor can see the service
    r = request_with_login(login=client.post, request=client.get, url=f"contracted_services/contractor/{email1}",
                           json_r={}, email=email1, pwd=pwd1)
    assert r.status_code == 200
    contracts = r.get_json()
    cstate = contracts[0]['state']
    assert cstate == 'done'

