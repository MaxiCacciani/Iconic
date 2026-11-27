"""Comisión de la venta: solo del Administrador y se resta de la ganancia."""

from decimal import Decimal

from sqlmodel import Session

from app.modules.ventas.models import Venta
from tests import test_ventas
from tests.conftest import auth_header
from tests.test_ventas import errores, item, vender, venta

# Las fixtures de las ventas, para no repetirlas.
datos = test_ventas.datos
tc = test_ventas.tc


def patch(client, usuario, venta_id, comision):
    return client.patch(
        f"/ventas/{venta_id}/comision",
        json={"comision_usd": comision},
        headers=auth_header(usuario),
    )


def test_admin_registra_con_comision_y_se_resta_de_la_ganancia(client, admin, datos, tc):
    r = vender(client, admin, venta(datos, [item(datos.iphone, "1000")], comision_usd="50"))
    assert r.status_code == 201, r.json()
    v = r.json()
    assert v["comision_usd"] == "50.00"
    assert v["ganancia_usd"] == "250.00"  # 1000 − 700 − 50
    assert v["margen_pct"] == "35.7"  # 250 / 700


def test_sin_comision_queda_en_cero(client, admin, datos, tc):
    r = vender(client, admin, venta(datos, [item(datos.iphone, "1000")]))
    assert r.json()["comision_usd"] == "0.00"
    assert r.json()["ganancia_usd"] == "300.00"


def test_la_del_vendedor_se_ignora(client, vendedor, datos, tc, session: Session):
    r = vender(client, vendedor, venta(datos, [item(datos.iphone, "1000")], comision_usd="50"))
    assert r.status_code == 201, r.json()
    assert "comision_usd" not in r.json()
    assert session.get(Venta, r.json()["id"]).comision_usd == Decimal(0)

    r = client.get("/ventas", headers=auth_header(vendedor))
    assert "comision_usd" not in r.json()["items"][0]


def test_negativa_da_422(client, admin, datos, tc):
    r = vender(client, admin, venta(datos, [item(datos.iphone, "1000")], comision_usd="-1"))
    assert r.status_code == 422
    assert "comision_usd" in errores(r)

    r = vender(client, admin, venta(datos, [item(datos.iphone, "1000")]))
    r = patch(client, admin, r.json()["id"], "-1")
    assert r.status_code == 422
    assert "comision_usd" in errores(r)


def test_patch_cambia_la_comision_y_la_ganancia_total(client, admin, vendedor, datos, tc):
    id = vender(client, admin, venta(datos, [item(datos.iphone, "1000")])).json()["id"]
    assert client.get("/ventas", headers=auth_header(admin)).json()["ganancia_total_usd"] == (
        "300.00"
    )

    r = patch(client, admin, id, "80,50")
    assert r.status_code == 200, r.json()
    assert r.json()["comision_usd"] == "80.50"
    assert r.json()["ganancia_usd"] == "219.50"
    assert client.get("/ventas", headers=auth_header(admin)).json()["ganancia_total_usd"] == (
        "219.50"
    )

    assert patch(client, vendedor, id, "10").status_code == 403
    assert patch(client, admin, 999, "10").status_code == 404


def test_cotizar_del_admin_la_descuenta(client, admin, vendedor, datos):
    body = {"items": [item(datos.iphone, "1000")], "comision_usd": "100"}
    r = client.post("/ventas/cotizar", json=body, headers=auth_header(admin))
    assert r.json()["ganancia_usd"] == "200.00"
    assert r.json()["margen_pct"] == "28.6"

    r = client.post("/ventas/cotizar", json=body, headers=auth_header(vendedor))
    assert "comision_usd" not in r.json()
    assert "ganancia_usd" not in r.json()
