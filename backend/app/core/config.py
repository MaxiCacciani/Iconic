from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración leída desde el entorno / `.env`."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_nombre: str = "Iconic API"
    entorno: str = "local"  # local | docker | test

    # "Hoy" es el día en Argentina, no el del servidor (que en Docker corre en UTC).
    zona_horaria: str = "America/Argentina/Buenos_Aires"

    # Base de datos: PostgreSQL en Docker, SQLite si se corre local sin Docker.
    database_url: str = "sqlite:///./iconic.db"
    sql_echo: bool = False

    # Seguridad (token Bearer de 60 minutos)
    jwt_secret: str = "cambiar-en-produccion"
    jwt_algoritmo: str = "HS256"
    jwt_minutos: int = 60

    # Cloudflare R2 (compatible S3) para comprobantes de garantía
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket: str = ""
    r2_url_ttl_segundos: int = 300

    @property
    def es_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
