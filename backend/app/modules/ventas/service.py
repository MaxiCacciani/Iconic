"""Lógica de negocio de ventas: cotizar, registrar, historial y borrar.

Reglas 4.2 a 4.9. Registrar y borrar son atómicos (`UnidadDeTrabajo`): si falla un paso,
no queda nada grabado. Los cálculos están en `dominio.py` y lo propio de cada modalidad,
en `modalidades.py`.

Decisiones:
- Sin TC del día no se registra la venta (se cotiza igual, sin pesos).
- Solo se vende lo disponible: un producto reservado se vende convirtiendo su reserva.
- El Vendedor ve solo las ventas que registró él; borrar es del Administrador.
- La comisión es solo del Administrador y se resta de la ganancia. La que mande un
  Vendedor se ignora (queda en 0), sin error: no tiene que enterarse de que existe.
- Al borrar una venta, el equipo que entró por su canje sale del stock con ella. Si ya
  se vendió o se reservó, o si un equipo vendido volvió a entrar con el mismo IMEI, la
  venta no se borra (409): devolverlo dejaría el stock inconsistente.
"""

from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any

from sqlmodel import col, select

from app.common.base import Pagina, ParamsPagina
from app.common.enums import EstadoCobroEnum, EstadoProductoEnum
from app.core import reloj
from app.core.excepciones import Conflicto, ErrorDeCampo, NoEncontrado, ReglaInvalida
from app.core.uow import UnidadDeTrabajo
from app.modules.catalogos.models import MetodoPago
from app.modules.clientes.models import Cliente
from app.modules.cobros.models import Cobro
from app.modules.cobros.service import cuota
from app.modules.packs.repository import PackRepository
from app.modules.productos.dominio import en_pesos, ganancia, margen_pct
from app.modules.productos.factory import ProductoFactory
from app.modules.productos.models import Producto
from app.modules.productos.repository import ProductoRepository
from app.modules.productos.schemas import Referencia
from app.modules.tipo_cambio.service import TipoCambioService
from app.modules.usuarios.models import Usuario
from app.modules.vendedores.models import Vendedor
from app.modules.vendedores.repository import VendedorRepository
from app.modules.vendedores.schemas import VendedorRead
from app.modules.ventas import dominio
from app.modules.ventas.comprobante import comprobante_pdf
from app.modules.ventas.modalidades import Pago, Plan, modalidad_de
from app.modules.ventas.models import Venta, VentaItem
from app.modules.ventas.repository import VentaRepository
from app.modules.ventas.schemas import (
    CanjeRead,
    CotizacionAdmin,
    CotizacionCreate,
    CotizacionVendedor,
    CuotaCotizada,
    ItemVentaAdmin,
    ItemVentaVendedor,
    PaginaVentasAdmin,
    PaginaVentasVendedor,
    ProductoVendido,
    VentaCreate,
    VentaReadAdmin,
    VentaReadVendedor,
)

_DISPONIBLE = EstadoProductoEnum.disponible


def _ref(x: Any) -> Referencia | None:
    return None if x is None else Referencia(id=x.id, nombre=x.nombre)


