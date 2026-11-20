from fastapi import HTTPException
from app.core.base_controller import BaseController
from app.core.decorators import manejar_errores
from app.repositories.vehiculo_repository import VehiculoRepository
from app.schemas.schemas import VehiculoCreate, VehiculoUpdate


class VehiculoController(BaseController):
    def __init__(self, repo: VehiculoRepository | None = None):
        self.repo = repo or VehiculoRepository()
        super().__init__(prefix="/vehiculos", tags=["Vehículos"])

    def _register_routes(self) -> None:
        r = self.router
        r.add_api_route("/", self.crear, methods=["POST"], summary="Crear un nuevo vehículo")
        r.add_api_route("/", self.listar, methods=["GET"], summary="Obtener todos los vehículos")
        r.add_api_route("/{id_vehiculo}", self.obtener, methods=["GET"], summary="Obtener un vehículo por ID")
        r.add_api_route("/{id_vehiculo}", self.actualizar, methods=["PUT"], summary="Actualizar un vehículo")
        r.add_api_route("/{id_vehiculo}", self.eliminar, methods=["DELETE"], summary="Eliminar un vehículo")

    @manejar_errores
    def crear(self, data: VehiculoCreate):
        resultado = self.repo.crear(data)
        return {
            "mensaje": "Vehículo creado exitosamente",
            "id_vehiculo": resultado.get("id_vehiculo") if resultado else None,
        }

    @manejar_errores
    def listar(self):
        return self.repo.listar()

    @manejar_errores
    def obtener(self, id_vehiculo: int):
        resultado = self.repo.obtener(id_vehiculo)
        if not resultado:
            raise HTTPException(status_code=404, detail="Vehículo no encontrado")
        return resultado

    @manejar_errores
    def actualizar(self, id_vehiculo: int, data: VehiculoUpdate):
        self.repo.actualizar(id_vehiculo, data)
        return {"mensaje": f"Vehículo con ID {id_vehiculo} actualizado exitosamente"}

    @manejar_errores
    def eliminar(self, id_vehiculo: int):
        self.repo.eliminar(id_vehiculo)
        return {"mensaje": f"Vehículo con ID {id_vehiculo} eliminado exitosamente"}


router = VehiculoController().router
