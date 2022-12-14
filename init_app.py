from flask import Flask
from populate_db import populate
from routes.reviews import reviews_bp
from routes.users import users_bp
from routes.services import services_bp
from routes.error import error_bp
from routes.login import login_bp
from routes.contracted_services import contracted_services_bp
from routes.chat_rooms import chat_rooms_bp
from routes.chat_messages import chat_message_bp
from routes.hashtags import hashtags_bp
from database import db
from flask_migrate import Migrate
from flask_cors import CORS
from database import secret_key


def init_app(database_location, develop=True):

    # creamos la app
    app = Flask(__name__)
    CORS(app)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_location
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = secret_key
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = 'atyourservice.noreply@gmail.com'
    app.config['MAIL_PASSWORD'] = 'huotojlsvpgnlfaz'
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
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
    app.register_blueprint(contracted_services_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(chat_rooms_bp)
    app.register_blueprint(chat_message_bp)
    app.register_blueprint(hashtags_bp)

    @app.route('/')
    def hello_world():  # put application's code here
        return 'Hello World!'

    return app, db
