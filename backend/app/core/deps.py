from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.common.enums import Rol
from app.core.db import get_session
from app.core.security import decodificar_token
from app.core.uow import UnidadDeTrabajo
from app.modules.usuarios.models import Usuario

SesionDep = Annotated[Session, Depends(get_session)]


def get_uow(session: SesionDep) -> UnidadDeTrabajo:
    return UnidadDeTrabajo(session)


UowDep = Annotated[UnidadDeTrabajo, Depends(get_uow)]

_bearer = HTTPBearer(auto_error=False)

_NO_AUTORIZADO = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No autenticado",
    headers={"WWW-Authenticate": "Bearer"},
)


def usuario_actual(
    session: SesionDep,
    credenciales: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Usuario:
    if credenciales is None:
        raise _NO_AUTORIZADO
    try:
        payload = decodificar_token(credenciales.credentials)
        usuario_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise _NO_AUTORIZADO from None
    usuario = session.get(Usuario, usuario_id)
    if usuario is None or not usuario.activo:
        raise _NO_AUTORIZADO
    return usuario


def solo_admin(usuario: Annotated[Usuario, Depends(usuario_actual)]) -> Usuario:
    if usuario.rol != Rol.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo Administrador")
    return usuario


Logueado = Annotated[Usuario, Depends(usuario_actual)]
SoloAdmin = Annotated[Usuario, Depends(solo_admin)]
