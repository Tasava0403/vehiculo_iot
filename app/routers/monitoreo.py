import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from pydantic import BaseModel
from app.database import get_db_connection
from app.websocket import websocket_manager

router = APIRouter(tags=["Monitoreo, Historial y Demos WebSocket"])

# --- Modelos Pydantic ---
class EstadoUpdate(BaseModel):
    id_vehiculo: int
    id_comando: int | None = None
    conectado: bool

class HistorialCreate(BaseModel):
    id_vehiculo: int
    id_comando: int
    origen: str = "MANUAL"

class DemoTriggerRequest(BaseModel):
    id_demo: int


# --- ENDPOINTS HTTP ---

@router.get("/vehiculos/{id_vehiculo}/estado", summary="Obtener estado actual del vehículo")
def obtener_estado(id_vehiculo: int):
    """Ejecuta el procedimiento almacenado sp_obtener_estado[cite: 1]."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_obtener_estado", (id_vehiculo,))
            resultado = cursor.fetchone()
            if not resultado:
                return {"id_vehiculo": id_vehiculo, "conectado": False, "mensaje": "Sin estado previo"}
            return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()


@router.post("/vehiculos/estado", summary="Actualizar estado del vehículo")
async def actualizar_estado_http(data: EstadoUpdate):
    """Actualiza el estado y notifica en tiempo real por WebSocket a los clientes de ese vehículo."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_actualizar_estado", (
                data.id_vehiculo,
                data.id_comando,
                data.conectado
            ))
            connection.commit()
            
            # Consultar estado actualizado con nombre de comando para el payload JSON
            cursor.callproc("sp_obtener_estado", (data.id_vehiculo,))
            estado_actual = cursor.fetchone()

        # Notificar vía WebSocket a todos los clientes suscritos a este vehículo
        payload = {
            "tipo_evento": "ACTUALIZACION_ESTADO",
            "id_vehiculo": data.id_vehiculo,
            "comando": estado_actual.get("comando") if estado_actual else None,
            "codigo": estado_actual.get("codigo") if estado_actual else None,
            "conectado": data.conectado,
            "marca_temporal": datetime.now().isoformat()
        }
        await vehicle_ws_manager.broadcast_to_vehicle(data.id_vehiculo, payload)

        return {"mensaje": "Estado actualizado exitosamente", "estado": estado_actual}
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()


@router.post("/historial/registrar", summary="Registrar movimiento en historial")
def registrar_historial(data: HistorialCreate):
    """Ejecuta sp_registrar_historial[cite: 1]."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_registrar_historial", (
                data.id_vehiculo,
                data.id_comando,
                data.origen
            ))
            connection.commit()
            return {"mensaje": "Movimiento registrado en el historial exitosamente"}
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()


@router.get("/vehiculos/{id_vehiculo}/historial/ultimos-10", summary="Obtener últimos 10 movimientos del historial")
def obtener_ultimos_10_historial(id_vehiculo: int):
    """Ejecuta sp_obtener_historial[cite: 1] limitado a los 10 registros más recientes[cite: 1]."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_obtener_historial", (id_vehiculo,))
            resultado = cursor.fetchall()
            return resultado[:10]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()


# --- CONTROLADOR ASÍNCRONO DE DEMAS (BACKGROUND TASK) ---

