"""Acceso a datos de clientes. Los repositorios heredan de `RepositorioBase[M]`."""

import re
import unicodedata
from typing import Any

from sqlalchemy import and_, or_
from sqlalchemy.orm import selectinload
from sqlmodel import col, func, select

from app.common.base import Pagina, ParamsPagina, RepositorioBase
from app.modules.clientes.models import Cliente

_SEPARADORES_DNI = re.compile(r"[.\s-]")

# Mayúsculas incluidas: el lower() de SQLite solo pasa a minúsculas las letras sin tilde.
_TILDES = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n"}
_TILDES |= {k.upper(): v for k, v in _TILDES.items()}


def _sin_tildes_sql(expresion: Any) -> Any:
    """`replace()` anidados: funciona igual en PostgreSQL y en SQLite (sin `unaccent`)."""
    for con, sin in _TILDES.items():
        expresion = func.replace(expresion, con, sin)
    return func.lower(expresion)


def _sin_tildes(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


class ClienteRepository(RepositorioBase[Cliente]):
    modelo = Cliente

    def buscar(self, texto: str | None, params: ParamsPagina) -> Pagina[Cliente]:
        """Por nombre o por DNI, ordenados por nombre.

        Nombre: cada palabra tiene que aparecer, en cualquier orden y sin distinguir
        mayúsculas ni tildes ("perez juan" encuentra a "Juan Pérez").
        DNI: parte del número, con o sin puntos ("30.123" encuentra 30123456).
        """
        consulta = select(Cliente)
        if texto and (texto := texto.strip()):
            nombre = _sin_tildes_sql(Cliente.nombre)
            por_nombre = [
                # autoescape: un "%" o "_" escrito se busca como tal, no como comodín.
                nombre.contains(palabra, autoescape=True)
                for palabra in _sin_tildes(texto).split()
            ]
            condiciones = [and_(*por_nombre)]
            digitos = _SEPARADORES_DNI.sub("", texto)
            if digitos.isdigit():
                condiciones.append(col(Cliente.dni).contains(digitos, autoescape=True))
            consulta = consulta.where(or_(*condiciones))

        total = self.session.exec(select(func.count()).select_from(consulta.subquery())).one()
        items = self.session.exec(
            consulta.options(selectinload(Cliente.localidad))  # type: ignore[arg-type]
            .order_by(func.lower(Cliente.nombre), col(Cliente.id))
            .offset(params.offset)
            .limit(params.tamanio)
        ).all()
        return Pagina(items=list(items), total=total, pagina=params.pagina, tamanio=params.tamanio)

    def con_detalle(self, id: int) -> Cliente | None:
        return self.session.exec(
            select(Cliente).where(Cliente.id == id).options(selectinload(Cliente.localidad))  # type: ignore[arg-type]
        ).first()

    def por_dni(self, dni: str) -> Cliente | None:
        return self.session.exec(select(Cliente).where(Cliente.dni == dni)).first()
