from datetime import datetime, date


def limpiar_fechas(obj):
    """Convierte de forma recursiva los datetime/date a string ISO."""
    if isinstance(obj, dict):
        return {k: limpiar_fechas(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [limpiar_fechas(v) for v in obj]
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return obj
