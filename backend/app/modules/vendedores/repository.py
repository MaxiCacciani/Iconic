"""Acceso a datos de vendedores. Los repositorios heredan de `RepositorioBase[M]`."""

from collections.abc import Sequence

from sqlmodel import select

from app.common.base import RepositorioBase
from app.modules.vendedores.models import Vendedor


class VendedorRepository(RepositorioBase[Vendedor]):
    modelo = Vendedor

    def todos(self) -> Sequence[Vendedor]:
        """Ordenados por número: así se los busca en la venta."""
        return self.session.exec(select(Vendedor).order_by(Vendedor.numero)).all()

    def por_numero(self, numero: int) -> Vendedor | None:
        return self.session.exec(select(Vendedor).where(Vendedor.numero == numero)).first()
