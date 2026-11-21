"""Junta datos de ventas, productos, reservas, cobros y garantías. No tiene tablas propias.

Cada fase le suma sus indicadores. Por ahora solo avisa si falta el TC del día.
"""

from app.core import reloj
from app.core.uow import UnidadDeTrabajo
from app.modules.resumen.schemas import AvisoRead, ResumenRead, TipoAviso
from app.modules.tipo_cambio.service import TipoCambioService


class ResumenService:
    def __init__(self, uow: UnidadDeTrabajo) -> None:
        self.tipo_cambio = TipoCambioService(uow)

    def resumen(self) -> ResumenRead:
        avisos: list[AvisoRead] = []
        if self.tipo_cambio.valor_hoy() is None:
            avisos.append(
                AvisoRead(
                    tipo=TipoAviso.tc_sin_cargar,
                    mensaje="Falta cargar el tipo de cambio de hoy.",
                )
            )
        return ResumenRead(fecha=reloj.hoy(), avisos=avisos)
