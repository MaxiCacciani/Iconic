"""Lógica de negocio de clientes: búsqueda, ficha, alta, edición y borrado.

Reglas (sección 3): nombre obligatorio, DNI de 7 u 8 dígitos y único, teléfono de 8 a 15
dígitos y localidad del catálogo. Los dos roles buscan, crean y editan (el Vendedor da de
alta al cliente durante la venta); borrar es solo del Administrador.

Decisión: un cliente con ventas, reservas o reclamos no se borra (es historial y la base
no lo permitiría). Se lee de las claves foráneas, así las fases siguientes quedan
cubiertas solas.
"""

from typing import Any

from app.common.base import Pagina, ParamsPagina
from app.core.excepciones import Conflicto, ErrorDeCampo, NoEncontrado
from app.core.uow import UnidadDeTrabajo
from app.modules.catalogos.models import Localidad
from app.modules.clientes.models import Cliente
from app.modules.clientes.repository import ClienteRepository
from app.modules.clientes.schemas import ClienteCreate, ClienteRead, ClienteUpdate, Referencia


def _enumerar(partes: list[str]) -> str:
    return partes[0] if len(partes) == 1 else f"{', '.join(partes[:-1])} y {partes[-1]}"


class ClienteService:
    def __init__(self, uow: UnidadDeTrabajo) -> None:
        self.uow = uow
        self.clientes = ClienteRepository(uow.session)

    # ─── Lectura ─────────────────────────────────────────────────────────────
    def buscar(self, texto: str | None, params: ParamsPagina) -> Pagina[ClienteRead]:
        pagina = self.clientes.buscar(texto, params)
        return Pagina[ClienteRead](
            items=[self._leer(c) for c in pagina.items], **pagina.model_dump(exclude={"items"})
        )

    def obtener(self, id: int) -> ClienteRead:
        cliente = self.clientes.con_detalle(id)
        if cliente is None:
            raise NoEncontrado(f"El cliente #{id} no existe.")
        return self._leer(cliente)

    # ─── Escritura ───────────────────────────────────────────────────────────
    def crear(self, datos: ClienteCreate) -> ClienteRead:
        with self.uow:
            self._validar(datos.model_dump())
            cliente = self.clientes.crear(Cliente(**datos.model_dump()))
        return self.obtener(cliente.id)  # type: ignore[arg-type]

    def actualizar(self, id: int, datos: ClienteUpdate) -> ClienteRead:
        with self.uow:
            cliente = self.clientes.obtener_o_falla(id)
            cambios: dict[str, Any] = datos.model_dump(exclude_unset=True)
            if "nombre" in cambios and cambios["nombre"] is None:
                raise ErrorDeCampo("nombre", "Este campo es obligatorio.")
            self._validar(cambios, id_en_edicion=cliente.id)
            for campo, valor in cambios.items():
                setattr(cliente, campo, valor)
            self.clientes.actualizar(cliente)
        self.uow.session.expire_all()
        return self.obtener(id)

    def eliminar(self, id: int) -> None:
        with self.uow:
            cliente = self.clientes.obtener_o_falla(id)
            usos = self.clientes.usos(cliente)
            if usos:
                partes = [f"{tabla} ({cantidad})" for tabla, cantidad in usos]
                raise Conflicto(
                    f"No se puede borrar a {cliente.nombre}: tiene {_enumerar(partes)}. "
                    "Quedan como historial."
                )
            self.clientes.eliminar(cliente)

    # ─── Reglas ──────────────────────────────────────────────────────────────
    def _validar(self, datos: dict[str, Any], id_en_edicion: int | None = None) -> None:
        """DNI único y localidad existente. `id_en_edicion`: que el DNI sea el del mismo
        cliente que se edita no cuenta como repetido."""
        if dni := datos.get("dni"):
            otro = self.clientes.por_dni(dni)
            if otro is not None and otro.id != id_en_edicion:
                raise ErrorDeCampo(
                    "dni", f"Ya hay un cliente con ese DNI: {otro.nombre} (#{otro.id})."
                )
        localidad_id = datos.get("localidad_id")
        if localidad_id is not None and self.uow.session.get(Localidad, localidad_id) is None:
            raise ErrorDeCampo("localidad_id", "Esa localidad no existe.")

    @staticmethod
    def _leer(c: Cliente) -> ClienteRead:
        return ClienteRead(
            id=c.id,  # type: ignore[arg-type]
            nombre=c.nombre,
            dni=c.dni,
            telefono=c.telefono,
            localidad=(
                Referencia(id=c.localidad.id, nombre=c.localidad.nombre)  # type: ignore[arg-type]
                if c.localidad
                else None
            ),
            creado_en=c.creado_en,
        )
