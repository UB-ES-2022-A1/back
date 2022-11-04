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


def test_login_correct_incorrect(client):
    # check empty database to start
    user1_dict = {'email': 'pepito@gmail.com', 'pwd': '12345678', 'name': 'Pepito'}
    r = client.post("users", json=user1_dict)
    assert r.status_code == 201

    login_dict = {'email': 'pepito@gmail.com', "pwd": '12345678'}
    r = client.post("login", json=login_dict)
    assert r.status_code == 200
    assert "token" in r.get_json()