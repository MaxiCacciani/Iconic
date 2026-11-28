"""Capa de presentación: endpoints HTTP de clientes.

Los dos roles buscan, ven la ficha, dan de alta y editan (el Vendedor carga al cliente
durante la venta). Borrar es solo del Administrador.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.common.base import ParamsPagina
from app.core.deps import UowDep, solo_admin, usuario_actual
from app.modules.clientes.schemas import ClienteCreate, ClienteRead, ClienteUpdate, PaginaClientes
from app.modules.clientes.service import ClienteService
from app.modules.cobros.schemas import CuotasClienteRead
from app.modules.cobros.service import CobroService

router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"],
    dependencies=[Depends(usuario_actual)],
)


@router.get("", response_model=PaginaClientes)
def listar(
    uow: UowDep,
    params: Annotated[ParamsPagina, Query()],
    buscar: Annotated[
        str | None, Query(max_length=100, description="Parte del nombre o del DNI")
    ] = None,
) -> PaginaClientes:
    return ClienteService(uow).buscar(buscar, params)


@router.get("/{cliente_id}", response_model=ClienteRead)
def obtener(cliente_id: int, uow: UowDep) -> ClienteRead:
    return ClienteService(uow).obtener(cliente_id)


@router.get("/{cliente_id}/cuotas", response_model=CuotasClienteRead)
def cuotas(cliente_id: int, uow: UowDep) -> CuotasClienteRead:
    """Saldo, mora y plan de cuotas de cada venta en cuotas del cliente."""
    ClienteService(uow).obtener(cliente_id)
    return CobroService(uow).de_cliente(cliente_id)


@router.post("", response_model=ClienteRead, status_code=status.HTTP_201_CREATED)
def crear(datos: ClienteCreate, uow: UowDep) -> ClienteRead:
    return ClienteService(uow).crear(datos)


@router.patch("/{cliente_id}", response_model=ClienteRead)
def actualizar(cliente_id: int, datos: ClienteUpdate, uow: UowDep) -> ClienteRead:
    return ClienteService(uow).actualizar(cliente_id, datos)


@router.delete(
    "/{cliente_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(solo_admin)],
)
def eliminar(cliente_id: int, uow: UowDep) -> None:
    ClienteService(uow).eliminar(cliente_id)
