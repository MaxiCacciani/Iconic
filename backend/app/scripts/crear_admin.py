"""Crea el primer Administrador.

uv run python -m app.scripts.crear_admin --nombre "Admin" --email admin@iconic.com
"""

import argparse
import getpass

from sqlmodel import Session

from app.common.enums import Rol
from app.core.config import get_settings
from app.core.db import crear_tablas_sqlite, engine
from app.core.security import hashear_password
from app.core.uow import UnidadDeTrabajo
from app.modules.usuarios.models import Usuario
from app.modules.usuarios.repository import UsuarioRepository


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nombre", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", help="Si no se pasa, se pide por consola")
    args = parser.parse_args()
    password = args.password or getpass.getpass("Contraseña: ")

    if get_settings().es_sqlite:
        crear_tablas_sqlite()

    with Session(engine) as session, UnidadDeTrabajo(session):
        repo = UsuarioRepository(session)
        if repo.por_email(args.email):
            raise SystemExit(f"Ya existe un usuario con el email {args.email}")
        repo.crear(
            Usuario(
                nombre=args.nombre,
                email=args.email,
                password_hash=hashear_password(password),
                rol=Rol.admin,
            )
        )
    print(f"Administrador {args.email} creado")


if __name__ == "__main__":
    main()
