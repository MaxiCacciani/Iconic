"""Acceso a datos de ventas. Los repositorios heredan de `RepositorioBase[M]`."""

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import selectinload
from sqlmodel import col, func, select

from app.common.base import Pagina, ParamsPagina, RepositorioBase
from app.modules.catalogos.models import Modelo
from app.modules.productos.models import Producto
from app.modules.ventas.models import Venta, VentaItem

_PRODUCTO = (
    selectinload(Producto.modelo).selectinload(Modelo.categoria),  # type: ignore[arg-type]
    selectinload(Producto.capacidad),  # type: ignore[arg-type]
    selectinload(Producto.color),  # type: ignore[arg-type]
)
# Lo que se muestra de cada venta, en la misma tanda de consultas (sin una por fila).
_CARGAR = (
    selectinload(Venta.items).selectinload(VentaItem.producto).options(*_PRODUCTO),  # type: ignore[arg-type]
    selectinload(Venta.canje_producto).options(*_PRODUCTO),  # type: ignore[arg-type]
    selectinload(Venta.cliente),  # type: ignore[arg-type]
    selectinload(Venta.usuario),  # type: ignore[arg-type]
    selectinload(Venta.vendedor),  # type: ignore[arg-type]
    selectinload(Venta.metodo_pago),  # type: ignore[arg-type]
)


class VentaRepository(RepositorioBase[Venta]):
    modelo = Venta

    def buscar(self, params: ParamsPagina, usuario_id: int | None) -> Pagina[Venta]:
        """Las últimas primero. Con `usuario_id`, solo las que registró ese usuario."""
        consulta = select(Venta)
        if usuario_id is not None:
            consulta = consulta.where(Venta.usuario_id == usuario_id)
        total = self.session.exec(select(func.count()).select_from(consulta.subquery())).one()
        items = self.session.exec(
            consulta.options(*_CARGAR)
            .order_by(col(Venta.id).desc())
            .offset(params.offset)
            .limit(params.tamanio)
        ).all()
        return Pagina(items=list(items), total=total, pagina=params.pagina, tamanio=params.tamanio)

    def con_detalle(self, id: int) -> Venta | None:
        return self.session.exec(select(Venta).where(Venta.id == id).options(*_CARGAR)).first()

    def desde(self, instante: datetime, usuario_id: int | None = None) -> Sequence[Venta]:
        consulta = select(Venta).where(Venta.fecha >= instante)  # type: ignore[arg-type]
        if usuario_id is not None:
            consulta = consulta.where(Venta.usuario_id == usuario_id)
        return self.session.exec(consulta.options(selectinload(Venta.items))).all()

    def ganancia_total(self) -> Decimal:
        """Total − costo − comisión de cada venta, sumando solo las que tienen el costo de
        todos sus ítems. Los regalos se guardan con precio 0, así que el total es la suma
        simple."""
        importe = col(VentaItem.cantidad) * col(VentaItem.precio_usd)
        costo = col(VentaItem.cantidad) * col(VentaItem.costo_usd)
        por_venta = (
            select(
                (func.sum(importe) - func.sum(costo) - col(Venta.comision_usd)).label("ganancia")
            )
            .select_from(VentaItem)
            .join(Venta, col(Venta.id) == col(VentaItem.venta_id))
            .group_by(col(Venta.id))
            .having(func.count() == func.count(col(VentaItem.costo_usd)))
            .subquery()
        )
        total = self.session.exec(select(func.coalesce(func.sum(por_venta.c.ganancia), 0))).one()
        return Decimal(str(total)).quantize(Decimal("0.01"))
