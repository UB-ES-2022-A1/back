import base64


def request_with_login(login, request, url, json_r, email, pwd):
    """
    This method makes a htttp request with a login
    :param login: login used method
    :param request: request used method
    :param url: url of the request
    :param json_r: content
    :param email: email used for login
    :param pwd: password used for login
    :return: the response
    """
    login_dict = {'email': email, "pwd": pwd}
    r = login("login", json=login_dict)

    rj = r.get_json()
    if 'token' not in rj:
        return r

    token = rj['token']
    credentials = base64.b64encode((token + ":contra").encode()).decode('utf-8')
    r = request(url, json=json_r, headers={"Authorization": "Basic {}".format(credentials)})
    return r
