import time
from database import db
from models.service import Service
from models.contracted_service import ContractedService
from models.chat_room import ChatRoom
from models.chat_message import ChatMessage
from flask import g, current_app
from flask_httpauth import HTTPBasicAuth
from jwt import encode, decode, ExpiredSignatureError, InvalidSignatureError
from passlib.apps import custom_app_context as pwd_context
from utils.privilegies import access

auth = HTTPBasicAuth()


class User(db.Model):
    __tablename__ = "users"

    # Campos obligatory
    email = db.Column(db.Text, primary_key=True)
    pwd = db.Column(db.Text, nullable=False)
    name = db.Column(db.Text, nullable=False)
    access = db.Column(db.Integer, nullable=False, default=1)
    verified_email = db.Column(db.Boolean, nullable=False, default=False)
    # https://docs.sqlalchemy.org/en/20/core/type_basics.html
    wallet = db.Column(db.Numeric(scale=2), default=0.0)
    user_grade = db.Column(db.Float, default=0.0)
    number_of_reviews = db.Column(db.Integer, default = 0)

    # Campos opcionales
    phone = db.Column(db.Integer, nullable=True)
    birthday = db.Column(db.Date, nullable=True)
    address = db.Column(db.Text, nullable=True)

    state = db.Column(db.Integer, nullable=False, default=0)  # 0 active, 1 not active

    services = db.relationship(Service, backref="user")
    contracted_services = db.relationship(ContractedService, backref="user")

    #chat relations
    seller = db.relationship(ChatRoom, backref = 'seller', lazy = 'dynamic', foreign_keys = 'ChatRoom.seller_email')
    client = db.relationship(ChatRoom, backref = 'client', lazy = 'dynamic', foreign_keys = 'ChatRoom.client_email')
    message = db.relationship(ChatMessage, backref="user")

    # Todo falta foto, gender (enum)
    def save_to_db(self):
        """
        This method saves the instance to the database
        """
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        """
        This method deactivates the instance from the database
        """
        self.state = 1
        db.session.commit()

    def definitive_delete_from_db(self):
        """
        This method deletes the instance from the database
        """
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def get_by_id(cls, instance_id):
        """
        Returns a user with the specified id
        :param instance_id: the user id
        :return: user with the corresponding id.
        """
        return cls.query.get(instance_id)

    @classmethod
    def get_all(cls):
        """
        Returns a list with all users
        :return: list with all users
        """
        return cls.query.all()

    @classmethod
    def hash_password(self, pwd):
        """
        This method encrypts the password and stores it
        :param password: password desired to encrypt
        :return hashed password
        """
        return pwd_context.encrypt(pwd)

    def verify_password(self, pwd):
        """
        Verifies if a given password is given correctly
        :param pwd: the password that it's going to be validated
        :return: true if the password matched the hash, else False
        """
        return pwd_context.verify(pwd, self.pwd)

    def generate_auth_token(self, expiration=60000):
        """
        This method generates the token used to encode user information
        :param expiration: when the token will expire
        :return: the token
        """
        return encode(
            {"email": self.email, "exp": int(time.time()) + expiration},
            current_app.secret_key,
            algorithm="HS256"
        )

    @classmethod
    def verify_auth_token(cls, token):
        """
        This method uses the given token to check if it is valid and then return the corresponding user
        :param token: token that encodes all the information
        :return: the user corresponding to the token
        """
        try:
            data = decode(token, current_app.secret_key, algorithms=["HS256"])
        except ExpiredSignatureError:
            return None  # expired token
        except InvalidSignatureError:
            return None  # invalid token

        user = cls.query.filter_by(email=data['email']).first()

        return user


@auth.verify_password
def verify_password(token, password):
    """
    This method verifies if a token is correct
    :param token: the token that contain all the information
    :param password: not used
    :return: the user itself
    """
    # When there is no credentials a visitor access is given.
    if len(token) == 0:
        u = User()
        u.access = 0
        g.user = u
        return u

    try:
        user = User.verify_auth_token(token)
    except:
        return False
    if user:
        g.user = user
        return user


@auth.get_user_roles
def get_user_roles(user):
    """
    This method return the user access level.
    :return: access level label
    """
    return access[user.access]
