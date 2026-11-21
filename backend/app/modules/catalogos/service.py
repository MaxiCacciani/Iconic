"""Lógica de negocio de los catálogos: un ABMC genérico que se configura por `Definicion`."""

from collections.abc import Sequence

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel

from app.core.excepciones import Conflicto, ErrorDeCampo, NoEncontrado
from app.core.uow import UnidadDeTrabajo
from app.modules.catalogos.definiciones import Asignacion, Definicion
from app.modules.catalogos.models import Modelo
from app.modules.catalogos.repository import CatalogoRepository


class CatalogoService:
    def __init__(self, uow: UnidadDeTrabajo, definicion: Definicion) -> None:
        self.uow = uow
        self.d = definicion
        self.repo = CatalogoRepository(
            uow.session, definicion.modelo, definicion.campo_texto, definicion.ambito
        )

    def listar(
        self, ambito_id: int | None = None, modelo_id: int | None = None
    ) -> Sequence[SQLModel]:
        if self.d.por_modelo and modelo_id is not None:
            return self.opciones_de_modelo(modelo_id)
        return self.repo.todos(ambito_id)

    def opciones_de_modelo(self, modelo_id: int) -> Sequence[SQLModel]:
        """Lo que se ofrece al cargar un producto de ese modelo: los colores (o capacidades)
        que tiene asignados o, si no tiene ninguno, todos los de su categoría."""
        modelo = _modelo_o_falla(self.uow, modelo_id)
        asignados = getattr(modelo, self.d.por_modelo)  # type: ignore[arg-type]
        if not asignados:
            return self.repo.todos(modelo.categoria_id)
        return sorted(asignados, key=lambda e: self._texto(e).lower())

    def crear(self, datos: BaseModel) -> SQLModel:
        with self.uow:
            # Todavía no está en la sesión, así que validar no la graba antes de tiempo.
            entidad = self.d.modelo(**datos.model_dump())
            self._validar(entidad)
            if self.d.marca and getattr(entidad, self.d.marca.campo):
                self._sacar_marca_a_las_demas(entidad)
            return self.repo.crear(entidad)

    def actualizar(self, id: int, datos: BaseModel) -> SQLModel:
        with self.uow:
            entidad = self.repo.obtener_o_falla(id)
            cambios = datos.model_dump(exclude_unset=True, exclude_none=True)
            marca = self.d.marca
            # ¿Se le está sacando la marca a la fila que la tiene?
            quitada = bool(
                marca and getattr(entidad, marca.campo) and cambios.get(marca.campo) is False
            )
            # Sin autoflush: las consultas de validación no tienen que grabar los cambios
            # antes de chequearlos (un nombre repetido chocaría con el UNIQUE de la base).
            with self.uow.session.no_autoflush:
                for campo, valor in cambios.items():
                    if not (marca and campo == marca.campo):
                        setattr(entidad, campo, valor)
                self._validar(entidad)
                if quitada:
                    raise ErrorDeCampo(marca.campo, marca.sin_marca)  # type: ignore[union-attr]
            # La marca se pone recién después de sacársela a la anterior (índice único parcial).
            if marca and cambios.get(marca.campo):
                self._sacar_marca_a_las_demas(entidad)
                setattr(entidad, marca.campo, True)
            self.repo.actualizar(entidad)
        self.uow.session.refresh(entidad)
        return entidad

    def eliminar(self, id: int) -> None:
        with self.uow:
            entidad = self.repo.obtener_o_falla(id)
            if self.d.marca and getattr(entidad, self.d.marca.campo):
                raise Conflicto(self.d.marca.al_borrar)
            usos = self.repo.usos(entidad)
            if usos:
                partes = [f"{tabla} ({cantidad})" for tabla, cantidad in usos]
                detalle = " y ".join(filter(None, [", ".join(partes[:-1]), partes[-1]]))
                raise Conflicto(f"No se puede borrar «{self._texto(entidad)}»: lo usan {detalle}.")
            try:
                self.repo.eliminar(entidad)
            except IntegrityError:
                # Por si lo usa una tabla que todavía no tiene modelo: la base igual lo frena.
                raise Conflicto(
                    f"No se puede borrar «{self._texto(entidad)}»: está en uso."
                ) from None

    # ─── Reglas comunes ──────────────────────────────────────────────────────
    def _texto(self, entidad: SQLModel) -> str:
        return getattr(entidad, self.d.campo_texto)

    def _validar(self, entidad: SQLModel) -> None:
        for campo, referencia in self.d.referencias.items():
            if self.uow.session.get(referencia.modelo, getattr(entidad, campo)) is None:
                raise ErrorDeCampo(campo, referencia.mensaje)

        ambito_id = getattr(entidad, self.d.ambito) if self.d.ambito else None
        existente = self.repo.por_texto(self._texto(entidad), ambito_id)
        if existente is not None and existente.id != entidad.id:  # type: ignore[attr-defined]
            raise ErrorDeCampo(self.d.campo_texto, self.d.repetido)

        if self.d.validar:
            self.d.validar(entidad)

    def _sacar_marca_a_las_demas(self, entidad: SQLModel) -> None:
        """La marca (predeterminado, inicial) queda en una sola fila: la que se está marcando."""
        campo = self.d.marca.campo  # type: ignore[union-attr]
        for otra in self.repo.marcados(campo):
            if otra.id != entidad.id:  # type: ignore[attr-defined]
                setattr(otra, campo, False)
                self.repo.actualizar(otra)


def _modelo_o_falla(uow: UnidadDeTrabajo, modelo_id: int) -> Modelo:
    modelo = uow.session.get(Modelo, modelo_id)
    if modelo is None:
        raise NoEncontrado(f"Modelo #{modelo_id} no existe")
    return modelo


class AsignacionService:
    """Qué colores o capacidades de su categoría tiene un modelo."""

    def __init__(self, uow: UnidadDeTrabajo, asignacion: Asignacion) -> None:
        self.uow = uow
        self.a = asignacion

    def asignar(self, modelo_id: int, ids: list[int]) -> Modelo:
        """Reemplaza la lista completa. Vacía, el modelo vuelve a ofrecer todos."""
        with self.uow:
            modelo = _modelo_o_falla(self.uow, modelo_id)
            elegidos = []
            for id in dict.fromkeys(ids):  # sin repetidos, en el orden en que llegaron
                item = self.uow.session.get(self.a.modelo, id)
                if item is None:
                    raise ErrorDeCampo("ids", self.a.no_existe)
                # La categoría de un modelo, color o capacidad no cambia, así que esto
                # alcanza para que la asignación siga siendo válida.
                if item.categoria_id != modelo.categoria_id:  # type: ignore[attr-defined]
                    raise ErrorDeCampo("ids", self.a.otra_categoria.format(item.nombre))  # type: ignore[attr-defined]
                elegidos.append(item)
            setattr(modelo, self.a.relacion, elegidos)
            self.uow.session.add(modelo)
        self.uow.session.refresh(modelo)
        return modelo
