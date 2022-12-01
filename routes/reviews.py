from flask import Blueprint, jsonify, request, Response
from marshmallow import validates
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from werkzeug.exceptions import NotFound, BadRequest
from database import db
from sqlalchemy.orm.util import has_identity
from models.review import Review
from models.service import Service
from models.user import auth, User
from flask import g

from utils.custom_exceptions import PrivilegeException
from utils.privilegies import access

reviews_bp = Blueprint("reviews", __name__, url_prefix="/reviews")


# Validación y serialización de servicios
class ReviewSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Review
        include_relationships = True  # Incluir relaciones como la de user
        load_instance = True  # Para que se puedan crear los objetos

    @validates("reviewer")
    def validates_reviewer(self, reviewer):
        """
        :param reviewer:  el que hace la review
        :return: None
        """
        if not has_identity(reviewer):
            raise NotFound("Usuario con id " + str(reviewer.email) + " no encontrado!")

    @validates("service")
    def validates_service(self, service):

        if not has_identity(service):
            raise NotFound("Servicio con id " + str(service.id) + " no encontrado!")

    @validates("stars")
    def validates_stars(self, stars):

        if not type(stars) == int:
            raise BadRequest("Number of stars must be an integer.")

        if not 1 <= stars <= 5:
            raise BadRequest("Number of stars must be between 1 and 5.")


review_schema_all = ReviewSchema()


@reviews_bp.route("", methods=["GET"])
@auth.login_required(role=[access[0], access[1], access[8], access[9]])
def get_all_reviews():
    return jsonify(review_schema_all.dump(Review.get_all(), many=True)), 200


@reviews_bp.route("/<int:review_id>", methods=["GET"])
@auth.login_required(role=[access[0], access[1], access[8], access[9]])
def get_review(review_id):
    review = Review.get_by_id(review_id)

    if not review:
        raise NotFound

    return jsonify(review_schema_all.dump(review, many=False)), 200


@reviews_bp.route("/service/<int:service_id>", methods=["GET"])
@auth.login_required(role=[access[0], access[1], access[8], access[9]])
def get_service_reviews(service_id):
    service = Service.get_by_id(service_id)
    if not service:
        raise NotFound('Servicio no encontrado.')

    return jsonify(review_schema_all.dump(service.parent.reviews, many=True)), 200


@reviews_bp.route("/user/<int:user_id>", methods=["GET"])
@auth.login_required(role=[access[0], access[1], access[8], access[9]])
def get_user_reviews(user_id):
    user = User.get_by_id(user_id)
    if not user:
        raise NotFound('Usuario no encontrado.')

    return jsonify(review_schema_all.dump(user.reviews, many=True)), 200


@reviews_bp.route("service/<int:service_id>/user/<int:user_id>", methods=["GET"])
@auth.login_required(role=[access[0], access[1], access[8], access[9]])
def get_user_service_review(service_id, user_id):
    service = Service.get_by_id(service_id)
    if not service:
        raise NotFound('No se ha encontrado el servicio')

    reviewer = User.get_by_id(user_id)
    if not reviewer:
        raise NotFound('No se ha encontrado el usuario')

    review = Review.query.filter(Review.reviewer_email == user_id,
                                 Review.service_id == service.parent.id
                                 ).first()

    return jsonify(review_schema_all.dump(review, many=False)), 200


@reviews_bp.route("/<int:service_id>", methods=["POST"])
@auth.login_required(role=[access[1], access[8], access[9]])
def post_review(service_id):
    """
    This method contracts a new service. Requires a token of a user to do the post.
    :return: Response
    """
    info = request.json  # Leer la info del json
    info["reviewer"] = g.user.email
    info['service'] = service_id
    new_review = review_schema_all.load(info, session=db.session)  # Crear el objeto mediante el schema
    new_review.service = new_review.service.parent
    new_review.save_to_db()  # Actualizamos la BD

    return {'saved_review': new_review.id}, 200


@reviews_bp.route("/<int:review_id>", methods=["DELETE"])
@auth.login_required(role=[access[1], access[8], access[9]])
def delete_review(review_id):
    review = Review.get_by_id(review_id)

    if not review:
        raise NotFound

    if review.reviewer_email != g.user.email and g.user.access < 8:
        raise PrivilegeException("Not enough privileges to access other users' contracts.")

    review.delete_from_db()

    return {'deleted review': review_id}, 200
