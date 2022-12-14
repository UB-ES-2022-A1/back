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

    r = request_with_login(login=client.post, request=client.put, url=f"users/{email2}/wallet", json_r={'money': 5},
                           email="madmin@gmail.com", pwd="password")

    assert r.status_code == 200

    # Post a service
    service1_dict = {'title': 'titleT2', 'description': 'description', 'price': 1}
    r = request_with_login(login=client.post, request=client.post, url="services", json_r=service1_dict, email=email1,
                           pwd=pwd1)
    assert r.status_code == 200

    service_id = r.get_json()['added_service_id']

    # User2 requests the service
    c_service1_dict = {'service': service_id}
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
    c_service1_dict = {'service': service_id}
    r = client.post("contracted_services", json=c_service1_dict)
    assert r.status_code == 403


def post_insufficient_funds(client):
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

    r = request_with_login(login=client.post, request=client.put, url=f"users/{email2}/wallet", json_r={'money': 19},
                           email="madmin@gmail.com", pwd="password")

    assert r.status_code == 200

    # Post a service
    service1_dict = {'title': 'titleT2', 'description': 'description', 'price': 10}
    r = request_with_login(login=client.post, request=client.post, url="services", json_r=service1_dict, email=email1,
                           pwd=pwd1)
    assert r.status_code == 200

    service_id = int(r.text.split()[-1])

    # User2 requests the service
    c_service1_dict = {'service': service_id}

    r = request_with_login(login=client.post, request=client.post, url="contracted_services", json_r=c_service1_dict,
                           email=email2, pwd=pwd2)
    assert r.status_code == 201

    # Check the client can see the service
    r = request_with_login(login=client.post, request=client.get, url=f"contracted_services/client/{email2}",
                           json_r={}, email=email2, pwd=pwd2)

    assert r.status_code == 200
    contracts = r.get_json()
    assert len(contracts) == 1

    r = request_with_login(login=client.post, request=client.post, url="contracted_services", json_r=c_service1_dict,
                           email=email2, pwd=pwd2)
    assert r.status_code == 400

    # Check the client can't see the service
    r = request_with_login(login=client.post, request=client.get, url=f"contracted_services/client/{email2}",
                           json_r={}, email=email2, pwd=pwd2)

    assert r.status_code == 200
    contracts = r.get_json()
    assert len(contracts) == 1


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
    assert j['message'] == 'Incorrect data'
    assert j['fields']['service'] == ['Missing data for required field.']

    # check no contracted services have been created
    r = request_with_login(login=client.post, request=client.get, url=f"contracted_services/client/{email1}",
                           json_r={}, email=email1, pwd=pwd1)
    assert r.status_code == 200
    assert len(r.get_json()) == 0


