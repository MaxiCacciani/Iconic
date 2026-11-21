"""DTOs de autenticación."""

from pydantic import BaseModel

from app.common.enums import Rol


class LoginCreate(BaseModel):
    email: str
    password: str


class TokenRead(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SesionRead(BaseModel):
    id: int
    nombre: str
    email: str
    rol: Rol
    permisos: list[str]
