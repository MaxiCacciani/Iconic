"""Fecha de "hoy" del negocio. Todo lo que dependa del día (TC, ventas, cuotas) la pide acá."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings


def hoy() -> date:
    """El día en la zona horaria del negocio (Argentina), no en la del servidor."""
    return datetime.now(ZoneInfo(get_settings().zona_horaria)).date()
