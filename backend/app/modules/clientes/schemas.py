"""DTOs de entrada y salida de clientes (Create / Read / Update).

Los clientes no tienen costos: los dos roles reciben el mismo `ClienteRead`.
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, StringConstraints

from app.common.base import Pagina
from app.common.tipos import DNI, Telefono

Nombre = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


def _vacio_es_nulo(valor: object) -> object:
    """Un campo opcional que se deja en blanco es "sin dato", no un DNI inválido."""
    return None if isinstance(valor, str) and not valor.strip() else valor


DNIOpcional = Annotated[DNI | None, BeforeValidator(_vacio_es_nulo)]
TelefonoOpcional = Annotated[Telefono | None, BeforeValidator(_vacio_es_nulo)]


class ClienteCreate(BaseModel):
    """El DNI y el teléfono aceptan puntos, espacios o guiones (`30.123.456`,
    `+54 9 11 5555-1234`): se guardan solo los dígitos."""

    nombre: Nombre
    dni: DNIOpcional = None
    telefono: TelefonoOpcional = None
    localidad_id: int | None = None


class ClienteUpdate(BaseModel):
    """Lo que no se manda queda como estaba. `null` borra el DNI, el teléfono o la
    localidad; el nombre es obligatorio y no se puede borrar."""

    nombre: Nombre | None = None
    dni: DNIOpcional = None
    telefono: TelefonoOpcional = None
    localidad_id: int | None = None


class Referencia(BaseModel):
    id: int
    nombre: str


class ClienteRead(BaseModel):
    id: int
    nombre: str
    dni: str | None
    telefono: str | None
    localidad: Referencia | None
    creado_en: datetime


PaginaClientes = Pagina[ClienteRead]
