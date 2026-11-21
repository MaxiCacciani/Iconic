"""Acceso a datos de usuarios. Los repositorios heredan de `RepositorioBase[M]`."""

from collections.abc import Sequence

from sqlmodel import func, select

from app.common.base import RepositorioBase
from app.common.enums import Rol
from app.modules.usuarios.models import Usuario


class UsuarioRepository(RepositorioBase[Usuario]):
    modelo = Usuario

    def por_email(self, email: str) -> Usuario | None:
        return self.session.exec(
            select(Usuario).where(func.lower(Usuario.email) == email.lower())
        ).first()

    def todos(self) -> Sequence[Usuario]:
        """Activos primero, después por nombre."""
        return self.session.exec(
            select(Usuario).order_by(Usuario.activo.desc(), Usuario.nombre)  # type: ignore[attr-defined]
        ).all()

    def admins_activos(self) -> int:
        return self.session.exec(
            select(func.count())
            .select_from(Usuario)
            .where(Usuario.rol == Rol.admin, Usuario.activo == True)  # noqa: E712
        ).one()
