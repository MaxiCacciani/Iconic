"""State de `Producto`: cada estado es una clase que decide qué acciones permite.

    disponible ──reservar──▶ reservado
    reservado  ──liberar───▶ disponible
    disponible ──vender────▶ vendido
    reservado  ──vender────▶ vendido
    vendido    ──devolver──▶ disponible

- `reservar`: entra en una reserva (Fase 9).
- `liberar`: la reserva se cancela o se borra y vuelve a estar a la venta.
- `vender`: se vende, directo o desde la reserva (Fase 7).
- `devolver`: se borra la venta y vuelve al stock (Fase 7).
- Editar y borrar solo se puede mientras está disponible: uno reservado tiene una seña
  calculada sobre su precio y uno vendido es parte del historial de una venta.

En la base se guarda el ENUM (`EstadoProductoEnum`); `estado_de` lo mapea a su clase.
Ver la página 4 de `DER-Iconic.pdf`.
"""

from typing import ClassVar

from app.common.enums import EstadoProductoEnum
from app.core.excepciones import TransicionInvalida


class EstadoProducto:
    valor: ClassVar[EstadoProductoEnum]
    # Cómo se nombra el estado en un mensaje: "un producto reservado".
    adjetivo: ClassVar[str]
    no_editable: ClassVar[str] = ""
    editable: ClassVar[bool] = False

    def _no_se_puede(self, accion: str) -> TransicionInvalida:
        return TransicionInvalida(f"No se puede {accion} un producto {self.adjetivo}.")

    def reservar(self) -> EstadoProductoEnum:
        raise self._no_se_puede("reservar")

    def liberar(self) -> EstadoProductoEnum:
        raise self._no_se_puede("liberar")

    def vender(self) -> EstadoProductoEnum:
        raise self._no_se_puede("vender")

    def devolver(self) -> EstadoProductoEnum:
        raise self._no_se_puede("devolver al stock")

    def editar(self) -> None:
        raise TransicionInvalida(f"No se puede editar: {self.no_editable}")

    def eliminar(self) -> None:
        raise TransicionInvalida(f"No se puede borrar: {self.no_editable}")


class Disponible(EstadoProducto):
    valor = EstadoProductoEnum.disponible
    adjetivo = "disponible"
    editable = True

    def reservar(self) -> EstadoProductoEnum:
        return EstadoProductoEnum.reservado

    def vender(self) -> EstadoProductoEnum:
        return EstadoProductoEnum.vendido

    def editar(self) -> None:
        return None

    def eliminar(self) -> None:
        return None


class Reservado(EstadoProducto):
    valor = EstadoProductoEnum.reservado
    adjetivo = "reservado"
    no_editable = "está reservado. Cancelá la reserva antes."

    def liberar(self) -> EstadoProductoEnum:
        return EstadoProductoEnum.disponible

    def vender(self) -> EstadoProductoEnum:
        return EstadoProductoEnum.vendido


class Vendido(EstadoProducto):
    valor = EstadoProductoEnum.vendido
    adjetivo = "vendido"
    no_editable = "ya se vendió y es parte del historial de la venta."

    def devolver(self) -> EstadoProductoEnum:
        return EstadoProductoEnum.disponible


_ESTADOS: dict[EstadoProductoEnum, EstadoProducto] = {
    e.valor: e() for e in (Disponible, Reservado, Vendido)
}


def estado_de(valor: EstadoProductoEnum | str) -> EstadoProducto:
    return _ESTADOS[EstadoProductoEnum(valor)]
