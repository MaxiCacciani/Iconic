"""Capa de presentación: endpoints HTTP de usuarios."""

from fastapi import APIRouter, Depends

from app.core.deps import solo_admin

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"],
    dependencies=[Depends(solo_admin)],
)
