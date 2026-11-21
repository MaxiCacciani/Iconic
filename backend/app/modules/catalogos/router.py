"""Capa de presentación: un juego de endpoints por catálogo, armado desde `DEFINICIONES`.

Todos los logueados los leen (el Vendedor los necesita para vender, tomar canjes y
cargar clientes); solo el Administrador los modifica.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import UowDep, solo_admin, usuario_actual
from app.modules.catalogos.definiciones import DEFINICIONES, Definicion
from app.modules.catalogos.service import CatalogoService

router = APIRouter(prefix="/catalogos", dependencies=[Depends(usuario_actual)])

_ADMIN = [Depends(solo_admin)]


def _agregar(d: Definicion) -> None:
    Crear, Editar, Leer = d.crear, d.editar, d.leer  # noqa: N806
    nombre = d.slug.replace("-", "_")
    tags: list[Any] = [f"Catálogos · {d.titulo}"]

    def leer(entidad: Any) -> Any:
        return Leer.model_validate(entidad)

    if d.ambito:

        def listar(
            uow: UowDep,
            categoria_id: Annotated[int | None, Query(description="Solo de esa categoría")] = None,
        ) -> Any:
            return [leer(e) for e in CatalogoService(uow, d).listar(categoria_id)]
    else:

        def listar(uow: UowDep) -> Any:  # type: ignore[misc]
            return [leer(e) for e in CatalogoService(uow, d).listar()]

    def crear(datos: Crear, uow: UowDep) -> Any:  # type: ignore[valid-type]
        return leer(CatalogoService(uow, d).crear(datos))

    def actualizar(item_id: int, datos: Editar, uow: UowDep) -> Any:  # type: ignore[valid-type]
        return leer(CatalogoService(uow, d).actualizar(item_id, datos))

    def eliminar(item_id: int, uow: UowDep) -> None:
        CatalogoService(uow, d).eliminar(item_id)

    ruta = f"/{d.slug}"
    router.add_api_route(
        ruta,
        listar,
        methods=["GET"],
        response_model=list[Leer],
        tags=tags,
        operation_id=f"listar_{nombre}",
    )
    router.add_api_route(
        ruta,
        crear,
        methods=["POST"],
        response_model=Leer,
        status_code=status.HTTP_201_CREATED,
        dependencies=_ADMIN,
        tags=tags,
        operation_id=f"crear_{nombre}",
    )
    router.add_api_route(
        f"{ruta}/{{item_id}}",
        actualizar,
        methods=["PATCH"],
        response_model=Leer,
        dependencies=_ADMIN,
        tags=tags,
        operation_id=f"actualizar_{nombre}",
    )
    router.add_api_route(
        f"{ruta}/{{item_id}}",
        eliminar,
        methods=["DELETE"],
        status_code=status.HTTP_204_NO_CONTENT,
        dependencies=_ADMIN,
        tags=tags,
        operation_id=f"eliminar_{nombre}",
    )


for _definicion in DEFINICIONES:
    _agregar(_definicion)
