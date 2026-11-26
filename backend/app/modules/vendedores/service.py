"""Lógica de negocio de vendedores: lista, búsqueda por número, alta, edición y borrado.

Reglas 4.6: el vendedor de una venta es opcional; se carga su número y el nombre sale de
esta lista. Si el número no está, se avisa "Vendedor no registrado".

Decisiones:
- El número no se repite (la base tiene `UNIQUE`); el 422 nombra a quién lo tiene.
- Un vendedor con ventas no se borra: es historial. Se lee de las claves foráneas, así la
  Fase 7 queda cubierta sola.
"""

from collections.abc import Sequence
from typing import Any

from app.core.excepciones import Conflicto, ErrorDeCampo, NoEncontrado
from app.core.uow import UnidadDeTrabajo
from app.modules.vendedores.models import Vendedor
from app.modules.vendedores.repository import VendedorRepository
from app.modules.vendedores.schemas import VendedorCreate, VendedorUpdate

NO_REGISTRADO = "Vendedor no registrado."


class VendedorService:
    def __init__(self, uow: UnidadDeTrabajo) -> None:
        self.uow = uow
        self.vendedores = VendedorRepository(uow.session)

    # ─── Lectura ─────────────────────────────────────────────────────────────
    def listar(self) -> Sequence[Vendedor]:
        return self.vendedores.todos()

    def por_numero(self, numero: int) -> Vendedor:
        vendedor = self.vendedores.por_numero(numero)
        if vendedor is None:
            raise NoEncontrado(NO_REGISTRADO)
        return vendedor

    # ─── Escritura (solo Administrador; lo resuelve el router) ───────────────
    def crear(self, datos: VendedorCreate) -> Vendedor:
        with self.uow:
            self._numero_libre(datos.numero)
            vendedor = self.vendedores.crear(Vendedor(**datos.model_dump()))
        return vendedor

    def actualizar(self, id: int, datos: VendedorUpdate) -> Vendedor:
        with self.uow:
            vendedor = self._obtener(id)
            cambios: dict[str, Any] = datos.model_dump(exclude_unset=True)
            for campo in ("numero", "nombre"):
                if campo in cambios and cambios[campo] is None:
                    raise ErrorDeCampo(campo, "Este campo es obligatorio.")
            if "numero" in cambios:
                self._numero_libre(cambios["numero"], id_en_edicion=id)
            for campo, valor in cambios.items():
                setattr(vendedor, campo, valor)
            self.vendedores.actualizar(vendedor)
        self.uow.session.refresh(vendedor)
        return vendedor

    def eliminar(self, id: int) -> None:
        with self.uow:
            vendedor = self._obtener(id)
            usos = self.vendedores.usos(vendedor)
            if usos:
                ventas = sum(cantidad for _, cantidad in usos)
                raise Conflicto(
                    f"No se puede borrar a {vendedor.nombre}: tiene "
                    f"{'1 venta' if ventas == 1 else f'{ventas} ventas'}. Quedan como historial."
                )
            self.vendedores.eliminar(vendedor)

    # ─── Reglas ──────────────────────────────────────────────────────────────
    def _obtener(self, id: int) -> Vendedor:
        vendedor = self.vendedores.obtener(id)
        if vendedor is None:
            raise NoEncontrado(f"El vendedor #{id} no existe.")
        return vendedor

    def _numero_libre(self, numero: int, id_en_edicion: int | None = None) -> None:
        otro = self.vendedores.por_numero(numero)
        if otro is not None and otro.id != id_en_edicion:
            raise ErrorDeCampo("numero", f"El número {numero} ya es de {otro.nombre}.")
