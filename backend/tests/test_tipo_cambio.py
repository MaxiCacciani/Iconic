from datetime import date, timedelta
from decimal import Decimal

import pytest
from pydantic import TypeAdapter, ValidationError

from app.common.tipos import Pesos
from app.core import reloj
from app.modules.tipo_cambio.models import TipoCambio
from tests.conftest import auth_header

HOY = date(2026, 11, 21)


@pytest.fixture(autouse=True)
def hoy_fijo(monkeypatch):
    monkeypatch.setattr(reloj, "hoy", lambda: HOY)


def _errores(r) -> dict[str, str]:
    return {e["loc"][-1]: e["msg"] for e in r.json()["detail"]}


def test_sin_sesion_401(client):
    assert client.get("/tipo-cambio/hoy").status_code == 401
    assert client.put("/tipo-cambio/hoy", json={"valor_ars": 1180}).status_code == 401


def test_arranca_vacio(client, vendedor):
    r = client.get("/tipo-cambio/hoy", headers=auth_header(vendedor))
    assert r.status_code == 200
    assert r.json() == {"fecha": "2026-11-21", "valor_ars": None, "cargado_por": None}


def test_no_se_arrastra_el_del_dia_anterior(client, session, admin):
    session.add(
        TipoCambio(fecha=HOY - timedelta(days=1), valor_ars=Decimal("1150"), usuario_id=admin.id)
    )
    session.commit()
    r = client.get("/tipo-cambio/hoy", headers=auth_header(admin))
    assert r.json()["valor_ars"] is None


def test_vendedor_no_puede_cargarlo(client, vendedor):
    r = client.put("/tipo-cambio/hoy", json={"valor_ars": 1180}, headers=auth_header(vendedor))
    assert r.status_code == 403


def test_admin_lo_carga_y_todos_lo_ven(client, admin, vendedor):
    r = client.put("/tipo-cambio/hoy", json={"valor_ars": "1180.50"}, headers=auth_header(admin))
    assert r.status_code == 200
    assert r.json() == {"fecha": "2026-11-21", "valor_ars": "1180.50", "cargado_por": admin.nombre}

    visto = client.get("/tipo-cambio/hoy", headers=auth_header(vendedor)).json()
    assert visto["valor_ars"] == "1180.50"


def test_corregirlo_no_crea_otro(client, session, admin):
    h = auth_header(admin)
    client.put("/tipo-cambio/hoy", json={"valor_ars": 1180}, headers=h)
    r = client.put("/tipo-cambio/hoy", json={"valor_ars": 1195}, headers=h)
    assert Decimal(r.json()["valor_ars"]) == Decimal("1195")
    assert len(session.exec(TipoCambio.__table__.select()).all()) == 1


def test_al_dia_siguiente_arranca_vacio_otra_vez(client, monkeypatch, admin):
    h = auth_header(admin)
    client.put("/tipo-cambio/hoy", json={"valor_ars": 1180}, headers=h)
    monkeypatch.setattr(reloj, "hoy", lambda: HOY + timedelta(days=1))
    assert client.get("/tipo-cambio/hoy", headers=h).json()["valor_ars"] is None


@pytest.mark.parametrize(
    ("valor", "mensaje"),
    [
        (0, "Tiene que ser mayor que 0."),
        (-5, "Tiene que ser mayor que 0."),
        ("abc", "Tiene que ser un número, por ejemplo 1.180,50."),
        ("1180,555", "Puede tener hasta 2 decimales."),
    ],
)
def test_valores_invalidos(client, admin, valor, mensaje):
    r = client.put("/tipo-cambio/hoy", json={"valor_ars": valor}, headers=auth_header(admin))
    assert r.status_code == 422
    assert _errores(r) == {"valor_ars": mensaje}


def test_falta_el_valor(client, admin):
    r = client.put("/tipo-cambio/hoy", json={}, headers=auth_header(admin))
    assert _errores(r) == {"valor_ars": "Este campo es obligatorio."}


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        (1180, "1180"),
        ("1180.5", "1180.5"),
        ("1180,5", "1180.5"),
        ("1.180", "1180"),
        ("1.180,50", "1180.50"),
        ("1.234.567,8", "1234567.8"),
        (" 1 180,50 ", "1180.50"),
    ],
)
def test_pesos_acepta_formato_argentino(entrada, esperado):
    assert TypeAdapter(Pesos).validate_python(entrada) == Decimal(esperado)


def test_pesos_rechaza_cero():
    with pytest.raises(ValidationError):
        TypeAdapter(Pesos).validate_python("0,00")


def test_hoy_usa_la_zona_de_argentina(monkeypatch):
    """A las 23:30 de Argentina ya es el día siguiente en UTC: tiene que seguir siendo hoy."""
    import datetime as dt

    from app.core import reloj as modulo

    class Fijo(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            utc = dt.datetime(2026, 11, 22, 2, 30, tzinfo=dt.UTC)  # 23:30 del 21 en Argentina
            return utc.astimezone(tz) if tz else utc

    monkeypatch.undo()  # sin el `hoy` fijo del fixture
    monkeypatch.setattr(modulo, "datetime", Fijo)
    assert modulo.hoy() == date(2026, 11, 21)
