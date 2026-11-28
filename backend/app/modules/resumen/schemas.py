"""DTOs de salida del resumen (por rol).

Los cobros (los del mes y el aviso de cuotas vencidas) son solo del Administrador: al
Vendedor le llega `cobros_del_mes` en `null`.
"""

from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field

from app.modules.cobros.schemas import TotalesCobros


class TipoAviso(StrEnum):
    """Qué avisa. El front lo usa para saber qué acción ofrecer junto al mensaje."""

    tc_sin_cargar = "tc_sin_cargar"
    cuotas_vencidas = "cuotas_vencidas"


class AvisoRead(BaseModel):
    tipo: TipoAviso
    mensaje: str


class StockRead(BaseModel):
    """En unidades, no en filas: un accesorio por cantidad suma todas las suyas."""

    disponibles: int
    nuevas: int


class VentasDelPeriodo(BaseModel):
    """En pesos, cada venta con su TC congelado: lo que realmente se cobró."""

    cantidad: int
    total_usd: Decimal
    total_ars: Decimal


class VentasRead(BaseModel):
    hoy: VentasDelPeriodo
    ultimos_7_dias: VentasDelPeriodo = Field(description="Hoy incluido.")
    solo_propias: bool = Field(
        description="El Vendedor ve solo las ventas que registró él; el admin, todas."
    )


class ResumenRead(BaseModel):
    fecha: date
    avisos: list[AvisoRead]
    stock: StockRead
    ventas: VentasRead
    cobros_del_mes: TotalesCobros | None = Field(
        description="Las cuotas que vencen este mes. Solo para el Administrador."
    )
