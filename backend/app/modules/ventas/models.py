"""Entidades SQLModel (table=True) de ventas. Ver `DER-Iconic.pdf` y `sql/schema.sql`.

Lo que se puede calcular no se guarda: el total, el costo y la ganancia salen de los ítems
(`dominio.py`). Cada ítem guarda el precio y el costo del momento de la venta.

Faltan columnas de fases siguientes, que en `schema.sql` ya están y toman su valor por
defecto: `reserva_id` (Fase 9), `cantidad_cuotas` y `anticipo_usd` (Fase 8).
"""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, Index, Numeric, SmallInteger
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel

from app.common.enums import Modalidad
from app.modules.catalogos.models import MetodoPago
from app.modules.clientes.models import Cliente
from app.modules.productos.models import Producto
from app.modules.usuarios.models import Usuario
from app.modules.vendedores.models import Vendedor


class VentaItem(SQLModel, table=True):
    """Un regalo se guarda con precio 0: es lo que se cobró (reglas 4.2)."""

    __tablename__ = "venta_items"
    __table_args__ = (Index("ix_venta_items_venta", "venta_id"),)

    id: int | None = Field(default=None, primary_key=True)
    venta_id: int | None = Field(default=None, foreign_key="ventas.id", ondelete="CASCADE")
    producto_id: int = Field(foreign_key="productos.id")
    cantidad: int = 1
    precio_usd: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    costo_usd: Decimal | None = Field(default=None, sa_column=Column(Numeric(12, 2)))
    es_regalo: bool = False

    producto: Producto = Relationship()


class Venta(SQLModel, table=True):
    __tablename__ = "ventas"
    __table_args__ = (
        Index("ix_ventas_fecha", "fecha"),
        Index("ix_ventas_cliente", "cliente_id"),
        Index("ix_ventas_usuario", "usuario_id"),
    )

    id: int | None = Field(default=None, primary_key=True)
    fecha: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    cliente_id: int = Field(foreign_key="clientes.id")
    usuario_id: int = Field(foreign_key="usuarios.id")
    vendedor_id: int | None = Field(default=None, foreign_key="vendedores.id")
    # El equipo que entró al stock por plan canje.
    canje_producto_id: int | None = Field(
        default=None, foreign_key="productos.id", unique=True, ondelete="SET NULL"
    )
    canje_valor_usd: Decimal | None = Field(default=None, sa_column=Column(Numeric(12, 2)))
    metodo_pago_id: int = Field(foreign_key="metodos_pago.id")
    modalidad: Modalidad = Field(
        sa_column=Column(SAEnum(Modalidad, name="modalidad"), nullable=False)
    )
    # El TC congelado al vender: el historial refleja lo que realmente se cobró.
    tc_ars: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    garantia_meses: int = Field(default=3, sa_column=Column(SmallInteger, nullable=False))
    # Solo la ve y la carga el Administrador; se resta de la ganancia.
    comision_usd: Decimal = Field(
        default=Decimal(0), sa_column=Column(Numeric(12, 2), nullable=False)
    )

    items: list[VentaItem] = Relationship(
        cascade_delete=True, sa_relationship_kwargs={"order_by": "VentaItem.id"}
    )
    cliente: Cliente = Relationship()
    usuario: Usuario = Relationship()
    vendedor: Vendedor | None = Relationship()
    metodo_pago: MetodoPago = Relationship()
    canje_producto: Producto | None = Relationship()
