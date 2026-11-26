"""DTOs de entrada y salida de vendedores (Create / Read / Update).

No tienen costos: los dos roles reciben el mismo `VendedorRead`.
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.modules.clientes.schemas import Nombre

# Un `int` de PostgreSQL: más grande no entra en la columna.
Numero = Annotated[int, Field(ge=1, le=2_147_483_647)]


class VendedorCreate(BaseModel):
    """El nombre se guarda con la inicial de cada palabra en mayúscula, como el de los
    clientes ("juan pérez" → "Juan Pérez")."""

    numero: Numero
    nombre: Nombre


class VendedorUpdate(BaseModel):
    """Lo que no se manda queda como estaba. Los dos son obligatorios: no se borran."""

    numero: Numero | None = None
    nombre: Nombre | None = None


class VendedorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int
    nombre: str
