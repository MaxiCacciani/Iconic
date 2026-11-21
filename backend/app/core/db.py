from collections.abc import Iterator

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings


def crear_engine(url: str | None = None) -> Engine:
    settings = get_settings()
    url = url or settings.database_url
    kwargs: dict = {"echo": settings.sql_echo}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


engine = crear_engine()


def crear_tablas_sqlite() -> None:
    """Solo para correr local con SQLite: las tablas salen de los modelos.

    En PostgreSQL el esquema lo crea `sql/schema.sql`.
    """
    import app.modules.models  # noqa: F401  registra todos los modelos

    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