def test_contract_correct(client):
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

    # Give user2 some money to buy service
    r = request_with_login(login=client.post, request=client.put, url=f"users/{email2}/wallet", json_r={'money': 5000},
                           email="madmin@gmail.com", pwd="password")

    # Post a service
    service1_dict = {'title': 'title', 'description': 'description', 'price': 1000}
    r = request_with_login(login=client.post, request=client.post, url="services", json_r=service1_dict, email=email1,
                           pwd=pwd1)
    assert r.status_code == 200

    service_id = r.get_json()['added_service_id']

    # User2 contracts
    c_service1_dict = {'service': service_id}
    r = request_with_login(login=client.post, request=client.post, url="contracted_services", json_r=c_service1_dict,
                           email=email2, pwd=pwd2)
    assert r.status_code == 201

    # Check the client can see the contract.
    r = request_with_login(login=client.post, request=client.get, url=f"contracted_services/client/{email2}",
                           json_r={}, email=email2, pwd=pwd2)
    assert r.status_code == 200
    contracts = r.get_json()
    assert len(contracts) == 1

    # Check the seller can see the contract.
    r = request_with_login(login=client.post, request=client.get, url=f"contracted_services/contractor/{email1}",
                           json_r={}, email=email1, pwd=pwd1)
    assert r.status_code == 200
    contracts = r.get_json()
    assert len(contracts) == 1

    contract_state = contracts[0]['state']
    contract_id = contracts[0]['contract_id']
    assert contract_state == 0

    # Check the money status of the client.
    r = request_with_login(login=client.post, request=client.get, url='users/'+email2 , json_r={}, email=email2, pwd=pwd2)
    assert r.status_code == 200
    user = r.get_json()
    assert '4000.00' ==user['wallet']

    # Check the seller can't validate the contract before accepting it.
    r = request_with_login(login=client.post, request=client.post, url=f"contracted_services/{contract_id}/validate",
                           json_r={}, email=email1, pwd=pwd1)
    assert r.status_code == 409

    # Check the buyer can't validate the contract before accepting it.
    r = request_with_login(login=client.post, request=client.post, url=f"contracted_services/{contract_id}/validate",
                           json_r={}, email=email2, pwd=pwd2)
    assert r.status_code == 409

    # Check the client can't accept it
    r = request_with_login(login=client.post, request=client.post, url=f"contracted_services/{contract_id}/accept",
                           json_r={}, email=email2, pwd=pwd2)
    assert r.status_code == 403

    # Check the seller can accept it
    r = request_with_login(login=client.post, request=client.post, url=f"contracted_services/{contract_id}/accept",
                           json_r={}, email=email1, pwd=pwd1)
    assert r.status_code == 200

    # Check the contract status is accepted
    r = request_with_login(login=client.post, request=client.get, url=f"contracted_services/contractor/{email1}",
                           json_r={}, email=email1, pwd=pwd1)
    contract = r.get_json()
    assert r.status_code == 200
    assert contract[0]["state"] == 1

    # Check the buyer can validate.
    r = request_with_login(login=client.post, request=client.post, url=f"contracted_services/{contract_id}/validate",
                           json_r={}, email=email1, pwd=pwd1)
    assert r.status_code == 200

    # Check the seller can validate.
    r = request_with_login(login=client.post, request=client.post, url=f"contracted_services/{contract_id}/validate",
                           json_r={}, email=email2, pwd=pwd2)
    assert r.status_code == 200

    # Check the money status of the seller.
    r = request_with_login(login=client.post, request=client.get, url="users/"+email1 , json_r={}, email=email1, pwd=pwd1)
    user = r.get_json()
    assert r.status_code == 200
    assert '1000.00' ==user['wallet']

    # Check the contract status is done
    r = request_with_login(login=client.post, request=client.get, url=f"contracted_services/contractor/{email1}",
                           json_r={}, email=email1, pwd=pwd1)
    contract = r.get_json()
    assert r.status_code == 200
    assert contract[0]["state"] == 2


def test_cancel_contract(client):
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

    # Give user2 some money to buy service
    r = request_with_login(login=client.post, request=client.put, url=f"users/{email2}/wallet", json_r={'money': 5000},
                           email="madmin@gmail.com", pwd="password")

    # Post a service
    service1_dict = {'title': 'title', 'description': 'description', 'price': 1000}
    r = request_with_login(login=client.post, request=client.post, url="services", json_r=service1_dict, email=email1,
                           pwd=pwd1)
    assert r.status_code == 200

    service_id = r.get_json()['added_service_id']

    # User2 contracts
    c_service1_dict = {'service': service_id}
    r = request_with_login(login=client.post, request=client.post, url="contracted_services", json_r=c_service1_dict,
                           email=email2, pwd=pwd2)
    assert r.status_code == 201

    # Check the client can see the contract.
    r = request_with_login(login=client.post, request=client.get, url=f"contracted_services/client/{email2}",
                           json_r={}, email=email2, pwd=pwd2)
    assert r.status_code == 200
    contracts = r.get_json()
    assert len(contracts) == 1

    # Check the seller can see the contract.
    r = request_with_login(login=client.post, request=client.get, url=f"contracted_services/contractor/{email1}",
                           json_r={}, email=email1, pwd=pwd1)
    assert r.status_code == 200
    contracts = r.get_json()
    assert len(contracts) == 1

    contract_state = contracts[0]['state']
    contract_id = contracts[0]['contract_id']
    assert contract_state == 0

    # Check the money status of the client.
    r = request_with_login(login=client.post, request=client.get, url='users/'+email2 , json_r={}, email=email2, pwd=pwd2)
    assert r.status_code == 200
    user = r.get_json()
    assert '4000.00' ==user['wallet']

    # User2 cancels
    r = request_with_login(login=client.post, request=client.delete, url="contracted_services/"+str(contract_id), json_r={},
                           email=email2, pwd=pwd2)
    assert r.status_code == 200

    # Check the money status of the client.
    r = request_with_login(login=client.post, request=client.get, url='users/'+email2 , json_r={}, email=email2, pwd=pwd2)
    assert r.status_code == 200
    user = r.get_json()
    assert '5000.00' ==user['wallet']

    # User2 contracts
    c_service1_dict = {'service': service_id}
    r = request_with_login(login=client.post, request=client.post, url="contracted_services", json_r=c_service1_dict,
                           email=email2, pwd=pwd2)
    assert r.status_code == 201

    # Check the seller can see the contract.
    r = request_with_login(login=client.post, request=client.get, url=f"contracted_services/contractor/{email1}",
                           json_r={}, email=email1, pwd=pwd1)
    assert r.status_code == 200
    contracts = r.get_json()
    assert len(contracts) == 2 # The previous contract has not been deleted from the database.

    # Check first contract cancelled
    assert 3 == contracts[0]['state']

    contract_state = contracts[1]['state']
    contract_id = contracts[1]['contract_id']
    assert contract_state == 0

    # User1 cancels
    r = request_with_login(login=client.post, request=client.delete, url="contracted_services/"+str(contract_id), json_r={},
                           email=email1, pwd=pwd1)
    assert r.status_code == 200

    # Check the money status of the client.
    r = request_with_login(login=client.post, request=client.get, url='users/'+email2 , json_r={}, email=email2, pwd=pwd2)
    assert r.status_code == 200
    user = r.get_json()
    assert '5000.00' ==user['wallet']


