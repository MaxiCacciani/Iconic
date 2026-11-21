"""Capa de presentación: endpoints HTTP de tipo de cambio.

Todos lo ven (el Vendedor también necesita saber si falta); solo el Administrador lo carga.
"""

from fastapi import APIRouter, Depends

from app.core.deps import SoloAdmin, UowDep, usuario_actual
from app.modules.tipo_cambio.schemas import TipoCambioHoyRead, TipoCambioUpdate
from app.modules.tipo_cambio.service import TipoCambioService

router = APIRouter(
    prefix="/tipo-cambio",
    tags=["Tipo de cambio"],
    dependencies=[Depends(usuario_actual)],
)


@router.get("/hoy", response_model=TipoCambioHoyRead)
def hoy(uow: UowDep) -> TipoCambioHoyRead:
    return TipoCambioService(uow).hoy()


@router.put("/hoy", response_model=TipoCambioHoyRead)
def cargar_hoy(datos: TipoCambioUpdate, uow: UowDep, actor: SoloAdmin) -> TipoCambioHoyRead:
    return TipoCambioService(uow).cargar_hoy(datos.valor_ars, actor)
