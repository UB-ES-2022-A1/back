from flask import Blueprint, jsonify
from sqlalchemy import func, desc
from models.search import term_frequency
from models.user import auth
from utils.privilegies import access

hashtags_bp = Blueprint("hashtags", __name__, url_prefix="/hashtags")


@hashtags_bp.route("/<int:nHashtags>", methods=["GET"])
@auth.login_required(role=[access[0], access[1], access[8], access[9]])
def get_all_services(nHashtags):
    all_tag_coincidences = term_frequency.query.filter(term_frequency.word.like('#%')).group_by(term_frequency.word). \
        order_by(desc(func.count(term_frequency.service_id))).limit(nHashtags).all()

    return jsonify([r.word for r in all_tag_coincidences]), 200
