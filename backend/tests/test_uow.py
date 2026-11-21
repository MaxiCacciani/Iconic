import pytest
from sqlmodel import select

from app.common.enums import Rol
from app.core.uow import UnidadDeTrabajo
from app.modules.usuarios.models import Usuario
from app.modules.usuarios.repository import UsuarioRepository


def _usuario(email: str) -> Usuario:
    return Usuario(nombre="x", email=email, password_hash="h", rol=Rol.vendedor)


def test_commit_si_no_falla(session):
    with UnidadDeTrabajo(session):
        UsuarioRepository(session).crear(_usuario("a@x.com"))
    assert session.exec(select(Usuario)).one().email == "a@x.com"


def test_rollback_si_falla(session):
    with pytest.raises(RuntimeError), UnidadDeTrabajo(session):
        UsuarioRepository(session).crear(_usuario("b@x.com"))
        raise RuntimeError("falla un paso")
    assert session.exec(select(Usuario)).all() == []
