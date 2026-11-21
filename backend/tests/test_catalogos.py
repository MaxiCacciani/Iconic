import pytest
from sqlmodel import select

from app.modules.catalogos.models import Categoria, MetodoPago, TipoCategoria
from app.modules.catalogos.semilla import sembrar_catalogos
from tests.conftest import auth_header

SLUGS = [
    "tipos-categoria", "categorias", "modelos", "capacidades", "colores", "proveedores",
    "defectos", "localidades", "diagnosticos", "estados-reclamo", "metodos-pago",
]  # fmt: skip


@pytest.fixture(autouse=True)
def semilla(session):
    sembrar_catalogos(session)


def _errores(r) -> dict[str, str]:
    return {e["loc"][-1]: e["msg"] for e in r.json()["detail"]}


def _categoria(client, admin, nombre: str) -> int:
    r = client.get("/catalogos/categorias", headers=auth_header(admin))
    return next(c["id"] for c in r.json() if c["nombre"] == nombre)


# ─── Semilla ─────────────────────────────────────────────────────────────────
def test_semilla_trae_las_listas_de_las_reglas(client, admin):
    h = auth_header(admin)

    def nombres(slug: str, campo: str = "nombre") -> list[str]:
        return [x[campo] for x in client.get(f"/catalogos/{slug}", headers=h).json()]

    tipos = {t["nombre"]: t for t in client.get("/catalogos/tipos-categoria", headers=h).json()}
    assert tipos["Equipo con IMEI"]["usa_imei"] and tipos["Equipo con IMEI"]["usa_bateria"]
    assert tipos["Consola"]["usa_controles"]
    assert tipos["Accesorio"]["por_cantidad"]

    categorias = client.get("/catalogos/categorias", headers=h).json()
    assert len(categorias) == 13
    tipo_de = {c["nombre"]: c["tipo_categoria_id"] for c in categorias}
    assert tipo_de["iPhone"] == tipos["Equipo con IMEI"]["id"]
    assert tipo_de["AirPods"] == tipos["Equipo sin IMEI"]["id"]
    assert tipo_de["PlayStation"] == tipos["Consola"]["id"]
    assert tipo_de["Funda/Case"] == tipos["Accesorio"]["id"]

    assert set(nombres("proveedores")) == {
        "Plan canje", "Importación personal", "Mariano Camara", "Lucas Bertorello"
    }  # fmt: skip
    assert len(nombres("diagnosticos")) == 13
    assert "Face ID / Touch ID" in nombres("diagnosticos")
    assert "Pantalla con micro-rayones" in nombres("defectos", "descripcion")

    metodos = client.get("/catalogos/metodos-pago", headers=h).json()
    assert [m["nombre"] for m in metodos if m["predeterminado"]] == ["Transferencia"]
    assert len(metodos) == 4

    estados = client.get("/catalogos/estados-reclamo", headers=h).json()
    assert estados == [{"id": estados[0]["id"], "nombre": "En gestión", "es_inicial": True}]


def test_semilla_no_duplica_ni_pisa(session):
    session.add(MetodoPago(nombre="Cripto"))
    session.commit()
    sembrar_catalogos(session)
    assert len(session.exec(select(TipoCategoria)).all()) == 4
    assert len(session.exec(select(Categoria)).all()) == 13
    assert len(session.exec(select(MetodoPago)).all()) == 5


# ─── Permisos ────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("slug", SLUGS)
def test_sin_sesion_401(client, slug):
    assert client.get(f"/catalogos/{slug}").status_code == 401


@pytest.mark.parametrize("slug", SLUGS)
def test_vendedor_lee_pero_no_modifica(client, vendedor, slug):
    h = auth_header(vendedor)
    assert client.get(f"/catalogos/{slug}", headers=h).status_code == 200
    assert client.post(f"/catalogos/{slug}", json={"nombre": "X"}, headers=h).status_code == 403
    assert client.patch(f"/catalogos/{slug}/1", json={}, headers=h).status_code == 403
    assert client.delete(f"/catalogos/{slug}/1", headers=h).status_code == 403


def test_admin_tiene_permiso_de_catalogos(client, admin, vendedor):
    assert "catalogos" in client.get("/auth/me", headers=auth_header(admin)).json()["permisos"]
    assert (
        "catalogos" not in client.get("/auth/me", headers=auth_header(vendedor)).json()["permisos"]
    )  # noqa: E501


