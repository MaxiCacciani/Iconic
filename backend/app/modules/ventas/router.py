"""Capa de presentación: endpoints HTTP de ventas.

Los dos roles cotizan y registran ventas. El rol decide el DTO: el Vendedor no recibe
costos, ganancia, margen ni "bajo costo", y en el historial ve solo sus ventas. Borrar
una venta es solo del Administrador.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.common.base import ParamsPagina
from app.common.enums import Rol
from app.core.deps import Logueado, UowDep, solo_admin, usuario_actual
from app.modules.ventas.schemas import (
    CotizacionAdmin,
    CotizacionCreate,
    CotizacionVendedor,
    PaginaVentasAdmin,
    PaginaVentasVendedor,
    VentaCreate,
    VentaReadAdmin,
    VentaReadVendedor,
)
from app.modules.ventas.service import VentaService

router = APIRouter(
    prefix="/ventas",
    tags=["Ventas"],
    dependencies=[Depends(usuario_actual)],
)


# El Administrador primero en cada unión, como en productos: la respuesta se valida contra
# el DTO con costos solo si el service lo armó con costos.
@router.post("/cotizar", response_model=CotizacionAdmin | CotizacionVendedor)
def cotizar(
    datos: CotizacionCreate, uow: UowDep, usuario: Logueado
) -> CotizacionAdmin | CotizacionVendedor:
    """Total, canje y saldo del carrito, en cada cambio del wizard. No graba nada."""
    return VentaService(uow).cotizar(datos, con_costos=usuario.rol == Rol.admin)


@router.get("", response_model=PaginaVentasAdmin | PaginaVentasVendedor)
def listar(
    uow: UowDep, usuario: Logueado, params: Annotated[ParamsPagina, Query()]
) -> PaginaVentasAdmin | PaginaVentasVendedor:
    es_admin = usuario.rol == Rol.admin
    return VentaService(uow).buscar(
        params, usuario_id=None if es_admin else usuario.id, con_costos=es_admin
    )


@router.post(
    "",
    response_model=VentaReadAdmin | VentaReadVendedor,
    status_code=status.HTTP_201_CREATED,
)
def crear(datos: VentaCreate, uow: UowDep, usuario: Logueado) -> VentaReadAdmin | VentaReadVendedor:
    """Sin TC del día, 422. Con un dato inválido, 422 en ese campo y no se graba nada."""
    return VentaService(uow).crear(datos, usuario, con_costos=usuario.rol == Rol.admin)


@router.delete(
    "/{venta_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(solo_admin)],
    responses={409: {"description": "Devolver el stock lo dejaría inconsistente."}},
)
def eliminar(venta_id: int, uow: UowDep) -> None:
    """Borra la venta y devuelve el stock. No se puede deshacer."""
    VentaService(uow).eliminar(venta_id)
