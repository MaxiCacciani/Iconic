"""ENUMs nativos: valores fijos de los que depende la lógica del código.

Deben coincidir con los `CREATE TYPE` de `sql/schema.sql`.
"""

from enum import StrEnum


class Rol(StrEnum):
    admin = "admin"
    vendedor = "vendedor"


class Condicion(StrEnum):
    nuevo = "nuevo"
    usado = "usado"


class EstadoProductoEnum(StrEnum):
    disponible = "disponible"
    reservado = "reservado"
    vendido = "vendido"


class EstadoReservaEnum(StrEnum):
    activa = "activa"
    convertida = "convertida"
    cancelada = "cancelada"


class EstadoCobroEnum(StrEnum):
    """`vencida` no se guarda: es una cuota pendiente con fecha pasada."""

    pendiente = "pendiente"
    cobrada = "cobrada"


class Modalidad(StrEnum):
    contado = "contado"
    cuotas = "cuotas"


class TipoArchivo(StrEnum):
    pdf = "pdf"
    jpg = "jpg"


class NivelBateria(StrEnum):
    """Solo indicación visual: >= 85 alta, 80-84 media, < 80 baja."""

    alta = "alta"
    media = "media"
    baja = "baja"
