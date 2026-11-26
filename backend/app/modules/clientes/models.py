"""Entidades SQLModel (table=True) de clientes. Ver `DER-Iconic.pdf` y `sql/schema.sql`.

El saldo y si está "en mora" no se guardan: salen de los cobros (Fase 8).
"""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, String
from sqlmodel import Field, Relationship, SQLModel

from app.modules.catalogos.models import Localidad


class Cliente(SQLModel, table=True):
    __tablename__ = "clientes"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str
    dni: str | None = Field(default=None, sa_column=Column(String(8), unique=True))
    telefono: str | None = Field(default=None, sa_column=Column(String(15)))
    localidad_id: int | None = Field(default=None, foreign_key="localidades.id")
    creado_en: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    localidad: Localidad | None = Relationship()
