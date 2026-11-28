"""Venta en cuotas, agenda de cobros, plan de cuotas del cliente, comprobante y Resumen."""

from datetime import date

import pytest
from sqlmodel import Session, select

from app.common.enums import EstadoCobroEnum
from app.core import reloj
from app.modules.cobros.models import Cobro
from tests import test_ventas
from tests.conftest import auth_header
from tests.test_ventas import errores, item, vender, venta

datos = test_ventas.datos
tc = test_ventas.tc

HOY = date(2026, 11, 28)


@pytest.fixture(autouse=True)
def hoy_fijo(monkeypatch):
    monkeypatch.setattr(reloj, "hoy", lambda: HOY)


def en_cuotas(d, cuotas=6, **extra):
    """El iPhone de US$ 1.000 en cuotas."""
    return venta(d, [item(d.iphone, "1000")], modalidad="cuotas", cantidad_cuotas=cuotas, **extra)


def pasar_a(monkeypatch, dia: date):
    monkeypatch.setattr(reloj, "hoy", lambda: dia)


def test_cotizar_en_cuotas_el_ejemplo_de_las_reglas(client, vendedor, datos):
    body = {**en_cuotas(datos), "anticipo_usd": "0"}
    r = client.post("/ventas/cotizar", json=body, headers=auth_header(vendedor))
    assert r.status_code == 200, r.json()
    c = r.json()
    assert c["saldo_usd"] == "1000"
    assert [x["monto_usd"] for x in c["cuotas"]] == ["167"] * 5 + ["165"]
    assert c["cuotas"][0] == {
        "numero": 1,
        "vencimiento": "2026-12-28",
        "monto_usd": "167",
        "cobrada": False,
    }


def test_vender_en_cuotas_genera_los_cobros(client, admin, session: Session, datos, tc):
    body = en_cuotas(datos, cuotas=3, anticipo_usd="100", canje_valor_usd=None)
    r = vender(client, admin, body)
    assert r.status_code == 201, r.json()
    v = r.json()
    assert (v["modalidad"], v["cantidad_cuotas"], v["anticipo_usd"]) == ("cuotas", 3, "100.00")
    assert v["saldo_usd"] == "900.00"
    assert [(c["numero"], c["vencimiento"], c["monto_usd"], c["estado"]) for c in v["cuotas"]] == [
        (1, "2026-12-28", "300.00", "pendiente"),
        (2, "2027-01-28", "300.00", "pendiente"),
        (3, "2027-02-28", "300.00", "pendiente"),
    ]


def test_primera_cuota_hoy_queda_cobrada(client, admin, datos, tc):
    v = vender(client, admin, en_cuotas(datos, cuotas=2, primera_cuota_hoy=True)).json()
    assert [(c["vencimiento"], c["estado"]) for c in v["cuotas"]] == [
        ("2026-11-28", "cobrada"),
        ("2026-12-28", "pendiente"),
    ]


def test_contado_no_genera_cobros(client, admin, session: Session, datos, tc):
    body = venta(datos, [item(datos.iphone, "1000")], cantidad_cuotas=6, anticipo_usd="100")
    v = vender(client, admin, body).json()
    assert (v["cantidad_cuotas"], v["anticipo_usd"], v["cuotas"]) == (None, "0.00", [])
    assert session.exec(select(Cobro)).all() == []


@pytest.mark.parametrize(
    ("extra", "campo"),
    [
        ({"cantidad_cuotas": 1}, "cantidad_cuotas"),
        ({"cantidad_cuotas": 61}, "cantidad_cuotas"),
        ({"anticipo_usd": "1000"}, "anticipo_usd"),
    ],
)
def test_en_cuotas_rechaza_y_no_graba_nada(
    client, admin, session: Session, datos, tc, extra, campo
):
    r = vender(client, admin, {**en_cuotas(datos), **extra})
    assert r.status_code == 422
    assert campo in errores(r)
    assert session.exec(select(Cobro)).all() == []


def test_agenda_del_mes_y_cobrar(client, admin, monkeypatch, datos, tc):
    vender(client, admin, en_cuotas(datos, cuotas=3))
    r = client.get("/cobros?anio=2026&mes=12", headers=auth_header(admin))
    assert r.status_code == 200
    agenda = r.json()
    assert (agenda["total_usd"], agenda["cobrado_usd"], agenda["pendiente_usd"]) == (
        "333.00",
        "0.00",
        "333.00",
    )
    [cuota] = agenda["cobros"]
    assert cuota["cliente"]["nombre"] == "Juan Pérez"
    assert (cuota["numero"], cuota["cantidad_cuotas"], cuota["monto_ars"]) == (1, 3, "333000.00")

    pasar_a(monkeypatch, date(2027, 1, 5))
    assert (
        client.get("/cobros?anio=2026&mes=12", headers=auth_header(admin)).json()["cobros"][0][
            "estado"
        ]
        == "vencida"
    )

    r = client.post(f"/cobros/{cuota['id']}/cobrar", headers=auth_header(admin))
    assert r.status_code == 200
    assert r.json()["estado"] == "cobrada"
    r = client.post(f"/cobros/{cuota['id']}/cobrar", headers=auth_header(admin))
    assert r.status_code == 409


