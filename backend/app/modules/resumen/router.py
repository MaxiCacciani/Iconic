"""Capa de presentación: pantalla de inicio (`GET /resumen`). Solo lectura."""

from fastapi import APIRouter, Depends

from app.core.deps import usuario_actual

router = APIRouter(prefix="/resumen", tags=["Resumen"], dependencies=[Depends(usuario_actual)])
