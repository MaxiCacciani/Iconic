"""Acceso a datos de packs. Los repositorios heredan de `RepositorioBase[M]`."""

from collections.abc import Sequence

from sqlalchemy.orm import selectinload
from sqlmodel import col, func, select

from app.common.base import RepositorioBase
from app.common.enums import EstadoProductoEnum
from app.modules.catalogos.models import Modelo
from app.modules.packs.models import Pack, PackItem
from app.modules.productos.models import Producto

# Lo que se muestra de cada ítem, en la misma tanda de consultas (sin una por fila).
_CARGAR = (
    selectinload(Pack.items).selectinload(PackItem.categoria),  # type: ignore[arg-type]
    selectinload(Pack.items)  # type: ignore[arg-type]
    .selectinload(PackItem.producto)  # type: ignore[arg-type]
    .selectinload(Producto.modelo)  # type: ignore[arg-type]
    .selectinload(Modelo.categoria),  # type: ignore[arg-type]
    selectinload(Pack.items).selectinload(PackItem.producto).selectinload(Producto.capacidad),  # type: ignore[arg-type]
    selectinload(Pack.items).selectinload(PackItem.producto).selectinload(Producto.color),  # type: ignore[arg-type]
)


class PackRepository(RepositorioBase[Pack]):
    modelo = Pack

    def todos(self) -> Sequence[Pack]:
        return self.session.exec(
            select(Pack).options(*_CARGAR).order_by(func.lower(Pack.nombre), col(Pack.id))
        ).all()

    def con_detalle(self, id: int) -> Pack | None:
        return self.session.exec(select(Pack).where(Pack.id == id).options(*_CARGAR)).first()

    def por_nombre(self, nombre: str) -> Pack | None:
        """Sin distinguir mayúsculas: "Combo iPhone" y "combo iphone" son el mismo."""
        return self.session.exec(
            select(Pack).where(func.lower(Pack.nombre) == nombre.lower())
        ).first()

    def unidades_disponibles_por_categoria(self, categoria_ids: set[int]) -> dict[int, int]:
        """Unidades (no filas) disponibles de cada categoría: un accesorio suma las suyas."""
        if not categoria_ids:
            return {}
        filas = self.session.exec(
            select(Modelo.categoria_id, func.sum(Producto.cantidad))
            .join(Modelo, col(Producto.modelo_id) == col(Modelo.id))
            .where(
                col(Modelo.categoria_id).in_(categoria_ids),
                Producto.estado == EstadoProductoEnum.disponible,
            )
            .group_by(Modelo.categoria_id)
        ).all()
        return {categoria_id: int(unidades) for categoria_id, unidades in filas}

    def borrar_items_de_producto(self, producto_id: int) -> None:
        """Lo que hace el ON DELETE CASCADE de PostgreSQL, también en SQLite (que no aplica
        las claves foráneas)."""
        for item in self.session.exec(select(PackItem).where(PackItem.producto_id == producto_id)):
            self.session.delete(item)
        self.session.flush()
