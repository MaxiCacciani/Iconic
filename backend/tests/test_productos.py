"""API de productos: alta según el tipo de categoría, validaciones, DTOs por rol y stock."""

from dataclasses import dataclass
from datetime import date

import pytest
from sqlmodel import Session, select

from app.common.tipos import luhn_valido
from app.core import reloj
from app.modules.catalogos.models import (
    Capacidad,
    Categoria,
    Color,
    Defecto,
    Modelo,
    ModeloColor,
    Proveedor,
    TipoCategoria,
)
from app.modules.catalogos.semilla import sembrar_catalogos
from app.modules.productos.models import Producto
from tests.conftest import auth_header


def imei(base: str) -> str:
    """Completa 14 dígitos con el dígito de control de Luhn."""
    return next(base + str(d) for d in range(10) if luhn_valido(base + str(d)))


IMEI_1 = imei("49015420323751")
IMEI_2 = imei("35209900176148")


@dataclass
class Datos:
    iphone: int
    iphone_15: int
    negro: int
    verde: int
    gb128: int
    airpods_pro: int
    ps5: int
    cargador: int
    proveedor: int
    defecto_comun: int


@pytest.fixture(autouse=True)
def hoy_fijo(monkeypatch):
    monkeypatch.setattr(reloj, "hoy", lambda: date(2026, 11, 21))


@pytest.fixture
def datos(session: Session) -> Datos:
    sembrar_catalogos(session)
    cat = {c.nombre: c.id for c in session.exec(select(Categoria)).all()}

    def agregar(entidad):
        session.add(entidad)
        session.flush()
        return entidad.id

    iphone_15 = agregar(Modelo(categoria_id=cat["iPhone"], nombre="iPhone 15"))
    negro = agregar(Color(categoria_id=cat["iPhone"], nombre="Negro"))
    verde = agregar(Color(categoria_id=cat["iPhone"], nombre="Verde alpino"))
    gb128 = agregar(Capacidad(categoria_id=cat["iPhone"], nombre="128 GB"))
    # El iPhone 15 solo vino en negro (de los colores cargados).
    session.add(ModeloColor(modelo_id=iphone_15, color_id=negro))
    d = Datos(
        iphone=cat["iPhone"],
        iphone_15=iphone_15,
        negro=negro,
        verde=verde,
        gb128=gb128,
        airpods_pro=agregar(Modelo(categoria_id=cat["AirPods"], nombre="AirPods Pro")),
        ps5=agregar(Modelo(categoria_id=cat["PlayStation"], nombre="PS5")),
        cargador=agregar(Modelo(categoria_id=cat["Cargador"], nombre="USB-C 20 W")),
        proveedor=session.exec(select(Proveedor)).first().id,
        defecto_comun=session.exec(select(Defecto)).first().id,
    )
    session.commit()
    return d


def _errores(r) -> dict[str, str]:
    return {e["loc"][-1]: e["msg"] for e in r.json()["detail"]}


def _iphone(d: Datos, **extra) -> dict:
    return {
        "modelo_id": d.iphone_15,
        "capacidad_id": d.gb128,
        "color_id": d.negro,
        "proveedor_id": d.proveedor,
        "condicion": "usado",
        "imei": IMEI_1,
        "bateria": 88,
        "precio_usd": "800",
        "costo_usd": "600",
        **extra,
    }


def _crear(client, admin, body: dict):
    return client.post("/productos", json=body, headers=auth_header(admin))


# ─── Permisos ────────────────────────────────────────────────────────────────
def test_sin_sesion_401(client):
    assert client.get("/productos").status_code == 401


def test_vendedor_no_carga_edita_ni_borra(client, vendedor, admin, datos):
    h = auth_header(vendedor)
    assert client.post("/productos", json=_iphone(datos), headers=h).status_code == 403
    pid = _crear(client, admin, _iphone(datos)).json()["id"]
    assert client.patch(f"/productos/{pid}", json={}, headers=h).status_code == 403
    assert client.delete(f"/productos/{pid}", headers=h).status_code == 403


