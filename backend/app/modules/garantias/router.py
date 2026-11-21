"""Capa de presentación: endpoints HTTP de garantías."""

from fastapi import APIRouter, Depends

from app.core.deps import usuario_actual

router = APIRouter(
    prefix="/garantias",
    tags=["Garantías"],
    dependencies=[Depends(usuario_actual)],
)
