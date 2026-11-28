"""State de `Cobro`: cada estado es una clase que decide qué acciones permite.

    pendiente ──cobrar──▶ cobrada
    vencida   ──cobrar──▶ cobrada

`vencida` no se guarda: es una cuota pendiente con fecha pasada (la de hoy todavía no
venció), así que `estado_de` necesita el día. Ver la página 4 de `DER-Iconic.pdf`.
"""

from datetime import date
from enum import StrEnum
from typing import ClassVar

from app.common.enums import EstadoCobroEnum
from app.core.excepciones import TransicionInvalida


class EstadoCuota(StrEnum):
    """Lo que se muestra: el guardado más `vencida`."""

    pendiente = "pendiente"
    vencida = "vencida"
    cobrada = "cobrada"


class EstadoCobro:
    valor: ClassVar[EstadoCuota]

    def cobrar(self) -> EstadoCobroEnum:
        raise TransicionInvalida("Esa cuota ya está cobrada.")


class Pendiente(EstadoCobro):
    valor = EstadoCuota.pendiente

    def cobrar(self) -> EstadoCobroEnum:
        return EstadoCobroEnum.cobrada


class Vencida(Pendiente):
    valor = EstadoCuota.vencida


class Cobrada(EstadoCobro):
    valor = EstadoCuota.cobrada


def estado_de(guardado: EstadoCobroEnum, vencimiento: date, hoy: date) -> EstadoCobro:
    if guardado == EstadoCobroEnum.cobrada:
        return Cobrada()
    return Vencida() if vencimiento < hoy else Pendiente()
