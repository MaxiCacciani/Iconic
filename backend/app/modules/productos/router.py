"""Capa de presentación: endpoints HTTP de productos."""

from fastapi import APIRouter, Depends

from app.core.deps import usuario_actual

router = APIRouter(
    prefix="/productos",
    tags=["Productos"],
    dependencies=[Depends(usuario_actual)],
)
