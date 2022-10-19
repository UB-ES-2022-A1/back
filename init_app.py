from flask import Flask
from populate_db import populate
from routes.users import users_bp
from routes.services import services_bp
from routes.error import error_bp
from routes.login import login_bp
from database import db
from flask_migrate import Migrate

def init_app(database_location):
    # creamos la app
    app = Flask(__name__)

    # URI a cambiar en producción.
    app.config["SQLALCHEMY_DATABASE_URI"] = database_location
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    Migrate(app, db)
    db.app = app
    db.init_app(app)

    with app.app_context():
        populate(db)

    # registramos los blueprints de los recursos
    app.register_blueprint(users_bp)
    app.register_blueprint(error_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(login_bp)

    @app.route('/')
    def hello_world():  # put application's code here
        return 'Hello World!'

    return app, db
