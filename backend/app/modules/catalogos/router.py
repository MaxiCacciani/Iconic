"""Capa de presentación: un juego de endpoints por catálogo, armado desde `DEFINICIONES`.

Todos los logueados los leen (el Vendedor los necesita para vender, tomar canjes y
cargar clientes); solo el Administrador los modifica.

Además, `PUT /catalogos/modelos/{id}/colores` (y `/capacidades`) elige qué colores y
capacidades de su categoría tiene cada modelo, y `GET /catalogos/colores?modelo_id=`
devuelve las opciones de ese modelo.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import UowDep, solo_admin, usuario_actual
from app.modules.catalogos.definiciones import ASIGNACIONES, DEFINICIONES, Asignacion, Definicion
from app.modules.catalogos.schemas import AsignacionUpdate, ModeloRead
from app.modules.catalogos.service import AsignacionService, CatalogoService

router = APIRouter(prefix="/catalogos", dependencies=[Depends(usuario_actual)])

_ADMIN = [Depends(solo_admin)]


def _agregar(d: Definicion) -> None:
    Crear, Editar, Leer = d.crear, d.editar, d.leer  # noqa: N806
    nombre = d.slug.replace("-", "_")
    tags: list[Any] = [f"Catálogos · {d.titulo}"]

    def leer(entidad: Any) -> Any:
        return Leer.model_validate(entidad)

    if d.por_modelo:

        def listar(
            uow: UowDep,
            categoria_id: Annotated[int | None, Query(description="Solo de esa categoría")] = None,
            modelo_id: Annotated[
                int | None,
                Query(
                    description="Las opciones de ese modelo: sus asignados o, si no tiene, "
                    "todos los de su categoría"
                ),
            ] = None,
        ) -> Any:
            servicio = CatalogoService(uow, d)
            return [leer(e) for e in servicio.listar(categoria_id, modelo_id)]
    elif d.ambito:

        def listar(  # type: ignore[misc]
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


def _agregar_asignacion(a: Asignacion) -> None:
    def asignar(item_id: int, datos: AsignacionUpdate, uow: UowDep) -> Any:
        return ModeloRead.model_validate(AsignacionService(uow, a).asignar(item_id, datos.ids))

    router.add_api_route(
        f"/modelos/{{item_id}}/{a.relacion}",
        asignar,
        methods=["PUT"],
        response_model=ModeloRead,
        dependencies=_ADMIN,
        tags=["Catálogos · Modelos"],
        operation_id=f"asignar_{a.relacion}_a_modelo",
    )


for _definicion in DEFINICIONES:
    _agregar(_definicion)

for _asignacion in ASIGNACIONES:
    _agregar_asignacion(_asignacion)
