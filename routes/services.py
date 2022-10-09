from flask import Blueprint

# Todas las url de servicios empiezan por esto
services_bp = Blueprint("services", __name__, url_prefix="/services")
