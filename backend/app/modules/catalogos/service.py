"""Lógica de negocio de los catálogos: un ABMC genérico que se configura por `Definicion`."""

from collections.abc import Sequence

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel

from app.core.excepciones import Conflicto, ErrorDeCampo
from app.core.uow import UnidadDeTrabajo
from app.modules.catalogos.definiciones import (
    ASIGNACION_POR_SLUG,
    ASIGNACIONES,
    TABLAS_DE_ASIGNACION,
    Asignacion,
    Definicion,
)
from app.modules.catalogos.models import Modelo
from app.modules.catalogos.repository import CatalogoRepository


class CatalogoService:
    def __init__(self, uow: UnidadDeTrabajo, definicion: Definicion) -> None:
        self.uow = uow
        self.d = definicion
        # Colores y capacidades: lo que un modelo elige de ellos.
        self.asignacion = ASIGNACION_POR_SLUG.get(definicion.slug)
        self.repo = CatalogoRepository(
            uow.session,
            definicion.modelo,
            definicion.campo_texto,
            definicion.ambito,
            cargar=[a.slug for a in ASIGNACIONES] if definicion.con_asignaciones else (),
        )

    def listar(
        self, ambito_id: int | None = None, modelo_id: int | None = None
    ) -> Sequence[SQLModel]:
        if self.asignacion and modelo_id is not None:
            if ambito_id is not None:
                # El modelo ya define la categoría: con las dos, una podría contradecir a la otra.
                raise ErrorDeCampo("modelo_id", "Pedí por categoría o por modelo, no por los dos.")
            return self.opciones_de_modelo(modelo_id)
        return self.repo.todos(ambito_id)

    def opciones_de_modelo(self, modelo_id: int) -> Sequence[SQLModel]:
        """Lo que se ofrece al cargar un producto de ese modelo: los colores (o capacidades)
        que tiene asignados o, si no tiene ninguno, todos los de su categoría."""
        a = self.asignacion
        assert a is not None
        modelo = CatalogoRepository(self.uow.session, Modelo).obtener_o_falla(modelo_id)
        asignados = self.repo.asignados(a.enlace, a.columna, modelo_id)
        return asignados or self.repo.todos(modelo.categoria_id)

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

    def eliminar(self, id: int) -> list[str]:
        """Borra y devuelve lo que hay que avisar (modelos que se quedaron sin opciones)."""
        with self.uow:
            entidad = self.repo.obtener_o_falla(id)
            if self.d.marca and getattr(entidad, self.d.marca.campo):
                raise Conflicto(self.d.marca.al_borrar)
            usos = self.repo.usos(entidad, ignorar=TABLAS_DE_ASIGNACION)
            if usos:
                partes = [f"{tabla} ({cantidad})" for tabla, cantidad in usos]
                detalle = " y ".join(filter(None, [", ".join(partes[:-1]), partes[-1]]))
                raise Conflicto(f"No se puede borrar «{self._texto(entidad)}»: lo usan {detalle}.")
            avisos = self._avisos_al_borrar(entidad)
            try:
                self.repo.eliminar(entidad)
            except IntegrityError:
                # Por si lo usa una tabla que todavía no tiene modelo: la base igual lo frena.
                raise Conflicto(
                    f"No se puede borrar «{self._texto(entidad)}»: está en uso."
                ) from None
        return avisos

    def _avisos_al_borrar(self, entidad: SQLModel) -> list[str]:
        """Si era el único color (o capacidad) marcado de un modelo, ese modelo pasa a
        ofrecer todos los de su categoría. Se deja borrar, pero se avisa."""
        a = self.asignacion
        if a is None:
            return []
        modelos = entidad.modelos  # type: ignore[attr-defined]
        quedan_sin = sorted(
            (m.nombre for m in modelos if len(getattr(m, a.slug)) == 1), key=str.lower
        )
        if not quedan_sin:
            return []
        nombres = [f"«{n}»" for n in quedan_sin]
        lista = " y ".join(filter(None, [", ".join(nombres[:-1]), nombres[-1]]))
        uno, varios = a.sin_opciones
        return [(uno if len(nombres) == 1 else varios).format(lista)]

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


class AsignacionService:
    """Qué colores y capacidades de su categoría tiene un modelo."""

    def __init__(self, uow: UnidadDeTrabajo) -> None:
        self.uow = uow
        self.modelos = CatalogoRepository(uow.session, Modelo)

    def asignar(self, modelo_id: int, cambios: dict[str, list[int]]) -> Modelo:
        """`cambios`: por campo (`color_ids`, `capacidad_ids`), la lista completa nueva.
        Vacía, el modelo vuelve a ofrecer todos. Se guarda todo junto o nada."""
        with self.uow:
            modelo = self.modelos.obtener_o_falla(modelo_id)
            for a in ASIGNACIONES:
                if a.campo in cambios:
                    setattr(modelo, a.slug, self._validados(a, modelo, cambios[a.campo]))
            self.uow.session.add(modelo)
        self.uow.session.refresh(modelo)
        return modelo

    def _validados(self, a: Asignacion, modelo: Modelo, ids: list[int]) -> list[SQLModel]:
        pedidos = set(ids)
        items = CatalogoRepository(self.uow.session, a.modelo).por_ids(pedidos)
        if len(items) != len(pedidos):
            raise ErrorDeCampo(a.campo, a.no_existe)
        # La categoría de un modelo, color o capacidad no cambia, así que esto alcanza
        # para que la asignación siga siendo válida.
        for item in sorted(items, key=lambda i: i.id):  # type: ignore[attr-defined]
            if item.categoria_id != modelo.categoria_id:  # type: ignore[attr-defined]
                raise ErrorDeCampo(a.campo, a.otra_categoria.format(item.nombre))  # type: ignore[attr-defined]
        return list(items)
