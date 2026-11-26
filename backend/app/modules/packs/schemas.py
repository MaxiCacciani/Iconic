"""DTOs de entrada y salida de packs (Create / Read / Update).

El pack en sí no tiene costos: los dos roles reciben el mismo `PackRead`. Al aplicarlo se
devuelven productos del stock, y ahí sí manda el rol: el Vendedor recibe
`PackAplicadoVendedor`, con los productos sin costo, ganancia ni margen.
"""

from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, StringConstraints, model_validator

from app.common.enums import Condicion, EstadoProductoEnum
from app.modules.productos.schemas import ProductoReadAdmin, ProductoReadVendedor, Referencia

NombrePack = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Descripcion = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]
Cantidad = Annotated[int, Field(ge=1, le=999)]


class PackItemCreate(BaseModel):
    """Un producto fijo del stock (`producto_id`) o una categoría (`categoria_id`), nunca
    los dos. Con una categoría, al aplicar el pack se toma el primer disponible."""

    producto_id: int | None = None
    categoria_id: int | None = None
    cantidad: Cantidad = 1
    es_regalo: bool = False

    @model_validator(mode="after")
    def _uno_u_otro(self) -> "PackItemCreate":
        if (self.producto_id is None) == (self.categoria_id is None):
            raise ValueError("Elegí un producto o una categoría (uno de los dos).")
        return self


def _con_items(items: list[PackItemCreate]) -> list[PackItemCreate]:
    if not items:
        raise ValueError("El pack tiene que tener al menos un producto o una categoría.")
    return items


Items = Annotated[list[PackItemCreate], AfterValidator(_con_items)]


def _vacio_es_nulo(valor: str | None) -> str | None:
    return valor or None


class PackCreate(BaseModel):
    nombre: NombrePack
    descripcion: Annotated[Descripcion | None, AfterValidator(_vacio_es_nulo)] = None
    items: Items


class PackUpdate(BaseModel):
    """Lo que no se manda queda como estaba. `items` reemplaza la lista entera."""

    nombre: NombrePack | None = None
    descripcion: Annotated[Descripcion | None, AfterValidator(_vacio_es_nulo)] = None
    items: Items | None = None


class ProductoEnPack(BaseModel):
    """Lo justo para reconocer el producto fijo de un ítem. Sin precios: al aplicar el
    pack se manda el producto completo."""

    id: int
    categoria: Referencia
    modelo: Referencia
    capacidad: Referencia | None
    color: Referencia | None
    imei: str | None
    condicion: Condicion
    estado: EstadoProductoEnum


class PackItemRead(BaseModel):
    id: int
    producto: ProductoEnPack | None
    categoria: Referencia | None
    cantidad: int
    es_regalo: bool
    unidades_disponibles: int = Field(
        description=(
            "Cuántas unidades hay hoy para este ítem: las del producto fijo si está "
            "disponible, o las disponibles de la categoría."
        )
    )


class PackRead(BaseModel):
    id: int
    nombre: str
    descripcion: str | None
    items: list[PackItemRead]


# ─── Aplicar ─────────────────────────────────────────────────────────────────
class EnCarrito(BaseModel):
    producto_id: int
    cantidad: Annotated[int, Field(ge=1)] = 1


class PackAplicar(BaseModel):
    """Lo que ya está en el carrito, para no volver a dar el mismo equipo (ni más unidades
    de un accesorio de las que hay)."""

    en_carrito: list[EnCarrito] = []


class Faltante(BaseModel):
    pack_item_id: int
    faltan: int = Field(description="Unidades que no se pudieron agregar.")
    mensaje: str


class LineaPackVendedor(BaseModel):
    pack_item_id: int
    producto: ProductoReadVendedor
    cantidad: int
    es_regalo: bool


class LineaPackAdmin(BaseModel):
    pack_item_id: int
    producto: ProductoReadAdmin
    cantidad: int
    es_regalo: bool


class PackAplicadoVendedor(BaseModel):
    """Las líneas para sumar al carrito y lo que no se pudo agregar. Un pack que no se
    puede completar no es un error: se agrega lo que hay y se avisa lo que falta."""

    pack: Referencia
    lineas: list[LineaPackVendedor]
    faltantes: list[Faltante]


class PackAplicadoAdmin(BaseModel):
    pack: Referencia
    lineas: list[LineaPackAdmin]
    faltantes: list[Faltante]
