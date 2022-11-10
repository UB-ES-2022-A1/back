#!/usr/bin/env python3
from flask_mail import Mail
from utils.mail import mail
from init_app import init_app

# TODO METER A FALSE EN PRODUCCIÓN
develop = True

if develop:
    db_url = "sqlite:///data.db"
else:
    db_url = "meter aqui URL de base de datos de producción"

app, _ = init_app(db_url, develop=develop)
mail = Mail(app)

with app.app_context():
    app.run(host='0.0.0.0', port=8000)
