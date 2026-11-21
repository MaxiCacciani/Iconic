"""Acceso a datos de los catálogos: un solo repositorio genérico para todas las tablas."""

from collections.abc import Sequence
from typing import Any

from sqlmodel import Session, SQLModel, func, select

from app.common.base import RepositorioBase

# Cómo se nombra, en un mensaje, a las filas de las tablas que usan un catálogo.
_NOMBRE_TABLA = {
    "producto_defectos": "productos",
    "pack_items": "packs",
    "venta_items": "ventas",
    "reserva_items": "reservas",
    "tipos_categoria": "tipos de categoría",
    "estados_reclamo": "estados de reclamo",
    "metodos_pago": "métodos de pago",
}


class CatalogoRepository[M: SQLModel](RepositorioBase[M]):
    """ABMC de un catálogo. `ambito` es la columna dentro de la cual el texto no se repite
    (por ejemplo, `categoria_id` en modelos); sin ámbito, no se repite en toda la tabla."""

    def __init__(
        self, session: Session, modelo: type[M], campo_texto: str, ambito: str | None = None
    ) -> None:
        super().__init__(session)
        self.modelo = modelo
        self.campo_texto = campo_texto
        self.ambito = ambito

    def _columna(self, campo: str) -> Any:
        return getattr(self.modelo, campo)

    def todos(self, ambito_id: int | None = None) -> Sequence[M]:
        consulta = select(self.modelo)
        if self.ambito and ambito_id is not None:
            consulta = consulta.where(self._columna(self.ambito) == ambito_id)
        # Sin distinguir mayúsculas, así "iPhone" no queda después de "Xbox".
        orden = func.lower(self._columna(self.campo_texto))
        return self.session.exec(consulta.order_by(orden)).all()

    def por_texto(self, texto: str, ambito_id: int | None = None) -> M | None:
        """Busca sin distinguir mayúsculas: "Rojo" y "rojo" son el mismo color."""
        consulta = select(self.modelo).where(
            func.lower(self._columna(self.campo_texto)) == texto.lower()
        )
        if self.ambito:
            consulta = consulta.where(self._columna(self.ambito) == ambito_id)
        return self.session.exec(consulta).first()

    def marcados(self, campo: str) -> Sequence[M]:
        return self.session.exec(select(self.modelo).where(self._columna(campo) == True)).all()  # noqa: E712

    def usos(self, entidad: M) -> list[tuple[str, int]]:
        """Qué tablas apuntan a esta fila y cuántas veces, leído de las claves foráneas.

        Así, cuando una fase suma una tabla que usa un catálogo, este chequeo la cubre sola.
        """
        tabla = self.modelo.__table__  # type: ignore[attr-defined]
        usos: list[tuple[str, int]] = []
        for otra in SQLModel.metadata.sorted_tables:
            for fk in otra.foreign_keys:
                if fk.column.table is not tabla:
                    continue
                cantidad = self.session.exec(
                    select(func.count()).select_from(otra).where(fk.parent == entidad.id)  # type: ignore[attr-defined]
                ).one()
                if cantidad:
                    usos.append((_NOMBRE_TABLA.get(otra.name, otra.name), cantidad))
        return usos
