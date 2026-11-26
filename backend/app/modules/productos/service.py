"""Lógica de negocio de productos: stock, alta, edición y borrado.

Lo arma y valida `ProductoFactory`; lo que se puede hacer según el estado lo decide el
State (`estados.py`). Las lecturas salen por rol: el Vendedor no recibe costos.
"""

from decimal import Decimal
from typing import Any

from app.common.base import Pagina, ParamsPagina
from app.common.enums import Condicion, EstadoProductoEnum
from app.core.excepciones import NoEncontrado
from app.core.uow import UnidadDeTrabajo
from app.modules.productos import dominio
from app.modules.productos.factory import ProductoFactory
from app.modules.productos.models import Producto
from app.modules.productos.repository import FiltrosProducto, ProductoRepository
from app.modules.productos.schemas import (
    DefectoDeProducto,
    ProductoCreate,
    ProductoReadAdmin,
    ProductoReadVendedor,
    ProductoUpdate,
    Referencia,
)
from app.modules.tipo_cambio.service import TipoCambioService


class ProductoService:
    def __init__(self, uow: UnidadDeTrabajo) -> None:
        self.uow = uow
        self.productos = ProductoRepository(uow.session)
        self.factory = ProductoFactory(uow)
        self.tipo_cambio = TipoCambioService(uow)

    # ─── Lectura ─────────────────────────────────────────────────────────────
    def buscar(
        self, filtros: FiltrosProducto, params: ParamsPagina, con_costos: bool
    ) -> Pagina[ProductoReadAdmin] | Pagina[ProductoReadVendedor]:
        pagina = self.productos.buscar(filtros, params)
        tc = self.tipo_cambio.valor_hoy()
        items = [self._leer(p, tc, con_costos) for p in pagina.items]
        datos = pagina.model_dump(exclude={"items"})
        if con_costos:
            return Pagina[ProductoReadAdmin](items=items, **datos)  # type: ignore[arg-type]
        return Pagina[ProductoReadVendedor](items=items, **datos)

    def obtener(self, id: int, con_costos: bool) -> ProductoReadAdmin | ProductoReadVendedor:
        return self._leer(self._detalle(id), self.tipo_cambio.valor_hoy(), con_costos)

    def stock(self) -> tuple[int, int]:
        """Unidades disponibles y cuántas de ellas son nuevas (para Resumen)."""
        disponible = EstadoProductoEnum.disponible
        return (
            self.productos.unidades(disponible),
            self.productos.unidades(disponible, Condicion.nuevo),
        )

    # ─── Escritura (solo Administrador; lo resuelve el router) ───────────────
    def crear(self, datos: ProductoCreate) -> ProductoReadAdmin:
        with self.uow:
            producto = self.productos.crear(self.factory.crear(datos.model_dump()))
        return self.obtener(producto.id, con_costos=True)  # type: ignore[arg-type, return-value]

    def actualizar(self, id: int, datos: ProductoUpdate) -> ProductoReadAdmin:
        with self.uow:
            producto = self.productos.obtener_o_falla(id)
            producto.verificar_editable()
            cambios: dict[str, Any] = datos.model_dump(exclude_unset=True)
            self.productos.actualizar(self.factory.actualizar(producto, cambios))
        self.uow.session.expire_all()
        return self.obtener(id, con_costos=True)  # type: ignore[return-value]

    def eliminar(self, id: int) -> None:
        """Lo borra de verdad (reglas 2.2). Solo mientras está disponible."""
        with self.uow:
            producto = self.productos.obtener_o_falla(id)
            producto.verificar_borrable()
            self.productos.eliminar(producto)

    # ─── Armado de las lecturas ──────────────────────────────────────────────
    def _detalle(self, id: int) -> Producto:
        producto = self.productos.con_detalle(id)
        if producto is None:
            raise NoEncontrado(f"El producto #{id} no existe.")
        return producto

    @staticmethod
    def _leer(
        p: Producto, tc: Decimal | None, con_costos: bool
    ) -> ProductoReadAdmin | ProductoReadVendedor:
        def ref(x: Any) -> Referencia | None:
            return None if x is None else Referencia(id=x.id, nombre=x.nombre)

        base: dict[str, Any] = {
            "id": p.id,
            "categoria": ref(p.modelo.categoria),
            "modelo": ref(p.modelo),
            "capacidad": ref(p.capacidad),
            "color": ref(p.color),
            "proveedor": ref(p.proveedor),
            "condicion": p.condicion,
            "estado": p.estado,
            "editable": p.estado_actual.editable,
            "imei": p.imei,
            "bateria": p.bateria,
            "bateria_nivel": dominio.nivel_bateria(p.bateria),
            "controles": p.controles,
            "extras": p.extras,
            "cantidad": p.cantidad,
            "precio_usd": p.precio_usd,
            "precio_ars": dominio.en_pesos(p.precio_usd, tc),
            "defectos": [
                DefectoDeProducto(id=d.id, descripcion=d.descripcion)  # type: ignore[arg-type]
                for d in sorted(p.defectos, key=lambda d: d.descripcion.lower())
            ],
            "creado_en": p.creado_en,
        }
        if not con_costos:
            return ProductoReadVendedor(**base)
        ganancia = dominio.ganancia(p.precio_usd, p.costo_usd)
        return ProductoReadAdmin(
            **base,
            costo_usd=p.costo_usd,
            costo_ars=dominio.en_pesos(p.costo_usd, tc),
            ganancia_usd=ganancia,
            ganancia_ars=dominio.en_pesos(ganancia, tc),
            margen_pct=dominio.margen_pct(p.precio_usd, p.costo_usd),
        )
