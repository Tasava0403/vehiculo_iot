from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import get_db_connection

router = APIRouter(prefix="/comandos", tags=["Comandos"])

# Modelos Pydantic para validación
class ComandoCreate(BaseModel):
    id_vehiculo: int
    nombre: str
    codigo: int
    descripcion: str | None = None

class ComandoUpdate(BaseModel):
    nombre: str
    codigo: int
    descripcion: str | None = None
    activo: bool


@router.post("/", summary="Crear un nuevo comando")
def crear_comando(data: ComandoCreate):
    """Ejecuta el procedimiento almacenado sp_crear_comando[cite: 1]."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_crear_comando", (
                data.id_vehiculo,
                data.nombre,
                data.codigo,
                data.descripcion
            ))
            connection.commit()
            resultado = cursor.fetchone()
            return {
                "mensaje": "Comando creado exitosamente",
                "id_comando": resultado.get("id_comando") if resultado else None
            }
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()


@router.get("/vehiculo/{id_vehiculo}", summary="Obtener comandos de un vehículo")
def obtener_comandos_vehiculo(id_vehiculo: int):
    """Ejecuta el procedimiento almacenado sp_obtener_comandos_vehiculo[cite: 1]."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_obtener_comandos_vehiculo", (id_vehiculo,))
            return cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()


@router.put("/{id_comando}", summary="Actualizar un comando")
def actualizar_comando(id_comando: int, data: ComandoUpdate):
    """Ejecuta el procedimiento almacenado sp_actualizar_comando[cite: 1]."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_actualizar_comando", (
                id_comando,
                data.nombre,
                data.codigo,
                data.descripcion,
                data.activo
            ))
            connection.commit()
            return {"mensaje": f"Comando con ID {id_comando} actualizado exitosamente"}
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()


@router.delete("/{id_comando}", summary="Eliminar un comando")
def eliminar_comando(id_comando: int):
    """Ejecuta el procedimiento almacenado sp_eliminar_comando[cite: 1]."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_eliminar_comando", (id_comando,))
            connection.commit()
            return {"mensaje": f"Comando con ID {id_comando} eliminado exitosamente"}
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()