"""Capa de presentación: endpoints HTTP de vendedores.

Todos los logueados leen la lista y buscan por número (el Vendedor lo carga al registrar
la venta). Dar de alta, editar y borrar es solo del Administrador.
"""

from fastapi import APIRouter, Depends, status

from app.core.deps import UowDep, solo_admin, usuario_actual
from app.modules.vendedores.schemas import VendedorCreate, VendedorRead, VendedorUpdate
from app.modules.vendedores.service import VendedorService

router = APIRouter(
    prefix="/vendedores",
    tags=["Vendedores"],
    dependencies=[Depends(usuario_actual)],
)

_ADMIN = [Depends(solo_admin)]


@router.get("", response_model=list[VendedorRead])
def listar(uow: UowDep) -> list[VendedorRead]:
    return [VendedorRead.model_validate(v) for v in VendedorService(uow).listar()]


@router.get(
    "/numero/{numero}",
    response_model=VendedorRead,
    responses={404: {"description": "Vendedor no registrado."}},
)
def por_numero(numero: int, uow: UowDep) -> VendedorRead:
    """El vendedor con ese número. Si no está, 404 con "Vendedor no registrado."."""
    return VendedorRead.model_validate(VendedorService(uow).por_numero(numero))


@router.post(
    "", response_model=VendedorRead, status_code=status.HTTP_201_CREATED, dependencies=_ADMIN
)
def crear(datos: VendedorCreate, uow: UowDep) -> VendedorRead:
    return VendedorRead.model_validate(VendedorService(uow).crear(datos))


@router.patch("/{vendedor_id}", response_model=VendedorRead, dependencies=_ADMIN)
def actualizar(vendedor_id: int, datos: VendedorUpdate, uow: UowDep) -> VendedorRead:
    return VendedorRead.model_validate(VendedorService(uow).actualizar(vendedor_id, datos))


@router.delete("/{vendedor_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=_ADMIN)
def eliminar(vendedor_id: int, uow: UowDep) -> None:
    VendedorService(uow).eliminar(vendedor_id)
