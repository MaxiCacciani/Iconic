"""Funciones puras de packs: sin base de datos, para testear primero.

Reglas 4.2: al aplicar un pack, los productos fijos se agregan tal cual (si están
disponibles) y, por cada categoría, el primer producto disponible, sin repetir el mismo
equipo.

`repartir` resuelve eso como un reparto de unidades:
- Cada ítem pide `cantidad` unidades y trae sus candidatos en orden de preferencia: el
  producto fijo solo, o los disponibles de la categoría del más antiguo al más nuevo.
- Se reparte en el orden en que vienen los ítems (el service pone primero los fijos, así
  una categoría no se lleva el producto que un fijo pidió por nombre).
- Una unidad no se da dos veces: un equipo (1 unidad) va a un solo ítem, y de un accesorio
  por cantidad se reparten las que tiene. Lo que ya está en el carrito no se vuelve a dar.
- Si un candidato no alcanza, se completa con el siguiente; lo que no se cubre es faltante.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Candidato:
    producto_id: int
    unidades: int
    """Las que tiene el producto: 1 para un equipo, las de la fila para un accesorio."""


@dataclass(frozen=True)
class Pedido:
    clave: int
    """Con qué se identifica el ítem en el resultado (el id del ítem del pack)."""
    cantidad: int
    candidatos: Sequence[Candidato]


@dataclass(frozen=True)
class Asignacion:
    clave: int
    producto_id: int
    cantidad: int


@dataclass(frozen=True)
class Reparto:
    asignaciones: list[Asignacion]
    faltantes: dict[int, int]
    """Por clave, cuántas unidades no se pudieron cubrir."""


def repartir(pedidos: Sequence[Pedido], ocupadas: Mapping[int, int] | None = None) -> Reparto:
    """`ocupadas`: unidades de cada producto que ya están en el carrito."""
    usadas: dict[int, int] = dict(ocupadas or {})
    asignaciones: list[Asignacion] = []
    faltantes: dict[int, int] = {}

    for pedido in pedidos:
        falta = pedido.cantidad
        for candidato in pedido.candidatos:
            if falta == 0:
                break
            libres = candidato.unidades - usadas.get(candidato.producto_id, 0)
            if libres <= 0:
                continue
            toma = min(libres, falta)
            usadas[candidato.producto_id] = usadas.get(candidato.producto_id, 0) + toma
            asignaciones.append(Asignacion(pedido.clave, candidato.producto_id, toma))
            falta -= toma
        if falta:
            faltantes[pedido.clave] = falta

    return Reparto(asignaciones, faltantes)
