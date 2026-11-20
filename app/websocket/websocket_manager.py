import asyncio
from typing import Dict, Set, Union

from fastapi import WebSocket


class ConnectionPool:
    """Conjunto de WebSockets con envío y limpieza de desconectados."""

    def __init__(self):
        self._clientes: Set[WebSocket] = set()

    def __len__(self) -> int:
        return len(self._clientes)

    def agregar(self, websocket: WebSocket) -> None:
        self._clientes.add(websocket)

    def quitar(self, websocket: WebSocket) -> None:
        self._clientes.discard(websocket)

    async def enviar(self, mensaje: Union[int, str, dict]) -> None:
        """dict -> JSON; cualquier otro valor -> texto plano."""
        caidos = []
        for ws in list(self._clientes):  # copia: el set puede cambiar
            try:
                if isinstance(mensaje, dict):
                    await ws.send_json(mensaje)
                else:
                    await ws.send_text(str(mensaje))
            except Exception:
                caidos.append(ws)
        for ws in caidos:
            self.quitar(ws)


class WebSocketManager:
    """Administra conexiones globales, por vehículo y demos activas."""

    def __init__(self):
        self._globales = ConnectionPool()
        self._por_vehiculo: Dict[int, ConnectionPool] = {}
        self.active_demos: Dict[int, asyncio.Task] = {}

    # --- Globales (/ws) ---
    async def conectar(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._globales.agregar(websocket)

    def desconectar(self, websocket: WebSocket) -> None:
        self._globales.quitar(websocket)

    async def enviar_a_todos(self, mensaje) -> None:
        await self._globales.enviar(mensaje)

    # --- Por vehículo (/ws/vehiculos/{id_vehiculo}) ---
    async def conectar_vehiculo(self, id_vehiculo: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._por_vehiculo.setdefault(id_vehiculo, ConnectionPool()).agregar(websocket)

    def desconectar_vehiculo(self, id_vehiculo: int, websocket: WebSocket) -> None:
        pool = self._por_vehiculo.get(id_vehiculo)
        if pool is None:
            return
        pool.quitar(websocket)
        if len(pool) == 0:
            del self._por_vehiculo[id_vehiculo]

    async def enviar_a_vehiculo(self, id_vehiculo: int, mensaje: Union[int, str, dict]) -> None:
        """Acepta un código numérico (texto plano) o un dict (JSON)."""
        pool = self._por_vehiculo.get(id_vehiculo)
        if pool is None:
            return
        await pool.enviar(mensaje)
        if len(pool) == 0:
            self._por_vehiculo.pop(id_vehiculo, None)

    # --- Demos activas ---
    def demo_activa(self, id_vehiculo: int) -> bool:
        task = self.active_demos.get(id_vehiculo)
        return task is not None and not task.done()

    def registrar_demo(self, id_vehiculo: int, task: asyncio.Task) -> None:
        self.active_demos[id_vehiculo] = task

    def quitar_demo(self, id_vehiculo: int) -> None:
        self.active_demos.pop(id_vehiculo, None)


# Instancia compartida por main.py, routers y servicios
websocket_manager = WebSocketManager()
