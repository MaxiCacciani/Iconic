"""Lógica de negocio de usuarios.

Decisiones (confirmadas el 21/11/2026, no están en las reglas):
- Los usuarios se desactivan, no se borran: ventas y reservas guardan `usuario_id`.
- Un admin no puede desactivarse ni quitarse el rol a sí mismo, y el sistema
  nunca queda sin un Administrador activo.
"""

from collections.abc import Sequence

from app.common.enums import Rol
from app.core.excepciones import ErrorDeCampo
from app.core.security import hashear_password
from app.core.uow import UnidadDeTrabajo
from app.modules.usuarios.models import Usuario
from app.modules.usuarios.repository import UsuarioRepository
from app.modules.usuarios.schemas import UsuarioCreate, UsuarioUpdate


class UsuarioService:
    def __init__(self, uow: UnidadDeTrabajo) -> None:
        self.uow = uow
        self.usuarios = UsuarioRepository(uow.session)

    def listar(self) -> Sequence[Usuario]:
        return self.usuarios.todos()

    def crear(self, datos: UsuarioCreate) -> Usuario:
        with self.uow:
            self._validar_email_disponible(datos.email)
            return self.usuarios.crear(
                Usuario(
                    nombre=datos.nombre,
                    email=datos.email,
                    password_hash=hashear_password(datos.password),
                    rol=datos.rol,
                )
            )

    def actualizar(self, usuario_id: int, datos: UsuarioUpdate, actor: Usuario) -> Usuario:
        with self.uow:
            usuario = self.usuarios.obtener_o_falla(usuario_id)
            cambios = datos.model_dump(exclude_unset=True, exclude_none=True)

            if "email" in cambios and cambios["email"] != usuario.email.lower():
                self._validar_email_disponible(cambios["email"], id_en_edicion=usuario.id)

            deja_de_ser_admin_activo = (
                usuario.rol == Rol.admin
                and usuario.activo
                and (
                    cambios.get("rol", Rol.admin) != Rol.admin
                    or cambios.get("activo", True) is False
                )
            )
            if deja_de_ser_admin_activo:
                campo = "activo" if cambios.get("activo") is False else "rol"
                if usuario.id == actor.id:
                    raise ErrorDeCampo(
                        campo,
                        "No podés desactivarte ni quitarte el rol de Administrador a vos mismo.",
                    )
                if self.usuarios.admins_activos() <= 1:
                    raise ErrorDeCampo(campo, "Tiene que quedar al menos un Administrador activo.")

            if "password" in cambios:
                usuario.password_hash = hashear_password(cambios.pop("password"))
            for campo, valor in cambios.items():
                setattr(usuario, campo, valor)
            self.usuarios.actualizar(usuario)
        self.uow.session.refresh(usuario)
        return usuario

    def _validar_email_disponible(self, email: str, id_en_edicion: int | None = None) -> None:
        """Falla si otro usuario ya tiene ese email.

        En una edición, `id_en_edicion` es el usuario que se está editando: que el email
        sea el suyo no cuenta como repetido.
        """
        existente = self.usuarios.por_email(email)
        if existente is not None and existente.id != id_en_edicion:
            raise ErrorDeCampo("email", "Ya hay un usuario con ese email.")
