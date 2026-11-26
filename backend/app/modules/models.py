"""Importa los modelos de todos los módulos para registrarlos en `SQLModel.metadata`.

Al sumar un `models.py` con entidades, importalo acá.
"""

from app.modules.catalogos import models as catalogos  # noqa: F401
from app.modules.productos import models as productos  # noqa: F401
from app.modules.tipo_cambio import models as tipo_cambio  # noqa: F401
from app.modules.usuarios import models as usuarios  # noqa: F401
