"""Lógica de autenticación."""

from fastapi import HTTPException, status
from sqlmodel import Session

from app.common.enums import Rol
from app.core.security import crear_token, verificar_password
from app.modules.auth.schemas import SesionRead, TokenRead
from app.modules.usuarios.models import Usuario
from app.modules.usuarios.repository import UsuarioRepository

# El front arma el menú y protege las rutas con esta lista.
PERMISOS: dict[Rol, list[str]] = {
    Rol.admin: [
        "resumen",
        "productos",
        "clientes",
        "ventas",
        "cobros",
        "reservas",
        "reclamos",
        "packs",
        "vendedores",
        "usuarios",
        "catalogos",
        "garantias",
        "tipo_cambio:editar",
        "productos:editar",
        "clientes:borrar",
        "ventas:borrar",
        "ver_costos",
    ],
    Rol.vendedor: ["resumen", "productos", "clientes", "ventas", "reservas", "garantias"],
}


class AuthService:
    def __init__(self, session: Session) -> None:
        self.usuarios = UsuarioRepository(session)

    def login(self, email: str, password: str) -> TokenRead:
        usuario = self.usuarios.por_email(email)
        if (
            usuario is None
            or not usuario.activo
            or not verificar_password(password, usuario.password_hash)
        ):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email o contraseña incorrectos")
        return TokenRead(access_token=crear_token(usuario.id, usuario.rol))

    @staticmethod
    def sesion(usuario: Usuario) -> SesionRead:
        return SesionRead(
            id=usuario.id,
            nombre=usuario.nombre,
            email=usuario.email,
            rol=usuario.rol,
            permisos=PERMISOS[usuario.rol],
        )
