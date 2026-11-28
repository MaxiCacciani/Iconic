"""Acceso a datos de cobros. Los repositorios heredan de `RepositorioBase[M]`."""

from collections.abc import Sequence
from datetime import date

from sqlalchemy.orm import selectinload
from sqlmodel import col, func, select

from app.common.base import RepositorioBase
from app.common.enums import EstadoCobroEnum
from app.modules.cobros.models import Cobro
from app.modules.ventas.models import Venta

_CON_CLIENTE = selectinload(Cobro.venta).selectinload(Venta.cliente)  # type: ignore[arg-type]


class CobroRepository(RepositorioBase[Cobro]):
    modelo = Cobro

    def con_cliente(self, id: int) -> Cobro | None:
        return self.session.exec(select(Cobro).where(Cobro.id == id).options(_CON_CLIENTE)).first()

    def entre(self, desde: date, hasta: date) -> Sequence[Cobro]:
        """Las que vencen desde `desde` hasta antes de `hasta`."""
        return self.session.exec(
            select(Cobro)
            .where(col(Cobro.fecha_vencimiento) >= desde, col(Cobro.fecha_vencimiento) < hasta)
            .options(_CON_CLIENTE)
            .order_by(col(Cobro.fecha_vencimiento), col(Cobro.venta_id), col(Cobro.numero_cuota))
        ).all()

    def de_cliente(self, cliente_id: int) -> Sequence[Cobro]:
        return self.session.exec(
            select(Cobro)
            .join(Venta, col(Venta.id) == col(Cobro.venta_id))
            .where(Venta.cliente_id == cliente_id)
            .options(selectinload(Cobro.venta))  # type: ignore[arg-type]
            .order_by(col(Cobro.venta_id).desc(), col(Cobro.numero_cuota))
        ).all()

    def vencidas(self, hoy: date) -> int:
        return self.session.exec(
            select(func.count()).where(
                Cobro.estado == EstadoCobroEnum.pendiente, col(Cobro.fecha_vencimiento) < hoy
            )
        ).one()