# ─── ABMC ────────────────────────────────────────────────────────────────────
def test_alta_edicion_y_baja(client, admin):
    h = auth_header(admin)
    r = client.post("/catalogos/localidades", json={"nombre": "  Rosario "}, headers=h)
    assert r.status_code == 201
    localidad = r.json()
    assert localidad["nombre"] == "Rosario"

    url = f"/catalogos/localidades/{localidad['id']}"
    r = client.patch(url, json={"nombre": "Funes"}, headers=h)
    assert r.status_code == 200 and r.json()["nombre"] == "Funes"

    assert client.delete(f"/catalogos/localidades/{localidad['id']}", headers=h).status_code == 204
    assert client.get("/catalogos/localidades", headers=h).json() == []
    assert client.patch("/catalogos/localidades/999", json={}, headers=h).status_code == 404


def test_lista_ordenada_por_nombre(client, admin):
    h = auth_header(admin)
    for nombre in ["Zárate", "Acassuso", "mendoza"]:
        client.post("/catalogos/localidades", json={"nombre": nombre}, headers=h)
    nombres = [x["nombre"] for x in client.get("/catalogos/localidades", headers=h).json()]
    assert nombres == ["Acassuso", "mendoza", "Zárate"]


def test_nombre_vacio_o_repetido(client, admin):
    h = auth_header(admin)
    r = client.post("/catalogos/proveedores", json={"nombre": "  "}, headers=h)
    assert r.status_code == 422 and "nombre" in _errores(r)

    r = client.post("/catalogos/proveedores", json={"nombre": "plan CANJE"}, headers=h)
    assert r.status_code == 422
    assert _errores(r) == {"nombre": "Ya hay un proveedor con ese nombre."}


def test_renombrar_a_uno_existente_no_rompe(client, admin):
    h = auth_header(admin)
    proveedores = client.get("/catalogos/proveedores", headers=h).json()
    r = client.patch(
        f"/catalogos/proveedores/{proveedores[0]['id']}",
        json={"nombre": proveedores[1]["nombre"]},
        headers=h,
    )
    assert r.status_code == 422 and "nombre" in _errores(r)
    # Guardar sin cambiar el nombre no cuenta como repetido.
    r = client.patch(
        f"/catalogos/proveedores/{proveedores[0]['id']}",
        json={"nombre": proveedores[0]["nombre"]},
        headers=h,
    )
    assert r.status_code == 200


def test_defectos_usan_descripcion(client, admin):
    h = auth_header(admin)
    r = client.post("/catalogos/defectos", json={"descripcion": "Tapa trasera rota"}, headers=h)
    assert r.status_code == 201 and r.json()["es_comun"] is True
    r = client.post("/catalogos/defectos", json={"descripcion": "marco desgastado"}, headers=h)
    assert _errores(r) == {"descripcion": "Ese defecto ya está en la lista."}


# ─── Por categoría ───────────────────────────────────────────────────────────
@pytest.mark.parametrize("slug", ["modelos", "capacidades", "colores"])
def test_se_filtran_por_categoria(client, admin, slug):
    h = auth_header(admin)
    iphone, ipad = _categoria(client, admin, "iPhone"), _categoria(client, admin, "iPad")
    client.post(f"/catalogos/{slug}", json={"categoria_id": iphone, "nombre": "A"}, headers=h)
    client.post(f"/catalogos/{slug}", json={"categoria_id": ipad, "nombre": "B"}, headers=h)

    r = client.get(f"/catalogos/{slug}", params={"categoria_id": iphone}, headers=h)
    assert [x["nombre"] for x in r.json()] == ["A"]
    assert len(client.get(f"/catalogos/{slug}", headers=h).json()) == 2


def test_mismo_nombre_en_otra_categoria(client, admin):
    h = auth_header(admin)
    iphone, ipad = _categoria(client, admin, "iPhone"), _categoria(client, admin, "iPad")
    datos = {"categoria_id": iphone, "nombre": "Negro"}
    assert client.post("/catalogos/colores", json=datos, headers=h).status_code == 201
    r = client.post("/catalogos/colores", json={**datos, "nombre": "negro"}, headers=h)
    assert _errores(r) == {"nombre": "Esta categoría ya tiene ese color."}
    r = client.post("/catalogos/colores", json={**datos, "categoria_id": ipad}, headers=h)
    assert r.status_code == 201


