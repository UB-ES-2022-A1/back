import base64


def request_with_login(login, request, url, json, email, pwd):

    login_dict = {'email': email, "pwd": pwd}
    r = login("login", json=login_dict)
    token = r.get_json()['token']
    credentials = base64.b64encode((token + ":contra").encode()).decode('utf-8')
    r = request(url, headers={"Authorization": "Basic {}".format(credentials)})

    return r

