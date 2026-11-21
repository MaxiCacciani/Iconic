from app.common.enums import Rol
from tests.conftest import _crear_usuario, auth_header

NUEVO = {"nombre": "Ana", "email": "Ana@Iconic.test", "password": "clave-segura", "rol": "vendedor"}


def _errores(r) -> dict[str, str]:
    return {e["loc"][-1]: e["msg"] for e in r.json()["detail"]}


def test_sin_sesion_401(client):
    assert client.get("/usuarios").status_code == 401


def test_vendedor_403(client, vendedor):
    h = auth_header(vendedor)
    assert client.get("/usuarios", headers=h).status_code == 403
    assert client.post("/usuarios", json=NUEVO, headers=h).status_code == 403
    assert (
        client.patch(f"/usuarios/{vendedor.id}", json={"rol": "admin"}, headers=h).status_code
        == 403
    )


def test_alta_y_listado_sin_hash(client, admin):
    h = auth_header(admin)
    r = client.post("/usuarios", json=NUEVO, headers=h)
    assert r.status_code == 201
    creado = r.json()
    assert creado["email"] == "ana@iconic.test"
    assert creado["activo"] is True
    assert "password" not in creado and "password_hash" not in creado

    lista = client.get("/usuarios", headers=h).json()
    assert {u["email"] for u in lista} == {"admin@iconic.test", "ana@iconic.test"}
    assert all("password_hash" not in u for u in lista)

    login = client.post(
        "/auth/login", json={"email": "ana@iconic.test", "password": "clave-segura"}
    )
    assert login.status_code == 200


def test_email_unico_sin_importar_mayusculas(client, admin):
    r = client.post(
        "/usuarios", json={**NUEVO, "email": "ADMIN@iconic.test"}, headers=auth_header(admin)
    )
    assert r.status_code == 422
    assert "email" in _errores(r)


def test_validaciones_por_campo_en_espanol(client, admin):
    r = client.post(
        "/usuarios",
        json={"nombre": " ", "email": "no-es-email", "password": "corta", "rol": "jefe"},
        headers=auth_header(admin),
    )
    assert r.status_code == 422
    errores = _errores(r)
    assert set(errores) == {"nombre", "email", "password", "rol"}
    assert errores["password"] == "Tiene que tener al menos 8 caracteres."


def test_editar_rol_y_nombre(client, admin, vendedor):
    r = client.patch(
        f"/usuarios/{vendedor.id}",
        json={"nombre": "Vende Dor", "rol": "admin"},
        headers=auth_header(admin),
    )
    assert r.status_code == 200
    assert r.json()["nombre"] == "Vende Dor"
    assert r.json()["rol"] == "admin"


def test_editar_email_repetido(client, admin, vendedor):
    r = client.patch(
        f"/usuarios/{vendedor.id}", json={"email": admin.email}, headers=auth_header(admin)
    )
    assert r.status_code == 422
    assert "email" in _errores(r)


def test_desactivar_y_reactivar(client, admin, vendedor):
    h = auth_header(admin)
    r = client.patch(f"/usuarios/{vendedor.id}", json={"activo": False}, headers=h)
    assert r.json()["activo"] is False
    login = client.post("/auth/login", json={"email": vendedor.email, "password": "secreto"})
    assert login.status_code == 401

    client.patch(f"/usuarios/{vendedor.id}", json={"activo": True}, headers=h)
    login = client.post("/auth/login", json={"email": vendedor.email, "password": "secreto"})
    assert login.status_code == 200


def test_blanqueo_de_password(client, admin, vendedor):
    r = client.patch(
        f"/usuarios/{vendedor.id}", json={"password": "nueva-clave"}, headers=auth_header(admin)
    )
    assert r.status_code == 200
    viejo = client.post("/auth/login", json={"email": vendedor.email, "password": "secreto"})
    nuevo = client.post("/auth/login", json={"email": vendedor.email, "password": "nueva-clave"})
    assert viejo.status_code == 401
    assert nuevo.status_code == 200


def test_admin_no_puede_desactivarse_ni_bajarse_el_rol(client, admin):
    h = auth_header(admin)
    r = client.patch(f"/usuarios/{admin.id}", json={"activo": False}, headers=h)
    assert r.status_code == 422 and "activo" in _errores(r)
    r = client.patch(f"/usuarios/{admin.id}", json={"rol": "vendedor"}, headers=h)
    assert r.status_code == 422 and "rol" in _errores(r)
    # Editar otros datos propios sí se puede.
    assert (
        client.patch(f"/usuarios/{admin.id}", json={"nombre": "Yo"}, headers=h).status_code == 200
    )


def test_otro_admin_si_puede_desactivarse(client, session, admin):
    otro = _crear_usuario(session, "otro@iconic.test", Rol.admin)
    r = client.patch(f"/usuarios/{otro.id}", json={"activo": False}, headers=auth_header(admin))
    assert r.status_code == 200


def test_usuario_inexistente(client, admin):
    assert (
        client.patch("/usuarios/999", json={"nombre": "x"}, headers=auth_header(admin)).status_code
        == 404
    )


def test_siempre_queda_un_admin_activo(session, admin, vendedor):
    import pytest

    from app.core.excepciones import ErrorDeCampo
    from app.core.uow import UnidadDeTrabajo
    from app.modules.usuarios.schemas import UsuarioUpdate
    from app.modules.usuarios.service import UsuarioService

    # Otro actor (no el propio admin) intenta dejar el sistema sin administradores.
    with pytest.raises(ErrorDeCampo, match="al menos un Administrador"):
        UsuarioService(UnidadDeTrabajo(session)).actualizar(
            admin.id, UsuarioUpdate(rol=Rol.vendedor), actor=vendedor
        )
