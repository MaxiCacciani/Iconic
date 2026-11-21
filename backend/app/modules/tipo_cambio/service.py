"""Lógica de negocio de tipo de cambio.

Reglas: uno por fecha, sin valor por defecto (cada día arranca vacío y no se arrastra el
del día anterior) y solo lo carga el Administrador (lo resuelve el router con `SoloAdmin`).
"""

from decimal import Decimal

from app.core import reloj
from app.core.uow import UnidadDeTrabajo
from app.modules.tipo_cambio.models import TipoCambio
from app.modules.tipo_cambio.repository import TipoCambioRepository
from app.modules.tipo_cambio.schemas import TipoCambioHoyRead
from app.modules.usuarios.models import Usuario


class TipoCambioService:
    def __init__(self, uow: UnidadDeTrabajo) -> None:
        self.uow = uow
        self.tipos_cambio = TipoCambioRepository(uow.session)

    def valor_hoy(self) -> Decimal | None:
        """El TC vigente para las equivalencias en pesos. `None` si hoy no se cargó."""
        tc = self.tipos_cambio.por_fecha(reloj.hoy())
        return tc.valor_ars if tc else None

    def hoy(self) -> TipoCambioHoyRead:
        fecha = reloj.hoy()
        tc = self.tipos_cambio.por_fecha(fecha)
        if tc is None:
            return TipoCambioHoyRead(fecha=fecha, valor_ars=None, cargado_por=None)
        usuario = self.uow.session.get(Usuario, tc.usuario_id)
        return TipoCambioHoyRead(
            fecha=fecha, valor_ars=tc.valor_ars, cargado_por=usuario.nombre if usuario else None
        )

    def cargar_hoy(self, valor_ars: Decimal, actor: Usuario) -> TipoCambioHoyRead:
        """Carga el TC de hoy o lo corrige si ya estaba. Las ventas ya hechas no cambian:
        cada una congela el TC al registrarse."""
        with self.uow:
            tc = self.tipos_cambio.por_fecha(reloj.hoy())
            if tc is None:
                self.tipos_cambio.crear(
                    TipoCambio(fecha=reloj.hoy(), valor_ars=valor_ars, usuario_id=actor.id)
                )
            else:
                tc.valor_ars = valor_ars
                tc.usuario_id = actor.id
                self.tipos_cambio.actualizar(tc)
        return self.hoy()
