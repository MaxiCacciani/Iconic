"""Entidades SQLModel (table=True) de usuarios. Ver `DER-Iconic.pdf`."""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from app.common.enums import Rol


class Usuario(SQLModel, table=True):
    __tablename__ = "usuarios"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str
    email: str = Field(unique=True)
    password_hash: str
    rol: Rol = Field(sa_column=Column(SAEnum(Rol, name="rol"), nullable=False))
    activo: bool = True
    creado_en: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
