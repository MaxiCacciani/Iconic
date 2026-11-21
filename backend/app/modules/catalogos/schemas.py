"""DTOs de entrada y salida de los catálogos (Create / Read / Update).

Los catálogos que solo tienen nombre (proveedores, localidades, diagnósticos) comparten
`ItemCatalogo*`. Modelos, capacidades y colores comparten `ItemDeCategoria*`; el modelo,
además, devuelve qué colores y capacidades de su categoría tiene asignados.
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class _Read(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int


# ─── Solo nombre ──────────────────────────────────────────────────────────────
class ItemCatalogoCreate(BaseModel):
    nombre: Texto


class ItemCatalogoUpdate(BaseModel):
    nombre: Texto | None = None


class ItemCatalogoRead(_Read):
    nombre: str


# ─── Modelos, capacidades y colores (cada uno de una categoría) ───────────────
class ItemDeCategoriaCreate(BaseModel):
    categoria_id: int
    nombre: Texto


class ItemDeCategoriaUpdate(BaseModel):
    """La categoría no se cambia: el ítem se borra y se crea en la otra."""

    nombre: Texto | None = None


class ItemDeCategoriaRead(_Read):
    categoria_id: int
    nombre: str


class ModeloRead(ItemDeCategoriaRead):
    """`color_ids` y `capacidad_ids` vacíos: el modelo ofrece todos los de su categoría."""

    color_ids: list[int]
    capacidad_ids: list[int]


class AsignacionUpdate(BaseModel):
    """Reemplaza la lista completa. Vacía: el modelo vuelve a ofrecer todos."""

    ids: list[int]


# ─── Tipos de categoría ───────────────────────────────────────────────────────
class TipoCategoriaCreate(BaseModel):
    nombre: Texto
    usa_imei: bool = False
    usa_bateria: bool = False
    usa_controles: bool = False
    por_cantidad: bool = False


class TipoCategoriaUpdate(BaseModel):
    nombre: Texto | None = None
    usa_imei: bool | None = None
    usa_bateria: bool | None = None
    usa_controles: bool | None = None
    por_cantidad: bool | None = None


class TipoCategoriaRead(_Read):
    nombre: str
    usa_imei: bool
    usa_bateria: bool
    usa_controles: bool
    por_cantidad: bool


# ─── Categorías ───────────────────────────────────────────────────────────────
class CategoriaCreate(BaseModel):
    nombre: Texto
    tipo_categoria_id: int


class CategoriaUpdate(BaseModel):
    nombre: Texto | None = None
    tipo_categoria_id: int | None = None


class CategoriaRead(_Read):
    nombre: str
    tipo_categoria_id: int


# ─── Defectos ─────────────────────────────────────────────────────────────────
class DefectoCreate(BaseModel):
    descripcion: Texto
    es_comun: bool = True


class DefectoUpdate(BaseModel):
    descripcion: Texto | None = None
    es_comun: bool | None = None


class DefectoRead(_Read):
    descripcion: str
    es_comun: bool


# ─── Estados de reclamo ───────────────────────────────────────────────────────
class EstadoReclamoCreate(BaseModel):
    nombre: Texto
    es_inicial: bool = False


class EstadoReclamoUpdate(BaseModel):
    nombre: Texto | None = None
    es_inicial: bool | None = None


class EstadoReclamoRead(_Read):
    nombre: str
    es_inicial: bool


# ─── Métodos de pago ──────────────────────────────────────────────────────────
class MetodoPagoCreate(BaseModel):
    nombre: Texto
    predeterminado: bool = False


class MetodoPagoUpdate(BaseModel):
    nombre: Texto | None = None
    predeterminado: bool | None = None


class MetodoPagoRead(_Read):
    nombre: str
    predeterminado: bool
