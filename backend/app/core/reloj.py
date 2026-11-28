"""Fecha de "hoy" del negocio. Todo lo que dependa del día (TC, ventas, cuotas) la pide acá."""

from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

from app.core.config import get_settings


def hoy() -> date:
    """El día en la zona horaria del negocio (Argentina), no en la del servidor."""
    return datetime.now(ZoneInfo(get_settings().zona_horaria)).date()


def inicio_del_dia(dia: date) -> datetime:
    """La medianoche de ese día en Argentina, en UTC (como se guardan los instantes)."""
    zona = ZoneInfo(get_settings().zona_horaria)
    return datetime.combine(dia, time.min, tzinfo=zona).astimezone(UTC)


def dia_de(instante: datetime) -> date:
    """El día en Argentina de un instante. Sin zona (SQLite la pierde), está en UTC."""
    if instante.tzinfo is None:
        instante = instante.replace(tzinfo=UTC)
    return instante.astimezone(ZoneInfo(get_settings().zona_horaria)).date()
