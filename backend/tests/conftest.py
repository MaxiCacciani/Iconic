import os
from collections.abc import Iterator

os.environ.setdefault("JWT_SECRET", "secreto-de-tests-de-al-menos-32-bytes!!")
os.environ.setdefault("ENTORNO", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import app.modules.models  # noqa: F401  registra los modelos
from app.common.enums import Rol
from app.core.db import get_session
from app.core.security import crear_token, hashear_password
from app.main import crear_app
from app.modules.usuarios.models import Usuario


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    app = crear_app()
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as c:
        yield c


def _crear_usuario(session: Session, email: str, rol: Rol) -> Usuario:
    usuario = Usuario(
        nombre=email.split("@")[0], email=email, password_hash=hashear_password("secreto"), rol=rol
    )
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


@pytest.fixture
def admin(session: Session) -> Usuario:
    return _crear_usuario(session, "admin@iconic.test", Rol.admin)


@pytest.fixture
def vendedor(session: Session) -> Usuario:
    return _crear_usuario(session, "vendedor@iconic.test", Rol.vendedor)


def auth_header(usuario: Usuario) -> dict[str, str]:
    return {"Authorization": f"Bearer {crear_token(usuario.id, usuario.rol)}"}
