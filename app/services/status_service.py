import json
from pathlib import Path


class StatusService:

    def __init__(self):
        self.archivo = (
            Path(__file__).resolve().parent.parent / "data" / "status.json"
        )

    def obtener_estado(self):
        with open(self.archivo, "r", encoding="utf-8") as archivo:
            return json.load(archivo)

    def guardar_estado(self, status: int):
        # Validar que el valor esté dentro del rango permitido (1 a 11)
        if not (1 <= status <= 11):
            raise ValueError(
                f"El estado debe ser un número entero entre 1 y 11. Valor recibido: {status}"
            )

        nuevo_estado = {"ESTADO": status}

        with open(self.archivo, "w", encoding="utf-8") as archivo:
            json.dump(nuevo_estado, archivo, indent=4)

        return nuevo_estado