"""Capa de presentación: endpoints HTTP de reclamos."""

from fastapi import APIRouter, Depends

from app.core.deps import solo_admin

router = APIRouter(
    prefix="/reclamos",
    tags=["Reclamos"],
    dependencies=[Depends(solo_admin)],
)