class VentaService:
    def __init__(self, uow: UnidadDeTrabajo) -> None:
        self.uow = uow
        self.ventas = VentaRepository(uow.session)
        self.productos = ProductoRepository(uow.session)
        self.tipo_cambio = TipoCambioService(uow)

    # ─── Cotizar ─────────────────────────────────────────────────────────────
    def cotizar(
        self, datos: CotizacionCreate, con_costos: bool
    ) -> CotizacionAdmin | CotizacionVendedor:
        """Lo que el wizard muestra en cada cambio. No graba nada."""
        lineas = self._lineas(datos)
        total = dominio.total(lineas)  # type: ignore[arg-type]
        canje = datos.canje_valor_usd or Decimal(0)
        plan = self._planear(datos, total)
        saldo = total - canje - plan.anticipo
        tc = self.tipo_cambio.valor_hoy()
        base: dict[str, Any] = {
            "total_usd": total,
            "total_ars": en_pesos(total, tc),
            "canje_usd": canje,
            "anticipo_usd": plan.anticipo,
            "saldo_usd": saldo,
            "saldo_ars": en_pesos(saldo, tc),
            "cuotas": [
                CuotaCotizada(
                    numero=c.numero, vencimiento=c.vencimiento, monto_usd=c.monto, cobrada=c.cobrada
                )
                for c in plan.cuotas
            ],
        }
        if not con_costos:
            return CotizacionVendedor(**base)
        costo = dominio.costo(lineas)  # type: ignore[arg-type]
        neto = total - datos.comision_usd
        return CotizacionAdmin(
            **base,
            costo_usd=costo,
            ganancia_usd=ganancia(neto, costo),
            margen_pct=margen_pct(neto, costo),
            bajo_costo=[n for n, x in enumerate(lineas) if dominio.bajo_costo(x)],  # type: ignore[arg-type]
        )

    # ─── Registrar ───────────────────────────────────────────────────────────
    def crear(
        self, datos: VentaCreate, actor: Usuario, con_costos: bool
    ) -> VentaReadAdmin | VentaReadVendedor:
        """Reglas 4.7: la venta con el TC congelado y el detalle de cada ítem, sus cuotas,
        el stock vendido y el equipo del canje al stock. Todo junto o nada."""
        with self.uow:
            tc = self.tipo_cambio.valor_hoy()
            if tc is None:
                raise ReglaInvalida(
                    "Falta cargar el tipo de cambio de hoy: sin TC no se registra la venta."
                )
            lineas = self._lineas(datos)
            plan = self._planear(datos, dominio.total(lineas))  # type: ignore[arg-type]
            if self.uow.session.get(Cliente, datos.cliente_id) is None:
                raise ErrorDeCampo("cliente_id", "Ese cliente no existe.")
            metodo = self._metodo_pago(datos.metodo_pago_id)
            vendedor = self._vendedor(datos.vendedor_numero)
            canje = self._canje(datos)

            for linea in lineas:
                linea.producto.vender(linea.cantidad)
            venta = self.ventas.crear(
                Venta(
                    cliente_id=datos.cliente_id,
                    usuario_id=actor.id,  # type: ignore[arg-type]
                    vendedor_id=vendedor.id if vendedor else None,
                    canje_producto_id=canje.id if canje else None,
                    canje_valor_usd=datos.canje_valor_usd,
                    metodo_pago_id=metodo.id,  # type: ignore[arg-type]
                    modalidad=datos.modalidad,
                    cantidad_cuotas=plan.cantidad_cuotas,
                    anticipo_usd=plan.anticipo,
                    tc_ars=tc,
                    garantia_meses=datos.garantia_meses,
                    comision_usd=datos.comision_usd if con_costos else Decimal(0),
                    items=lineas,
                    cobros=[
                        Cobro(
                            numero_cuota=c.numero,
                            fecha_vencimiento=c.vencimiento,
                            monto_usd=c.monto,
                            estado=EstadoCobroEnum.cobrada
                            if c.cobrada
                            else EstadoCobroEnum.pendiente,
                        )
                        for c in plan.cuotas
                    ],
                )
            )
        return self.obtener(venta.id, con_costos)  # type: ignore[arg-type]

    @staticmethod
    def _planear(datos: CotizacionCreate, total: Decimal) -> Plan:
        """Valida los montos según la modalidad y arma las cuotas desde hoy."""
        pago = Pago(
            anticipo=datos.anticipo_usd,
            cantidad_cuotas=datos.cantidad_cuotas,
            primera_cuota_hoy=datos.primera_cuota_hoy,
        )
        return modalidad_de(datos.modalidad).planear(
            total, datos.canje_valor_usd or Decimal(0), pago, reloj.hoy()
        )

    def _lineas(self, datos: CotizacionCreate) -> list[VentaItem]:
        """Los ítems, validados contra el stock: cada producto existe y está disponible, y
        no se venden más unidades de las que tiene la fila (sumando el renglón con precio y
        el de regalo). Un equipo es una sola unidad. El costo es el del producto hoy."""
        productos = {p.id: p for p in self.productos.por_ids({i.producto_id for i in datos.items})}
        pedidas: dict[int, int] = defaultdict(int)
        lineas: list[VentaItem] = []
        for n, item in enumerate(datos.items):
            producto = productos.get(item.producto_id)
            if producto is None:
                raise ErrorDeCampo(
                    f"items.{n}.producto_id", f"El producto #{item.producto_id} no existe."
                )
            if producto.estado != _DISPONIBLE:
                raise ErrorDeCampo(
                    f"items.{n}.producto_id",
                    f"El producto #{producto.id} está {producto.estado_actual.adjetivo}.",
                )
            pedidas[producto.id] += item.cantidad  # type: ignore[index]
            if pedidas[producto.id] > producto.cantidad:  # type: ignore[index]
                hay = (
                    "una sola unidad" if producto.cantidad == 1 else f"{producto.cantidad} unidades"
                )
                raise ErrorDeCampo(f"items.{n}.cantidad", f"Del producto #{producto.id} hay {hay}.")
            lineas.append(
                VentaItem(
                    producto=producto,
                    producto_id=producto.id,  # type: ignore[arg-type]
                    cantidad=item.cantidad,
                    precio_usd=Decimal(0) if item.es_regalo else item.precio_usd,
                    costo_usd=producto.costo_usd,
                    es_regalo=item.es_regalo,
                )
            )
        return lineas

    def _metodo_pago(self, id: int | None) -> MetodoPago:
        """Sin elegir, el predeterminado del catálogo (reglas 4.4: transferencia)."""
        session = self.uow.session
        if id is None:
            metodo = session.exec(select(MetodoPago).where(col(MetodoPago.predeterminado))).first()
        else:
            metodo = session.get(MetodoPago, id)
        if metodo is None:
            raise ErrorDeCampo("metodo_pago_id", "Elegí un método de pago.")
        return metodo

    def _vendedor(self, numero: int | None) -> Vendedor | None:
        """Reglas 4.6: opcional; se carga el número y el nombre sale de la lista."""
        if numero is None:
            return None
        vendedor = VendedorRepository(self.uow.session).por_numero(numero)
        if vendedor is None:
            raise ErrorDeCampo("vendedor_numero", "Vendedor no registrado.")
        return vendedor

    def _canje(self, datos: VentaCreate) -> Producto | None:
        """El equipo entregado entra al stock (reglas 4.5). Los errores de sus datos van
        marcados en `canje.<campo>`."""
        if datos.canje is None and datos.canje_valor_usd is None:
            return None
        if datos.canje_valor_usd is None:
            raise ErrorDeCampo("canje_valor_usd", "Cargá el valor del canje.")
        if datos.canje is None:
            raise ErrorDeCampo("canje", "Faltan los datos del equipo que entrega el cliente.")
        try:
            producto = ProductoFactory(self.uow).desde_canje(
                datos.canje.model_dump(), datos.canje_valor_usd
            )
        except ErrorDeCampo as e:
            raise ErrorDeCampo(f"canje.{e.campo}", e.mensaje) from None
        return self.productos.crear(producto)

    # ─── Lectura ─────────────────────────────────────────────────────────────
    def buscar(
        self, params: ParamsPagina, usuario_id: int | None, con_costos: bool
    ) -> PaginaVentasAdmin | PaginaVentasVendedor:
        """Con `usuario_id`, solo las ventas de ese usuario (el Vendedor ve las suyas)."""
        pagina = self.ventas.buscar(params, usuario_id)
        items = [self._leer(v, con_costos) for v in pagina.items]
        datos = pagina.model_dump(exclude={"items"})
        if con_costos:
            return PaginaVentasAdmin(
                items=items,  # type: ignore[arg-type]
                ganancia_total_usd=self.ventas.ganancia_total(),
                **datos,
            )
        return Pagina[VentaReadVendedor](items=items, **datos)

    def obtener(self, id: int, con_costos: bool) -> VentaReadAdmin | VentaReadVendedor:
        return self._leer(self._detalle(id), con_costos)

    def desde_el_dia(
        self, dia: date, usuario_id: int | None = None
    ) -> tuple[int, Decimal, Decimal]:
        """Las ventas desde ese día (en Argentina) hasta ahora: cantidad, total en USD y en
        pesos, cada una con su TC congelado. Con `usuario_id`, solo las que registró ese
        usuario (como en el historial). Para Resumen."""
        ventas = self.ventas.desde(reloj.inicio_del_dia(dia), usuario_id)
        totales = [(dominio.total(v.items), v.tc_ars) for v in ventas]  # type: ignore[arg-type]
        return (
            len(ventas),
            sum((t for t, _ in totales), Decimal(0)),
            sum((en_pesos(t, tc) for t, tc in totales), Decimal(0)),  # type: ignore[misc]
        )

    def comprobante(self, id: int, usuario_id: int | None) -> bytes:
        """Con `usuario_id`, solo si la registró ese usuario: otra venta es un 404."""
        venta = self._detalle(id)
        if usuario_id is not None and venta.usuario_id != usuario_id:
            raise NoEncontrado(f"La venta #{id} no existe.")
        return comprobante_pdf(self._leer(venta, con_costos=False))  # type: ignore[arg-type]

    def cambiar_comision(self, id: int, comision: Decimal) -> VentaReadAdmin:
        with self.uow:
            venta = self._detalle(id)
            venta.comision_usd = comision
        return self.obtener(id, con_costos=True)  # type: ignore[return-value]

    # ─── Borrar ──────────────────────────────────────────────────────────────
    def eliminar(self, id: int) -> None:
        """Reglas 4.9: borra la venta y sus cuotas, cobradas o no, y devuelve el stock."""
        with self.uow:
            venta = self._detalle(id)
            for item in venta.items:
                producto = item.producto
                if producto.imei and producto.estado == EstadoProductoEnum.vendido:
                    otro = self.productos.otro_con_imei(producto)
                    if otro is not None:
                        raise Conflicto(
                            f"No se puede borrar la venta: el {producto.modelo.nombre} "
                            f"#{producto.id} volvió a entrar con el mismo IMEI "
                            f"(producto #{otro.id})."
                        )
                producto.devolver(item.cantidad)

            canje = venta.canje_producto
            if canje is not None and canje.estado != _DISPONIBLE:
                raise Conflicto(
                    f"No se puede borrar la venta: el equipo que entró por canje "
                    f"(producto #{canje.id}) ya está {canje.estado_actual.adjetivo}."
                )
            self.ventas.eliminar(venta)
            if canje is not None:
                PackRepository(self.uow.session).borrar_items_de_producto(canje.id)  # type: ignore[arg-type]
                self.productos.eliminar(canje)

    # ─── Armado de las lecturas ──────────────────────────────────────────────
    def _detalle(self, id: int) -> Venta:
        venta = self.ventas.con_detalle(id)
        if venta is None:
            raise NoEncontrado(f"La venta #{id} no existe.")
        return venta

    @staticmethod
    def _producto(p: Producto) -> ProductoVendido:
        return ProductoVendido(
            id=p.id,  # type: ignore[arg-type]
            categoria=_ref(p.modelo.categoria),  # type: ignore[arg-type]
            modelo=_ref(p.modelo),  # type: ignore[arg-type]
            capacidad=_ref(p.capacidad),
            color=_ref(p.color),
            imei=p.imei,
        )

    def _leer(self, v: Venta, con_costos: bool) -> VentaReadAdmin | VentaReadVendedor:
        total = dominio.total(v.items)  # type: ignore[arg-type]
        saldo = total - (v.canje_valor_usd or Decimal(0)) - v.anticipo_usd
        hoy = reloj.hoy()
        base: dict[str, Any] = {
            "id": v.id,
            "fecha": v.fecha,
            "cliente": _ref(v.cliente),
            "usuario": _ref(v.usuario),
            "vendedor": VendedorRead.model_validate(v.vendedor) if v.vendedor else None,
            "metodo_pago": _ref(v.metodo_pago),
            "modalidad": v.modalidad,
            "cantidad_cuotas": v.cantidad_cuotas,
            "tc_ars": v.tc_ars,
            "garantia_meses": v.garantia_meses,
            "canje": None
            if v.canje_valor_usd is None
            else CanjeRead(
                valor_usd=v.canje_valor_usd,
                producto=self._producto(v.canje_producto) if v.canje_producto else None,
            ),
            "total_usd": total,
            "total_ars": en_pesos(total, v.tc_ars),
            "anticipo_usd": v.anticipo_usd,
            "saldo_usd": saldo,
            "saldo_ars": en_pesos(saldo, v.tc_ars),
            "cuotas": [cuota(c, hoy) for c in v.cobros],
        }

        def item(i: VentaItem) -> ItemVentaAdmin | ItemVentaVendedor:
            datos: dict[str, Any] = {
                "producto": self._producto(i.producto),
                "cantidad": i.cantidad,
                "precio_usd": i.precio_usd,
                "es_regalo": i.es_regalo,
            }
            if not con_costos:
                return ItemVentaVendedor(**datos)
            return ItemVentaAdmin(**datos, costo_usd=i.costo_usd, bajo_costo=dominio.bajo_costo(i))  # type: ignore[arg-type]

        items = [item(i) for i in v.items]
        if not con_costos:
            return VentaReadVendedor(**base, items=items)
        costo = dominio.costo(v.items)  # type: ignore[arg-type]
        neto = total - v.comision_usd
        return VentaReadAdmin(
            **base,
            items=items,
            comision_usd=v.comision_usd,
            costo_usd=costo,
            ganancia_usd=ganancia(neto, costo),
            margen_pct=margen_pct(neto, costo),
        )
