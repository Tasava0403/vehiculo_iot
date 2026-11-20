from typing import Any, Literal
from app.database import get_db_connection


class BaseRepository:
    """Encapsula el patrón repetido: abrir conexión, llamar SP,
    commit/rollback y cerrar."""

    def _call(
        self,
        procedure: str,
        params: tuple = (),
        *,
        fetch: Literal["one", "all", None] = None,
        commit: bool = False,
    ) -> Any:
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.callproc(procedure, params)
                if commit:
                    connection.commit()
                if fetch == "one":
                    return cursor.fetchone()
                if fetch == "all":
                    return cursor.fetchall()
                return None
        except Exception:
            if commit:
                connection.rollback()
            raise
        finally:
            connection.close()
