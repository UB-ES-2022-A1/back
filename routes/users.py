from flask import Blueprint, jsonify, request, Response
from marshmallow import validates, ValidationError, validate
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from werkzeug.exceptions import NotFound, Conflict
from database import db
from utils.custom_exceptions import PrivilegeException, NotAcceptedPrivilege
from models.user import User
from models.user import auth
from utils.privilegies import acces
from flask import g

# Todas las url de users empiezan por esto
users_bp = Blueprint("users", __name__, url_prefix="/users")


# Validación y serialización de usuarios
class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True

    @validates("phone")
    def validates_phone(self, value):
        """
        This method validates the phone number
        :param value: the phone number
        :return: None. Raises an Exception
        """
        if len(str(value)) != 9:
            raise ValidationError("El teléfono tiene que tener 9 dígitos.")

    @validates("pwd")
    def validates_pwd(self, value):
        """
        This method validates the password
        :param value: the password
        :return: None. Raises an Exception
        """
        if len(value) < 5:
            raise ValidationError("Al menos 5 carácteres de contraseña.")

    @validates("email")
    def validates_email(self, value):
        """
        This phone validates the email
        :param value: the email
        :return: None. Raises an Exception
        """
        validator = validate.Email()
        return validator(value)

    # TODO remove para crear el admin maximo. Se quita esta función se crea el admin y se vuelve a añadir la función. También se puede hacer atentando contra la base de datos.
    @validates("acces")
    def validates_acces(self, value):
        if value > 1:
            raise PrivilegeException("No se puede crear un usuario con estos privilegios.")


# Para representar usuario sin exponer info sensible
user_schema_repr = UserSchema(only=("name", "email", "birthday"))

# Para crear usuario
user_schema_create = UserSchema()

user_schema_profile = UserSchema(exclude=['pwd'])


@users_bp.route("", methods=["GET"])
@auth.login_required(role=[acces[0], acces[1], acces[8], acces[9]])
def get_all_users():
    """
    This method return all users
    :return: Response with a list of all users
    """
    all_users = User.query.all()
    return jsonify(user_schema_repr.dump(all_users, many=True)), 200


@users_bp.route("/<string:email>", methods=["GET"])
@auth.login_required(role=[acces[0], acces[1], acces[8], acces[9]])
def get_user(email):
    """
    This method returns a user given an email
    :param email: the mail of the user that we are searching the information
    :return: Response with the user
    """
    usr = User.query.get(email)
    if not usr:
        raise NotFound
    return jsonify(user_schema_profile.dump(usr, many=False)), 200


@users_bp.route("/<string:email>", methods=["DELETE"])
@auth.login_required(role=[acces[1], acces[8], acces[9]])
def delete_user(email):
    """
    This method deletes a user given an email
    :param email: the mail of the user that we are searching the information
    :return: Response with the user
    """
    usr = User.query.get(email)
    if not usr:
        raise NotFound

    # If there is no privilege we can't do this action.
    if email != g.user.email and g.user.acces < 8:
        raise PrivilegeException("Not enough privileges to modify other resources.")
    usr.delete_from_db()
    return Response("Se ha eliminado correctamente el usuario con identificador: " + str(email), status=200)


@users_bp.route("", methods=["POST"])
@auth.login_required(role=[acces[0], acces[1], acces[8], acces[9]])
def create_user():
    """
    This method creates a user
    :return: Response
    """
    d = request.json
    new_user = user_schema_create.load(d, session=db.session)
    # si ya existe no se puede
    if User.query.get(new_user.email) is not None:
        raise Conflict

    new_user.pwd = User.hash_password(new_user.pwd)
    new_user.save_to_db()
    return jsonify(user_schema_profile.dump(new_user, many=False)), 201


@users_bp.route("/<string:email>/privileges/<int:privilege>", methods=["PUT"])
@auth.login_required(role=[acces[9]])
def changes_privileges(email, privilege):
    """
    This method changes the access privileges of a user
    :param email: the email address of the user whose privileges will change
    :param privilege: the privilege that is going to be assigned
    :return: Response
    """
    usr = User.query.get(email)
    if not usr:
        raise NotFound

    if privilege > 8 or privilege < 0:
        raise NotAcceptedPrivilege("No se puede dar este nivel de privilegio.")
    usr.acces = privilege
    usr.save_to_db()

    return jsonify("Privilegios modificados correctamente"), 200
