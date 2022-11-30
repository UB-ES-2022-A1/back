from flask import Blueprint, jsonify, request, Response
from marshmallow import validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy import and_
from werkzeug.exceptions import NotFound, BadRequest
from database import db
from sqlalchemy.orm.util import has_identity

from models.contracted_service import ContractedService
from models.review import Review
from models.service import Service
from models.user import auth
from flask import g
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
    return review_schema_all.dump(Review.get_all(), many=True)


@reviews_bp.route("", methods=["POST"])
@auth.login_required(role=[access[1], access[8], access[9]])
def put_review():
    """
    This method contracts a new service. Requires a token of a user to do the post.
    :return: Response
    """
    info = request.json  # Leer la info del json
    info["reviewer"] = g.user.email
    new_review = review_schema_all.load(info, session=db.session)  # Crear el objeto mediante el schema
    new_review.service = new_review.service.parent
    new_review.save_to_db()  # Actualizamos la BD

    return Response("Review posteada correctamente con el identificador: " + str(new_review.id),
                    status=201)