def test_vendedor_ve_el_stock_sin_costos(client, admin, vendedor, datos):
    pid = _crear(client, admin, _iphone(datos)).json()["id"]
    h = auth_header(vendedor)
    lista = client.get("/productos", headers=h).json()
    uno = client.get(f"/productos/{pid}", headers=h).json()
    for producto in (lista["items"][0], uno):
        assert producto["precio_usd"] == "800.00"
        for campo in ("costo_usd", "costo_ars", "ganancia_usd", "ganancia_ars", "margen_pct"):
            assert campo not in producto


def test_admin_ve_costo_ganancia_y_margen(client, admin, datos):
    p = _crear(client, admin, _iphone(datos)).json()
    assert p["costo_usd"] == "600.00"
    assert p["ganancia_usd"] == "200.00"
    assert p["margen_pct"] == "33.3"
    listado = client.get("/productos", headers=auth_header(admin)).json()["items"][0]
    assert listado["margen_pct"] == "33.3"


# ─── Alta según el tipo de categoría ─────────────────────────────────────────
def test_alta_de_equipo_con_imei(client, admin, datos):
    r = _crear(client, admin, _iphone(datos, defecto_ids=[datos.defecto_comun]))
    assert r.status_code == 201, r.text
    p = r.json()
    assert p["categoria"]["nombre"] == "iPhone"
    assert p["modelo"]["nombre"] == "iPhone 15"
    assert p["color"]["nombre"] == "Negro"
    assert p["estado"] == "disponible"
    assert p["editable"] is True
    assert p["imei"] == IMEI_1
    assert p["bateria_nivel"] == "alta"
    assert p["cantidad"] == 1
    assert len(p["defectos"]) == 1


def test_imei_obligatorio_valido_y_sin_duplicados(client, admin, datos):
    assert _errores(_crear(client, admin, _iphone(datos, imei=None)))["imei"] == (
        "El IMEI es obligatorio en iPhone."
    )
    malo = IMEI_1[:-1] + str((int(IMEI_1[-1]) + 1) % 10)
    assert "dígito de control" in _errores(_crear(client, admin, _iphone(datos, imei=malo)))["imei"]
    assert "15 dígitos" in _errores(_crear(client, admin, _iphone(datos, imei="123")))["imei"]
    pid = _crear(client, admin, _iphone(datos)).json()["id"]
    r = _crear(client, admin, _iphone(datos))
    assert r.status_code == 422
    assert _errores(r)["imei"] == f"Ese IMEI ya está cargado en el producto #{pid}."


def test_equipo_sin_imei(client, admin, datos):
    body = {
        "modelo_id": datos.airpods_pro,
        "proveedor_id": datos.proveedor,
        "condicion": "nuevo",
        "precio_usd": 250,
    }
    assert _crear(client, admin, body).status_code == 201
    assert _errores(_crear(client, admin, {**body, "imei": IMEI_2}))["imei"] == (
        "AirPods no lleva IMEI."
    )
    assert _errores(_crear(client, admin, {**body, "bateria": 90}))["bateria"] == (
        "AirPods no lleva batería."
    )
    assert _errores(_crear(client, admin, {**body, "cantidad": 3}))["cantidad"].startswith(
        "AirPods va de a una unidad"
    )


def test_consola_con_controles_y_extras(client, admin, datos):
    body = {
        "modelo_id": datos.ps5,
        "proveedor_id": datos.proveedor,
        "condicion": "usado",
        "precio_usd": 450,
        "controles": 2,
        "extras": "  Caja original y 2 juegos  ",
    }
    p = _crear(client, admin, body).json()
    assert p["controles"] == 2
    assert p["extras"] == "Caja original y 2 juegos"
    assert "controles" in _errores(_crear(client, admin, {**body, "controles": 5}))


