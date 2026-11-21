"""Capa de presentación: endpoints HTTP de tipo de cambio."""

from fastapi import APIRouter, Depends

from app.core.deps import usuario_actual

router = APIRouter(
    prefix="/tipo-cambio",
    tags=["Tipo de cambio"],
    dependencies=[Depends(usuario_actual)],
)
