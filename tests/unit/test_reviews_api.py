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

    assert r.status_code == 200

    review_id = r.get_json()['saved_review_id']

    r = client.get('reviews')
    assert r.status_code == 200
    assert review_id in [rev['id'] for rev in r.get_json()]

    r = client.get(f'reviews/service/{service_id}')
    assert r.status_code == 200
    assert review_id in [rev['id'] for rev in r.get_json()]

    r = client.get(f'reviews/user/{email1}')
    assert r.status_code == 200
    assert review_id not in [rev['id'] for rev in r.get_json()]

    r = client.get(f'reviews/user/{email2}')
    assert r.status_code == 200
    assert review_id in [rev['id'] for rev in r.get_json()]

    service1_dict = {"title" : "new_service"}
    r = request_with_login(login=client.post, request=client.put, url=f"services/{service_id}", json_r=service1_dict, email=email1,
                           pwd=pwd1)
    assert r.status_code == 200

    # changing a service yields 2 different service ids
    service_id_2 = r.get_json()['modified_service_id']
    assert service_id_2 != service_id

    # but both have the correct review

    r = client.get(f'reviews/service/{service_id}')
    assert r.status_code == 200
    assert review_id in [rev['id'] for rev in r.get_json()]

    r = client.get(f'reviews/service/{service_id_2}')
    assert r.status_code == 200
    assert review_id in [rev['id'] for rev in r.get_json()]

def test_average_ratings(client):
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
    r = request_with_login(login=client.post, request=client.post, url="services", json_r=service1_dict,
                           email=email1,
                           pwd=pwd1)

    assert r.status_code == 200

    service_id = r.get_json()['added_service_id']

    review1_dict = {'title': 'Mi pimera review', 'text': 'ni bien ni mal bro', 'stars': 3}
    r = request_with_login(login=client.post, request=client.post, url=f'reviews/{service_id}', json_r=review1_dict,
                           email=email2, pwd=pwd2)

    assert r.status_code == 200

    r = client.get("users")
    assert r.status_code == 200

    r = client.get(f'services/{service_id}')
    service = r.get_json()
    assert service["service_grade"] == 3
    assert service["number_of_reviews"] == 1

    r = request_with_login(login=client.post, request=client.get, url="users/"+email1, json_r={}, email=email1, pwd=pwd1)
    user1 = r.get_json()
    assert user1["user_grade"] == 3
    assert user1["number_of_reviews"] == 1

    review1_dict = {'title': 'Review de mi propio servicio jeje', 'text': '10/10 lo volvería a contratar', 'stars': 5}
    r = request_with_login(login=client.post, request=client.post, url=f'reviews/{service_id}', json_r=review1_dict,
                           email=email1, pwd=pwd1)
    assert r.status_code == 200

    r = client.get(f'services/{service_id}')
    service = r.get_json()
    assert service["service_grade"] == 4
    assert service["number_of_reviews"] == 2

    r = request_with_login(login=client.post, request=client.get, url="users/" + email1, json_r={}, email=email1,
                           pwd=pwd1)
    user1 = r.get_json()
    assert user1["user_grade"] == 4
    assert user1["number_of_reviews"] == 2



