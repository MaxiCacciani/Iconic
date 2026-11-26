"""Capa de presentación: endpoints HTTP de packs.

Todos los logueados leen los packs y los aplican (el Vendedor los usa al armar el carrito).
Armarlos, editarlos y borrarlos es solo del Administrador. Al aplicar, el rol decide el
DTO de los productos: el Vendedor no recibe costos.
"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, status

from app.common.enums import Rol
from app.core.deps import Logueado, UowDep, solo_admin, usuario_actual
from app.modules.packs.schemas import (
    PackAplicadoAdmin,
    PackAplicadoVendedor,
    PackAplicar,
    PackCreate,
    PackRead,
    PackUpdate,
)
from app.modules.packs.service import PackService

router = APIRouter(
    prefix="/packs",
    tags=["Packs"],
    dependencies=[Depends(usuario_actual)],
)

_ADMIN = [Depends(solo_admin)]


@router.get("", response_model=list[PackRead])
def listar(uow: UowDep) -> list[PackRead]:
    return PackService(uow).listar()


@router.get("/{pack_id}", response_model=PackRead)
def obtener(pack_id: int, uow: UowDep) -> PackRead:
    return PackService(uow).obtener(pack_id)


# El Administrador primero: con los dos, la respuesta se valida contra el que tiene costos
# solo si el service lo armó con costos (como en productos).
@router.post(
    "/{pack_id}/aplicar",
    response_model=PackAplicadoAdmin | PackAplicadoVendedor,
    responses={409: {"description": "No hay stock para algún ítem: no se agrega nada."}},
)
def aplicar(
    pack_id: int,
    uow: UowDep,
    usuario: Logueado,
    datos: Annotated[PackAplicar | None, Body()] = None,
) -> PackAplicadoAdmin | PackAplicadoVendedor:
    """Los productos del pack para sumar al carrito. Va entero o no va: si falta stock de
    algo, 409. No reserva nada: el stock se toca recién al vender."""
    return PackService(uow).aplicar(
        pack_id, datos or PackAplicar(), con_costos=usuario.rol == Rol.admin
    )


@router.post("", response_model=PackRead, status_code=status.HTTP_201_CREATED, dependencies=_ADMIN)
def crear(datos: PackCreate, uow: UowDep) -> PackRead:
    return PackService(uow).crear(datos)


@router.patch("/{pack_id}", response_model=PackRead, dependencies=_ADMIN)
def actualizar(pack_id: int, datos: PackUpdate, uow: UowDep) -> PackRead:
    return PackService(uow).actualizar(pack_id, datos)


@router.delete("/{pack_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=_ADMIN)
def eliminar(pack_id: int, uow: UowDep) -> None:
    PackService(uow).eliminar(pack_id)
