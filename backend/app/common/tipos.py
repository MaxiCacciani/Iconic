"""Value Objects como tipos `Annotated` de Pydantic. La validación vive en un solo lugar."""

from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator, Field


def luhn_valido(numero: str) -> bool:
    total = 0
    for i, digito in enumerate(reversed(numero)):
        n = int(digito)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def _validar_imei(valor: str) -> str:
    if not (valor.isdigit() and len(valor) == 15):
        raise ValueError("El IMEI debe tener exactamente 15 dígitos")
    if not luhn_valido(valor):
        raise ValueError("El IMEI no tiene un dígito de control válido")
    return valor


def _validar_digitos(minimo: int, maximo: int, nombre: str):
    def validar(valor: str) -> str:
        if not (valor.isdigit() and minimo <= len(valor) <= maximo):
            raise ValueError(f"El {nombre} debe tener entre {minimo} y {maximo} dígitos")
        return valor

    return validar


# Siempre Decimal, nunca float.
USD = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]
IMEI = Annotated[str, AfterValidator(_validar_imei)]
DNI = Annotated[str, AfterValidator(_validar_digitos(7, 8, "DNI"))]
Telefono = Annotated[str, AfterValidator(_validar_digitos(8, 15, "teléfono"))]
