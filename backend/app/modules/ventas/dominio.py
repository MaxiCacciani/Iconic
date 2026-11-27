"""Funciones puras de ventas: sin base de datos, para testear primero.

Reglas 4.2 y 4.8:
- Total: precio × cantidad de los ítems que no son regalo.
- Costo: costo × cantidad de todos los ítems, regalos incluidos.
- "Bajo costo": un ítem con precio por debajo de su costo. Avisa, no bloquea.
"""

from decimal import Decimal
from typing import Protocol


class Linea(Protocol):
    precio_usd: Decimal
    costo_usd: Decimal | None
    cantidad: int
    es_regalo: bool


def total(lineas: list[Linea]) -> Decimal:
    return sum((x.precio_usd * x.cantidad for x in lineas if not x.es_regalo), Decimal(0))


def costo(lineas: list[Linea]) -> Decimal | None:
    """Si algún ítem no tiene costo cargado, la venta no tiene costo: la ganancia saldría
    inflada."""
    if any(x.costo_usd is None for x in lineas):
        return None
    return sum((x.costo_usd * x.cantidad for x in lineas), Decimal(0))  # type: ignore[operator]


def bajo_costo(linea: Linea) -> bool:
    """Un regalo va a precio 0 a propósito: no cuenta."""
    if linea.es_regalo or linea.costo_usd is None:
        return False
    return linea.precio_usd < linea.costo_usd
