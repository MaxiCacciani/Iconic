"""Acceso a datos de productos. Los repositorios heredan de `RepositorioBase[M]`."""

from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import or_
from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, func, select

from app.common.base import Pagina, ParamsPagina, RepositorioBase
from app.common.enums import Condicion, EstadoProductoEnum
from app.modules.catalogos.models import Categoria, Defecto, Modelo
from app.modules.productos.models import Producto


@dataclass(frozen=True)
class FiltrosProducto:
    estado: EstadoProductoEnum | None = None
    categoria_id: int | None = None
    modelo_id: int | None = None
    condicion: Condicion | None = None
    buscar: str | None = None
    """Parte del IMEI o del nombre del modelo, sin distinguir mayúsculas."""


# Lo que se muestra de cada producto, en la misma tanda de consultas (sin una por fila).
_CARGAR = (
    selectinload(Producto.modelo).selectinload(Modelo.categoria),  # type: ignore[arg-type]
    selectinload(Producto.capacidad),  # type: ignore[arg-type]
    selectinload(Producto.color),  # type: ignore[arg-type]
    selectinload(Producto.proveedor),  # type: ignore[arg-type]
    selectinload(Producto.defectos),  # type: ignore[arg-type]
)


class ProductoRepository(RepositorioBase[Producto]):
    modelo = Producto

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def buscar(self, filtros: FiltrosProducto, params: ParamsPagina) -> Pagina[Producto]:
        consulta = select(Producto).join(Modelo, col(Producto.modelo_id) == col(Modelo.id))
        if filtros.estado:
            consulta = consulta.where(Producto.estado == filtros.estado)
        if filtros.categoria_id:
            consulta = consulta.where(Modelo.categoria_id == filtros.categoria_id)
        if filtros.modelo_id:
            consulta = consulta.where(Producto.modelo_id == filtros.modelo_id)
        if filtros.condicion:
            consulta = consulta.where(Producto.condicion == filtros.condicion)
        if filtros.buscar and (texto := filtros.buscar.strip()):
            consulta = consulta.where(
                or_(
                    # autoescape: un "%" o "_" escrito se busca como tal, no como comodín.
                    col(Producto.imei).contains(texto, autoescape=True),
                    func.lower(Modelo.nombre).contains(texto.lower(), autoescape=True),
                )
            )

        total = self.session.exec(select(func.count()).select_from(consulta.subquery())).one()
        items = self.session.exec(
            consulta.options(*_CARGAR)
            .order_by(col(Producto.id).desc())  # los últimos cargados, primero
            .offset(params.offset)
            .limit(params.tamanio)
        ).all()
        return Pagina(items=list(items), total=total, pagina=params.pagina, tamanio=params.tamanio)

    def con_detalle(self, id: int) -> Producto | None:
        return self.session.exec(
            select(Producto).where(Producto.id == id).options(*_CARGAR)
        ).first()

    def en_stock_por_imei(self, imei: str) -> Producto | None:
        """El producto no vendido (disponible o reservado) con ese IMEI. Los vendidos no
        cuentan: el mismo equipo puede volver a entrar por canje."""
        return self.session.exec(
            select(Producto).where(
                Producto.imei == imei, Producto.estado != EstadoProductoEnum.vendido
            )
        ).first()

    def unidades(self, estado: EstadoProductoEnum, condicion: Condicion | None = None) -> int:
        """Unidades (no filas): un accesorio por cantidad suma todas las suyas."""
        consulta = select(func.coalesce(func.sum(Producto.cantidad), 0)).where(
            Producto.estado == estado
        )
        if condicion:
            consulta = consulta.where(Producto.condicion == condicion)
        return int(self.session.exec(consulta).one())

    def de_categoria(self, categoria_id: int) -> int:
        return self.session.exec(
            select(func.count())
            .select_from(Producto)
            .join(Modelo, col(Producto.modelo_id) == col(Modelo.id))
            .where(Modelo.categoria_id == categoria_id)
        ).one()

    def de_tipo_categoria(self, tipo_categoria_id: int) -> int:
        return self.session.exec(
            select(func.count())
            .select_from(Producto)
            .join(Modelo, col(Producto.modelo_id) == col(Modelo.id))
            .join(Categoria, col(Modelo.categoria_id) == col(Categoria.id))
            .where(Categoria.tipo_categoria_id == tipo_categoria_id)
        ).one()


class DefectoRepository(RepositorioBase[Defecto]):
    modelo = Defecto

    def por_ids(self, ids: set[int]) -> Sequence[Defecto]:
        return self.session.exec(select(Defecto).where(col(Defecto.id).in_(ids))).all()

    def por_descripcion(self, descripcion: str) -> Defecto | None:
        """Sin distinguir mayúsculas: "Marco desgastado" y "marco desgastado" son el mismo."""
        return self.session.exec(
            select(Defecto).where(func.lower(Defecto.descripcion) == descripcion.lower())
        ).first()
