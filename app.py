from init_app import init_app

# todo esto funciona para testing, hay que cambiarlo cuando estemos en produccion
app, _ = init_app("sqlite:///data.db")
with app.app_context():
    app.run()
