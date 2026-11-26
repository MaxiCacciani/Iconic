"""Funciones puras de productos: sin base de datos, para testear primero.

Reglas 2.2: ganancia = precio − costo; margen % = ganancia / costo. Batería por
intervalos de color (solo visual, sin alertas): 85 o más alta, de 80 a 84 media,
menos de 80 baja.
"""

from decimal import ROUND_HALF_UP, Decimal

from app.common.enums import NivelBateria

_CENTAVOS = Decimal("0.01")
_DECIMA = Decimal("0.1")


def nivel_bateria(bateria: int | None) -> NivelBateria | None:
    if bateria is None:
        return None
    if bateria >= 85:
        return NivelBateria.alta
    if bateria >= 80:
        return NivelBateria.media
    return NivelBateria.baja


def ganancia(precio: Decimal, costo: Decimal | None) -> Decimal | None:
    """Sin costo cargado no hay ganancia que calcular."""
    return None if costo is None else precio - costo


def margen_pct(precio: Decimal, costo: Decimal | None) -> Decimal | None:
    """En porcentaje, con un decimal. Sin costo (o con costo 0) no hay margen: es una
    división por el costo."""
    if not costo:
        return None
    return ((precio - costo) / costo * 100).quantize(_DECIMA, rounding=ROUND_HALF_UP)


def en_pesos(usd: Decimal | None, tc: Decimal | None) -> Decimal | None:
    """Equivalencia con el TC del día. Sin TC cargado no hay equivalencia."""
    if usd is None or tc is None:
        return None
    return (usd * tc).quantize(_CENTAVOS, rounding=ROUND_HALF_UP)
