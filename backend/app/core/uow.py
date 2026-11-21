from types import TracebackType

from sqlmodel import Session


class UnidadDeTrabajo:
    """Unit of Work: hace atómicas las operaciones de varios pasos.

    Los repositorios solo hacen `add`/`flush`; el commit (o rollback) lo decide la UoW.

        with self.uow:
            ...  # varios repositorios sobre la misma sesión
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def __enter__(self) -> "UnidadDeTrabajo":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is None:
            self.session.commit()
        else:
            self.session.rollback()
