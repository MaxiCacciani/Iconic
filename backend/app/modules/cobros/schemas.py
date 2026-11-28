"""DTOs de salida de cobros. No llevan costos: el Vendedor ve el plan de cuotas en la
ficha del cliente con el mismo DTO que el Administrador."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.modules.cobros.estados import EstadoCuota
from app.modules.productos.schemas import Referencia


class CuotaRead(BaseModel):
    id: int
    numero: int
    vencimiento: date
    monto_usd: Decimal
    estado: EstadoCuota


class CobroAgendaRead(CuotaRead):
    venta_id: int
    cantidad_cuotas: int
    cliente: Referencia
    monto_ars: Decimal | None = Field(description="Con el TC de hoy; `null` sin TC.")


class TotalesCobros(BaseModel):
    total_usd: Decimal
    cobrado_usd: Decimal
    pendiente_usd: Decimal = Field(description="Lo no cobrado, vencido o no.")


class AgendaRead(TotalesCobros):
    """Las cuotas que vencen en el mes, por fecha."""

    anio: int
    mes: int
    cobros: list[CobroAgendaRead]


class PlanCuotasRead(BaseModel):
    venta_id: int
    fecha: datetime
    cantidad_cuotas: int
    pagadas: int
    saldo_usd: Decimal
    proxima: CuotaRead | None = Field(description="La primera sin cobrar.")
    en_mora_desde: date | None = Field(description="El vencimiento de la primera vencida.")
    cuotas: list[CuotaRead]


class CuotasClienteRead(BaseModel):
    """Reglas 3: el saldo es la suma de las cuotas sin cobrar y "en mora" es tener al
    menos una vencida. Las ventas más nuevas primero."""

    saldo_usd: Decimal
    saldo_ars: Decimal | None = Field(description="Con el TC de hoy; `null` sin TC.")
    en_mora: bool
    planes: list[PlanCuotasRead]
