Para ejecutar el SERVIDOR utilizamos el formato sugerido:

$ python server.py <ServerIP> <ServerPort>

-donde:
• <ServerIP>
Dirección IP donde el servidor aceptará conexiones, por ejemplo 127.0.0.1

• <ServerPort>
Puerto donde el servidor aceptará conexiones, por ejemplo 2022

/////////////////////////////////////////////////////////////////////////////

Para ejecutar el CLIENTE utilizamos el formato sugerido: 

$ python cliente.py <ServerIP> <ServerPort> <Op> <Key> [<Value>]

-donde:
• <ServerIP>
Dirección IP del servidor al que se desea conectar, por ejemplo 127.0.0.1

• <ServerPort>
Puerto del servidor al que se desea conectar, por ejemplo 2022

• <Op>
Operación a realizar: GET (leer un valor e imprimirlo), SET (escribir un
valor) o DEL (borrar un valor).

• <Key>
Clave del valor que se desea leer, escribir o borrar.

• <Value>
Puede ser un argumento del comando cuando <Op> es SET para indicar
el valor a almacenar. Si se omite en la operación SET, el valor a escribir se
lee de la entrada estándar.

-Luego el cliente queda en loop esperando por nuevos comandos (GET, SET, DEL) o en caso de querer salir EXIT