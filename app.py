from flask import Flask
from routes.users import users_bp
from routes.services import services_bp
from routes.error import error_bp
from routes.login import login_bp
from database import db
from flask_migrate import Migrate
from populate_db import populate

# Creamos la app
app = Flask(__name__)
# Indicamos la ubicación de la base de datos. Cambiar en producción.
if __name__ == '__main__':
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test_data.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

migrate = Migrate(app, db)
db.app = app
db.init_app(app)

# Todo esto funciona para testing, hay que cambiarlo cuando estemos en produccion
with app.app_context():
    populate(db)

# Registramos los blueprints de los recursos
app.register_blueprint(users_bp)
app.register_blueprint(error_bp)
app.register_blueprint(services_bp)
app.register_blueprint(login_bp)


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
