"""Entidades SQLModel (table=True) de vendedores. Ver `DER-Iconic.pdf` y `sql/schema.sql`.

Reglas 4.6: en la venta se carga el número del vendedor (opcional) y el nombre se busca en
esta lista. La venta apunta al `id`, así que el número se puede corregir sin tocar ventas.
"""

from sqlmodel import Field, SQLModel


class Vendedor(SQLModel, table=True):
    __tablename__ = "vendedores"

    id: int | None = Field(default=None, primary_key=True)
    numero: int = Field(unique=True)
    nombre: str
