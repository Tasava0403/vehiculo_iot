from app.core.base_controller import BaseController
from app.core.decorators import manejar_errores
from app.repositories.comando_repository import ComandoRepository
from app.schemas.schemas import ComandoCreate, ComandoUpdate


class ComandoController(BaseController):
    def __init__(self, repo: ComandoRepository | None = None):
        self.repo = repo or ComandoRepository()
        super().__init__(prefix="/comandos", tags=["Comandos"])

    def _register_routes(self) -> None:
        r = self.router
        r.add_api_route("/", self.crear, methods=["POST"], summary="Crear un nuevo comando")
        r.add_api_route("/vehiculo/{id_vehiculo}", self.listar_por_vehiculo, methods=["GET"],
                        summary="Obtener comandos de un vehículo")
        r.add_api_route("/{id_comando}", self.actualizar, methods=["PUT"], summary="Actualizar un comando")
        r.add_api_route("/{id_comando}", self.eliminar, methods=["DELETE"], summary="Eliminar un comando")

    @manejar_errores
    def crear(self, data: ComandoCreate):
        resultado = self.repo.crear(data)
        return {
            "mensaje": "Comando creado exitosamente",
            "id_comando": resultado.get("id_comando") if resultado else None,
        }

    @manejar_errores
    def listar_por_vehiculo(self, id_vehiculo: int):
        return self.repo.listar_por_vehiculo(id_vehiculo)

    @manejar_errores
    def actualizar(self, id_comando: int, data: ComandoUpdate):
        self.repo.actualizar(id_comando, data)
        return {"mensaje": f"Comando con ID {id_comando} actualizado exitosamente"}

    @manejar_errores
    def eliminar(self, id_comando: int):
        self.repo.eliminar(id_comando)
        return {"mensaje": f"Comando con ID {id_comando} eliminado exitosamente"}


router = ComandoController().router
