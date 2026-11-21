"""Capa de presentación: login y sesión."""

from fastapi import APIRouter

from app.core.deps import Logueado, SesionDep
from app.modules.auth.schemas import LoginCreate, SesionRead, TokenRead
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenRead)
def login(datos: LoginCreate, session: SesionDep) -> TokenRead:
    return AuthService(session).login(datos.email, datos.password)


@router.get("/me", response_model=SesionRead)
def me(usuario: Logueado) -> SesionRead:
    return AuthService.sesion(usuario)
