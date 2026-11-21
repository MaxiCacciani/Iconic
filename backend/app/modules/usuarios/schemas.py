"""DTOs de entrada y salida de usuarios (Create / Read / Update).

Ningún DTO de salida expone `password_hash`.
"""

import re
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, StringConstraints

from app.common.enums import Rol

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validar_email(valor: str) -> str:
    valor = valor.strip().lower()
    if not _EMAIL.match(valor):
        raise ValueError("Ingresá un email válido, por ejemplo nombre@iconic.com.")
    return valor


Nombre = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Email = Annotated[str, AfterValidator(_validar_email)]
Password = Annotated[str, StringConstraints(min_length=8, max_length=128)]


class UsuarioCreate(BaseModel):
    nombre: Nombre
    email: Email
    password: Password
    rol: Rol


class UsuarioUpdate(BaseModel):
    """Edición parcial. `password` blanquea la contraseña; `activo` activa o desactiva."""

    nombre: Nombre | None = None
    email: Email | None = None
    rol: Rol | None = None
    activo: bool | None = None
    password: Password | None = None


class UsuarioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: str
    rol: Rol
    activo: bool
    creado_en: datetime
