from collections.abc import Collection, Sequence

from pydantic import BaseModel, Field
from sqlmodel import Session, SQLModel, func, select

from app.core.excepciones import NoEncontrado

# Cómo se nombra, en un mensaje, a las filas de las tablas que apuntan a otra.
_NOMBRE_TABLA = {
    "producto_defectos": "productos",
    "pack_items": "packs",
    "venta_items": "ventas",
    "reserva_items": "reservas",
    "tipos_categoria": "tipos de categoría",
    "estados_reclamo": "estados de reclamo",
    "metodos_pago": "métodos de pago",
}


class ParamsPagina(BaseModel):
    pagina: int = Field(1, ge=1)
    tamanio: int = Field(50, ge=1, le=200)

    @property
    def offset(self) -> int:
        return (self.pagina - 1) * self.tamanio


class Pagina[T](BaseModel):
    items: list[T]
    total: int
    pagina: int
    tamanio: int


class RepositorioBase[M: SQLModel]:
    """ABMC genérico. Las consultas de negocio van como métodos explícitos en cada subclase.

    Nunca hace commit: solo `add`/`flush`. El commit lo decide la `UnidadDeTrabajo`.
    """

    modelo: type[M]

    def __init__(self, session: Session) -> None:
        self.session = session

    def obtener(self, id: int) -> M | None:
        return self.session.get(self.modelo, id)

    def obtener_o_falla(self, id: int) -> M:
        entidad = self.obtener(id)
        if entidad is None:
            raise NoEncontrado(f"{self.modelo.__name__} #{id} no existe")
        return entidad

    def listar(self, params: ParamsPagina | None = None) -> Pagina[M]:
        params = params or ParamsPagina()
        total = self.session.exec(select(func.count()).select_from(self.modelo)).one()
        items: Sequence[M] = self.session.exec(
            select(self.modelo)
            .order_by(self.modelo.id)  # type: ignore[attr-defined]
            .offset(params.offset)
            .limit(params.tamanio)
        ).all()
        return Pagina(items=list(items), total=total, pagina=params.pagina, tamanio=params.tamanio)

    def crear(self, entidad: M) -> M:
        self.session.add(entidad)
        self.session.flush()
        self.session.refresh(entidad)
        return entidad

    def actualizar(self, entidad: M) -> M:
        self.session.add(entidad)
        self.session.flush()
        return entidad

    def eliminar(self, entidad: M) -> None:
        self.session.delete(entidad)
        self.session.flush()

    def usos(self, entidad: M, ignorar: Collection[str] = ()) -> list[tuple[str, int]]:
        """Qué tablas apuntan a esta fila y cuántas veces, leído de las claves foráneas.

        Así, cuando una fase suma una tabla que apunta a otra (una venta a su cliente, un
        producto a su modelo), este chequeo la cubre sola. `ignorar`: tablas cuyas filas se
        van con la que se borra (por ejemplo, las asignaciones de los modelos), así que no
        cuentan como uso.
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
