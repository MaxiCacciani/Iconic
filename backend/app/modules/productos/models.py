"""Entidades SQLModel (table=True) de productos. Ver `DER-Iconic.pdf` y `sql/schema.sql`.

La categoría del producto no se guarda: sale del modelo (3FN). El estado se guarda como
ENUM y se mapea a su clase de `estados.py`: las acciones (`reservar`, `vender`…) se
delegan en ella y una transición no permitida lanza `TransicionInvalida`.
"""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, Index, Numeric, SmallInteger, String, text
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel

from app.common.enums import Condicion, EstadoProductoEnum
from app.modules.catalogos.models import Capacidad, Color, Defecto, Modelo, Proveedor
from app.modules.productos.estados import EstadoProducto, estado_de


class ProductoDefecto(SQLModel, table=True):
    """Los defectos de cada producto. Los escritos a mano quedan en `defectos` como no comunes."""

    __tablename__ = "producto_defectos"

    producto_id: int = Field(foreign_key="productos.id", primary_key=True, ondelete="CASCADE")
    defecto_id: int = Field(foreign_key="defectos.id", primary_key=True)


class Producto(SQLModel, table=True):
    __tablename__ = "productos"
    __table_args__ = (
        Index(
            "uq_productos_imei",
            "imei",
            unique=True,
            # Solo en el stock (lo no vendido): un equipo vendido puede volver por canje.
            sqlite_where=text("imei IS NOT NULL AND estado <> 'vendido'"),
            postgresql_where=text("imei IS NOT NULL AND estado <> 'vendido'"),
        ),
        Index("ix_productos_estado", "estado"),
        Index("ix_productos_modelo", "modelo_id"),
    )

    id: int | None = Field(default=None, primary_key=True)
    modelo_id: int = Field(foreign_key="modelos.id")
    capacidad_id: int | None = Field(default=None, foreign_key="capacidades.id")
    color_id: int | None = Field(default=None, foreign_key="colores.id")
    proveedor_id: int = Field(foreign_key="proveedores.id")
    condicion: Condicion = Field(
        sa_column=Column(SAEnum(Condicion, name="condicion"), nullable=False)
    )
    imei: str | None = Field(default=None, sa_column=Column(String(15)))
    bateria: int | None = Field(default=None, sa_column=Column(SmallInteger))
    controles: int | None = Field(default=None, sa_column=Column(SmallInteger))
    extras: str | None = None
    cantidad: int = 1
    precio_usd: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    costo_usd: Decimal | None = Field(default=None, sa_column=Column(Numeric(12, 2)))
    estado: EstadoProductoEnum = Field(
        default=EstadoProductoEnum.disponible,
        sa_column=Column(
            SAEnum(EstadoProductoEnum, name="estado_producto"),
            nullable=False,
            default=EstadoProductoEnum.disponible,
        ),
    )
    creado_en: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    modelo: Modelo = Relationship()
    capacidad: Capacidad | None = Relationship()
    color: Color | None = Relationship()
    proveedor: Proveedor = Relationship()
    defectos: list[Defecto] = Relationship(link_model=ProductoDefecto)

    # ─── State: cada acción la resuelve la clase del estado actual ───────────
    @property
    def estado_actual(self) -> EstadoProducto:
        return estado_de(self.estado)

    def reservar(self) -> None:
        self.estado = self.estado_actual.reservar()

    def liberar(self) -> None:
        self.estado = self.estado_actual.liberar()

    def vender(self) -> None:
        self.estado = self.estado_actual.vender()

    def devolver(self) -> None:
        self.estado = self.estado_actual.devolver()

    def verificar_editable(self) -> None:
        self.estado_actual.editar()

    def verificar_borrable(self) -> None:
        self.estado_actual.eliminar()