def test_agenda_sin_mes_es_el_actual(client, admin):
    r = client.get("/cobros", headers=auth_header(admin)).json()
    assert (r["anio"], r["mes"], r["cobros"]) == (2026, 11, [])


def test_agenda_y_cobrar_son_del_admin(client, vendedor):
    assert client.get("/cobros", headers=auth_header(vendedor)).status_code == 403
    assert client.post("/cobros/1/cobrar", headers=auth_header(vendedor)).status_code == 403


def test_plan_de_cuotas_en_la_ficha(client, admin, vendedor, monkeypatch, datos, tc):
    venta_id = vender(client, admin, en_cuotas(datos, cuotas=3)).json()["id"]
    pasar_a(monkeypatch, date(2027, 1, 5))  # la cuota 1 (28/12) venció
    r = client.get(f"/clientes/{datos.cliente}/cuotas", headers=auth_header(vendedor))
    assert r.status_code == 200
    ficha = r.json()
    assert (ficha["saldo_usd"], ficha["saldo_ars"], ficha["en_mora"]) == (
        "1000.00",
        None,  # el TC cargado es del 28/11
        True,
    )
    [plan] = ficha["planes"]
    assert (plan["venta_id"], plan["pagadas"], plan["cantidad_cuotas"]) == (venta_id, 0, 3)
    assert plan["en_mora_desde"] == "2026-12-28"
    assert plan["proxima"]["numero"] == 1

    client.post(f"/cobros/{plan['cuotas'][0]['id']}/cobrar", headers=auth_header(admin))
    ficha = client.get(f"/clientes/{datos.cliente}/cuotas", headers=auth_header(admin)).json()
    assert (ficha["saldo_usd"], ficha["en_mora"]) == ("667.00", False)
    assert (ficha["planes"][0]["pagadas"], ficha["planes"][0]["proxima"]["numero"]) == (1, 2)


def test_ficha_de_un_cliente_que_no_existe(client, admin):
    assert client.get("/clientes/999/cuotas", headers=auth_header(admin)).status_code == 404


def test_borrar_la_venta_borra_sus_cuotas(client, admin, session: Session, datos, tc):
    v = vender(client, admin, en_cuotas(datos, cuotas=2, primera_cuota_hoy=True)).json()
    assert client.delete(f"/ventas/{v['id']}", headers=auth_header(admin)).status_code == 204
    assert session.exec(select(Cobro)).all() == []


def test_comprobante_en_pdf(client, admin, vendedor, datos, tc):
    venta_id = vender(client, vendedor, en_cuotas(datos)).json()["id"]
    for usuario in (admin, vendedor):
        r = client.get(f"/ventas/{venta_id}/comprobante", headers=auth_header(usuario))
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert r.content.startswith(b"%PDF")


def test_el_vendedor_solo_descarga_el_comprobante_de_sus_ventas(client, admin, vendedor, datos, tc):
    venta_id = vender(client, admin, venta(datos, [item(datos.iphone, "1000")])).json()["id"]
    r = client.get(f"/ventas/{venta_id}/comprobante", headers=auth_header(vendedor))
    assert r.status_code == 404


def test_resumen_cobros_del_mes_y_vencidas_solo_para_el_admin(
    client, admin, vendedor, session: Session, monkeypatch, datos, tc
):
    vender(client, admin, en_cuotas(datos, cuotas=2, primera_cuota_hoy=True))
    r = client.get("/resumen", headers=auth_header(admin)).json()
    assert r["cobros_del_mes"] == {
        "total_usd": "500.00",
        "cobrado_usd": "500.00",
        "pendiente_usd": "0",
    }

    pasar_a(monkeypatch, date(2027, 1, 2))
    r = client.get("/resumen", headers=auth_header(admin)).json()
    aviso = {"tipo": "cuotas_vencidas", "mensaje": "Hay 1 cuota vencida sin cobrar."}
    assert aviso in r["avisos"]
    r = client.get("/resumen", headers=auth_header(vendedor)).json()
    assert r["cobros_del_mes"] is None
    assert all(a["tipo"] != "cuotas_vencidas" for a in r["avisos"])
    assert session.exec(select(Cobro.estado)).all() == [
        EstadoCobroEnum.cobrada,
        EstadoCobroEnum.pendiente,
    ]