async def ejecutar_secuencia_demo(id_vehiculo: int, id_demo: int):
    """Procesa los N movimientos de la demo de forma asíncrona, respetando tiempos y actualizando estado[cite: 1]."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_obtener_movimientos_demo", (id_demo,))
            movimientos = cursor.fetchall()
    except Exception as e:
        await vehicle_ws_manager.broadcast_to_vehicle(id_vehiculo, {
            "tipo_evento": "ERROR_DEMO",
            "id_vehiculo": id_vehiculo,
            "error": str(e),
            "marca_temporal": datetime.now().isoformat()
        })
        return
    finally:
        connection.close()

    if not movimientos:
        await vehicle_ws_manager.broadcast_to_vehicle(id_vehiculo, {
            "tipo_evento": "ERROR_DEMO",
            "id_vehiculo": id_vehiculo,
            "error": "La demo no contiene movimientos registrados.",
            "marca_temporal": datetime.now().isoformat()
        })
        if id_vehiculo in vehicle_ws_manager.active_demos:
            del vehicle_ws_manager.active_demos[id_vehiculo]
        return

    try:
        # Evento de inicio de Demo
        await vehicle_ws_manager.broadcast_to_vehicle(id_vehiculo, {
            "tipo_evento": "INICIO_DEMO",
            "id_vehiculo": id_vehiculo,
            "id_demo": id_demo,
            "total_movimientos": len(movimientos),
            "marca_temporal": datetime.now().isoformat()
        })

        for mov in movimientos:
            # 1. Actualizar estado del vehículo con el comando actual de la demo (SIN tocar historial)
            conn_up = get_db_connection()
            try:
                with conn_up.cursor() as cur_up:
                    cur_up.callproc("sp_actualizar_estado", (id_vehiculo, mov["id_comando"], True))
                    conn_up.commit()
            except Exception:
                conn_up.rollback()
            finally:
                conn_up.close()

            # 2. Emitir mensaje por movimiento vía WebSocket
            await vehicle_ws_manager.broadcast_to_vehicle(id_vehiculo, {
                "tipo_evento": "MOVIMIENTO_DEMO",
                "id_vehiculo": id_vehiculo,
                "orden": mov["orden"],
                "comando": mov["comando"],
                "codigo": mov["codigo"],
                "duracion_ms": mov["duracion_ms"],
                "pausa_ms": mov["pausa_ms"],
                "marca_temporal": datetime.now().isoformat()
            })

            # 3. Respetar duracion_ms
            await asyncio.sleep(mov["duracion_ms"] / 1000.0)

            # 4. Respetar pausa_ms si existe
            if mov["pausa_ms"] > 0:
                await asyncio.sleep(mov["pausa_ms"] / 1000.0)

        # Evento de finalización de Demo
        await vehicle_ws_manager.broadcast_to_vehicle(id_vehiculo, {
            "tipo_evento": "FIN_DEMO",
            "id_vehiculo": id_vehiculo,
            "id_demo": id_demo,
            "marca_temporal": datetime.now().isoformat()
        })

    except asyncio.CancelledError:
        # Manejo de cancelación explícita de la Demo
        await vehicle_ws_manager.broadcast_to_vehicle(id_vehiculo, {
            "tipo_evento": "CANCELACION_DEMO",
            "id_vehiculo": id_vehiculo,
            "id_demo": id_demo,
            "marca_temporal": datetime.now().isoformat()
        })
        raise
    finally:
        # Limpiar referencia de tarea activa
        if id_vehiculo in vehicle_ws_manager.active_demos:
            del vehicle_ws_manager.active_demos[id_vehiculo]


@router.post("/vehiculos/{id_vehiculo}/demo/iniciar", summary="Iniciar una Demo en el vehículo")
async def iniciar_demo(id_vehiculo: int, data: DemoTriggerRequest):
    """Inicia la ejecución asíncrona de una demo validando concurrencia (impide 2 demos simultáneas por vehículo)."""
    if id_vehiculo in vehicle_ws_manager.active_demos and not vehicle_ws_manager.active_demos[id_vehiculo].done():
        raise HTTPException(status_code=400, detail="Ya existe una DEMO en ejecución para este vehículo.")

    # Lanzar tarea en segundo plano vinculada al vehículo
    task = asyncio.create_task(ejecutar_secuencia_demo(id_vehiculo, data.id_demo))
    vehicle_ws_manager.active_demos[id_vehiculo] = task

    return {"mensaje": f"Demo {data.id_demo} iniciada exitosamente para el vehículo {id_vehiculo}"}


@router.post("/vehiculos/{id_vehiculo}/demo/cancelar", summary="Cancelar la Demo en ejecución")
async def cancelar_demo(id_vehiculo: int):
    """Cancela inmediatamente la emisión de movimientos de la Demo activa para el vehículo."""
    if id_vehiculo in vehicle_ws_manager.active_demos:
        task = vehicle_ws_manager.active_demos[id_vehiculo]
        if not task.done():
            task.cancel()
            return {"mensaje": f"Demo cancelada para el vehículo {id_vehiculo}"}
    
    raise HTTPException(status_code=404, detail="No hay ninguna DEMO activa en este momento para el vehículo.")


# --- ENDPOINT WEBSOCKET POR VEHÍCULO ---

@router.websocket("/ws/vehiculos/{id_vehiculo}")
async def websocket_vehiculo_endpoint(websocket: WebSocket, id_vehiculo: int):
    """WebSocket asociado al ID del vehículo. Envía el último estado disponible al conectar y aísla los eventos."""
    await vehicle_ws_manager.connect(id_vehiculo, websocket)
    
    # Consultar RDS y enviar el último estado disponible al abrir la conexión
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_obtener_estado", (id_vehiculo,))
            estado_inicial = cursor.fetchone()
            await websocket.send_json({
                "tipo_evento": "ESTADO_INICIAL",
                "id_vehiculo": id_vehiculo,
                "datos": estado_inicial if estado_inicial else {"conectado": False},
                "marca_temporal": datetime.now().isoformat()
            })
    except Exception as e:
        await websocket.send_json({"tipo_evento": "ERROR", "detalle": str(e)})
    finally:
        connection.close()

    try:
        while True:
            # Mantener la conexión abierta y escuchar posibles mensajes de clientes
            data = await websocket.receive_text()
            # Opcional: puedes procesar comandos de control entrantes aquí si se requiere
    except WebSocketDisconnect:
        vehicle_ws_manager.disconnect(id_vehiculo, websocket)