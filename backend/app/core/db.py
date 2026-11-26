from collections.abc import Iterator

from sqlalchemy import Engine, inspect
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


def tablas_faltantes(motor: Engine | None = None) -> list[str]:
    """Tablas de los modelos que la base no tiene.

    En PostgreSQL el esquema lo crea `sql/schema.sql` solo la primera vez que se crea el
    volumen: si después se suman tablas, la base vieja no las tiene y cada consulta que las
    usa falla con un 500. Mejor enterarse al arrancar.
    """
    import app.modules.models  # noqa: F401  registra todos los modelos

    existentes = set(inspect(motor or engine).get_table_names())
    return sorted(t for t in SQLModel.metadata.tables if t not in existentes)


def verificar_esquema() -> None:
    faltantes = tablas_faltantes()
    if faltantes:
        raise RuntimeError(
            f"A la base le faltan tablas de sql/schema.sql: {', '.join(faltantes)}. "
            "El esquema solo se aplica al crear el volumen. Recrealo con "
            "`docker compose down -v && docker compose up --build` (borra los datos) "
            "o creá esas tablas a mano con su CREATE TABLE de sql/schema.sql."
        )


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
