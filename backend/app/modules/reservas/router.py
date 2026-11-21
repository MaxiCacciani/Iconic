"""Capa de presentación: endpoints HTTP de reservas."""

from fastapi import APIRouter, Depends

from app.core.deps import usuario_actual

router = APIRouter(
    prefix="/reservas",
    tags=["Reservas"],
    dependencies=[Depends(usuario_actual)],
)