def test_get_done(client):
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

    # Give user2 some money to buy service
    r = request_with_login(login=client.post, request=client.put, url=f"users/{email2}/wallet", json_r={'money': 5000},
                           email="madmin@gmail.com", pwd="password")

    # Post a service
    service1_dict = {'title': 'title', 'description': 'description', 'price': 1000}
    r = request_with_login(login=client.post, request=client.post, url="services", json_r=service1_dict, email=email1,
                           pwd=pwd1)
    assert r.status_code == 200

    service_id = r.get_json()['added_service_id']

    # User2 contracts
    c_service1_dict = {'service': service_id}
    r = request_with_login(login=client.post, request=client.post, url="contracted_services", json_r=c_service1_dict,
                           email=email2, pwd=pwd2)
    assert r.status_code == 201

    # Check the client can see the contract.
    r = request_with_login(login=client.post, request=client.get, url=f"contracted_services/client/{email2}",
                           json_r={}, email=email2, pwd=pwd2)
    assert r.status_code == 200
    contracts = r.get_json()
    assert len(contracts) == 1

    # Check the seller can see the contract.
    r = request_with_login(login=client.post, request=client.get, url=f"contracted_services/contractor/{email1}",
                           json_r={}, email=email1, pwd=pwd1)
    assert r.status_code == 200
    contracts = r.get_json()
    assert len(contracts) == 1

    contract_state = contracts[0]['state']
    contract_id = contracts[0]['contract_id']
    assert contract_state == 0

    # Check the seller can accept it
    r = request_with_login(login=client.post, request=client.post, url=f"contracted_services/{contract_id}/accept",
                           json_r={}, email=email1, pwd=pwd1)
    assert r.status_code == 200

    # Check the contract status is accepted
    r = request_with_login(login=client.post, request=client.get, url=f"contracted_services/contractor/{email1}",
                           json_r={}, email=email1, pwd=pwd1)
    contract = r.get_json()
    assert r.status_code == 200
    assert contract[0]["state"] == 1

    # Check the buyer can validate.
    r = request_with_login(login=client.post, request=client.post, url=f"contracted_services/{contract_id}/validate",
                           json_r={}, email=email1, pwd=pwd1)
    assert r.status_code == 200

    # Check the seller can validate.
    r = request_with_login(login=client.post, request=client.post, url=f"contracted_services/{contract_id}/validate",
                           json_r={}, email=email2, pwd=pwd2)
    assert r.status_code == 200

    # Check the contract status is done
    r = request_with_login(login=client.post, request=client.get, url=f"contracted_services/{email2}/done",
                           json_r={}, email=email1, pwd=pwd1)
    contract = r.get_json()
    assert r.status_code == 200
    assert contract[0]["id"] == contract_id