from app.core.base_controller import BaseController
from app.core.decorators import manejar_errores
from app.repositories.demo_repository import DemoRepository
from app.schemas.schemas import (
    DemoCreate, DemoUpdate, DemoMovimientoCreate, DemoMovimientoUpdate,
)


class DemoController(BaseController):
    def __init__(self, repo: DemoRepository | None = None):
        self.repo = repo or DemoRepository()
        super().__init__(prefix="/demos", tags=["Demos y Movimientos"])

    def _register_routes(self) -> None:
        r = self.router
        # Demos
        r.add_api_route("/", self.crear, methods=["POST"], summary="Crear una nueva demo")
        r.add_api_route("/vehiculo/{id_vehiculo}", self.listar_por_vehiculo, methods=["GET"],
                        summary="Obtener demos de un vehículo")
        r.add_api_route("/{id_demo}", self.actualizar, methods=["PUT"], summary="Actualizar una demo")
        r.add_api_route("/{id_demo}", self.eliminar, methods=["DELETE"], summary="Eliminar una demo")
        # Movimientos
        r.add_api_route("/movimientos", self.agregar_movimiento, methods=["POST"],
                        summary="Agregar movimiento a una demo")
        r.add_api_route("/{id_demo}/movimientos", self.obtener_movimientos, methods=["GET"],
                        summary="Obtener movimientos de una demo")
        r.add_api_route("/movimientos/{id_demo_movimiento}", self.actualizar_movimiento, methods=["PUT"],
                        summary="Actualizar movimiento de una demo")
        r.add_api_route("/movimientos/{id_demo_movimiento}", self.eliminar_movimiento, methods=["DELETE"],
                        summary="Eliminar movimiento de una demo")

    # --- Demos ---
    @manejar_errores
    def crear(self, data: DemoCreate):
        resultado = self.repo.crear(data)
        return {
            "mensaje": "Demo creada exitosamente",
            "id_demo": resultado.get("id_demo") if resultado else None,
        }

    @manejar_errores
    def listar_por_vehiculo(self, id_vehiculo: int):
        return self.repo.listar_por_vehiculo(id_vehiculo)

    @manejar_errores
    def actualizar(self, id_demo: int, data: DemoUpdate):
        self.repo.actualizar(id_demo, data)
        return {"mensaje": f"Demo con ID {id_demo} actualizada exitosamente"}

    @manejar_errores
    def eliminar(self, id_demo: int):
        self.repo.eliminar(id_demo)
        return {"mensaje": f"Demo con ID {id_demo} eliminada exitosamente"}

    # --- Movimientos ---
    @manejar_errores
    def agregar_movimiento(self, data: DemoMovimientoCreate):
        self.repo.agregar_movimiento(data)
        return {"mensaje": "Movimiento de demo agregado exitosamente"}

    @manejar_errores
    def obtener_movimientos(self, id_demo: int):
        return self.repo.obtener_movimientos(id_demo)

    @manejar_errores
    def actualizar_movimiento(self, id_demo_movimiento: int, data: DemoMovimientoUpdate):
        self.repo.actualizar_movimiento(id_demo_movimiento, data)
        return {"mensaje": f"Movimiento de demo con ID {id_demo_movimiento} actualizado exitosamente"}

    @manejar_errores
    def eliminar_movimiento(self, id_demo_movimiento: int):
        self.repo.eliminar_movimiento(id_demo_movimiento)
        return {"mensaje": f"Movimiento de demo con ID {id_demo_movimiento} eliminado exitosamente"}


router = DemoController().router
