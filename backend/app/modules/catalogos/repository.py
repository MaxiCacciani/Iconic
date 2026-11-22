"""Acceso a datos de los catálogos: un solo repositorio genérico para todas las tablas."""

from collections.abc import Collection, Sequence
from typing import Any

from sqlalchemy.orm import selectinload
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
        self,
        session: Session,
        modelo: type[M],
        campo_texto: str = "nombre",
        ambito: str | None = None,
        cargar: Collection[str] = (),
    ) -> None:
        """`cargar`: relaciones que el listado trae en la misma consulta (los colores y
        capacidades de los modelos), así no se pide una por fila."""
        super().__init__(session)
        self.modelo = modelo
        self.campo_texto = campo_texto
        self.ambito = ambito
        self.cargar = cargar

    def _columna(self, campo: str) -> Any:
        return getattr(self.modelo, campo)

    def _orden(self) -> Any:
        # Sin distinguir mayúsculas, así "iPhone" no queda después de "Xbox".
        return func.lower(self._columna(self.campo_texto))

    def todos(self, ambito_id: int | None = None) -> Sequence[M]:
        consulta = select(self.modelo).options(
            *(selectinload(self._columna(r)) for r in self.cargar)
        )
        if self.ambito and ambito_id is not None:
            consulta = consulta.where(self._columna(self.ambito) == ambito_id)
        return self.session.exec(consulta.order_by(self._orden())).all()

    def por_ids(self, ids: Collection[int]) -> Sequence[M]:
        return self.session.exec(select(self.modelo).where(self._columna("id").in_(ids))).all()

    def asignados(self, enlace: type[SQLModel], columna: str, modelo_id: int) -> Sequence[M]:
        """Los de este catálogo que el modelo tiene asignados en `enlace`, con el mismo
        orden que `todos`."""
        consulta = (
            select(self.modelo)
            .join(enlace, getattr(enlace, columna) == self._columna("id"))
            .where(enlace.modelo_id == modelo_id)  # type: ignore[attr-defined]
            .order_by(self._orden())
        )
        return self.session.exec(consulta).all()

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

    def usos(self, entidad: M, ignorar: Collection[str] = ()) -> list[tuple[str, int]]:
        """Qué tablas apuntan a esta fila y cuántas veces, leído de las claves foráneas.

        Así, cuando una fase suma una tabla que usa un catálogo, este chequeo la cubre sola.
        `ignorar`: tablas cuyas filas se van con la que se borra (las asignaciones de los
        modelos), así que no cuentan como uso.
        """
        tabla = self.modelo.__table__  # type: ignore[attr-defined]
        usos: list[tuple[str, int]] = []
        for otra in SQLModel.metadata.sorted_tables:
            for fk in otra.foreign_keys:
                if fk.column.table is not tabla or otra.name in ignorar:
                    continue
                cantidad = self.session.exec(
                    select(func.count()).select_from(otra).where(fk.parent == entidad.id)  # type: ignore[attr-defined]
                ).one()
                if cantidad:
                    usos.append((_NOMBRE_TABLA.get(otra.name, otra.name), cantidad))
        return usos
