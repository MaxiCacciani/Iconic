"""Strategy `ModalidadPago` (reglas 4.3): cada modalidad valida sus montos y arma su plan.

El service pide la estrategia con `modalidad_de` en vez de preguntar `if modalidad == …`.
Convertir una reserva (Fase 9) reutiliza la misma estrategia, con la seña como anticipo.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from app.common.enums import Modalidad
from app.core.excepciones import ErrorDeCampo
from app.modules.ventas.dominio import Cuota, plan_de_cuotas


@dataclass(frozen=True)
class Pago:
    """Lo que el usuario eligió para pagar. Cada modalidad usa lo que le corresponde."""

    anticipo: Decimal = Decimal(0)
    cantidad_cuotas: int | None = None
    primera_cuota_hoy: bool = False


@dataclass(frozen=True)
class Plan:
    """Lo que se guarda en la venta y los cobros que se generan."""

    anticipo: Decimal = Decimal(0)
    cantidad_cuotas: int | None = None
    cuotas: list[Cuota] = field(default_factory=list)


class ModalidadPago(ABC):
    @abstractmethod
    def planear(self, total: Decimal, canje: Decimal, pago: Pago, dia: date) -> Plan: ...

    @staticmethod
    def _validar_canje(total: Decimal, canje: Decimal) -> None:
        if canje and canje >= total:
            raise ErrorDeCampo(
                "canje_valor_usd", "El valor del canje tiene que ser menor al total de la venta."
            )


class Contado(ModalidadPago):
    """Pago único: el canje se descuenta del saldo. El anticipo y las cuotas no aplican."""

    def planear(self, total: Decimal, canje: Decimal, pago: Pago, dia: date) -> Plan:
        self._validar_canje(total, canje)
        return Plan()


class EnCuotas(ModalidadPago):
    """Se financia el total − anticipo − canje, con cuotas de al menos US$ 1."""

    def planear(self, total: Decimal, canje: Decimal, pago: Pago, dia: date) -> Plan:
        self._validar_canje(total, canje)
        anticipo, cantidad_cuotas = pago.anticipo, pago.cantidad_cuotas
        if cantidad_cuotas is None:
            raise ErrorDeCampo("cantidad_cuotas", "Elegí en cuántas cuotas.")
        if anticipo >= total:
            raise ErrorDeCampo(
                "anticipo_usd", "El anticipo cubre el total: es una venta al contado."
            )
        if anticipo + canje >= total:
            raise ErrorDeCampo(
                "anticipo_usd", "El anticipo y el canje cubren el total: es una venta al contado."
            )
        financiado = total - anticipo - canje
        cuotas = plan_de_cuotas(financiado, cantidad_cuotas, dia, pago.primera_cuota_hoy)
        if min(c.monto for c in cuotas) < 1:
            raise ErrorDeCampo(
                "cantidad_cuotas",
                f"No alcanza para {cantidad_cuotas} cuotas de al menos US$ 1.",
            )
        return Plan(anticipo=anticipo, cantidad_cuotas=cantidad_cuotas, cuotas=cuotas)


_MODALIDADES: dict[Modalidad, ModalidadPago] = {
    Modalidad.contado: Contado(),
    Modalidad.cuotas: EnCuotas(),
}


def modalidad_de(modalidad: Modalidad) -> ModalidadPago:
    return _MODALIDADES[modalidad]