def test_accesorio_por_cantidad(client, admin, datos):
    body = {
        "modelo_id": datos.cargador,
        "proveedor_id": datos.proveedor,
        "condicion": "nuevo",
        "precio_usd": "15",
        "cantidad": 10,
    }
    assert _crear(client, admin, body).json()["cantidad"] == 10
    assert _errores(_crear(client, admin, {**body, "controles": 1}))["controles"] == (
        "Cargador no lleva controles."
    )
    assert "cantidad" in _errores(_crear(client, admin, {**body, "cantidad": 0}))


def test_color_y_capacidad_entre_las_opciones_del_modelo(client, admin, datos):
    # El iPhone 15 tiene marcado solo el negro: el verde no se ofrece.
    r = _crear(client, admin, _iphone(datos, color_id=datos.verde))
    assert _errores(r)["color_id"] == "Ese color no está entre las opciones de iPhone 15."
    # Sin capacidades marcadas, se ofrecen todas las de la categoría.
    assert _crear(client, admin, _iphone(datos)).status_code == 201
    # Una capacidad de otra categoría no.
    otra = _crear(client, admin, _iphone(datos, imei=IMEI_2, capacidad_id=9999))
    assert "capacidad_id" in _errores(otra)


def test_precio_y_costo(client, admin, datos):
    assert "precio_usd" in _errores(_crear(client, admin, _iphone(datos, precio_usd=0)))
    assert "costo_usd" in _errores(_crear(client, admin, _iphone(datos, costo_usd=-1)))
    assert _errores(_crear(client, admin, _iphone(datos, costo_usd=801)))["costo_usd"] == (
        "El costo no puede ser mayor al precio de venta."
    )
    # Sin costo: sin ganancia ni margen.
    p = _crear(client, admin, _iphone(datos, costo_usd=None)).json()
    assert p["ganancia_usd"] is None and p["margen_pct"] is None


def test_precio_en_formato_argentino(client, admin, datos):
    p = _crear(client, admin, _iphone(datos, precio_usd="1.250,50", costo_usd="1.000")).json()
    assert p["precio_usd"] == "1250.50"
    assert p["costo_usd"] == "1000.00"


def test_bateria_fuera_de_rango(client, admin, datos):
    assert "bateria" in _errores(_crear(client, admin, _iphone(datos, bateria=0)))
    assert "bateria" in _errores(_crear(client, admin, _iphone(datos, bateria=101)))
    p = _crear(client, admin, _iphone(datos, bateria=79)).json()
    assert p["bateria_nivel"] == "baja"


def test_equivalencia_en_pesos_con_el_tc_del_dia(client, admin, datos):
    p = _crear(client, admin, _iphone(datos)).json()
    assert p["precio_ars"] is None  # sin TC cargado
    client.put("/tipo-cambio/hoy", json={"valor_ars": 1200}, headers=auth_header(admin))
    p = client.get(f"/productos/{p['id']}", headers=auth_header(admin)).json()
    assert p["precio_ars"] == "960000.00"
    assert p["costo_ars"] == "720000.00"


# ─── Defectos ────────────────────────────────────────────────────────────────
def test_defectos_de_la_lista_y_escritos_a_mano(client, admin, datos, session):
    comun = session.get(Defecto, datos.defecto_comun)
    r = _crear(
        client,
        admin,
        _iphone(
            datos,
            defecto_ids=[datos.defecto_comun],
            # Uno nuevo y uno que ya está en la lista, escrito con otras mayúsculas.
            defectos_nuevos=["Tapa trasera astillada", comun.descripcion.upper()],
        ),
    )
    assert r.status_code == 201, r.text
    descripciones = [d["descripcion"] for d in r.json()["defectos"]]
    assert descripciones == sorted([comun.descripcion, "Tapa trasera astillada"], key=str.lower)
    nuevo = session.exec(
        select(Defecto).where(Defecto.descripcion == "Tapa trasera astillada")
    ).one()
    assert nuevo.es_comun is False  # no aparece para elegir
    assert "defecto_ids" in _errores(
        _crear(client, admin, _iphone(datos, imei=IMEI_2, defecto_ids=[999]))
    )


