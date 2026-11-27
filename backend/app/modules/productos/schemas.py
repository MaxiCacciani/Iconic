"""DTOs de entrada y salida de productos (Create / Read / Update).

Por rol: el Vendedor recibe `ProductoReadVendedor`, sin costo, ganancia ni margen.
El Administrador recibe `ProductoReadAdmin`, que le suma esos datos. Los montos en pesos
son equivalencias con el TC del día: `null` si hoy no se cargó.
"""

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.common.base import Pagina
from app.common.enums import Condicion, EstadoProductoEnum, NivelBateria
from app.common.tipos import IMEI, USD, PrecioUSD

TextoDefecto = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]
Extras = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]
Bateria = Annotated[int, Field(ge=1, le=100)]
Controles = Annotated[int, Field(ge=0, le=4)]
Cantidad = Annotated[int, Field(ge=1)]
# El stock de la fila: un accesorio por cantidad puede quedar en 0 (sin stock).
CantidadStock = Annotated[int, Field(ge=0)]


class ProductoCreate(BaseModel):
    """Qué datos lleva depende del tipo de la categoría del modelo: IMEI y batería, controles
    y extras, o cantidad. Los que no corresponden van en `null` (o se omiten).

    Defectos: `defecto_ids` son los elegidos de la lista y `defectos_nuevos`, los escritos a
    mano (si ya existe uno igual, se usa ese)."""

    modelo_id: int
    capacidad_id: int | None = None
    color_id: int | None = None
    proveedor_id: int
    condicion: Condicion
    imei: IMEI | None = None
    bateria: Bateria | None = None
    controles: Controles | None = None
    extras: Extras | None = None
    cantidad: CantidadStock = 1
    precio_usd: PrecioUSD
    costo_usd: USD | None = None
    defecto_ids: list[int] = []
    defectos_nuevos: list[TextoDefecto] = []


class ProductoUpdate(BaseModel):
    """Lo que no se manda queda como estaba. El producto resultante se valida completo, así
    que al cambiar a un modelo de otro tipo hay que mandar en `null` lo que ya no lleva.
    `defecto_ids` y `defectos_nuevos` reemplazan juntos la lista de defectos."""

    modelo_id: int | None = None
    capacidad_id: int | None = None
    color_id: int | None = None
    proveedor_id: int | None = None
    condicion: Condicion | None = None
    imei: IMEI | None = None
    bateria: Bateria | None = None
    controles: Controles | None = None
    extras: Extras | None = None
    cantidad: CantidadStock | None = None
    precio_usd: PrecioUSD | None = None
    costo_usd: USD | None = None
    defecto_ids: list[int] | None = None
    defectos_nuevos: list[TextoDefecto] | None = None


class Referencia(BaseModel):
    id: int
    nombre: str


class DefectoDeProducto(BaseModel):
    id: int
    descripcion: str


class ProductoReadVendedor(BaseModel):
    id: int
    categoria: Referencia
    modelo: Referencia
    capacidad: Referencia | None
    color: Referencia | None
    proveedor: Referencia
    condicion: Condicion
    estado: EstadoProductoEnum
    editable: bool = Field(
        description="Si se puede editar o borrar en su estado (solo mientras está disponible)."
    )
    imei: str | None
    bateria: int | None
    bateria_nivel: NivelBateria | None = Field(
        description="Color de la batería: alta (85 o más), media (80 a 84) o baja (menos de 80)."
    )
    controles: int | None
    extras: str | None
    cantidad: int
    precio_usd: Decimal
    precio_ars: Decimal | None
    defectos: list[DefectoDeProducto]
    creado_en: datetime


class ProductoReadAdmin(ProductoReadVendedor):
    """Sin costo cargado, costo, ganancia y margen van en `null`."""

    costo_usd: Decimal | None
    costo_ars: Decimal | None
    ganancia_usd: Decimal | None
    ganancia_ars: Decimal | None
    margen_pct: Decimal | None = Field(description="Ganancia sobre costo, en %.")


PaginaProductosVendedor = Pagina[ProductoReadVendedor]
PaginaProductosAdmin = Pagina[ProductoReadAdmin]
