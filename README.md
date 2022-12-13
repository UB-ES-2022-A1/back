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
| URL                                        | METHODS     | SECURITY     | FUNCTIONALITY                                                                                                                                        | 
|--------------------------------------------|-------------|--------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| /login                                     | POST        | None         | If the json(email and pwd) are correct returns user token                                                                                            |
| /users                                     | GET         | 0,1,8,9      | Returns all users (name,email, birthday // whole information minus pwd if admin)                                                                     |
| /users/@email                              | GET         | 0,1,8,9      | Return a concrete user. (*1See comment below)                                                                                                        |
| /users/@email                              | DELETE      | 1,8,9        | Deletes concrete user if correct token                                                                                                               |                         
| /users                                     | POST        | 0,1,8,9      | Creates a new user with the data provided in the json                                                                                                |
| /users/forget_pwd/@email                   | POST        | 0,1,8,9      | If the given email is correct it sends to the mail an URL to change the password                                                                     | 
| /users/reset_pwd                           | POST        | 1,8,9        | This method needs the token. It takes a pwd from the body which is used to change the user's (given by token)                                        | 
| /users/@email/privileges/@value            | PUT         | 9            | Used to change other user privileges by max admin                                                                                                    |
| /users/@email/transactions                 | GET         | 1,8,9        | Returns a dict: number_transactions and transactions. The second one is a ordered(recent 1st) list with transactions(description, quantity, wallet). |
| /services                                  | POST        | 1,8,9        | Creates a new service with the data provided in the json if correct token                                                                            |            
| /services                                  | GET         | 0,1,8,9      | Returns all services                                                                                                                                 |
| /services/@id                              | GET         | 0,1,8,9      | Returns a concrete service                                                                                                                           |
| /services/@id/user                         | GET         | 0,1,8,9      | Returns the creator of a service                                                                                                                     |
| /services/@email/service                   | GET         | 0,1,8,9      | Returns the services of a user                                                                                                                       |
| /service/@id                               | PUT, DELETE | 1,8,9        | Deletes or upgrades concrete service if the correct token                                                                                            |
| /contracted_services                       | POST        | 1,8,9        | Creates a contracted service with the data provided in the json                                                                                      | 
| /contracted_services                       | GET         | 8,9          | Returns all contracted services                                                                                                                      | 
| /services/search                           | GET, POST   | 0,1,8,9      | Returns all services constrained by passed search text, filters and ordering                                                                         |
| /contracted_services/@id                   | GET         | 0,1,8,9      | Returns a concrete contracted service                                                                                                                |
| /contracted_services/@id/user              | GET         | 0,1,8,9      | Returns the creator of a contracted service                                                                                                          |
| /contracted_services/client/@email         | GET         | 1,8,9        | Returns the services contracted by a user                                                                                                            |
| /contracted_services/contractor/@email     | GET         | 1,8,9        | Returns the services requested to a user                                                                                                             |
| /contracted_services/@id                   | PUT, DELETE | 1,8,9        | Deletes or upgrades concrete contracted service if the correct token                                                                                 |
| /contracted_services/@id/accept            | POST        | 1,8,9        | Sets the contract as "accepted", only available to the creator of the service or admin. (*2 See comment below)                                       |
| /contracted_services/@id/validate          | POST        | 1,8,9        | Validates de contract for client or seller. If admin validates for both. When validated for both accepts contract.                                   |
| /reviews                                   | GET         | 0,1,8,9      | Gets all reviews                                                                                                                                     |
| /reviews/@review_id                        | GET, DELETE | 1,8,9        | gets/deletes your own review                                                                                                                         |
| /reviews/service/@service_id               | GET, POST   | 0(get),1,8,9 | gets the reviews to a service. If logged in can post own review                                                                                      |
| /reviews/user/@user_id                     | GET         | 0,1,8,9      | gets all reviews of a user                                                                                                                           |
| /reviews/service/@service_id/user/@user_id | GET         | 0,1,8,9      | gets a user's review of a service                                                                                                                    |


*Comments*
1. If the user doesn't exist return not found. If the request maker(RM) is admin return whole user profile minus pwd. If RM not admin and the user that is searched is not verified (email) return not found.
Otherwise (mail verified), if the RM is the searched user returns whole minus pwd, access, verified_email. Finally, if the RM is not the searched user returns same as before minus wallet.
2. When the contract is created it has status 0. When it is accepted it has status 1. When client or seller validates it changes an independent variable status to 1. When both
have validated the status changes to 2. Summary of status: 0 Creates, 1 Accepted, 2 Completed. Use variables validate_c or validate_s to know if client or seller have validated contract.

**0 corresponds to a not logged user, and it's created by default**

**1 corresponds to a normal logged user**

**8 corresponds to an admin**

**9 corresponds to max the admin**

*Correct token means that either it's admin user or the normal user is the creator of the data that it's going to be treated, etc* 

Values used in POST methods (PUT may contain only a subset of them). Other parameters are extra ones from de db.

User states: 0 -> active, 1 -> not active
Service states: 0 -> active, 1 -> paused (not implemented), 2 -> not active

| CLASS    | REQUEST PARAMETERS                                                                             | OTHER PARAMETERS                      |
|----------|------------------------------------------------------------------------------------------------|---------------------------------------|
| USER     | email, pwd, name, phone, birthday, address, state                                              | access, verified_email, wallet, image |
| SERVICE  | user_email, title, description, price, begin, end, cooldown, requires-place, created_at, state | id                                    | 
| CONTRACT | user_email, service_id, state, price                                                           | None                                  |


MaxAdmin: "madmin@gmail.com" ; with password "password"

Other users: "emailX@gmail.com" where X is a number between 1 and 9; with password "password"

.

.

.

ESTO ES TEMPORAL

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
