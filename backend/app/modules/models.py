"""Importa los modelos de todos los módulos para registrarlos en `SQLModel.metadata`.

Al sumar un `models.py` con entidades, importalo acá.
"""

from app.modules.usuarios import models as usuarios  # noqa: F401
