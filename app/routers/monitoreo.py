from fastapi import WebSocket, WebSocketDisconnect
from app.core.base_controller import BaseController
from app.core.decorators import manejar_errores
from app.repositories.comando_repository import ComandoRepository
from app.repositories.demo_repository import DemoRepository
from app.repositories.monitoreo_repository import EstadoRepository, HistorialRepository
from app.schemas.schemas import EstadoUpdate, HistorialCreate, DemoTriggerRequest
from app.services.demo_service import DemoService
from app.websocket.websocket_manager import WebSocketManager, websocket_manager

CODIGO_POR_DEFECTO = 11  # código enviado cuando el vehículo no tiene estado previo


class MonitoreoController(BaseController):
    def __init__(
        self,
        estado_repo: EstadoRepository | None = None,
        historial_repo: HistorialRepository | None = None,
        ws_manager: WebSocketManager | None = None,
        demo_service: DemoService | None = None,
    ):
        self.estado_repo = estado_repo or EstadoRepository()
        self.historial_repo = historial_repo or HistorialRepository()
        self.ws_manager = ws_manager or websocket_manager
        self.demo_service = demo_service or DemoService(
            DemoRepository(), self.estado_repo, ComandoRepository(), self.ws_manager
        )
        super().__init__(tags=["Monitoreo, Historial y Demos WebSocket"])

    def _register_routes(self) -> None:
        r = self.router
        r.add_api_route("/vehiculos/{id_vehiculo}/estado", self.obtener_estado, methods=["GET"],
                        summary="Obtener estado actual del vehículo")
        r.add_api_route("/vehiculos/estado", self.actualizar_estado, methods=["POST"],
                        summary="Actualizar estado del vehículo")
        r.add_api_route("/historial/registrar", self.registrar_historial, methods=["POST"],
                        summary="Registrar movimiento en historial")
        r.add_api_route("/vehiculos/{id_vehiculo}/historial/ultimos-10", self.ultimos_10_historial,
                        methods=["GET"], summary="Obtener últimos 10 movimientos del historial")
        r.add_api_route("/vehiculos/{id_vehiculo}/demo/iniciar", self.iniciar_demo, methods=["POST"],
                        summary="Iniciar una Demo en el vehículo")
        r.add_api_route("/vehiculos/{id_vehiculo}/demo/cancelar", self.cancelar_demo, methods=["POST"],
                        summary="Cancelar la Demo en ejecución")
        r.add_api_websocket_route("/ws/vehiculos/{id_vehiculo}", self.websocket_vehiculo)

    # --- HTTP ---
    @manejar_errores
    def obtener_estado(self, id_vehiculo: int):
        resultado = self.estado_repo.obtener(id_vehiculo)
        if not resultado:
            return {"id_vehiculo": id_vehiculo, "conectado": False, "mensaje": "Sin estado previo"}
        return resultado

    @manejar_errores
    async def actualizar_estado(self, data: EstadoUpdate):
        estado_actual = self.estado_repo.actualizar_y_registrar(data)
        codigo = estado_actual.get("codigo") if estado_actual else CODIGO_POR_DEFECTO
        await self.ws_manager.enviar_a_vehiculo(data.id_vehiculo, codigo)
        return {
            "mensaje": "Estado actualizado e historial registrado exitosamente",
            "estado": estado_actual,
        }

    @manejar_errores
    def registrar_historial(self, data: HistorialCreate):
        self.historial_repo.registrar(data)
        return {"mensaje": "Movimiento registrado en el historial exitosamente"}

    @manejar_errores
    def ultimos_10_historial(self, id_vehiculo: int):
        return self.historial_repo.ultimos(id_vehiculo, 10)

    @manejar_errores
    async def iniciar_demo(self, id_vehiculo: int, data: DemoTriggerRequest):
        return await self.demo_service.iniciar(id_vehiculo, data.id_demo)

    @manejar_errores
    async def cancelar_demo(self, id_vehiculo: int):
        return await self.demo_service.cancelar(id_vehiculo)

    # --- WebSocket ---
    async def websocket_vehiculo(self, websocket: WebSocket, id_vehiculo: int):
        await self.ws_manager.conectar_vehiculo(id_vehiculo, websocket)
        try:
            estado = self.estado_repo.obtener(id_vehiculo)
            codigo = estado.get("codigo") if estado else CODIGO_POR_DEFECTO
            await websocket.send_text(str(codigo))
        except Exception as e:
            await websocket.send_json({"tipo_evento": "ERROR", "detalle": str(e)})

        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            self.ws_manager.desconectar_vehiculo(id_vehiculo, websocket)


router = MonitoreoController().router
