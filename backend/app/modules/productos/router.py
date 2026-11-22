"""Capa de presentación: endpoints HTTP de productos.

Todos los logueados ven el stock (el Vendedor lo necesita para vender), pero el rol decide
el DTO: el Vendedor recibe `ProductoReadVendedor`, sin costo, ganancia ni margen. Cargar,
editar y borrar es solo del Administrador.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.common.base import ParamsPagina
from app.common.enums import Condicion, EstadoProductoEnum, Rol
from app.core.deps import Logueado, UowDep, solo_admin, usuario_actual
from app.modules.productos.repository import FiltrosProducto
from app.modules.productos.schemas import (
    PaginaProductosAdmin,
    PaginaProductosVendedor,
    ProductoCreate,
    ProductoReadAdmin,
    ProductoReadVendedor,
    ProductoUpdate,
)
from app.modules.productos.service import ProductoService

router = APIRouter(
    prefix="/productos",
    tags=["Productos"],
    dependencies=[Depends(usuario_actual)],
)

_ADMIN = [Depends(solo_admin)]


def _filtros(
    estado: EstadoProductoEnum | None = None,
    categoria_id: int | None = None,
    modelo_id: int | None = None,
    condicion: Condicion | None = None,
    buscar: Annotated[
        str | None, Query(max_length=100, description="Parte del IMEI o del modelo")
    ] = None,
) -> FiltrosProducto:
    return FiltrosProducto(estado, categoria_id, modelo_id, condicion, buscar)


# El Administrador primero: con los dos, la respuesta se valida contra el que tiene costos
# solo si el service lo armó con costos (el del Vendedor no trae esos campos).
@router.get("", response_model=PaginaProductosAdmin | PaginaProductosVendedor)
def listar(
    uow: UowDep,
    usuario: Logueado,
    filtros: Annotated[FiltrosProducto, Depends(_filtros)],
    params: Annotated[ParamsPagina, Query()],
) -> PaginaProductosAdmin | PaginaProductosVendedor:
    return ProductoService(uow).buscar(filtros, params, con_costos=usuario.rol == Rol.admin)


@router.get("/{producto_id}", response_model=ProductoReadAdmin | ProductoReadVendedor)
def obtener(
    producto_id: int, uow: UowDep, usuario: Logueado
) -> ProductoReadAdmin | ProductoReadVendedor:
    return ProductoService(uow).obtener(producto_id, con_costos=usuario.rol == Rol.admin)


@router.post(
    "",
    response_model=ProductoReadAdmin,
    status_code=status.HTTP_201_CREATED,
    dependencies=_ADMIN,
)
def crear(datos: ProductoCreate, uow: UowDep) -> ProductoReadAdmin:
    return ProductoService(uow).crear(datos)


@router.patch("/{producto_id}", response_model=ProductoReadAdmin, dependencies=_ADMIN)
def actualizar(producto_id: int, datos: ProductoUpdate, uow: UowDep) -> ProductoReadAdmin:
    return ProductoService(uow).actualizar(producto_id, datos)


@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=_ADMIN)
def eliminar(producto_id: int, uow: UowDep) -> None:
    ProductoService(uow).eliminar(producto_id)
