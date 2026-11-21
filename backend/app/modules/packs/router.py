"""Capa de presentación: endpoints HTTP de packs."""

from fastapi import APIRouter, Depends

from app.core.deps import usuario_actual

router = APIRouter(
    prefix="/packs",
    tags=["Packs"],
    dependencies=[Depends(usuario_actual)],
)
