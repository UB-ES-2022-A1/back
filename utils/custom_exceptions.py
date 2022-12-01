
class PrivilegeException(Exception):
    """Raised when there is not enough privilege to use a resource"""


class UserNotMatchException(Exception):
    """Raised when there is an acces to the resources of an user with the privileges of another"""


class NotAcceptedPrivilege(Exception):
    """Raised when MaxAdmin tries to update the privileges of a user with not accepted ones"""


class EmailNotVerified(Exception):
    """Raised when the email is not verified"""
