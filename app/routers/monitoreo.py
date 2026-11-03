import asyncio
import json
from datetime import datetime, date
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Dict, Set, Union
from app.database import get_db_connection

router = APIRouter(tags=["Monitoreo, Historial y Demos WebSocket"])

# --- ADMINISTRADOR DE WEBSOCKETS POR VEHÍCULO ---
class VehicleWebSocketManager:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.active_demos: Dict[int, asyncio.Task] = {}

    async def connect(self, id_vehiculo: int, websocket: WebSocket):
        await websocket.accept()
        if id_vehiculo not in self.active_connections:
            self.active_connections[id_vehiculo] = set()
        self.active_connections[id_vehiculo].add(websocket)

    def disconnect(self, id_vehiculo: int, websocket: WebSocket):
        if id_vehiculo in self.active_connections:
            self.active_connections[id_vehiculo].discard(websocket)
            if not self.active_connections[id_vehiculo]:
                del self.active_connections[id_vehiculo]

    async def broadcast_to_vehicle(self, id_vehiculo: int, message: Union[int, dict]):
        """Permite enviar tanto un código numérico (texto plano) como un diccionario estructurado (JSON)."""
        if id_vehiculo in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[id_vehiculo]:
                try:
                    if isinstance(message, dict):
                        await websocket.send_json(message)
                    else:
                        await websocket.send_text(str(message))
                except Exception:
                    disconnected.append(websocket)
            for ws in disconnected:
                self.disconnect(id_vehiculo, ws)

# Instancia requerida por los endpoints y WebSockets de este archivo
vehicle_ws_manager = VehicleWebSocketManager()

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
    """Ejecuta el procedimiento almacenado sp_obtener_estado."""
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
    """Actualiza el estado, registra automáticamente en el historial y notifica por WebSocket."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 1. Actualizar el estado del vehículo
            cursor.callproc("sp_actualizar_estado", (
                data.id_vehiculo,
                data.id_comando,
                data.conectado
            ))

            # 2. Registrar automáticamente en el historial si hay comando y está conectado
            if data.id_comando is not None and data.conectado:
                cursor.callproc("sp_registrar_historial", (
                    data.id_vehiculo,
                    data.id_comando,
                    "AUTOMATICO"
                ))

            connection.commit()

            # 3. Consultar estado actualizado
            cursor.callproc("sp_obtener_estado", (data.id_vehiculo,))
            estado_actual = cursor.fetchone()

        # Notificar vía WebSocket el código del comando en texto plano
        codigo_enviar = estado_actual.get("codigo") if estado_actual else 11
        await vehicle_ws_manager.broadcast_to_vehicle(data.id_vehiculo, codigo_enviar)

        return {
            "mensaje": "Estado actualizado e historial registrado exitosamente", 
            "estado": estado_actual
        }
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()


@router.post("/historial/registrar", summary="Registrar movimiento en historial")
def registrar_historial(data: HistorialCreate):
    """Ejecuta sp_registrar_historial."""
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
    """Ejecuta sp_obtener_historial limitado a los 10 registros más recientes."""
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
    """Procesa los N movimientos de la demo de forma asíncrona."""
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
        # Evento de inicio de Demo (Diccionario estructurado)
        await vehicle_ws_manager.broadcast_to_vehicle(id_vehiculo, {
            "tipo_evento": "INICIO_DEMO",
            "id_vehiculo": id_vehiculo,
            "id_demo": id_demo,
            "total_movimientos": len(movimientos),
            "marca_temporal": datetime.now().isoformat()
        })

        for mov in movimientos:
            # 1. Actualizar estado del vehículo
            conn_up = get_db_connection()
            try:
                with conn_up.cursor() as cur_up:
                    cur_up.callproc("sp_actualizar_estado", (id_vehiculo, mov["id_comando"], True))
                    conn_up.commit()
            except Exception:
                conn_up.rollback()
            finally:
                conn_up.close()

            # 2. Emitir únicamente el código numérico del movimiento vía WebSocket
            await vehicle_ws_manager.broadcast_to_vehicle(id_vehiculo, mov["codigo"])

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
        # Manejo de cancelación explícita
        await vehicle_ws_manager.broadcast_to_vehicle(id_vehiculo, {
            "tipo_evento": "CANCELACION_DEMO",
            "id_vehiculo": id_vehiculo,
            "id_demo": id_demo,
            "marca_temporal": datetime.now().isoformat()
        })
        raise
    finally:
        if id_vehiculo in vehicle_ws_manager.active_demos:
            del vehicle_ws_manager.active_demos[id_vehiculo]


@router.post("/vehiculos/{id_vehiculo}/demo/iniciar", summary="Iniciar una Demo en el vehículo")
async def iniciar_demo(id_vehiculo: int, data: DemoTriggerRequest):
    """Inicia la ejecución asíncrona de una demo."""
    if id_vehiculo in vehicle_ws_manager.active_demos and not vehicle_ws_manager.active_demos[id_vehiculo].done():
        raise HTTPException(status_code=400, detail="Ya existe una DEMO en ejecución para este vehículo.")

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_obtener_movimientos_demo", (data.id_demo,))
            movimientos = cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los movimientos de la demo: {str(e)}")
    finally:
        connection.close()

    if not movimientos:
        raise HTTPException(status_code=404, detail="La demo no contiene movimientos registrados o no existe.")

    task = asyncio.create_task(ejecutar_secuencia_demo(id_vehiculo, data.id_demo))
    vehicle_ws_manager.active_demos[id_vehiculo] = task

    movimientos_serializables = limpiar_fechas(movimientos)

    return {
        "mensaje": f"Demo {data.id_demo} iniciada exitosamente para el vehículo {id_vehiculo}",
        "total_movimientos": len(movimientos_serializables),
        "movimientos": movimientos_serializables
    }


@router.post("/vehiculos/{id_vehiculo}/demo/cancelar", summary="Cancelar la Demo en ejecución")
async def cancelar_demo(id_vehiculo: int):
    """Cancela inmediatamente la demo activa."""
    if id_vehiculo in vehicle_ws_manager.active_demos:
        task = vehicle_ws_manager.active_demos[id_vehiculo]
        if not task.done():
            task.cancel()
            return {"mensaje": f"Demo cancelada para el vehículo {id_vehiculo}"}
    
    raise HTTPException(status_code=404, detail="No hay ninguna DEMO activa en este momento para el vehículo.")


# --- ENDPOINT WEBSOCKET POR VEHÍCULO ---

def limpiar_fechas(obj):
    """Convierte de forma recursiva los campos datetime/date a string ISO."""
    if isinstance(obj, dict):
        return {k: limpiar_fechas(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [limpiar_fechas(v) for v in obj]
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return obj


@router.websocket("/ws/vehiculos/{id_vehiculo}")
async def websocket_vehiculo_endpoint(websocket: WebSocket, id_vehiculo: int):
    """WebSocket asociado al ID del vehículo."""
    await vehicle_ws_manager.connect(id_vehiculo, websocket)
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_obtener_estado", (id_vehiculo,))
            estado_inicial = cursor.fetchone()

            codigo_inicial = estado_inicial.get("codigo") if estado_inicial else 11
            await websocket.send_text(str(codigo_inicial))
    except Exception as e:
        await websocket.send_json({"tipo_evento": "ERROR", "detalle": str(e)})
    finally:
        connection.close()

    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        vehicle_ws_manager.disconnect(id_vehiculo, websocket)