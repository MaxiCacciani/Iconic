"""Entidades SQLModel (table=True) de los catálogos. Ver `DER-Iconic.pdf` y `sql/schema.sql`.

Son las listas que el negocio amplía desde la app. Los valores fijos de los que depende
la lógica (estados, modalidad, rol, condición) no están acá: son ENUMs (`common/enums.py`).
"""

from sqlalchemy import Index, UniqueConstraint, text
from sqlmodel import Field, Relationship, SQLModel


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


class ModeloColor(SQLModel, table=True):
    """Qué colores de su categoría tiene cada modelo (el iPhone 15 no vino en verde alpino).

    Un modelo sin colores asignados ofrece todos los de su categoría. Al borrar el modelo
    o el color, la asignación se va con él.
    """

    __tablename__ = "modelo_colores"

    modelo_id: int = Field(foreign_key="modelos.id", primary_key=True, ondelete="CASCADE")
    color_id: int = Field(foreign_key="colores.id", primary_key=True, ondelete="CASCADE")


class ModeloCapacidad(SQLModel, table=True):
    """Qué capacidades de su categoría tiene cada modelo (el iPhone 15 Pro no tiene 64 GB).

    Igual que `ModeloColor`: sin asignar, ofrece todas las de la categoría.
    """

    __tablename__ = "modelo_capacidades"

    modelo_id: int = Field(foreign_key="modelos.id", primary_key=True, ondelete="CASCADE")
    capacidad_id: int = Field(foreign_key="capacidades.id", primary_key=True, ondelete="CASCADE")


class Modelo(SQLModel, table=True):
    __tablename__ = "modelos"
    __table_args__ = (UniqueConstraint("categoria_id", "nombre"),)

    id: int | None = Field(default=None, primary_key=True)
    categoria_id: int = Field(foreign_key="categorias.id")
    nombre: str

    colores: list["Color"] = Relationship(
        back_populates="modelos",
        link_model=ModeloColor,
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    capacidades: list["Capacidad"] = Relationship(
        back_populates="modelos",
        link_model=ModeloCapacidad,
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    @property
    def color_ids(self) -> list[int]:
        return sorted(c.id for c in self.colores if c.id is not None)

    @property
    def capacidad_ids(self) -> list[int]:
        return sorted(c.id for c in self.capacidades if c.id is not None)


class Capacidad(SQLModel, table=True):
    __tablename__ = "capacidades"
    __table_args__ = (UniqueConstraint("categoria_id", "nombre"),)

    id: int | None = Field(default=None, primary_key=True)
    categoria_id: int = Field(foreign_key="categorias.id")
    nombre: str

    modelos: list[Modelo] = Relationship(back_populates="capacidades", link_model=ModeloCapacidad)


class Color(SQLModel, table=True):
    __tablename__ = "colores"
    __table_args__ = (UniqueConstraint("categoria_id", "nombre"),)

    id: int | None = Field(default=None, primary_key=True)
    categoria_id: int = Field(foreign_key="categorias.id")
    nombre: str

    modelos: list[Modelo] = Relationship(back_populates="colores", link_model=ModeloColor)


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
