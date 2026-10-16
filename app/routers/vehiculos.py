from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import get_db_connection

router = APIRouter(prefix="/vehiculos", tags=["Vehículos"])

# Modelos Pydantic para la validación de datos
class VehiculoCreate(BaseModel):
    nombre: str
    modelo: str | None = None
    descripcion: str | None = None
    microcontrolador: str | None = None

class VehiculoUpdate(BaseModel):
    nombre: str
    modelo: str | None = None
    descripcion: str | None = None
    microcontrolador: str | None = None
    activo: bool


@router.post("/", summary="Crear un nuevo vehículo")
def crear_vehiculo(data: VehiculoCreate):
    """Ejecuta el procedimiento almacenado sp_crear_vehiculo[cite: 1]."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_crear_vehiculo", (
                data.nombre,
                data.modelo,
                data.descripcion,
                data.microcontrolador
            ))
            connection.commit()
            resultado = cursor.fetchone()
            return {
                "mensaje": "Vehículo creado exitosamente",
                "id_vehiculo": resultado.get("id_vehiculo") if resultado else None
            }
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()


@router.get("/", summary="Obtener todos los vehículos")
def obtener_vehiculos():
    """Ejecuta el procedimiento almacenado sp_obtener_vehiculos[cite: 1]."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_obtener_vehiculos")
            return cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()


@router.get("/{id_vehiculo}", summary="Obtener un vehículo por ID")
def obtener_vehiculo(id_vehiculo: int):
    """Ejecuta el procedimiento almacenado sp_obtener_vehiculo[cite: 1]."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_obtener_vehiculo", (id_vehiculo,))
            resultado = cursor.fetchone()
            if not resultado:
                raise HTTPException(status_code=404, detail="Vehículo no encontrado")
            return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()


@router.put("/{id_vehiculo}", summary="Actualizar un vehículo")
def actualizar_vehiculo(id_vehiculo: int, data: VehiculoUpdate):
    """Ejecuta el procedimiento almacenado sp_actualizar_vehiculo[cite: 1]."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_actualizar_vehiculo", (
                id_vehiculo,
                data.nombre,
                data.modelo,
                data.descripcion,
                data.microcontrolador,
                data.activo
            ))
            connection.commit()
            return {"mensaje": f"Vehículo con ID {id_vehiculo} actualizado exitosamente"}
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()


@router.delete("/{id_vehiculo}", summary="Eliminar un vehículo")
def eliminar_vehiculo(id_vehiculo: int):
    """Ejecuta el procedimiento almacenado sp_eliminar_vehiculo[cite: 1]."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_eliminar_vehiculo", (id_vehiculo,))
            connection.commit()
            return {"mensaje": f"Vehículo con ID {id_vehiculo} eliminado exitosamente"}
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()