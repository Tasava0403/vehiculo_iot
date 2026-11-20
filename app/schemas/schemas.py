from pydantic import BaseModel


# Vehículos
class VehiculoCreate(BaseModel):
    nombre: str
    modelo: str | None = None
    descripcion: str | None = None
    microcontrolador: str | None = None


class VehiculoUpdate(VehiculoCreate):
    activo: bool


# Comandos
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


# Demos
class DemoCreate(BaseModel):
    id_vehiculo: int
    nombre: str
    descripcion: str | None = None


class DemoUpdate(BaseModel):
    nombre: str
    descripcion: str | None = None
    activo: bool


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


# Monitoreo
class EstadoUpdate(BaseModel):
    id_vehiculo: int
    id_comando: int | None = None
    conectado: bool


class HistorialCreate(BaseModel):
    id_vehiculo: int
    id_comando: int
    origen: str = "MANUAL"


class DemoTriggerRequest(BaseModel):
    id_demo: int
