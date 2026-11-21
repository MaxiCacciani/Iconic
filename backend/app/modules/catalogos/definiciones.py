"""Qué catálogos hay y qué tiene de particular cada uno.

El ABMC es el mismo para todos (`service.py`, `router.py`); acá se declara lo que cambia:
el campo de texto, si se agrupa por categoría, a qué otra tabla apunta y si tiene un
valor que tiene que ser único (el método de pago predeterminado, el estado inicial).
"""

from collections.abc import Callable
from dataclasses import dataclass, field

from pydantic import BaseModel
from sqlmodel import SQLModel

from app.core.excepciones import ErrorDeCampo
from app.modules.catalogos import schemas as s
from app.modules.catalogos.models import (
    Capacidad,
    Categoria,
    Color,
    Defecto,
    Diagnostico,
    EstadoReclamo,
    Localidad,
    MetodoPago,
    Modelo,
    Proveedor,
    TipoCategoria,
)


@dataclass(frozen=True)
class Referencia:
    modelo: type[SQLModel]
    mensaje: str


@dataclass(frozen=True)
class Marca:
    """Un booleano que tiene que estar en una sola fila, y siempre en una.

    Marcar otra fila se lo saca a la anterior; no se puede desmarcar ni borrar la marcada.
    """

    campo: str
    sin_marca: str
    al_borrar: str


@dataclass(frozen=True)
class Definicion:
    slug: str
    titulo: str
    modelo: type[SQLModel]
    crear: type[BaseModel]
    editar: type[BaseModel]
    leer: type[BaseModel]
    repetido: str
    campo_texto: str = "nombre"
    ambito: str | None = None
    referencias: dict[str, Referencia] = field(default_factory=dict)
    marca: Marca | None = None
    validar: Callable[[SQLModel], None] | None = None


def _validar_tipo_categoria(tipo: SQLModel) -> None:
    # Reglas 2.1: lo que va por cantidad son varias unidades en una fila; IMEI, batería
    # y controles son datos de una sola unidad.
    assert isinstance(tipo, TipoCategoria)
    if tipo.por_cantidad and (tipo.usa_imei or tipo.usa_bateria or tipo.usa_controles):
        raise ErrorDeCampo(
            "por_cantidad",
            "Un tipo por cantidad no puede llevar IMEI, batería ni controles: "
            "esos datos son de una sola unidad.",
        )


_CATEGORIA = Referencia(Categoria, "Esa categoría no existe.")

DEFINICIONES: list[Definicion] = [
    Definicion(
        slug="tipos-categoria",
        titulo="Tipos de categoría",
        modelo=TipoCategoria,
        crear=s.TipoCategoriaCreate,
        editar=s.TipoCategoriaUpdate,
        leer=s.TipoCategoriaRead,
        repetido="Ya hay un tipo de categoría con ese nombre.",
        validar=_validar_tipo_categoria,
    ),
    Definicion(
        slug="categorias",
        titulo="Categorías",
        modelo=Categoria,
        crear=s.CategoriaCreate,
        editar=s.CategoriaUpdate,
        leer=s.CategoriaRead,
        repetido="Ya hay una categoría con ese nombre.",
        referencias={
            "tipo_categoria_id": Referencia(TipoCategoria, "Ese tipo de categoría no existe.")
        },
    ),
    Definicion(
        slug="modelos",
        titulo="Modelos",
        modelo=Modelo,
        crear=s.ItemDeCategoriaCreate,
        editar=s.ItemDeCategoriaUpdate,
        leer=s.ItemDeCategoriaRead,
        repetido="Esta categoría ya tiene un modelo con ese nombre.",
        ambito="categoria_id",
        referencias={"categoria_id": _CATEGORIA},
    ),
    Definicion(
        slug="capacidades",
        titulo="Capacidades",
        modelo=Capacidad,
        crear=s.ItemDeCategoriaCreate,
        editar=s.ItemDeCategoriaUpdate,
        leer=s.ItemDeCategoriaRead,
        repetido="Esta categoría ya tiene esa capacidad.",
        ambito="categoria_id",
        referencias={"categoria_id": _CATEGORIA},
    ),
    Definicion(
        slug="colores",
        titulo="Colores",
        modelo=Color,
        crear=s.ItemDeCategoriaCreate,
        editar=s.ItemDeCategoriaUpdate,
        leer=s.ItemDeCategoriaRead,
        repetido="Esta categoría ya tiene ese color.",
        ambito="categoria_id",
        referencias={"categoria_id": _CATEGORIA},
    ),
    Definicion(
        slug="proveedores",
        titulo="Proveedores",
        modelo=Proveedor,
        crear=s.ItemCatalogoCreate,
        editar=s.ItemCatalogoUpdate,
        leer=s.ItemCatalogoRead,
        repetido="Ya hay un proveedor con ese nombre.",
    ),
    Definicion(
        slug="defectos",
        titulo="Defectos",
        modelo=Defecto,
        crear=s.DefectoCreate,
        editar=s.DefectoUpdate,
        leer=s.DefectoRead,
        repetido="Ese defecto ya está en la lista.",
        campo_texto="descripcion",
    ),
    Definicion(
        slug="localidades",
        titulo="Localidades",
        modelo=Localidad,
        crear=s.ItemCatalogoCreate,
        editar=s.ItemCatalogoUpdate,
        leer=s.ItemCatalogoRead,
        repetido="Ya hay una localidad con ese nombre.",
    ),
    Definicion(
        slug="diagnosticos",
        titulo="Diagnósticos",
        modelo=Diagnostico,
        crear=s.ItemCatalogoCreate,
        editar=s.ItemCatalogoUpdate,
        leer=s.ItemCatalogoRead,
        repetido="Ese diagnóstico ya está en la lista.",
    ),
    Definicion(
        slug="estados-reclamo",
        titulo="Estados de reclamo",
        modelo=EstadoReclamo,
        crear=s.EstadoReclamoCreate,
        editar=s.EstadoReclamoUpdate,
        leer=s.EstadoReclamoRead,
        repetido="Ya hay un estado con ese nombre.",
        marca=Marca(
            campo="es_inicial",
            sin_marca="Los reclamos necesitan un estado inicial. Marcá otro como inicial.",
            al_borrar="No se puede borrar el estado inicial. Marcá otro como inicial antes.",
        ),
    ),
    Definicion(
        slug="metodos-pago",
        titulo="Métodos de pago",
        modelo=MetodoPago,
        crear=s.MetodoPagoCreate,
        editar=s.MetodoPagoUpdate,
        leer=s.MetodoPagoRead,
        repetido="Ya hay un método de pago con ese nombre.",
        marca=Marca(
            campo="predeterminado",
            sin_marca="Tiene que haber un método predeterminado. Marcá otro como predeterminado.",
            al_borrar="No se puede borrar el método predeterminado. Marcá otro antes.",
        ),
    ),
]

POR_SLUG = {d.slug: d for d in DEFINICIONES}
