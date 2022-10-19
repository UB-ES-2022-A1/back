from init_app import init_app

# TODO METER A FALSE EN PRODUCCIÓN
develop = True

app, _ = init_app("sqlite:///data.db", develop=develop)
with app.app_context():
    app.run()
