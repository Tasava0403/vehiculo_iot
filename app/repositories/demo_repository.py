from app.repositories.base_repository import BaseRepository
from app.schemas.schemas import (
    DemoCreate, DemoUpdate, DemoMovimientoCreate, DemoMovimientoUpdate,
)


class DemoRepository(BaseRepository):
    # --- Demos ---
    def crear(self, data: DemoCreate):
        return self._call(
            "sp_crear_demo",
            (data.id_vehiculo, data.nombre, data.descripcion),
            fetch="one", commit=True,
        )

    def listar_por_vehiculo(self, id_vehiculo: int):
        return self._call("sp_obtener_demos", (id_vehiculo,), fetch="all")

    def actualizar(self, id_demo: int, data: DemoUpdate):
        self._call(
            "sp_actualizar_demo",
            (id_demo, data.nombre, data.descripcion, data.activo),
            commit=True,
        )

    def eliminar(self, id_demo: int):
        self._call("sp_eliminar_demo", (id_demo,), commit=True)

    # --- Movimientos ---
    def agregar_movimiento(self, data: DemoMovimientoCreate):
        self._call(
            "sp_agregar_movimiento_demo",
            (data.id_demo, data.id_comando, data.orden, data.duracion_ms, data.pausa_ms),
            commit=True,
        )

    def obtener_movimientos(self, id_demo: int):
        return self._call("sp_obtener_movimientos_demo", (id_demo,), fetch="all")

    def actualizar_movimiento(self, id_demo_movimiento: int, data: DemoMovimientoUpdate):
        self._call(
            "sp_actualizar_movimiento_demo",
            (id_demo_movimiento, data.id_comando, data.orden,
             data.duracion_ms, data.pausa_ms),
            commit=True,
        )

    def eliminar_movimiento(self, id_demo_movimiento: int):
        self._call("sp_eliminar_movimiento_demo", (id_demo_movimiento,), commit=True)
