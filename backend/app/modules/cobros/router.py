"""Capa de presentación: endpoints HTTP de cobros.

La agenda y marcar una cuota como cobrada son del Administrador. El plan de cuotas de un
cliente lo ven los dos roles, en su ficha (`GET /clientes/{id}/cuotas`).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.deps import UowDep, solo_admin
from app.modules.cobros.schemas import AgendaRead, CobroAgendaRead
from app.modules.cobros.service import CobroService

router = APIRouter(prefix="/cobros", tags=["Cobros"], dependencies=[Depends(solo_admin)])


@router.get("", response_model=AgendaRead)
def agenda(
    uow: UowDep,
    anio: Annotated[int | None, Query(ge=2000, le=2100)] = None,
    mes: Annotated[int | None, Query(ge=1, le=12, description="Sin mes, el actual.")] = None,
) -> AgendaRead:
    return CobroService(uow).agenda(anio, mes)


@router.post("/{cobro_id}/cobrar", response_model=CobroAgendaRead)
def cobrar(cobro_id: int, uow: UowDep) -> CobroAgendaRead:
    """Una cuota ya cobrada da 409."""
    return CobroService(uow).cobrar(cobro_id)
