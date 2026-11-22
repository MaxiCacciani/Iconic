"""Junta datos de ventas, productos, reservas, cobros y garantías. No tiene tablas propias.

Cada fase le suma sus indicadores: el aviso de TC del día (Fase 2) y el stock (Fase 4).
"""

from app.core import reloj
from app.core.uow import UnidadDeTrabajo
from app.modules.productos.service import ProductoService
from app.modules.resumen.schemas import AvisoRead, ResumenRead, StockRead, TipoAviso
from app.modules.tipo_cambio.service import TipoCambioService


class ResumenService:
    def __init__(self, uow: UnidadDeTrabajo) -> None:
        self.tipo_cambio = TipoCambioService(uow)
        self.productos = ProductoService(uow)

    def resumen(self) -> ResumenRead:
        avisos: list[AvisoRead] = []
        if self.tipo_cambio.valor_hoy() is None:
            avisos.append(
                AvisoRead(
                    tipo=TipoAviso.tc_sin_cargar,
                    mensaje="Falta cargar el tipo de cambio de hoy.",
                )
            )
        disponibles, nuevas = self.productos.stock()
        return ResumenRead(
            fecha=reloj.hoy(),
            avisos=avisos,
            stock=StockRead(disponibles=disponibles, nuevas=nuevas),
        )
