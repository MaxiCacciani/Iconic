"""Strategy `ModalidadPago` (reglas 4.3): cada modalidad valida sus montos.

El service pide la estrategia con `modalidad_de` en vez de preguntar `if modalidad == …`.
La Fase 8 suma `EnCuotas`, que además valida el anticipo y genera los cobros.
"""

from abc import ABC, abstractmethod
from decimal import Decimal

from app.common.enums import Modalidad
from app.core.excepciones import ErrorDeCampo


class ModalidadPago(ABC):
    @abstractmethod
    def validar(self, total: Decimal, canje: Decimal) -> None: ...


class Contado(ModalidadPago):
    """Pago único: el canje se descuenta del saldo a pagar y no puede cubrir el total."""

    def validar(self, total: Decimal, canje: Decimal) -> None:
        if canje and canje >= total:
            raise ErrorDeCampo(
                "canje_valor_usd", "El valor del canje tiene que ser menor al total de la venta."
            )


_MODALIDADES: dict[Modalidad, ModalidadPago] = {Modalidad.contado: Contado()}


def modalidad_de(modalidad: Modalidad) -> ModalidadPago:
    try:
        return _MODALIDADES[modalidad]
    except KeyError:
        raise ErrorDeCampo("modalidad", "Por ahora solo se puede vender al contado.") from None
