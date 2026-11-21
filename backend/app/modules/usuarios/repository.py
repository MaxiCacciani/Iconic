"""Acceso a datos de usuarios. Los repositorios heredan de `RepositorioBase[M]`."""

from sqlmodel import select

from app.common.base import RepositorioBase
from app.modules.usuarios.models import Usuario


class UsuarioRepository(RepositorioBase[Usuario]):
    modelo = Usuario

    def por_email(self, email: str) -> Usuario | None:
        return self.session.exec(select(Usuario).where(Usuario.email == email)).first()
