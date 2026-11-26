"""Qué catálogos hay y qué tiene de particular cada uno.

El ABMC es el mismo para todos (`service.py`, `router.py`); acá se declara lo que cambia:
el campo de texto, si se agrupa por categoría, a qué otra tabla apunta y si tiene un
valor que tiene que ser único (el método de pago predeterminado, el estado inicial).

`ASIGNACIONES` declara lo que cada modelo elige de su categoría (colores y capacidades).
Es la única lista: de ahí salen el `?modelo_id=` de esos catálogos, el
`PUT /catalogos/modelos/{id}/asignaciones` y qué tablas no frenan un borrado.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

from pydantic import BaseModel
from sqlmodel import Session, SQLModel

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
    ModeloCapacidad,
    ModeloColor,
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
class FijoConProductos:
    """Campos que no se cambian si ya hay productos que dependen de la fila.

    Cambiar qué datos lleva un tipo de categoría (o el tipo de una categoría) dejaría a
    los productos cargados con datos que ya no corresponden: un iPhone sin IMEI o un
    accesorio con batería. `contar` dice cuántos productos dependen de la fila.
    """

    campos: tuple[str, ...]
    contar: Callable[[Session, int], int]
    mensaje: str
    """Con `{}` para la cantidad: "1 producto cargado", "3 productos cargados"."""


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
    con_asignaciones: bool = False
    """Modelos: al listarlos se cargan sus colores y capacidades (ver `ASIGNACIONES`)."""
    fijo_con_productos: FijoConProductos | None = None


@dataclass(frozen=True)
class Asignacion:
    """Lo que un modelo elige de su categoría.

    `slug` es a la vez el catálogo (`colores`) y el atributo de `Modelo` con los asignados.
    `enlace` es la tabla intermedia y `columna`, su clave hacia el catálogo.
    `campo` es la lista de ids en `ModeloRead` y en `AsignacionesUpdate`.
    """

    slug: str
    modelo: type[SQLModel]
    enlace: type[SQLModel]
    columna: str
    campo: str
    no_existe: str
    otra_categoria: str
    """Con `{}` para el nombre: "«Verde alpino» no es un color de la categoría del modelo"."""
    sin_opciones: tuple[str, str]
    """Aviso al borrar el último asignado de un modelo, en singular y en plural, con `{}`
    para los nombres de los modelos."""


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


def _productos_de_tipo(session: Session, tipo_id: int) -> int:
    # Import diferido: productos depende de catálogos, no al revés.
    from app.modules.productos.repository import ProductoRepository

    return ProductoRepository(session).de_tipo_categoria(tipo_id)


def _productos_de_categoria(session: Session, categoria_id: int) -> int:
    from app.modules.productos.repository import ProductoRepository

    return ProductoRepository(session).de_categoria(categoria_id)


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
        fijo_con_productos=FijoConProductos(
            campos=("usa_imei", "usa_bateria", "usa_controles", "por_cantidad"),
            contar=_productos_de_tipo,
            mensaje="No se puede cambiar qué datos lleva: ya hay {} de este tipo. "
            "Solo se puede cambiar el nombre.",
        ),
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
        fijo_con_productos=FijoConProductos(
            campos=("tipo_categoria_id",),
            contar=_productos_de_categoria,
            mensaje="No se puede cambiar el tipo: ya hay {} en esta categoría.",
        ),
    ),
    Definicion(
        slug="modelos",
        titulo="Modelos",
        modelo=Modelo,
        crear=s.ItemDeCategoriaCreate,
        editar=s.ItemDeCategoriaUpdate,
        leer=s.ModeloRead,
        repetido="Esta categoría ya tiene un modelo con ese nombre.",
        ambito="categoria_id",
        referencias={"categoria_id": _CATEGORIA},
        con_asignaciones=True,
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

ASIGNACIONES: list[Asignacion] = [
    Asignacion(
        slug="colores",
        modelo=Color,
        enlace=ModeloColor,
        columna="color_id",
        campo="color_ids",
        no_existe="Uno de los colores no existe.",
        otra_categoria="«{}» no es un color de la categoría del modelo.",
        sin_opciones=(
            "{} se quedó sin colores marcados: ahora ofrece todos los de su categoría.",
            "{} se quedaron sin colores marcados: ahora ofrecen todos los de su categoría.",
        ),
    ),
    Asignacion(
        slug="capacidades",
        modelo=Capacidad,
        enlace=ModeloCapacidad,
        columna="capacidad_id",
        campo="capacidad_ids",
        no_existe="Una de las capacidades no existe.",
        otra_categoria="«{}» no es una capacidad de la categoría del modelo.",
        sin_opciones=(
            "{} se quedó sin capacidades marcadas: ahora ofrece todas las de su categoría.",
            "{} se quedaron sin capacidades marcadas: ahora ofrecen todas las de su categoría.",
        ),
    ),
]

ASIGNACION_POR_SLUG = {a.slug: a for a in ASIGNACIONES}

TABLAS_DE_ASIGNACION = frozenset(a.enlace.__tablename__ for a in ASIGNACIONES)  # type: ignore[attr-defined]
"""Las asignaciones no cuentan como "en uso": se borran con el color o el modelo."""
