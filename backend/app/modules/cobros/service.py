"""Lógica de negocio de cobros: la agenda del mes, cobrar una cuota y el plan de cuotas
del cliente (reglas 3 y 7).

Los cobros los genera la venta en cuotas (`ventas.modalidades.EnCuotas`) y se borran con
ella. Marcar una cuota como cobrada solo cambia su estado: no se guarda la fecha real de
pago ni hay pagos parciales.
"""

from collections.abc import Iterable, Sequence
from datetime import date
from decimal import Decimal
from itertools import groupby

from app.common.enums import EstadoCobroEnum
from app.core import reloj
from app.core.excepciones import NoEncontrado
from app.core.uow import UnidadDeTrabajo
from app.modules.cobros.estados import EstadoCuota
from app.modules.cobros.models import Cobro
from app.modules.cobros.repository import CobroRepository
from app.modules.cobros.schemas import (
    AgendaRead,
    CobroAgendaRead,
    CuotaRead,
    CuotasClienteRead,
    PlanCuotasRead,
    TotalesCobros,
)
from app.modules.productos.dominio import en_pesos
from app.modules.productos.schemas import Referencia
from app.modules.tipo_cambio.service import TipoCambioService


def _mes(anio: int, mes: int) -> tuple[date, date]:
    """Del primer día del mes al primero del siguiente."""
    siguiente = date(anio + 1, 1, 1) if mes == 12 else date(anio, mes + 1, 1)
    return date(anio, mes, 1), siguiente


def _sin_cobrar(cobros: Iterable[Cobro]) -> Decimal:
    return sum((c.monto_usd for c in cobros if c.estado != EstadoCobroEnum.cobrada), Decimal(0))


def cuota(c: Cobro, hoy: date) -> CuotaRead:
    return CuotaRead(
        id=c.id,  # type: ignore[arg-type]
        numero=c.numero_cuota,
        vencimiento=c.fecha_vencimiento,
        monto_usd=c.monto_usd,
        estado=c.estado_al(hoy).valor,
    )


class CobroService:
    def __init__(self, uow: UnidadDeTrabajo) -> None:
        self.uow = uow
        self.cobros = CobroRepository(uow.session)
        self.tipo_cambio = TipoCambioService(uow)

    def agenda(self, anio: int | None, mes: int | None) -> AgendaRead:
        """Sin mes, el actual (en Argentina)."""
        hoy = reloj.hoy()
        anio, mes = anio or hoy.year, mes or hoy.month
        cobros = self.cobros.entre(*_mes(anio, mes))
        tc = self.tipo_cambio.valor_hoy()
        return AgendaRead(
            anio=anio,
            mes=mes,
            cobros=[self._de_agenda(c, hoy, tc) for c in cobros],
            **self._totales(cobros).model_dump(),
        )

    def del_mes(self, dia: date) -> TotalesCobros:
        """Las cuotas que vencen en el mes de `dia`. Para Resumen."""
        return self._totales(self.cobros.entre(*_mes(dia.year, dia.month)))

    def vencidas(self) -> int:
        """Cuántas cuotas vencieron sin cobrar. Para Resumen."""
        return self.cobros.vencidas(reloj.hoy())

    def cobrar(self, id: int) -> CobroAgendaRead:
        """Una cuota cobrada no se vuelve a cobrar (409)."""
        with self.uow:
            cobro = self.cobros.con_cliente(id)
            if cobro is None:
                raise NoEncontrado(f"La cuota #{id} no existe.")
            cobro.cobrar()
        return self._de_agenda(cobro, reloj.hoy(), self.tipo_cambio.valor_hoy())

    def de_cliente(self, cliente_id: int) -> CuotasClienteRead:
        hoy = reloj.hoy()
        planes = [
            self._plan(list(cobros), hoy)
            for _, cobros in groupby(self.cobros.de_cliente(cliente_id), key=lambda c: c.venta_id)
        ]
        saldo = sum((p.saldo_usd for p in planes), Decimal(0))
        return CuotasClienteRead(
            saldo_usd=saldo,
            saldo_ars=en_pesos(saldo, self.tipo_cambio.valor_hoy()),
            en_mora=any(p.en_mora_desde for p in planes),
            planes=planes,
        )

    @staticmethod
    def _plan(cobros: list[Cobro], hoy: date) -> PlanCuotasRead:
        cuotas = [cuota(c, hoy) for c in cobros]
        sin_cobrar = [c for c in cuotas if c.estado != EstadoCuota.cobrada]
        vencidas = [c for c in cuotas if c.estado == EstadoCuota.vencida]
        venta = cobros[0].venta
        return PlanCuotasRead(
            venta_id=venta.id,  # type: ignore[arg-type]
            fecha=venta.fecha,
            cantidad_cuotas=len(cuotas),
            pagadas=len(cuotas) - len(sin_cobrar),
            saldo_usd=sum((c.monto_usd for c in sin_cobrar), Decimal(0)),
            proxima=sin_cobrar[0] if sin_cobrar else None,
            en_mora_desde=vencidas[0].vencimiento if vencidas else None,
            cuotas=cuotas,
        )

    @staticmethod
    def _totales(cobros: Sequence[Cobro]) -> TotalesCobros:
        total = sum((c.monto_usd for c in cobros), Decimal(0))
        pendiente = _sin_cobrar(cobros)
        return TotalesCobros(
            total_usd=total, cobrado_usd=total - pendiente, pendiente_usd=pendiente
        )

    @staticmethod
    def _de_agenda(c: Cobro, hoy: date, tc: Decimal | None) -> CobroAgendaRead:
        venta = c.venta
        return CobroAgendaRead(
            **cuota(c, hoy).model_dump(),
            venta_id=venta.id,  # type: ignore[arg-type]
            cantidad_cuotas=venta.cantidad_cuotas,  # type: ignore[arg-type]
            cliente=Referencia(id=venta.cliente.id, nombre=venta.cliente.nombre),  # type: ignore[arg-type]
            monto_ars=en_pesos(c.monto_usd, tc),
        )
