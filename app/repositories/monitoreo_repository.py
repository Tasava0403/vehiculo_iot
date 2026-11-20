from app.database import get_db_connection
from app.repositories.base_repository import BaseRepository
from app.schemas.schemas import EstadoUpdate, HistorialCreate


class EstadoRepository(BaseRepository):
    def obtener(self, id_vehiculo: int):
        return self._call("sp_obtener_estado", (id_vehiculo,), fetch="one")

    def actualizar(self, id_vehiculo: int, id_comando: int | None, conectado: bool):
        self._call(
            "sp_actualizar_estado",
            (id_vehiculo, id_comando, conectado),
            commit=True,
        )

    def actualizar_y_registrar(self, data: EstadoUpdate):
        """Actualiza estado + historial en una sola transacción y
        devuelve el estado resultante."""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.callproc(
                    "sp_actualizar_estado",
                    (data.id_vehiculo, data.id_comando, data.conectado),
                )
                if data.id_comando is not None and data.conectado:
                    cursor.callproc(
                        "sp_registrar_historial",
                        (data.id_vehiculo, data.id_comando, "AUTOMATICO"),
                    )
                connection.commit()
                cursor.callproc("sp_obtener_estado", (data.id_vehiculo,))
                return cursor.fetchone()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()


class HistorialRepository(BaseRepository):
    def registrar(self, data: HistorialCreate):
        self._call(
            "sp_registrar_historial",
            (data.id_vehiculo, data.id_comando, data.origen),
            commit=True,
        )

    def ultimos(self, id_vehiculo: int, limite: int = 10):
        resultado = self._call("sp_obtener_historial", (id_vehiculo,), fetch="all")
        return resultado[:limite]
