"""Entidades SQLModel (table=True) de tipo de cambio. Ver `DER-Iconic.pdf`."""

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, Numeric
from sqlmodel import Field, SQLModel


class TipoCambio(SQLModel, table=True):
    """TC del día: pesos por dólar. Uno por fecha; si no hay fila para hoy, no está cargado."""

    __tablename__ = "tipos_cambio"

    id: int | None = Field(default=None, primary_key=True)
    fecha: date = Field(unique=True)
    valor_ars: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    # Quién lo cargó por última vez.
    usuario_id: int = Field(foreign_key="usuarios.id")
    creado_en: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
