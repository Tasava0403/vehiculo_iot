import asyncio
from datetime import datetime
from fastapi import HTTPException

from app.core.utils import limpiar_fechas
from app.repositories.comando_repository import ComandoRepository
from app.repositories.demo_repository import DemoRepository
from app.repositories.monitoreo_repository import EstadoRepository
from app.websocket.websocket_manager import WebSocketManager


CODIGO_DETENER = 11  # comando "detener todo": estado al que vuelve el vehículo tras una demo


class DemoService:
    """Lógica de negocio para iniciar, ejecutar y cancelar demos."""

    def __init__(
        self,
        demo_repo: DemoRepository,
        estado_repo: EstadoRepository,
        comando_repo: ComandoRepository,
        ws_manager: WebSocketManager,
    ):
        self.demo_repo = demo_repo
        self.estado_repo = estado_repo
        self.comando_repo = comando_repo
        self.ws = ws_manager

    # --- API pública ---
    async def iniciar(self, id_vehiculo: int, id_demo: int) -> dict:
        if self.ws.demo_activa(id_vehiculo):
            raise HTTPException(400, "Ya existe una DEMO en ejecución para este vehículo.")

        try:
            movimientos = self.demo_repo.obtener_movimientos(id_demo)
        except Exception as e:
            raise HTTPException(500, f"Error al obtener los movimientos de la demo: {e}")

        if not movimientos:
            raise HTTPException(404, "La demo no contiene movimientos registrados o no existe.")

        task = asyncio.create_task(self._ejecutar_secuencia(id_vehiculo, id_demo))
        self.ws.registrar_demo(id_vehiculo, task)

        serializables = limpiar_fechas(movimientos)
        return {
            "mensaje": f"Demo {id_demo} iniciada exitosamente para el vehículo {id_vehiculo}",
            "total_movimientos": len(serializables),
            "movimientos": serializables,
        }

    async def cancelar(self, id_vehiculo: int) -> dict:
        if self.ws.demo_activa(id_vehiculo):
            self.ws.active_demos[id_vehiculo].cancel()
            return {"mensaje": f"Demo cancelada para el vehículo {id_vehiculo}"}
        raise HTTPException(404, "No hay ninguna DEMO activa en este momento para el vehículo.")

    # --- internos ---
    @staticmethod
    def _evento(tipo: str, id_vehiculo: int, **extra) -> dict:
        return {
            "tipo_evento": tipo,
            "id_vehiculo": id_vehiculo,
            **extra,
            "marca_temporal": datetime.now().isoformat(),
        }

    async def _detener_vehiculo(self, id_vehiculo: int) -> None:
        """Deja el vehículo en 'detener todo' (código 11) y avisa por WebSocket."""
        try:
            comandos = self.comando_repo.listar_por_vehiculo(id_vehiculo)
            detener = next(
                (c for c in comandos if int(c["codigo"]) == CODIGO_DETENER), None
            )
            if detener is not None:
                self.estado_repo.actualizar(id_vehiculo, detener["id_comando"], True)
        except Exception:
            pass  # aun si falla la BD, se avisa al vehículo que se detenga
        await self.ws.enviar_a_vehiculo(id_vehiculo, CODIGO_DETENER)

    async def _ejecutar_secuencia(self, id_vehiculo: int, id_demo: int) -> None:
        try:
            try:
                movimientos = self.demo_repo.obtener_movimientos(id_demo)
            except Exception as e:
                await self.ws.enviar_a_vehiculo(
                    id_vehiculo, self._evento("ERROR_DEMO", id_vehiculo, error=str(e)))
                return

            if not movimientos:
                await self.ws.enviar_a_vehiculo(
                    id_vehiculo,
                    self._evento("ERROR_DEMO", id_vehiculo,
                                 error="La demo no contiene movimientos registrados."))
                return

            await self.ws.enviar_a_vehiculo(
                id_vehiculo,
                self._evento("INICIO_DEMO", id_vehiculo, id_demo=id_demo,
                             total_movimientos=len(movimientos)))

            for mov in movimientos:
                try:
                    self.estado_repo.actualizar(id_vehiculo, mov["id_comando"], True)
                except Exception:
                    pass  # igual que antes: un fallo de BD no detiene la demo

                await self.ws.enviar_a_vehiculo(id_vehiculo, mov["codigo"])
                await asyncio.sleep(mov["duracion_ms"] / 1000.0)
                if mov["pausa_ms"] > 0:
                    await asyncio.sleep(mov["pausa_ms"] / 1000.0)

            await self.ws.enviar_a_vehiculo(
                id_vehiculo, self._evento("FIN_DEMO", id_vehiculo, id_demo=id_demo))

        except asyncio.CancelledError:
            await self.ws.enviar_a_vehiculo(
                id_vehiculo, self._evento("CANCELACION_DEMO", id_vehiculo, id_demo=id_demo))
            raise
        finally:
            await self._detener_vehiculo(id_vehiculo)
            self.ws.quitar_demo(id_vehiculo)
