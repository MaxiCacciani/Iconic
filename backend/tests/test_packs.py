"""API de packs: ABM del Administrador, validación de los ítems y aplicar un pack."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session, select

from app.common.enums import Condicion, EstadoProductoEnum
from app.core import reloj
from app.modules.catalogos.models import Categoria, Modelo, Proveedor
from app.modules.catalogos.semilla import sembrar_catalogos
from app.modules.productos.models import Producto
from tests.conftest import auth_header


@pytest.fixture(autouse=True)
def hoy_fijo(monkeypatch):
    monkeypatch.setattr(reloj, "hoy", lambda: date(2026, 11, 21))


@dataclass
class Stock:
    iphone: int  # categoría
    cable: int  # categoría (por cantidad)
    funda: int  # categoría sin stock
    iphone_a: int  # productos
    iphone_b: int
    iphone_vendido: int
    iphone_reservado: int
    cable_x3: int
    cable_x5: int


@pytest.fixture
def stock(session: Session) -> Stock:
    sembrar_catalogos(session)
    cat = {c.nombre: c.id for c in session.exec(select(Categoria)).all()}
    proveedor = session.exec(select(Proveedor)).first().id

    def agregar(entidad):
        session.add(entidad)
        session.flush()
        return entidad.id

    iphone_15 = agregar(Modelo(categoria_id=cat["iPhone"], nombre="iPhone 15"))
    cable_usbc = agregar(Modelo(categoria_id=cat["Cable"], nombre="USB-C 1 m"))

    def producto(modelo, estado=EstadoProductoEnum.disponible, cantidad=1, precio="800"):
        return agregar(
            Producto(
                modelo_id=modelo,
                proveedor_id=proveedor,
                condicion=Condicion.nuevo,
                cantidad=cantidad,
                precio_usd=Decimal(precio),
                costo_usd=Decimal(precio) / 2,
                estado=estado,
            )
        )

    s = Stock(
        iphone=cat["iPhone"],
        cable=cat["Cable"],
        funda=cat["Funda/Case"],
        iphone_a=producto(iphone_15),
        iphone_b=producto(iphone_15),
        iphone_vendido=producto(iphone_15, EstadoProductoEnum.vendido),
        iphone_reservado=producto(iphone_15, EstadoProductoEnum.reservado),
        cable_x3=producto(cable_usbc, cantidad=3, precio="10"),
        cable_x5=producto(cable_usbc, cantidad=5, precio="10"),
    )
    session.commit()
    return s


def crear(client, usuario, **datos):
    return client.post("/packs", json=datos, headers=auth_header(usuario))


def aplicar(client, usuario, pack_id, en_carrito=None):
    body = {"en_carrito": en_carrito} if en_carrito is not None else None
    return client.post(f"/packs/{pack_id}/aplicar", json=body, headers=auth_header(usuario))


def errores(r) -> dict[str, str]:
    return {".".join(str(p) for p in e["loc"][1:]): e["msg"] for e in r.json()["detail"]}


def lineas(r) -> list[tuple[int, int, bool]]:
    return [(x["producto"]["id"], x["cantidad"], x["es_regalo"]) for x in r.json()["lineas"]]


# ─── ABM ─────────────────────────────────────────────────────────────────────
def test_alta_con_fijo_y_categoria(client, admin, stock):
    r = crear(
        client,
        admin,
        nombre=" Combo iPhone ",
        descripcion="",
        items=[
            {"categoria_id": stock.iphone},
            {"producto_id": stock.cable_x5, "cantidad": 2, "es_regalo": True},
        ],
    )
    assert r.status_code == 201, r.json()
    pack = r.json()
    assert pack["nombre"] == "Combo iPhone"
    assert pack["descripcion"] is None
    categoria, fijo = pack["items"]
    assert categoria["categoria"] == {"id": stock.iphone, "nombre": "iPhone"}
    assert categoria["producto"] is None
    assert categoria["unidades_disponibles"] == 2  # los vendidos y reservados no cuentan
    assert fijo["producto"]["id"] == stock.cable_x5
    assert fijo["producto"]["modelo"]["nombre"] == "USB-C 1 m"
    assert fijo["producto"]["categoria"]["nombre"] == "Cable"
    assert (fijo["cantidad"], fijo["es_regalo"], fijo["unidades_disponibles"]) == (2, True, 5)
    assert "precio_usd" not in fijo["producto"] and "costo_usd" not in fijo["producto"]


def test_item_es_producto_o_categoria(client, admin, stock):
    r = crear(
        client,
        admin,
        nombre="P",
        items=[{"producto_id": stock.cable_x3, "categoria_id": stock.cable}, {}],
    )
    assert r.status_code == 422
    assert errores(r) == {
        "items.0": "Elegí un producto o una categoría (uno de los dos).",
        "items.1": "Elegí un producto o una categoría (uno de los dos).",
    }


def test_pack_sin_items_y_nombre_obligatorio(client, admin, stock):
    r = crear(client, admin, nombre="  ", items=[])
    assert errores(r) == {
        "nombre": "Tiene que tener al menos 1 caracteres.",
        "items": "El pack tiene que tener al menos un producto o una categoría.",
    }


@pytest.mark.parametrize(
    "item,campo,mensaje",
    [
        ({"producto_id": 999}, "producto_id", "El producto #999 no existe."),
        ({"categoria_id": 999}, "categoria_id", "Esa categoría no existe."),
        (
            {"producto_id": "iphone_vendido"},
            "producto_id",
            "El producto #{id} ya se vendió.",
        ),
        (
            {"producto_id": "iphone_a", "cantidad": 2},
            "cantidad",
            "Es un equipo: va una sola unidad. Para sumar otro, agregá otro ítem.",
        ),
        ({"categoria_id": "iphone", "cantidad": 0}, "cantidad", "Tiene que ser 1 o más."),
    ],
)
def test_items_invalidos(client, admin, stock, item, campo, mensaje):
    item = {k: getattr(stock, v) if isinstance(v, str) else v for k, v in item.items()}
    r = crear(client, admin, nombre="P", items=[{"categoria_id": stock.cable}, item])
    assert r.status_code == 422
    id_ = item.get("producto_id")
    assert errores(r) == {f"items.1.{campo}": mensaje.format(id=id_)}


def test_la_cantidad_no_se_valida_contra_el_stock(client, admin, stock):
    """El pack dice qué trae; el stock se mira recién al aplicarlo."""
    r = crear(client, admin, nombre="P", items=[{"producto_id": stock.cable_x3, "cantidad": 4}])
    assert r.status_code == 201, r.text
    assert r.json()["items"][0]["unidades_disponibles"] == 3


def test_un_producto_fijo_no_se_repite(client, admin, stock):
    item = {"producto_id": stock.iphone_a}
    r = crear(client, admin, nombre="P", items=[item, item])
    assert errores(r) == {"items.1.producto_id": "Ese producto ya está en el pack."}


def test_nombre_unico_sin_mayusculas(client, admin, stock):
    crear(client, admin, nombre="Combo", items=[{"categoria_id": stock.cable}])
    r = crear(client, admin, nombre="COMBO", items=[{"categoria_id": stock.cable}])
    assert errores(r) == {"nombre": "Ya hay un pack con ese nombre."}


def test_editar_reemplaza_los_items(client, admin, stock, session):
    pack = crear(client, admin, nombre="Combo", items=[{"categoria_id": stock.iphone}]).json()
    h = auth_header(admin)
    r = client.patch(f"/packs/{pack['id']}", json={"descripcion": "Con regalo"}, headers=h)
    assert r.json()["descripcion"] == "Con regalo"
    assert len(r.json()["items"]) == 1  # sin `items`, quedan como estaban
    nuevos = [{"producto_id": stock.iphone_a}, {"categoria_id": stock.cable, "cantidad": 2}]
    r = client.patch(f"/packs/{pack['id']}", json={"items": nuevos}, headers=h)
    assert r.status_code == 200
    assert [
        (i["producto"] and i["producto"]["id"], i["categoria"] and i["categoria"]["id"])
        for i in r.json()["items"]
    ] == [(stock.iphone_a, None), (None, stock.cable)]
    # Su propio nombre no cuenta como repetido.
    assert (
        client.patch(f"/packs/{pack['id']}", json={"nombre": "combo"}, headers=h).status_code == 200
    )


def test_un_fijo_que_se_vendio_puede_quedar(client, admin, stock, session):
    pack = crear(client, admin, nombre="Combo", items=[{"producto_id": stock.iphone_a}]).json()
    session.get(Producto, stock.iphone_a).estado = EstadoProductoEnum.vendido
    session.commit()
    h = auth_header(admin)
    items = [{"producto_id": stock.iphone_a}, {"categoria_id": stock.cable}]
    r = client.patch(f"/packs/{pack['id']}", json={"items": items}, headers=h)
    assert r.status_code == 200
    assert r.json()["items"][0]["producto"]["estado"] == "vendido"
    assert r.json()["items"][0]["unidades_disponibles"] == 0


def test_borrar(client, admin, stock):
    pack = crear(client, admin, nombre="Combo", items=[{"categoria_id": stock.iphone}]).json()
    h = auth_header(admin)
    assert client.delete(f"/packs/{pack['id']}", headers=h).status_code == 204
    assert client.get("/packs", headers=h).json() == []
    assert client.get(f"/packs/{pack['id']}", headers=h).status_code == 404


def test_borrar_el_producto_lo_saca_del_pack(client, admin, stock):
    items = [{"producto_id": stock.iphone_a}, {"categoria_id": stock.cable}]
    pack = crear(client, admin, nombre="Combo", items=items).json()
    h = auth_header(admin)
    assert client.delete(f"/productos/{stock.iphone_a}", headers=h).status_code == 204
    restantes = client.get(f"/packs/{pack['id']}", headers=h).json()["items"]
    assert [i["categoria"]["id"] for i in restantes] == [stock.cable]


def test_lista_ordenada_por_nombre(client, admin, stock):
    for nombre in ("Zeta", "alfa", "Beta"):
        crear(client, admin, nombre=nombre, items=[{"categoria_id": stock.cable}])
    lista = client.get("/packs", headers=auth_header(admin)).json()
    assert [p["nombre"] for p in lista] == ["alfa", "Beta", "Zeta"]


def test_permisos(client, admin, vendedor, stock):
    assert client.get("/packs").status_code == 401
    pack = crear(client, admin, nombre="Combo", items=[{"categoria_id": stock.iphone}]).json()
    h = auth_header(vendedor)
    assert client.get("/packs", headers=h).status_code == 200
    assert aplicar(client, vendedor, pack["id"]).status_code == 200
    assert crear(client, vendedor, nombre="X", items=[{"categoria_id": 1}]).status_code == 403
    assert client.patch(f"/packs/{pack['id']}", json={}, headers=h).status_code == 403
    assert client.delete(f"/packs/{pack['id']}", headers=h).status_code == 403


# ─── Aplicar ─────────────────────────────────────────────────────────────────
def test_aplicar_no_repite_equipos(client, admin, stock):
    pack = crear(
        client,
        admin,
        nombre="Dos iPhone",
        items=[{"categoria_id": stock.iphone}, {"categoria_id": stock.iphone, "es_regalo": True}],
    ).json()
    r = aplicar(client, admin, pack["id"])
    assert r.status_code == 200
    # El más antiguo primero, y el segundo ítem se lleva otro equipo. Ni el vendido ni el
    # reservado entran.
    assert lineas(r) == [(stock.iphone_a, 1, False), (stock.iphone_b, 1, True)]
    assert r.json()["pack"] == {"id": pack["id"], "nombre": "Dos iPhone"}


def test_aplicar_el_fijo_va_aunque_la_categoria_venga_antes(client, admin, stock):
    items = [{"categoria_id": stock.iphone}, {"producto_id": stock.iphone_a}]
    pack = crear(client, admin, nombre="P", items=items).json()
    # La categoría no se lleva el iPhone A: lo pidió el fijo. Las líneas, en el orden del pack.
    assert lineas(aplicar(client, admin, pack["id"])) == [
        (stock.iphone_b, 1, False),
        (stock.iphone_a, 1, False),
    ]


def test_aplicar_descuenta_lo_del_carrito(client, admin, stock):
    pack = crear(client, admin, nombre="P", items=[{"categoria_id": stock.iphone}]).json()
    r = aplicar(client, admin, pack["id"], [{"producto_id": stock.iphone_a, "cantidad": 1}])
    assert lineas(r) == [(stock.iphone_b, 1, False)]


def test_aplicar_accesorios_por_cantidad(client, admin, stock):
    items = [{"categoria_id": stock.cable, "cantidad": 4, "es_regalo": True}]
    pack = crear(client, admin, nombre="P", items=items).json()
    # 3 de la primera fila y 1 de la segunda.
    assert lineas(aplicar(client, admin, pack["id"])) == [
        (stock.cable_x3, 3, True),
        (stock.cable_x5, 1, True),
    ]
    # Con 2 de la primera ya en el carrito: 1 de esa y 3 de la otra.
    r = aplicar(client, admin, pack["id"], [{"producto_id": stock.cable_x3, "cantidad": 2}])
    assert lineas(r) == [(stock.cable_x3, 1, True), (stock.cable_x5, 3, True)]


def sin_stock(r) -> str:
    assert r.status_code == 409, r.text
    return r.json()["detail"]


def test_aplicar_sin_stock_no_agrega_nada(client, admin, stock, session):
    items = [
        {"categoria_id": stock.cable},
        {"producto_id": stock.iphone_a},
        {"producto_id": stock.iphone_b},
        {"categoria_id": stock.funda},
        {"categoria_id": stock.funda, "es_regalo": True},
    ]
    pack = crear(client, admin, nombre="P", items=items).json()
    session.get(Producto, stock.iphone_a).estado = EstadoProductoEnum.vendido
    session.get(Producto, stock.iphone_b).estado = EstadoProductoEnum.reservado
    session.commit()

    # El cable hay, pero el pack no va a medias. La categoría repetida se nombra una vez.
    assert sin_stock(aplicar(client, admin, pack["id"])) == (
        "No se pudo agregar el pack por falta de stock de "
        f"iPhone 15 #{stock.iphone_a}, iPhone 15 #{stock.iphone_b} y Funda/Case."
    )


def test_aplicar_sin_unidades_suficientes(client, admin, stock):
    items = [{"producto_id": stock.cable_x3, "cantidad": 3}]
    pack = crear(client, admin, nombre="P", items=items).json()
    r = aplicar(client, admin, pack["id"], [{"producto_id": stock.cable_x3, "cantidad": 1}])
    assert sin_stock(r) == (
        f"No se pudo agregar el pack por falta de stock de USB-C 1 m #{stock.cable_x3}."
    )
    # Con la categoría: hay 8 cables, se piden 9.
    pack = crear(client, admin, nombre="Q", items=[{"categoria_id": stock.cable, "cantidad": 9}])
    assert sin_stock(aplicar(client, admin, pack.json()["id"])) == (
        "No se pudo agregar el pack por falta de stock de Cable."
    )


def test_aplicar_fijo_que_ya_esta_en_el_carrito(client, admin, stock):
    pack = crear(client, admin, nombre="P", items=[{"producto_id": stock.iphone_a}]).json()
    r = aplicar(client, admin, pack["id"], [{"producto_id": stock.iphone_a}])
    assert sin_stock(r) == (
        f"No se pudo agregar el pack por falta de stock de iPhone 15 #{stock.iphone_a}."
    )


def test_aplicar_por_rol(client, admin, vendedor, stock):
    pack = crear(client, admin, nombre="P", items=[{"categoria_id": stock.iphone}]).json()
    del_admin = aplicar(client, admin, pack["id"]).json()["lineas"][0]["producto"]
    del_vendedor = aplicar(client, vendedor, pack["id"]).json()["lineas"][0]["producto"]
    assert del_admin["costo_usd"] == "400.00"
    assert del_vendedor["precio_usd"] == "800.00"
    for campo in ("costo_usd", "costo_ars", "ganancia_usd", "ganancia_ars", "margen_pct"):
        assert campo not in del_vendedor


def test_aplicar_con_tc_trae_pesos(client, admin, stock):
    client.put("/tipo-cambio/hoy", json={"valor_ars": 1200}, headers=auth_header(admin))
    pack = crear(client, admin, nombre="P", items=[{"categoria_id": stock.iphone}]).json()
    producto = aplicar(client, admin, pack["id"]).json()["lineas"][0]["producto"]
    assert Decimal(producto["precio_ars"]) == Decimal("960000")


def test_aplicar_pack_inexistente(client, admin):
    assert aplicar(client, admin, 999).status_code == 404
