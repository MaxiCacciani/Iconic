"""Capa de presentación: endpoints HTTP de vendedores."""

from fastapi import APIRouter, Depends

from app.core.deps import usuario_actual

router = APIRouter(
    prefix="/vendedores",
    tags=["Vendedores"],
    dependencies=[Depends(usuario_actual)],
)
