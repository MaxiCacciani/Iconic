"""Capa de presentación: endpoints HTTP de cobros."""

from fastapi import APIRouter, Depends

from app.core.deps import usuario_actual

router = APIRouter(
    prefix="/cobros",
    tags=["Cobros"],
    dependencies=[Depends(usuario_actual)],
)
