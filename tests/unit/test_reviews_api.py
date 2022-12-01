import pytest
from init_app import init_app
from utils.secure_request import request_with_login

app, db = init_app("sqlite:///data_test.db")


@pytest.fixture(scope='function', autouse=True)
def client():
    with app.test_request_context():
        db.drop_all()
        db.create_all()
        yield app.test_client()


def test_post_review(client):

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

    service1_dict = {'title': 'titleT2', 'description': 'description', 'price': 1}
    r = request_with_login(login=client.post, request=client.post, url="services", json_r=service1_dict, email=email1,
                           pwd=pwd1)

    assert r.status_code == 200

    service_id = r.get_json()['added_service_id']

    review1_dict = {'title': 'Mi pimera review', 'text': 'ni bien ni mal bro', 'stars': 3}
    r = request_with_login(login=client.post, request=client.post, url=f'reviews/{service_id}', json_r=review1_dict,
                           email=email2, pwd=pwd2)
    #assert r.status_code == 200
    assert r.get_json() == 'sdfasdf'

