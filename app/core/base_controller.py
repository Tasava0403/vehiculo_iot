from abc import ABC, abstractmethod
from fastapi import APIRouter


class BaseController(ABC):
    """Clase base de los controladores. Cada subclase crea su APIRouter
    y registra sus rutas en _register_routes()."""

    def __init__(self, prefix: str = "", tags: list[str] | None = None):
        self.router = APIRouter(prefix=prefix, tags=tags)
        self._register_routes()

    @abstractmethod
    def _register_routes(self) -> None:
        ...
