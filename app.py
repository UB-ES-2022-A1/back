from init_app import init_app

# TODO METER A FALSE EN PRODUCCIÓN
develop = True

if develop:
    db_url = "sqlite:///data.db"
else:
    db_url = "meter aqui URL de base de datos de producción"

app, _ = init_app(db_url, develop=develop)
with app.app_context():
    app.run(host='0.0.0.0')
