import asyncio
from functools import wraps
from fastapi import HTTPException


def manejar_errores(func):
    """Convierte cualquier excepción inesperada en HTTP 500.
    Las HTTPException (404, 400, etc.) se dejan pasar intactas."""
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    else:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    return wrapper
