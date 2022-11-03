# SETUP

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

# ENDPOINTS
| URL                                            | METHODS     | SECURITY | FUNCTIONALITY                                                             |
|------------------------------------------------|-------------|----------|---------------------------------------------------------------------------|
| /login                                         | POST        | None     | If the json(email and pwd) are correct returns user token                 |
| /users                                         | GET         | 0,1,8,9  | Returns all users                                                         |
| /users/@email                                  | GET         | 0,1,8,9  | Return a concrete user.                                                   |
| /users/@email                                  | DELETE      | 1,8,9    | Deletes concrete user if correct token                                    |                         
| /users                                         | POST        | 0,1,8,9  | Creates a new user with the data provided in the json                     |
| /services                                      | POST        | 1,8,9    | Creates a new service with the data provided in the json if correct token |            
| /services                                      | GET         | 0,1,8,9  | Returns all services                                                      |
| /services/@id                                  | GET         | 0,1,8,9  | Returns a concrete service                                                |
| /services/@id/user                             | GET         | 0,1,8,9  | Returns the creator of a service                                          |
| /services/@email/service                       | GET         | 0,1,8,9  | Returns the services of a user                                            |
| /service/@id                                   | PUT, DELETE | 1,8,9    | Deletes or upgrades concrete service if the correct token                 |
| /users/@email/privileges/@value                | PUT         | 9        | Used to change other user privileges by max admin                         | 
| /contracted_services                           | POST        | 1,8,9    | Creates a contracted service with the data provided in the json           | 
| /contracted_services                           | GET         | 0,1,8,9  | Returns all contracted services                                           | 
| /contracted_services/@id                       | GET         | 0,1,8,9  | Returns a concrete contracted service                                     |
| /contracted_services/@id/user                  | GET         | 0,1,8,9  | Returns the creator of a contracted service                               |
| /contracted_services/@email/contracted_service | GET         | 0,1,8,9  | Returns the contracted services of a user                                 |
| /contracted_service/@id                        | PUT, DELETE | 1,8,9    | Deletes or upgrades concrete contracted service if the correct token      |

**0 corresponds to a not logged user, and it's created by default**

**1 corresponds to a normal logged user**

**8 corresponds to an admin**

**9 corresponds to max the admin**

*Correct token means that either it's admin user or the normal user is the creator of the data that it's going to be treated, etc* 

* Para los tests con login hay un método en utils llamado secure_request. Se puede ver como usarlo en test_api_user
* También se puede ver como crear un usuario admin para tests que requieran este privilegio.
* Recordad borrar las bases de dats ya que han sido modificadas.
* Casi todos los métodos contienen el secure login, si se incluye un 0 quiere decir que realmente no es necessario.
* Hay un listado de los privilegios en utils.priviledies.py
* El tema login se puede ver en utils.secure_request.py 
* El máximo admin creado en develop con el populate es "madmin@gmail.com" con contra "password"


*Seria interesante añadir una variable de active tanto en user como en service. 
En service iria de 0,1,2 donde 0 es le aparece a todos los usuarios, 1 solo al creador
y 2 solo a los admins --> Esto permitiria activar/desactivar al servicio o "borrarlo".
De la misma forma en user 0,1 donde 0 es que el usuario aparece y 1 que no.
Que no aparezca significa que no aparece en las búsquedas normales. Pero de esta forma si accedemos 
a un contrato se podra comprovar información de este.
Es decir que solo se puedan obtener los datos de servicios y usuarios, en estado "eliminado", solo si se es admin o si se es el propietario del servicio y está en estado 1
Por otro lado cuando se obtengan los contratos que en el backend se pueda rellenar la información correctamente.*