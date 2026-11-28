"""Entidades SQLModel (table=True) de cobros. Ver `DER-Iconic.pdf` y `sql/schema.sql`.

Cada cuota de una venta en cuotas es un cobro. Se guarda `pendiente` o `cobrada`; la
cuota vencida se calcula al leer (`estados.py`).
"""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Column, Index, Numeric, SmallInteger, UniqueConstraint, text
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel

from app.common.enums import EstadoCobroEnum
from app.core import reloj
from app.modules.cobros.estados import EstadoCobro, estado_de

if TYPE_CHECKING:
    from app.modules.ventas.models import Venta


class Cobro(SQLModel, table=True):
    __tablename__ = "cobros"
    __table_args__ = (
        UniqueConstraint("venta_id", "numero_cuota"),
        Index(
            "ix_cobros_pendientes",
            "fecha_vencimiento",
            sqlite_where=text("estado = 'pendiente'"),
            postgresql_where=text("estado = 'pendiente'"),
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    venta_id: int | None = Field(default=None, foreign_key="ventas.id", ondelete="CASCADE")
    numero_cuota: int = Field(sa_column=Column(SmallInteger, nullable=False))
    fecha_vencimiento: date
    monto_usd: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    estado: EstadoCobroEnum = Field(
        default=EstadoCobroEnum.pendiente,
        sa_column=Column(
            SAEnum(EstadoCobroEnum, name="estado_cobro"),
            nullable=False,
            default=EstadoCobroEnum.pendiente,
        ),
    )

    venta: "Venta" = Relationship(back_populates="cobros")

    def estado_al(self, hoy: date) -> EstadoCobro:
        return estado_de(self.estado, self.fecha_vencimiento, hoy)

    def cobrar(self) -> None:
        self.estado = self.estado_al(reloj.hoy()).cobrar()
