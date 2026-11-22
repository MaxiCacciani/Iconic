"""DTOs de salida del resumen (por rol).

Por ahora Admin y Vendedor reciben lo mismo. Cuando se sumen indicadores con costos o
ganancias, se separan en `ResumenReadVendedor` y `ResumenReadAdmin`.
"""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel


class TipoAviso(StrEnum):
    """Qué avisa. El front lo usa para saber qué acción ofrecer junto al mensaje."""

    tc_sin_cargar = "tc_sin_cargar"


class AvisoRead(BaseModel):
    tipo: TipoAviso
    mensaje: str


class StockRead(BaseModel):
    """En unidades, no en filas: un accesorio por cantidad suma todas las suyas."""

    disponibles: int
    nuevas: int


class ResumenRead(BaseModel):
    fecha: date
    avisos: list[AvisoRead]
    stock: StockRead
