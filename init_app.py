from flask import Flask
from populate_db import populate
from routes.users import users_bp
from routes.services import services_bp
from routes.error import error_bp
from routes.login import login_bp
from database import db
from flask_migrate import Migrate


def init_app(database_location, develop=True):

    # creamos la app
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_location
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if develop:

        Migrate(app, db)
        db.app = app
        db.init_app(app)

        # poblamos la BD de develop con datos de prueba
        with app.app_context():
            populate(db)

    else:

        # TODO meter aquí la configuración de la BD de producción
        pass

    # registramos los blueprints de los recursos
    app.register_blueprint(users_bp)
    app.register_blueprint(error_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(login_bp)

    @app.route('/')
    def hello_world():  # put application's code here
        return 'Hello World!'

    return app, db
