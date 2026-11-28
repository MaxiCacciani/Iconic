"""Funciones puras de ventas: sin base de datos, para testear primero.

Reglas 4.2 y 4.8:
- Total: precio × cantidad de los ítems que no son regalo.
- Costo: costo × cantidad de todos los ítems, regalos incluidos.
- "Bajo costo": un ítem con precio por debajo de su costo. Avisa, no bloquea.

Reglas 4.3 (cuotas): cada cuota se redondea a dólares enteros y la última ajusta el
redondeo. Una cuota por mes, el mismo día de la venta (o el último día del mes si no lo
tiene); la primera vence al mes siguiente, o hoy con "primera cuota hoy".
"""

from calendar import monthrange
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
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


@dataclass(frozen=True)
class Cuota:
    numero: int
    vencimiento: date
    monto: Decimal
    cobrada: bool = False


def dividir(monto: Decimal, cuotas: int) -> list[Decimal]:
    """US$ 1.000 en 6 cuotas: 5 de 167 y una de 165."""
    base = (monto / cuotas).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    return [base] * (cuotas - 1) + [monto - base * (cuotas - 1)]


def sumar_meses(dia: date, meses: int) -> date:
    """Siempre desde el día original: del 31/01, el 28/02 y después el 31/03."""
    indice = dia.month - 1 + meses
    anio, mes = dia.year + indice // 12, indice % 12 + 1
    return date(anio, mes, min(dia.day, monthrange(anio, mes)[1]))


def plan_de_cuotas(monto: Decimal, cuotas: int, dia: date, primera_hoy: bool) -> list[Cuota]:
    """Con `primera_hoy`, la cuota 1 vence hoy y queda cobrada al registrar la venta."""
    corrimiento = 0 if primera_hoy else 1
    return [
        Cuota(n, sumar_meses(dia, n - 1 + corrimiento), parte, cobrada=primera_hoy and n == 1)
        for n, parte in enumerate(dividir(monto, cuotas), start=1)
    ]
