"""Capa de presentación: endpoints HTTP de clientes."""

from fastapi import APIRouter, Depends

from app.core.deps import usuario_actual

router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"],
    dependencies=[Depends(usuario_actual)],
)
