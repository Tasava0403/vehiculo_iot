from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import get_db_connection

router = APIRouter(prefix="/demos", tags=["Demos y Movimientos"])

# --- Modelos Pydantic para Demos ---
class DemoCreate(BaseModel):
    id_vehiculo: int
    nombre: str
    descripcion: str | None = None

class DemoUpdate(BaseModel):
    nombre: str
    descripcion: str | None = None
    activo: bool

# --- Modelos Pydantic para Movimientos de Demo ---
class DemoMovimientoCreate(BaseModel):
    id_demo: int
    id_comando: int
    orden: int
    duracion_ms: int
    pausa_ms: int = 0

class DemoMovimientoUpdate(BaseModel):
    id_comando: int
    orden: int
    duracion_ms: int
    pausa_ms: int


# --- ENDPOINTS PARA DEMOS ---

@router.post("/", summary="Crear una nueva demo")
def crear_demo(data: DemoCreate):
    """Ejecuta el procedimiento almacenado sp_crear_demo[cite: 1]."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_crear_demo", (
                data.id_vehiculo,
                data.nombre,
                data.descripcion
            ))
            connection.commit()
            resultado = cursor.fetchone()
            return {
                "mensaje": "Demo creada exitosamente",
                "id_demo": resultado.get("id_demo") if resultado else None
            }
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()


@router.get("/vehiculo/{id_vehiculo}", summary="Obtener demos de un vehículo")
def obtener_demos(id_vehiculo: int):
    """Ejecuta el procedimiento almacenado sp_obtener_demos[cite: 1]."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_obtener_demos", (id_vehiculo,))
            return cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()


@router.put("/{id_demo}", summary="Actualizar una demo")
def actualizar_demo(id_demo: int, data: DemoUpdate):
    """Ejecuta el procedimiento almacenado sp_actualizar_demo[cite: 1]."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_actualizar_demo", (
                id_demo,
                data.nombre,
                data.descripcion,
                data.activo
            ))
            connection.commit()
            return {"mensaje": f"Demo con ID {id_demo} actualizada exitosamente"}
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()


@router.delete("/{id_demo}", summary="Eliminar una demo")
def eliminar_demo(id_demo: int):
    """Ejecuta el procedimiento almacenado sp_eliminar_demo[cite: 1]."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_eliminar_demo", (id_demo,))
            connection.commit()
            return {"mensaje": f"Demo con ID {id_demo} eliminada exitosamente"}
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()


# --- ENDPOINTS PARA MOVIMIENTOS DE DEMO ---

@router.post("/movimientos", summary="Agregar movimiento a una demo")
def agregar_movimiento_demo(data: DemoMovimientoCreate):
    """Ejecuta el procedimiento almacenado sp_agregar_movimiento_demo[cite: 1]."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_agregar_movimiento_demo", (
                data.id_demo,
                data.id_comando,
                data.orden,
                data.duracion_ms,
                data.pausa_ms
            ))
            connection.commit()
            return {"mensaje": "Movimiento de demo agregado exitosamente"}
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()


@router.get("/{id_demo}/movimientos", summary="Obtener movimientos de una demo")
def obtener_movimientos_demo(id_demo: int):
    """Ejecuta el procedimiento almacenado sp_obtener_movimientos_demo[cite: 1]."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_obtener_movimientos_demo", (id_demo,))
            return cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()


@router.put("/movimientos/{id_demo_movimiento}", summary="Actualizar movimiento de una demo")
def actualizar_movimiento_demo(id_demo_movimiento: int, data: DemoMovimientoUpdate):
    """Ejecuta el procedimiento almacenado sp_actualizar_movimiento_demo[cite: 1]."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_actualizar_movimiento_demo", (
                id_demo_movimiento,
                data.id_comando,
                data.orden,
                data.duracion_ms,
                data.pausa_ms
            ))
            connection.commit()
            return {"mensaje": f"Movimiento de demo con ID {id_demo_movimiento} actualizado exitosamente"}
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()


@router.delete("/movimientos/{id_demo_movimiento}", summary="Eliminar movimiento de una demo")
def eliminar_movimiento_demo(id_demo_movimiento: int):
    """Ejecuta el procedimiento almacenado sp_eliminar_movimiento_demo[cite: 1]."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_eliminar_movimiento_demo", (id_demo_movimiento,))
            connection.commit()
            return {"mensaje": f"Movimiento de demo con ID {id_demo_movimiento} eliminado exitosamente"}
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()