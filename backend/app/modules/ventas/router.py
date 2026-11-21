"""Capa de presentación: endpoints HTTP de ventas."""

from fastapi import APIRouter, Depends

from app.core.deps import usuario_actual

router = APIRouter(
    prefix="/ventas",
    tags=["Ventas"],
    dependencies=[Depends(usuario_actual)],
)
