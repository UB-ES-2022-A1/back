
class PrivilegeException(Exception):
    """Raised when there is not enough privilege to use a resource"""


class UserNotMatchException(Exception):
    """Raised when there is an acces to the resources of an user with the privileges of another"""