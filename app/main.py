import os
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.routers import vehiculos, comandos, demos, monitoreo
from app.models.estado import Estado
from app.services.status_service import StatusService
from app.websocket.websocket_manager import websocket_manager
from app.database import get_db_connection


class ServidorIoT:
    """Construye y configura la aplicación FastAPI."""

    def __init__(self):
        self.app = FastAPI(
            title="Servidor IoT",
            description="API HTTP y WebSocket para práctica IoT",
            version="1.0",
        )
        self._configurar_cors()
        self.status_service = StatusService()
        self.websocket_manager = websocket_manager
        self._registrar_routers()
        self._registrar_rutas()

    def _configurar_cors(self) -> None:
        """Solo orígenes autorizados (CORS_ORIGINS, separados por coma; sin ruta)."""
        origenes = [
            o.strip()
            for o in os.getenv(
                "CORS_ORIGINS", "https://tasava0403.github.io,http://127.0.0.1:5500"
            ).split(",")
            if o.strip()
        ]
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origenes,
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type"],
        )

    def _registrar_routers(self) -> None:
        for modulo in (comandos, vehiculos, demos, monitoreo):
            self.app.include_router(modulo.router)

    def _registrar_rutas(self) -> None:
        self.app.add_api_route("/status", self.obtener_estado, methods=["GET"])
        self.app.add_api_route("/status", self.cambiar_estado, methods=["POST"])
        self.app.add_api_route("/salud/db", self.salud_bd, methods=["GET"], tags=["Salud"])
        self.app.add_api_websocket_route("/ws", self.websocket_endpoint)

    # --- handlers ---
    def obtener_estado(self):
        return self.status_service.obtener_estado()

    async def cambiar_estado(self, estado: Estado):
        nuevo_estado = self.status_service.guardar_estado(estado.status)
        await self.websocket_manager.enviar_a_todos(nuevo_estado)
        return nuevo_estado

    def salud_bd(self):
        """Diagnóstico seguro: ejecuta SELECT 1 y no expone detalles internos."""
        try:
            conexion = get_db_connection()
            try:
                with conexion.cursor() as cursor:
                    cursor.execute("SELECT 1")
            finally:
                conexion.close()
            return {"base_datos": "disponible"}
        except Exception:
            raise HTTPException(status_code=503, detail="Base de datos no disponible")

    async def websocket_endpoint(self, websocket: WebSocket):
        await self.websocket_manager.conectar(websocket)
        await websocket.send_json(self.status_service.obtener_estado())
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            self.websocket_manager.desconectar(websocket)

    def run(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        import uvicorn
        uvicorn.run("app.main:app", host=host, port=port)


servidor = ServidorIoT()
app = servidor.app  # uvicorn app.main:app

if __name__ == "__main__":
    servidor.run()