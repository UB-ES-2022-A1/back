from flask import Flask
from routes.users import users_bp
from routes.services import services_bp
from routes.error import error_bp
from routes.login import login_bp
from database import db
from flask_migrate import Migrate

# creamos la app
app = Flask(__name__)

# URI a cambiar en producción.
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

migrate = Migrate(app, db)
db.app = app
db.init_app(app)

#todo esto funciona para testing, hay que cambiarlo cuando estemos en produccion
with app.app_context():
    db.create_all()


# registramos los blueprints de los recursos
app.register_blueprint(users_bp)
app.register_blueprint(error_bp)
app.register_blueprint(services_bp)
app.register_blueprint(login_bp)


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
