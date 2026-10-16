from fastapi import WebSocket
from typing import List, Dict, Set

class WebSocketManager:
    def __init__(self):
        # Para conexiones globales (ej. /ws)
        self.clientes_globales: List[WebSocket] = []
        # Para conexiones por vehículo (ej. /ws/vehiculos/{id_vehiculo})
        self.clientes_por_vehiculo: Dict[int, Set[WebSocket]] = {}

    # --- Métodos Globales ---
    async def conectar(self, websocket: WebSocket):
        await websocket.accept()
        self.clientes_globales.append(websocket)

    def desconectar(self, websocket: WebSocket):
        if websocket in self.clientes_globales:
            self.clientes_globales.remove(websocket)

    async def enviar_a_todos(self, mensaje):
        desconectados = []
        for cliente in self.clientes_globales:
            try:
                await cliente.send_json(mensaje)
            except Exception:
                desconectados.append(cliente)
        for cliente in desconectados:
            self.desconectar(cliente)

    # --- Métodos Específicos por Vehículo ---
    async def conectar_vehiculo(self, id_vehiculo: int, websocket: WebSocket):
        await websocket.accept()
        if id_vehiculo not in self.clientes_por_vehiculo:
            self.clientes_por_vehiculo[id_vehiculo] = set()
        self.clientes_por_vehiculo[id_vehiculo].add(websocket)

    def desconectar_vehiculo(self, id_vehiculo: int, websocket: WebSocket):
        if id_vehiculo in self.clientes_por_vehiculo:
            self.clientes_por_vehiculo[id_vehiculo].discard(websocket)
            if not self.clientes_por_vehiculo[id_vehiculo]:
                del self.clientes_por_vehiculo[id_vehiculo]

    async def enviar_a_vehiculo(self, id_vehiculo: int, mensaje: dict):
        if id_vehiculo in self.clientes_por_vehiculo:
            desconectados = []
            for websocket in self.clientes_por_vehiculo[id_vehiculo]:
                try:
                    await websocket.send_json(mensaje)
                except Exception:
                    desconectados.append(websocket)
            for ws in desconectados:
                self.desconectar_vehiculo(id_vehiculo, ws)