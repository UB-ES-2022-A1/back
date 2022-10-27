import time
from database import secret_key
from database import db
from models.service import Service
from passlib.apps import custom_app_context as pwd_context
from jwt import encode, decode, ExpiredSignatureError, InvalidSignatureError

class User(db.Model):
    __tablename__ = "users"

    # Campos obligatory
    email = db.Column(db.Text, primary_key=True)
    pwd = db.Column(db.Text, nullable=False)
    name = db.Column(db.Text, nullable=False)

    # Campos opcionales
    phone = db.Column(db.Integer, nullable=True)
    birthday = db.Column(db.Date, nullable=True)
    address = db.Column(db.Text, nullable=True)

    services = db.relationship(Service, backref="user", cascade="all, delete-orphan")

    # Todo falta foto, gender (enum)
    def save_to_db(self):
        """
        This method saves the instance to the database
        """
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
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
        :param password: the password that it's going to be validated
        :return: true if the password matched the hash, else False
        """
        return pwd_context.verify(pwd, self.pwd)

    def generate_auth_token(self, expiration=600):
        """
        This method generates the token used to encode user information
        :param expiration: when the token will expire
        :return: the token
        """
        return encode(
            {"email": self.email, "exp": int(time.time()) + expiration},
            secret_key,
            algorithm="HS256"
        )

    @classmethod
    def verify_auth_token(cls, token):
        """
        This methods uses the given token to check if it is valid and then return the corresponding user
        :param token: token that encodes all the information
        :return: the user corresponding to the token
        """
        try:
            data = decode(token, secret_key, algorithms=["HS256"])
        except ExpiredSignatureError:
            return None  # expired token
        except InvalidSignatureError:
            return None  # invalid token

        user = cls.query.filter_by(email=data['email']).first()

        return user