def test_un_defecto_en_uso_no_se_borra(client, admin, datos):
    _crear(client, admin, _iphone(datos, defecto_ids=[datos.defecto_comun]))
    r = client.delete(f"/catalogos/defectos/{datos.defecto_comun}", headers=auth_header(admin))
    assert r.status_code == 409
    assert "productos (1)" in r.json()["detail"]


# ─── Edición y borrado ───────────────────────────────────────────────────────
def test_editar(client, admin, datos):
    p = _crear(client, admin, _iphone(datos, defecto_ids=[datos.defecto_comun])).json()
    h = auth_header(admin)
    r = client.patch(f"/productos/{p['id']}", json={"precio_usd": 900, "bateria": 82}, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["precio_usd"] == "900.00"
    assert r.json()["bateria_nivel"] == "media"
    assert len(r.json()["defectos"]) == 1  # no se mandaron: quedan como estaban
    r = client.patch(f"/productos/{p['id']}", json={"defecto_ids": []}, headers=h)
    assert r.json()["defectos"] == []
    # El resultado se valida completo: el costo no puede quedar arriba del precio nuevo.
    r = client.patch(f"/productos/{p['id']}", json={"precio_usd": 500}, headers=h)
    assert _errores(r)["costo_usd"] == "El costo no puede ser mayor al precio de venta."
    # Su propio IMEI no cuenta como repetido.
    assert (
        client.patch(f"/productos/{p['id']}", json={"imei": IMEI_1}, headers=h).status_code == 200
    )


def test_cambiar_a_un_modelo_de_otro_tipo(client, admin, datos):
    p = _crear(client, admin, _iphone(datos)).json()
    h = auth_header(admin)
    r = client.patch(f"/productos/{p['id']}", json={"modelo_id": datos.airpods_pro}, headers=h)
    assert r.status_code == 422  # todavía tiene IMEI, color y capacidad de iPhone
    r = client.patch(
        f"/productos/{p['id']}",
        json={
            "modelo_id": datos.airpods_pro,
            "imei": None,
            "bateria": None,
            "color_id": None,
            "capacidad_id": None,
        },
        headers=h,
    )
    assert r.status_code == 200, r.text
    assert r.json()["categoria"]["nombre"] == "AirPods"


def test_obligatorios_no_se_borran_al_editar(client, admin, datos):
    p = _crear(client, admin, _iphone(datos)).json()
    r = client.patch(f"/productos/{p['id']}", json={"precio_usd": None}, headers=auth_header(admin))
    assert _errores(r)["precio_usd"] == "Este campo es obligatorio."


def test_borrar(client, admin, datos):
    p = _crear(client, admin, _iphone(datos, defecto_ids=[datos.defecto_comun])).json()
    h = auth_header(admin)
    assert client.delete(f"/productos/{p['id']}", headers=h).status_code == 204
    assert client.get(f"/productos/{p['id']}", headers=h).status_code == 404
    # El IMEI queda libre.
    assert _crear(client, admin, _iphone(datos)).status_code == 201


def test_reservado_o_vendido_no_se_edita_ni_borra(client, admin, datos, session):
    pid = _crear(client, admin, _iphone(datos)).json()["id"]
    producto = session.get(Producto, pid)
    producto.reservar()
    session.add(producto)
    session.commit()
    h = auth_header(admin)
    r = client.patch(f"/productos/{pid}", json={"precio_usd": 900}, headers=h)
    assert r.status_code == 409
    assert "reservado" in r.json()["detail"]
    assert client.delete(f"/productos/{pid}", headers=h).status_code == 409
    assert client.get(f"/productos/{pid}", headers=h).json()["editable"] is False


def test_no_existe_404(client, admin, datos):
    h = auth_header(admin)
    assert client.get("/productos/999", headers=h).status_code == 404
    assert client.patch("/productos/999", json={}, headers=h).status_code == 404
    assert client.delete("/productos/999", headers=h).status_code == 404


# ─── Listado ─────────────────────────────────────────────────────────────────
def test_filtros_y_paginas(client, admin, datos, session):
    _crear(client, admin, _iphone(datos))
    _crear(client, admin, _iphone(datos, imei=IMEI_2, condicion="nuevo"))
    base = {"proveedor_id": datos.proveedor, "condicion": "nuevo", "precio_usd": 15}
    _crear(client, admin, {**base, "modelo_id": datos.cargador, "cantidad": 4})
    h = auth_header(admin)

    def ids(**params) -> list[int]:
        r = client.get("/productos", params=params, headers=h)
        assert r.status_code == 200, r.text
        return [p["id"] for p in r.json()["items"]]

    assert len(ids()) == 3
    assert len(ids(categoria_id=datos.iphone)) == 2
    assert len(ids(condicion="nuevo")) == 2
    assert len(ids(buscar=IMEI_2[3:9])) == 1
    assert len(ids(buscar="usb-c")) == 1
    assert len(ids(modelo_id=datos.iphone_15)) == 2
    todos = ids()
    assert todos == sorted(todos, reverse=True)  # los últimos cargados, primero

    session.get(Producto, todos[0]).vender()
    session.commit()
    assert len(ids(estado="disponible")) == 2
    assert len(ids(estado="vendido")) == 1

    r = client.get("/productos", params={"tamanio": 2, "pagina": 2}, headers=h).json()
    assert r["total"] == 3 and len(r["items"]) == 1


# ─── Resumen y catálogos ─────────────────────────────────────────────────────
def test_resumen_cuenta_unidades_disponibles_y_nuevas(client, admin, vendedor, datos, session):
    _crear(client, admin, _iphone(datos))  # usado
    base = {"proveedor_id": datos.proveedor, "condicion": "nuevo", "precio_usd": 15}
    _crear(client, admin, {**base, "modelo_id": datos.cargador, "cantidad": 4})
    vendido = _crear(client, admin, {**base, "modelo_id": datos.airpods_pro}).json()["id"]
    session.get(Producto, vendido).vender()
    session.commit()
    for usuario in (admin, vendedor):
        stock = client.get("/resumen", headers=auth_header(usuario)).json()["stock"]
        assert stock == {"disponibles": 5, "nuevas": 4}


def test_con_productos_no_cambia_lo_que_lleva_el_tipo(client, admin, datos, session):
    h = auth_header(admin)
    tipo_id = session.get(Categoria, datos.iphone).tipo_categoria_id
    sin_imei = session.exec(
        select(TipoCategoria).where(TipoCategoria.nombre == "Equipo sin IMEI")
    ).one()
    # Sin productos, se puede.
    r = client.patch(
        f"/catalogos/tipos-categoria/{tipo_id}", json={"usa_bateria": False}, headers=h
    )
    assert r.status_code == 200
    client.patch(f"/catalogos/tipos-categoria/{tipo_id}", json={"usa_bateria": True}, headers=h)

    _crear(client, admin, _iphone(datos))
    r = client.patch(f"/catalogos/tipos-categoria/{tipo_id}", json={"usa_imei": False}, headers=h)
    assert r.status_code == 422
    assert _errores(r)["usa_imei"].startswith(
        "No se puede cambiar qué datos lleva: ya hay 1 producto cargado de este tipo."
    )
    # El nombre sí, y mandar el mismo valor no es un cambio.
    r = client.patch(
        f"/catalogos/tipos-categoria/{tipo_id}",
        json={"nombre": "Con IMEI", "usa_imei": True},
        headers=h,
    )
    assert r.status_code == 200
    r = client.patch(
        f"/catalogos/categorias/{datos.iphone}", json={"tipo_categoria_id": sin_imei.id}, headers=h
    )
    assert _errores(r)["tipo_categoria_id"] == (
        "No se puede cambiar el tipo: ya hay 1 producto cargado en esta categoría."
    )


def test_un_modelo_con_productos_no_se_borra(client, admin, datos):
    _crear(client, admin, _iphone(datos))
    r = client.delete(f"/catalogos/modelos/{datos.iphone_15}", headers=auth_header(admin))
    assert r.status_code == 409
