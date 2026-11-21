"""DTOs de entrada y salida de tipo de cambio (Create / Read / Update)."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.common.tipos import Pesos


class TipoCambioUpdate(BaseModel):
    """Carga o corrige el TC de hoy. Acepta `1180.5` o el formato argentino `"1.180,50"`."""

    valor_ars: Pesos


class TipoCambioHoyRead(BaseModel):
    """TC de hoy. `valor_ars` es `null` mientras no se haya cargado: no hay valor por defecto."""

    fecha: date
    valor_ars: Decimal | None
    cargado_por: str | None
