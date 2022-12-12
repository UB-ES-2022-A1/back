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


def test_post_chat_message(client):
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
    assert contracts[0]['contract_id'] == 1

    # Check the client can see the service
    r = request_with_login(login=client.post, request=client.get, url="/chats/rooms",
                           json_r={}, email=email2, pwd=pwd2)
    assert r.status_code == 200

    # post the new chatroom
    r = request_with_login(login=client.post, request=client.post, url="/chats/new",
                           json_r={'contracted_service':contracts[0]['contract_id']}, email=email2, pwd=pwd2)

    assert r.status_code == 201
    assert r.get_json()['request_id'] == contracts[0]['contract_id']

    # check if client can see the room
    r = request_with_login(login=client.post, request=client.get, url="/chats/rooms",
                           json_r={}, email=email2, pwd=pwd2)

    assert len(r.get_json()) == 1

    # check if seller can see the room
    r = request_with_login(login=client.post, request=client.get, url="/chats/rooms",
                           json_r={}, email=email1, pwd=pwd1)

    assert len(r.get_json()) == 1

    first_chat = r.get_json()[0]['update']

    room = contracts[0]['contract_id']

    messageJson = {
        'chat_room': room,
        'text':'testmesssage'
    }

    # check if client can post message
    r = request_with_login(login=client.post, request=client.post, url="/messages/new",
                           json_r=messageJson, email=email2, pwd=pwd2)

    assert r.status_code == 201

    # check if seller can post message
    r = request_with_login(login=client.post, request=client.post, url="/messages/new",
                           json_r=messageJson, email=email1, pwd=pwd1)

    assert r.status_code == 201

    #room_id:int, page:int, pagesize:int
    pageJson = {
        'room_id': room,
        'page' : 0,
        'pagesize' : 10
    }

    # check if seller can post message
    r = request_with_login(login=client.post, request=client.get, url="/messages/get",
                           json_r=pageJson, email=email1, pwd=pwd1)

    assert len(r.get_json()) == 2

    r = request_with_login(login=client.post, request=client.post, url="/messages/new",
                           json_r=messageJson, email=email1, pwd=pwd1)
    r = request_with_login(login=client.post, request=client.post, url="/messages/new",
                           json_r=messageJson, email=email1, pwd=pwd1)
    r = request_with_login(login=client.post, request=client.post, url="/messages/new",
                           json_r=messageJson, email=email1, pwd=pwd1)
    r = request_with_login(login=client.post, request=client.post, url="/messages/new",
                           json_r=messageJson, email=email1, pwd=pwd1)
    r = request_with_login(login=client.post, request=client.post, url="/messages/new",
                           json_r=messageJson, email=email1, pwd=pwd1)
    r = request_with_login(login=client.post, request=client.post, url="/messages/new",
                           json_r=messageJson, email=email1, pwd=pwd1)
    r = request_with_login(login=client.post, request=client.post, url="/messages/new",
                           json_r=messageJson, email=email1, pwd=pwd1)
    r = request_with_login(login=client.post, request=client.post, url="/messages/new",
                           json_r=messageJson, email=email1, pwd=pwd1)
    r = request_with_login(login=client.post, request=client.post, url="/messages/new",
                           json_r=messageJson, email=email1, pwd=pwd1)

    r = request_with_login(login=client.post, request=client.get, url="/messages/get",
                           json_r=pageJson, email=email1, pwd=pwd1)

    assert len(r.get_json()) == 10

    pageJson = {
        'room_id': room,
        'page' : 1,
        'pagesize' : 10
    }

    r = request_with_login(login=client.post, request=client.get, url="/messages/get",
                           json_r=pageJson, email=email1, pwd=pwd1)

    assert len(r.get_json()) == 1

    r = request_with_login(login=client.post, request=client.get, url="/chats/rooms",
                           json_r=pageJson, email=email1, pwd=pwd1)

    assert first_chat != r.get_json()[0]['update']
    assert len(r.get_json()) == 1