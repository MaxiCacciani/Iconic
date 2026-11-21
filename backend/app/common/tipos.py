"""Value Objects como tipos `Annotated` de Pydantic. La validación vive en un solo lugar."""

import re
from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator, BeforeValidator, Field


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


_MILES = re.compile(r"^\d{1,3}(\.\d{3})+$")


def _normalizar_pesos(valor: object) -> object:
    """Acepta el formato argentino además del número JSON: `1.180,50`, `1180,5`, `1.180`.

    Con coma, los puntos son de miles. Sin coma, un punto seguido de grupos de 3 dígitos
    también es de miles (`1.180` = 1180), porque un TC nunca se escribe como `1,18`.
    """
    if not isinstance(valor, str):
        return valor
    texto = valor.strip().replace(" ", "")
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif _MILES.match(texto):
        texto = texto.replace(".", "")
    return texto


# Monto en pesos mayor a 0 (por ejemplo, el TC del día: pesos por cada dólar).
Pesos = Annotated[
    Decimal, BeforeValidator(_normalizar_pesos), Field(gt=0, max_digits=12, decimal_places=2)
]
