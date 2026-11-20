from app.repositories.base_repository import BaseRepository
from app.schemas.schemas import ComandoCreate, ComandoUpdate


class ComandoRepository(BaseRepository):
    def crear(self, data: ComandoCreate):
        return self._call(
            "sp_crear_comando",
            (data.id_vehiculo, data.nombre, data.codigo, data.descripcion),
            fetch="one", commit=True,
        )

    def listar_por_vehiculo(self, id_vehiculo: int):
        return self._call("sp_obtener_comandos_vehiculo", (id_vehiculo,), fetch="all")

    def actualizar(self, id_comando: int, data: ComandoUpdate):
        self._call(
            "sp_actualizar_comando",
            (id_comando, data.nombre, data.codigo, data.descripcion, data.activo),
            commit=True,
        )

    def eliminar(self, id_comando: int):
        self._call("sp_eliminar_comando", (id_comando,), commit=True)
