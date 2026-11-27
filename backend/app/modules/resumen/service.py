"""Junta datos de ventas, productos, reservas, cobros y garantías. No tiene tablas propias.

Cada fase le suma sus indicadores: el aviso de TC del día (Fase 2), el stock (Fase 4) y
las ventas (Fase 7).
"""

from datetime import timedelta

from app.common.enums import Rol
from app.core import reloj
from app.core.uow import UnidadDeTrabajo
from app.modules.productos.service import ProductoService
from app.modules.resumen.schemas import (
    AvisoRead,
    ResumenRead,
    StockRead,
    TipoAviso,
    VentasDelPeriodo,
    VentasRead,
)
from app.modules.tipo_cambio.service import TipoCambioService
from app.modules.usuarios.models import Usuario
from app.modules.ventas.service import VentaService


class ResumenService:
    def __init__(self, uow: UnidadDeTrabajo) -> None:
        self.tipo_cambio = TipoCambioService(uow)
        self.productos = ProductoService(uow)
        self.ventas = VentaService(uow)

    def resumen(self, usuario: Usuario) -> ResumenRead:
        avisos: list[AvisoRead] = []
        if self.tipo_cambio.valor_hoy() is None:
            avisos.append(
                AvisoRead(
                    tipo=TipoAviso.tc_sin_cargar,
                    mensaje="Falta cargar el tipo de cambio de hoy.",
                )
            )
        disponibles, nuevas = self.productos.stock()
        hoy = reloj.hoy()
        # El Vendedor ve solo las ventas que registró él, igual que en el historial.
        solo_de = None if usuario.rol == Rol.admin else usuario.id

        def ventas_desde(dia) -> VentasDelPeriodo:
            cantidad, usd, ars = self.ventas.desde_el_dia(dia, solo_de)
            return VentasDelPeriodo(cantidad=cantidad, total_usd=usd, total_ars=ars)

        return ResumenRead(
            fecha=hoy,
            avisos=avisos,
            stock=StockRead(disponibles=disponibles, nuevas=nuevas),
            ventas=VentasRead(
                hoy=ventas_desde(hoy),
                ultimos_7_dias=ventas_desde(hoy - timedelta(days=6)),
                solo_propias=solo_de is not None,
            ),
        )