def test_categoria_inexistente(client, admin):
    h = auth_header(admin)
    r = client.post("/catalogos/modelos", json={"categoria_id": 999, "nombre": "X"}, headers=h)
    assert _errores(r) == {"categoria_id": "Esa categoría no existe."}
    r = client.post(
        "/catalogos/categorias", json={"nombre": "Kindle", "tipo_categoria_id": 999}, headers=h
    )
    assert _errores(r) == {"tipo_categoria_id": "Ese tipo de categoría no existe."}


def test_no_se_borra_lo_que_esta_en_uso(client, admin):
    h = auth_header(admin)
    iphone = _categoria(client, admin, "iPhone")
    client.post("/catalogos/modelos", json={"categoria_id": iphone, "nombre": "15 Pro"}, headers=h)
    client.post("/catalogos/colores", json={"categoria_id": iphone, "nombre": "Negro"}, headers=h)

    r = client.delete(f"/catalogos/categorias/{iphone}", headers=h)
    assert r.status_code == 409
    assert r.json()["detail"] == "No se puede borrar «iPhone»: lo usan colores (1) y modelos (1)."

    otro = _categoria(client, admin, "Otro accesorio")
    assert client.delete(f"/catalogos/categorias/{otro}", headers=h).status_code == 204


# ─── Tipos de categoría ──────────────────────────────────────────────────────
def test_tipo_por_cantidad_sin_datos_de_unidad(client, admin):
    h = auth_header(admin)
    r = client.post(
        "/catalogos/tipos-categoria",
        json={"nombre": "Repuesto", "por_cantidad": True, "usa_imei": True},
        headers=h,
    )
    assert r.status_code == 422 and "por_cantidad" in _errores(r)

    accesorio = next(
        t for t in client.get("/catalogos/tipos-categoria", headers=h).json()
        if t["por_cantidad"]
    )  # fmt: skip
    r = client.patch(
        f"/catalogos/tipos-categoria/{accesorio['id']}", json={"usa_controles": True}, headers=h
    )
    assert r.status_code == 422 and "por_cantidad" in _errores(r)


# ─── Marca única (predeterminado / inicial) ─────────────────────────────────
def _metodos(client, h) -> dict[str, dict]:
    return {m["nombre"]: m for m in client.get("/catalogos/metodos-pago", headers=h).json()}


def test_marcar_otro_predeterminado_desmarca_el_anterior(client, admin):
    h = auth_header(admin)
    efectivo = _metodos(client, h)["Efectivo"]
    r = client.patch(
        f"/catalogos/metodos-pago/{efectivo['id']}", json={"predeterminado": True}, headers=h
    )
    assert r.status_code == 200
    assert [n for n, m in _metodos(client, h).items() if m["predeterminado"]] == ["Efectivo"]

    r = client.post(
        "/catalogos/metodos-pago", json={"nombre": "Cripto", "predeterminado": True}, headers=h
    )
    assert r.status_code == 201
    assert [n for n, m in _metodos(client, h).items() if m["predeterminado"]] == ["Cripto"]


def test_no_se_puede_quedar_sin_predeterminado(client, admin):
    h = auth_header(admin)
    transferencia = _metodos(client, h)["Transferencia"]
    url = f"/catalogos/metodos-pago/{transferencia['id']}"
    r = client.patch(url, json={"predeterminado": False}, headers=h)
    assert r.status_code == 422 and "predeterminado" in _errores(r)
    r = client.delete(url, headers=h)
    assert r.status_code == 409
    assert _metodos(client, h)["Transferencia"]["predeterminado"] is True


def test_estado_inicial_unico(client, admin):
    h = auth_header(admin)
    r = client.post(
        "/catalogos/estados-reclamo", json={"nombre": "Resuelto", "es_inicial": True}, headers=h
    )
    assert r.status_code == 201
    estados = client.get("/catalogos/estados-reclamo", headers=h).json()
    assert [e["nombre"] for e in estados if e["es_inicial"]] == ["Resuelto"]
