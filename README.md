# Backend

setup: ejecutar lo siguiente.

    pip install -r requirements.txt
    flask db init
    flask db migrate -m "Initial migration"
    flask db upgrade

estos dos últimos pasos habrá que repetirlos (con un mensaje distinto) si cambiamos la estructura de la base de datos.

finalmente, ejecutamos:

    python3 app.py

y ya tendríamos nuestra API funcionando en localhost:5000

Cada vez que cambiemos los modelos de la base de datos:

    flask db migrate -m "Initial migration".
    flask db upgrade

En caso de que algo no vaya probar de borrar las migrations y ejecutar:

    flask db init

Notemos que este proyecto está preparado para ejecutarse en local. Para prepararlo para producción, poner la variable develop de app.py a False, y rellenar la parte correspondiente a la configuración de producción de init_app.py


