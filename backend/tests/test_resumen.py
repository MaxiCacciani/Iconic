from datetime import date

import pytest

from app.core import reloj
from tests.conftest import auth_header


@pytest.fixture(autouse=True)
def hoy_fijo(monkeypatch):
    monkeypatch.setattr(reloj, "hoy", lambda: date(2026, 11, 21))


def test_sin_sesion_401(client):
    assert client.get("/resumen").status_code == 401


def test_avisa_que_falta_el_tc_a_los_dos_roles(client, admin, vendedor):
    for usuario in (admin, vendedor):
        r = client.get("/resumen", headers=auth_header(usuario))
        assert r.status_code == 200
        assert r.json() == {
            "fecha": "2026-11-21",
            "avisos": [
                {"tipo": "tc_sin_cargar", "mensaje": "Falta cargar el tipo de cambio de hoy."}
            ],
            "stock": {"disponibles": 0, "nuevas": 0},
            "ventas": {
                "hoy": {"cantidad": 0, "total_usd": "0", "total_ars": "0"},
                "ultimos_7_dias": {"cantidad": 0, "total_usd": "0", "total_ars": "0"},
                "solo_propias": usuario is vendedor,
            },
            "cobros_del_mes": None
            if usuario is vendedor
            else {"total_usd": "0", "cobrado_usd": "0", "pendiente_usd": "0"},
        }


def test_el_aviso_desaparece_para_todos_al_cargarlo(client, admin, vendedor):
    client.put("/tipo-cambio/hoy", json={"valor_ars": 1180}, headers=auth_header(admin))
    for usuario in (admin, vendedor):
        assert client.get("/resumen", headers=auth_header(usuario)).json()["avisos"] == []
