from app.repositories.base_repository import BaseRepository
from app.schemas.schemas import VehiculoCreate, VehiculoUpdate


class VehiculoRepository(BaseRepository):
    def crear(self, data: VehiculoCreate):
        return self._call(
            "sp_crear_vehiculo",
            (data.nombre, data.modelo, data.descripcion, data.microcontrolador),
            fetch="one", commit=True,
        )

    def listar(self):
        return self._call("sp_obtener_vehiculos", fetch="all")

    def obtener(self, id_vehiculo: int):
        return self._call("sp_obtener_vehiculo", (id_vehiculo,), fetch="one")

    def actualizar(self, id_vehiculo: int, data: VehiculoUpdate):
        self._call(
            "sp_actualizar_vehiculo",
            (id_vehiculo, data.nombre, data.modelo, data.descripcion,
             data.microcontrolador, data.activo),
            commit=True,
        )

    def eliminar(self, id_vehiculo: int):
        self._call("sp_eliminar_vehiculo", (id_vehiculo,), commit=True)
