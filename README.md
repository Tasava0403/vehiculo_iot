21 APIs para el sistema de vehículos IoT

URLs de consulta: 

Link de WebSocket: ws://vehículos-aws-iot.duckdns.org:8000/ws/vehículos/2

Link de Swagger UI: http://vehiculos-aws-iot.duckdns.org:8000/docs

Link de repositorio de Github: https://github.com/Tasava0403/vehiculo_iot.git

1. Módulo de vehículos
Administra el registro, consulta, modificación y eliminación de los vehículos del sistema.
N.º	Método y endpoint	Función

1	POST /vehiculos/	Registrar un vehículo nuevo.

2	GET /vehiculos/	Obtener todos los vehículos registrados.

3	GET /vehiculos/{id_vehiculo}	Consultar un vehículo por su ID.

4	PUT /vehiculos/{id_vehiculo}	Actualizar los datos y el estado de un vehículo.

5	DELETE /vehiculos/{id_vehiculo}	Eliminar un vehículo.

Procedimientos almacenados: sp_crear_vehiculo, sp_obtener_vehiculos, sp_obtener_vehiculo, sp_actualizar_vehiculo y sp_eliminar_vehiculo.

4. Módulo de comandos
Permite definir las instrucciones que puede ejecutar cada vehículo, como avanzar, retroceder o girar.
N.º	Método y endpoint	Función

6	POST /comandos/	Crear un comando asociado a un vehículo.

7	GET /comandos/vehiculo/{id_vehiculo}	Consultar los comandos de un vehículo, ordenados por código.

8	PUT /comandos/{id_comando}	Modificar un comando existente.

9	DELETE /comandos/{id_comando}	Eliminar un comando.

Procedimientos almacenados: sp_crear_comando, sp_obtener_comandos_vehiculo, sp_actualizar_comando y sp_eliminar_comando.

Datos importantes de un comando:
- id_vehiculo: vehículo al que pertenece.
- nombre: nombre de la acción.
- codigo: identificador numérico de la acción.
- descripcion: explicación del movimiento.
- activo: indica si el comando está habilitado.
  
3. Módulo de demos y movimientos
Gestiona secuencias automatizadas de movimientos. Una demo está formada por varios pasos ejecutados en un orden determinado.
N.º	Método y endpoint	Función

10	POST /demos/	Crear una demo para un vehículo.

11	GET /demos/vehiculo/{id_vehiculo}	Listar las demos de un vehículo.

12	PUT /demos/{id_demo}	Actualizar una demo.

13	DELETE /demos/{id_demo}	Eliminar una demo.

14	POST /demos/movimientos	Agregar un movimiento a una demo.

15	GET /demos/{id_demo}/movimientos	Consultar los movimientos ordenados de una demo.

16	PUT /demos/movimientos/{id_demo_movimiento}	Modificar un movimiento.

17	DELETE /demos/movimientos/{id_demo_movimiento}	Eliminar un movimiento de una demo.

Procedimientos almacenados: sp_crear_demo, sp_obtener_demos, sp_actualizar_demo, sp_eliminar_demo, sp_agregar_movimiento_demo, sp_obtener_movimientos_demo, sp_actualizar_movimiento_demo y sp_eliminar_movimiento_demo.

Parámetros de un movimiento:
- id_demo: demo a la que pertenece.
- id_comando: acción que ejecutará el vehículo.
- orden: posición del movimiento en la secuencia.
- duracion_ms: tiempo durante el cual se ejecuta el movimiento, en milisegundos.
- pausa_ms: tiempo de espera antes de continuar con el siguiente paso, en milisegundos.
Ejemplo: una duración de 2000 equivale a 2 segundos, mientras que una pausa de 400 equivale a 0.4 segundos.

4. Módulo de monitoreo, estados e historial
Permite conocer el estado actual del vehículo y consultar los últimos comandos registrados.
N.º	Método y endpoint	Función

18	GET /vehiculos/{id_vehiculo}/estado	Consultar el estado de conexión y el último comando activo.

19	POST /vehiculos/estado	Actualizar el estado y notificar a los clientes mediante WebSocket.

20	POST /historial/registrar	Registrar un comando ejecutado en el historial.

21	GET /vehiculos/{id_vehiculo}/historial/ultimos-10	Consultar los últimos 10 registros del historial.

Procedimientos almacenados: sp_obtener_estado, sp_actualizar_estado, sp_registrar_historial y sp_obtener_historial.

Importante: las demos automatizadas no registran cada movimiento en el historial por diseño, aunque sí actualizan el estado del vehículo y transmiten eventos.

6. Servicio WebSocket y control de demos
Además de los 21 endpoints HTTP, el sistema cuenta con un servicio WebSocket y dos endpoints adicionales para controlar demos.
Método y ruta	Función

WS /ws/vehiculos/{id_vehiculo}	Mantiene una conexión en tiempo real para un vehículo específico.

POST /vehiculos/{id_vehiculo}/demo/iniciar	Inicia la ejecución asíncrona de una demo existente.

POST /vehiculos/{id_vehiculo}/demo/cancelar	Cancela la demo activa del vehículo.

El WebSocket envía el último estado al conectarse y notifica eventos posteriores únicamente a los clientes que monitorean ese vehículo. Los mensajes incluyen el tipo de evento, el ID del vehículo, el comando, su código y la marca temporal.
