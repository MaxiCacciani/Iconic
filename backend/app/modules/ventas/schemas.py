"""DTOs de entrada y salida de ventas (Create / Read).

Por rol: el Vendedor recibe la cotización y la venta sin costos, ganancia, margen,
comisión ni la advertencia de "bajo costo". El Administrador recibe `…Admin`, que les
suma esos datos.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field

from app.common.base import Pagina
from app.common.enums import Condicion, Modalidad
from app.common.tipos import IMEI, USD, PrecioUSD
from app.modules.cobros.schemas import CuotaRead
from app.modules.productos.schemas import Bateria, Cantidad, Controles, Extras, Referencia
from app.modules.vendedores.schemas import VendedorRead


# ─── Entrada ─────────────────────────────────────────────────────────────────
class ItemVentaCreate(BaseModel):
    """El precio es el del renglón y se puede editar. Un regalo cuenta US$ 0, mande el
    precio que mande, y va en un renglón aparte de las unidades con precio."""

    producto_id: int
    cantidad: Cantidad = 1
    precio_usd: USD
    es_regalo: bool = False


def _con_items(items: list[ItemVentaCreate]) -> list[ItemVentaCreate]:
    if not items:
        raise ValueError("Agregá al menos un producto.")
    return items


class CotizacionCreate(BaseModel):
    """Lo que hace falta para cotizar. El wizard puede mandar la venta entera: lo demás se
    ignora."""

    items: Annotated[list[ItemVentaCreate], AfterValidator(_con_items)]
    modalidad: Modalidad = Modalidad.contado
    canje_valor_usd: PrecioUSD | None = None
    # Solo en cuotas; al contado se ignoran.
    cantidad_cuotas: Annotated[int, Field(ge=2, le=60)] | None = None
    anticipo_usd: USD = Decimal(0)
    primera_cuota_hoy: bool = Field(
        default=False, description="La cuota 1 vence hoy y queda cobrada al registrar."
    )
    comision_usd: USD = Field(
        default=Decimal(0), description="Solo del Administrador: la de un Vendedor se ignora."
    )


class ComisionUpdate(BaseModel):
    comision_usd: USD


class CanjeCreate(BaseModel):
    """El equipo que entrega el cliente (reglas 4.5). Los datos que lleva dependen del tipo
    de la categoría, como al cargar un producto, pero el IMEI es opcional."""

    modelo_id: int
    capacidad_id: int | None = None
    color_id: int | None = None
    condicion: Condicion
    imei: IMEI | None = None
    bateria: Bateria | None = None
    controles: Controles | None = None
    extras: Extras | None = None


class VentaCreate(CotizacionCreate):
    """Con canje van los dos: `canje_valor_usd` y `canje` (el equipo). Sin método de pago,
    el predeterminado del catálogo (reglas 4.4: transferencia)."""

    cliente_id: int
    metodo_pago_id: int | None = None
    canje: CanjeCreate | None = None
    vendedor_numero: int | None = None
    garantia_meses: Annotated[int, Field(ge=0, le=120)] = 3


# ─── Cotización ──────────────────────────────────────────────────────────────
class CuotaCotizada(BaseModel):
    numero: int
    vencimiento: date
    monto_usd: Decimal
    cobrada: bool


class CotizacionVendedor(BaseModel):
    """Los montos en pesos son con el TC de hoy: `null` si no se cargó."""

    total_usd: Decimal
    total_ars: Decimal | None
    canje_usd: Decimal
    anticipo_usd: Decimal
    saldo_usd: Decimal = Field(
        description="Total − canje − anticipo: al contado, lo que se paga; en cuotas, lo "
        "que se financia."
    )
    saldo_ars: Decimal | None
    cuotas: list[CuotaCotizada] = Field(
        description="Vacía al contado. La última ajusta el redondeo."
    )


class CotizacionAdmin(CotizacionVendedor):
    costo_usd: Decimal | None
    ganancia_usd: Decimal | None = Field(description="Total − costo − comisión.")
    margen_pct: Decimal | None
    bajo_costo: list[int] = Field(
        description="Posiciones (desde 0) de los ítems con precio por debajo del costo."
    )


# ─── Lectura ─────────────────────────────────────────────────────────────────
class ProductoVendido(BaseModel):
    id: int
    categoria: Referencia
    modelo: Referencia
    capacidad: Referencia | None
    color: Referencia | None
    imei: str | None


class ItemVentaVendedor(BaseModel):
    producto: ProductoVendido
    cantidad: int
    precio_usd: Decimal
    es_regalo: bool


class ItemVentaAdmin(ItemVentaVendedor):
    costo_usd: Decimal | None
    bajo_costo: bool


class CanjeRead(BaseModel):
    valor_usd: Decimal
    producto: ProductoVendido | None


class VentaReadVendedor(BaseModel):
    """Los montos en pesos son con el TC congelado de la venta (`tc_ars`)."""

    id: int
    fecha: datetime
    cliente: Referencia
    usuario: Referencia
    vendedor: VendedorRead | None
    metodo_pago: Referencia
    modalidad: Modalidad
    cantidad_cuotas: int | None
    tc_ars: Decimal
    garantia_meses: int
    items: list[ItemVentaVendedor]
    canje: CanjeRead | None
    total_usd: Decimal
    total_ars: Decimal
    anticipo_usd: Decimal
    saldo_usd: Decimal = Field(description="Total − canje − anticipo.")
    saldo_ars: Decimal
    cuotas: list[CuotaRead]


class VentaReadAdmin(VentaReadVendedor):
    items: list[ItemVentaAdmin]  # type: ignore[assignment]
    comision_usd: Decimal
    costo_usd: Decimal | None
    ganancia_usd: Decimal | None = Field(description="Total − costo − comisión.")
    margen_pct: Decimal | None


PaginaVentasVendedor = Pagina[VentaReadVendedor]


class PaginaVentasAdmin(Pagina[VentaReadAdmin]):
    ganancia_total_usd: Decimal = Field(
        description="Ganancia registrada de todas las ventas (descontada la comisión), sumando "
        "solo las que tienen costo."
    )
