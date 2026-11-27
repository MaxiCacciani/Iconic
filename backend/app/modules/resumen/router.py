"""Capa de presentación: pantalla de inicio (`GET /resumen`). Solo lectura."""

from fastapi import APIRouter, Depends

from app.core.deps import Logueado, UowDep, usuario_actual
from app.modules.resumen.schemas import ResumenRead
from app.modules.resumen.service import ResumenService

router = APIRouter(prefix="/resumen", tags=["Resumen"], dependencies=[Depends(usuario_actual)])


@router.get("", response_model=ResumenRead)
def resumen(uow: UowDep, usuario: Logueado) -> ResumenRead:
    return ResumenService(uow).resumen(usuario)
