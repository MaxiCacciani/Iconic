from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.db import crear_tablas_sqlite
from app.core.excepciones import registrar_manejadores
from app.modules.auth.router import router as auth
from app.modules.clientes.router import router as clientes
from app.modules.cobros.router import router as cobros
from app.modules.garantias.router import router as garantias
from app.modules.packs.router import router as packs
from app.modules.productos.router import router as productos
from app.modules.reclamos.router import router as reclamos
from app.modules.reservas.router import router as reservas
from app.modules.resumen.router import router as resumen
from app.modules.tipo_cambio.router import router as tipo_cambio
from app.modules.usuarios.router import router as usuarios
from app.modules.vendedores.router import router as vendedores
from app.modules.ventas.router import router as ventas

ROUTERS = [
    auth,
    usuarios,
    productos,
    clientes,
    ventas,
    cobros,
    reservas,
    reclamos,
    packs,
    vendedores,
    garantias,
    tipo_cambio,
    resumen,
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    if settings.es_sqlite and settings.entorno != "test":
        crear_tablas_sqlite()
    yield


def crear_app() -> FastAPI:
    app = FastAPI(title=get_settings().app_nombre, lifespan=lifespan)
    registrar_manejadores(app)
    for router in ROUTERS:
        app.include_router(router)

    @app.get("/health", tags=["Sistema"])
    def health() -> dict[str, str]:
        return {"estado": "ok"}

    return app


app = crear_app()
