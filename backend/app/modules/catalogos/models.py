"""Entidades SQLModel (table=True) de los catálogos. Ver `DER-Iconic.pdf` y `sql/schema.sql`.

Son las listas que el negocio amplía desde la app. Los valores fijos de los que depende
la lógica (estados, modalidad, rol, condición) no están acá: son ENUMs (`common/enums.py`).
"""

from sqlalchemy import Index, UniqueConstraint, text
from sqlmodel import Field, SQLModel


class TipoCategoria(SQLModel, table=True):
    """Qué datos lleva cada producto de las categorías de este tipo."""

    __tablename__ = "tipos_categoria"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True)
    usa_imei: bool = False
    usa_bateria: bool = False
    usa_controles: bool = False
    por_cantidad: bool = False


class Categoria(SQLModel, table=True):
    __tablename__ = "categorias"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True)
    tipo_categoria_id: int = Field(foreign_key="tipos_categoria.id")


class Modelo(SQLModel, table=True):
    __tablename__ = "modelos"
    __table_args__ = (UniqueConstraint("categoria_id", "nombre"),)

    id: int | None = Field(default=None, primary_key=True)
    categoria_id: int = Field(foreign_key="categorias.id")
    nombre: str


class Capacidad(SQLModel, table=True):
    __tablename__ = "capacidades"
    __table_args__ = (UniqueConstraint("categoria_id", "nombre"),)

    id: int | None = Field(default=None, primary_key=True)
    categoria_id: int = Field(foreign_key="categorias.id")
    nombre: str


class Color(SQLModel, table=True):
    __tablename__ = "colores"
    __table_args__ = (UniqueConstraint("categoria_id", "nombre"),)

    id: int | None = Field(default=None, primary_key=True)
    categoria_id: int = Field(foreign_key="categorias.id")
    nombre: str


class Proveedor(SQLModel, table=True):
    __tablename__ = "proveedores"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True)


class Defecto(SQLModel, table=True):
    """`es_comun`: aparece en la lista para elegir. Los escritos a mano no son comunes."""

    __tablename__ = "defectos"

    id: int | None = Field(default=None, primary_key=True)
    descripcion: str = Field(unique=True)
    es_comun: bool = False


class Localidad(SQLModel, table=True):
    __tablename__ = "localidades"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True)


class Diagnostico(SQLModel, table=True):
    __tablename__ = "diagnosticos"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True)


class EstadoReclamo(SQLModel, table=True):
    """`es_inicial`: el estado con el que arranca un reclamo. Hay uno solo."""

    __tablename__ = "estados_reclamo"
    __table_args__ = (
        Index(
            "uq_estados_reclamo_inicial",
            "es_inicial",
            unique=True,
            sqlite_where=text("es_inicial"),
            postgresql_where=text("es_inicial"),
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True)
    es_inicial: bool = False


class MetodoPago(SQLModel, table=True):
    """`predeterminado`: el que viene elegido al vender. Hay uno solo."""

    __tablename__ = "metodos_pago"
    __table_args__ = (
        Index(
            "uq_metodos_pago_predeterminado",
            "predeterminado",
            unique=True,
            sqlite_where=text("predeterminado"),
            postgresql_where=text("predeterminado"),
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True)
    predeterminado: bool = False
