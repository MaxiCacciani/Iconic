from tests.conftest import auth_header


def test_health(client):
    assert client.get("/health").json() == {"estado": "ok"}


def test_login_ok(client, admin):
    r = client.post("/auth/login", json={"email": admin.email, "password": "secreto"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["rol"] == "admin"


def test_login_password_incorrecta(client, admin):
    r = client.post("/auth/login", json={"email": admin.email, "password": "otra"})
    assert r.status_code == 401


def test_sin_sesion_no_hay_acceso(client):
    assert client.get("/auth/me").status_code == 401


def test_vendedor_no_ve_costos(client, vendedor):
    permisos = client.get("/auth/me", headers=auth_header(vendedor)).json()["permisos"]
    assert "ver_costos" not in permisos
    assert "tipo_cambio:editar" not in permisos
