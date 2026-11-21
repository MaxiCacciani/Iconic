"""Acceso a datos de tipo de cambio. Los repositorios heredan de `RepositorioBase[M]`."""

from datetime import date

from sqlmodel import select

from app.common.base import RepositorioBase
from app.modules.tipo_cambio.models import TipoCambio


class TipoCambioRepository(RepositorioBase[TipoCambio]):
    modelo = TipoCambio

    def por_fecha(self, fecha: date) -> TipoCambio | None:
        return self.session.exec(select(TipoCambio).where(TipoCambio.fecha == fecha)).first()
