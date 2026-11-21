"""Capa de presentación: endpoints HTTP de usuarios (solo Administrador)."""

from fastapi import APIRouter, Depends, status

from app.core.deps import SoloAdmin, UowDep, solo_admin
from app.modules.usuarios.schemas import UsuarioCreate, UsuarioRead, UsuarioUpdate
from app.modules.usuarios.service import UsuarioService

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"],
    dependencies=[Depends(solo_admin)],
)


@router.get("", response_model=list[UsuarioRead])
def listar(uow: UowDep) -> list[UsuarioRead]:
    return [UsuarioRead.model_validate(u) for u in UsuarioService(uow).listar()]


@router.post("", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
def crear(datos: UsuarioCreate, uow: UowDep) -> UsuarioRead:
    return UsuarioRead.model_validate(UsuarioService(uow).crear(datos))


@router.patch("/{usuario_id}", response_model=UsuarioRead)
def actualizar(usuario_id: int, datos: UsuarioUpdate, uow: UowDep, actor: SoloAdmin) -> UsuarioRead:
    return UsuarioRead.model_validate(UsuarioService(uow).actualizar(usuario_id, datos, actor))
