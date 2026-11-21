from collections.abc import Sequence

from pydantic import BaseModel, Field
from sqlmodel import Session, SQLModel, func, select

from app.core.excepciones import NoEncontrado


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
