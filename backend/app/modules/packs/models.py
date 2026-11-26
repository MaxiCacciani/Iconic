"""Entidades SQLModel (table=True) de packs. Ver `DER-Iconic.pdf` y `sql/schema.sql`.

Reglas 4.2: un pack es un combo predefinido ("iPhone + accesorios de regalo"). Cada ítem es
un producto fijo del stock o una categoría, nunca los dos.
"""

from sqlalchemy import CheckConstraint
from sqlmodel import Field, Relationship, SQLModel

from app.modules.catalogos.models import Categoria
from app.modules.productos.models import Producto


class PackItem(SQLModel, table=True):
    __tablename__ = "pack_items"
    __table_args__ = (
        # Producto fijo o categoría, nunca los dos.
        CheckConstraint(
            "(producto_id IS NULL) <> (categoria_id IS NULL)", name="producto_o_categoria"
        ),
        CheckConstraint("cantidad >= 1", name="cantidad_positiva"),
    )

    id: int | None = Field(default=None, primary_key=True)
    pack_id: int = Field(foreign_key="packs.id", ondelete="CASCADE")
    # Si el producto se borra del stock, el ítem se va con él (ON DELETE CASCADE).
    producto_id: int | None = Field(default=None, foreign_key="productos.id", ondelete="CASCADE")
    categoria_id: int | None = Field(default=None, foreign_key="categorias.id")
    cantidad: int = 1
    es_regalo: bool = False

    producto: Producto | None = Relationship()
    categoria: Categoria | None = Relationship()


class Pack(SQLModel, table=True):
    __tablename__ = "packs"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str
    descripcion: str | None = None

    items: list[PackItem] = Relationship(
        cascade_delete=True, sa_relationship_kwargs={"order_by": "PackItem.id"}
    )
