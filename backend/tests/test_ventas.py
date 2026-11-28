"""API de ventas: cotizar, registrar (con regalos y canje), historial por rol y borrar."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlmodel import Session, select

from app.common.enums import Condicion, EstadoProductoEnum
from app.modules.catalogos.models import Categoria, Modelo, Proveedor
from app.modules.catalogos.semilla import sembrar_catalogos
from app.modules.clientes.models import Cliente
from app.modules.productos.models import Producto
from app.modules.vendedores.models import Vendedor
from app.modules.ventas.models import Venta
from tests.conftest import auth_header
from tests.test_productos import IMEI_1, IMEI_2


@dataclass
class Datos:
    cliente: int
    iphone_15: int  # modelo
    iphone: int  # productos
    iphone_reservado: int
    cable_x5: int
    sin_costo: int


@pytest.fixture
def datos(session: Session) -> Datos:
    sembrar_catalogos(session)
    cat = {c.nombre: c.id for c in session.exec(select(Categoria)).all()}
    proveedor = session.exec(select(Proveedor).where(Proveedor.nombre != "Plan canje")).first()

    def agregar(entidad):
        session.add(entidad)
        session.flush()
        return entidad.id

    iphone_15 = agregar(Modelo(categoria_id=cat["iPhone"], nombre="iPhone 15"))
    cable = agregar(Modelo(categoria_id=cat["Cable"], nombre="USB-C 1 m"))

    def producto(modelo, precio, costo, cantidad=1, imei=None, estado="disponible"):
        return agregar(
            Producto(
                modelo_id=modelo,
                proveedor_id=proveedor.id,
                condicion=Condicion.nuevo,
                imei=imei,
                cantidad=cantidad,
                precio_usd=Decimal(precio),
                costo_usd=None if costo is None else Decimal(costo),
                estado=EstadoProductoEnum(estado),
            )
        )

    d = Datos(
        cliente=agregar(Cliente(nombre="Juan Pérez")),
        iphone_15=iphone_15,
        iphone=producto(iphone_15, "1000", "700", imei=IMEI_1),
        iphone_reservado=producto(iphone_15, "900", "600", estado="reservado"),
        cable_x5=producto(cable, "10", "4", cantidad=5),
        sin_costo=producto(cable, "20", None),
    )
    agregar(Vendedor(numero=7, nombre="Ana"))
    session.commit()
    return d


@pytest.fixture
def tc(client, admin):
    client.put("/tipo-cambio/hoy", json={"valor_ars": 1000}, headers=auth_header(admin))


def item(producto_id, precio, cantidad=1, es_regalo=False):
    return {
        "producto_id": producto_id,
        "precio_usd": precio,
        "cantidad": cantidad,
        "es_regalo": es_regalo,
    }


def venta(d: Datos, items, **extra):
    return {"cliente_id": d.cliente, "items": items, **extra}


def vender(client, usuario, body):
    return client.post("/ventas", json=body, headers=auth_header(usuario))


def errores(r) -> dict[str, str]:
    return {".".join(str(p) for p in e["loc"][1:]): e["msg"] for e in r.json()["detail"]}


def canje(d: Datos, **extra):
    return {"modelo_id": d.iphone_15, "condicion": "usado", **extra}


# ─── Cotizar ─────────────────────────────────────────────────────────────────
def test_cotizar_por_rol(client, admin, vendedor, datos, tc):
    body = {
        "items": [
            item(datos.iphone, "650"),  # bajo costo (700)
            item(datos.cable_x5, "10", cantidad=2),
            item(datos.cable_x5, "10", es_regalo=True),  # cuenta 0
        ],
        "canje_valor_usd": "200",
    }
    r = client.post("/ventas/cotizar", json=body, headers=auth_header(admin))
    assert r.status_code == 200, r.json()
    assert r.json() == {
        "total_usd": "670",
        "total_ars": "670000.00",
        "canje_usd": "200",
        "anticipo_usd": "0",
        "saldo_usd": "470",
        "saldo_ars": "470000.00",
        "cuotas": [],
        "costo_usd": "712.00",
        "ganancia_usd": "-42.00",
        "margen_pct": "-5.9",
        "bajo_costo": [0],
    }

    r = client.post("/ventas/cotizar", json=body, headers=auth_header(vendedor))
    assert set(r.json()) == {
        "total_usd",
        "total_ars",
        "canje_usd",
        "anticipo_usd",
        "saldo_usd",
        "saldo_ars",
        "cuotas",
    }


def test_cotizar_sin_tc_no_tiene_pesos(client, vendedor, datos):
    r = client.post(
        "/ventas/cotizar",
        json={"items": [item(datos.iphone, "1000")]},
        headers=auth_header(vendedor),
    )
    assert r.json()["total_ars"] is None


@pytest.mark.parametrize(
    ("body", "campo", "mensaje"),
    [
        ({"items": []}, "items", "Agregá al menos un producto."),
        (
            {"items": [{"producto_id": 1, "precio_usd": "10"}], "canje_valor_usd": "2000"},
            "canje_valor_usd",
            "El valor del canje tiene que ser menor al total de la venta.",
        ),
        (
            {"items": [{"producto_id": 1, "precio_usd": "10"}], "modalidad": "cuotas"},
            "cantidad_cuotas",
            "Elegí en cuántas cuotas.",
        ),
    ],
)
def test_cotizar_rechaza(client, vendedor, datos, body, campo, mensaje):
    if body["items"]:
        body["items"][0]["producto_id"] = datos.iphone
    r = client.post("/ventas/cotizar", json=body, headers=auth_header(vendedor))
    assert r.status_code == 422
    assert errores(r)[campo] == mensaje


def test_stock_del_carrito(client, vendedor, datos):
    def cotizar(*items):
        return client.post(
            "/ventas/cotizar", json={"items": list(items)}, headers=auth_header(vendedor)
        )

    r = cotizar(item(datos.iphone_reservado, "900"))
    assert errores(r) == {
        "items.0.producto_id": f"El producto #{datos.iphone_reservado} está reservado."
    }
    r = cotizar(item(datos.iphone, "1000"), item(datos.iphone, "0", es_regalo=True))
    assert errores(r) == {"items.1.cantidad": f"Del producto #{datos.iphone} hay una sola unidad."}
    # Con precio y de regalo suman: 4 + 2 > 5.
    r = cotizar(item(datos.cable_x5, "10", cantidad=4), item(datos.cable_x5, "0", 2, True))
    assert errores(r) == {"items.1.cantidad": f"Del producto #{datos.cable_x5} hay 5 unidades."}
    r = cotizar(item(999, "10"))
    assert errores(r) == {"items.0.producto_id": "El producto #999 no existe."}


# ─── Registrar ───────────────────────────────────────────────────────────────
def test_sin_tc_no_se_vende(client, vendedor, datos, session):
    r = vender(client, vendedor, venta(datos, [item(datos.iphone, "1000")]))
    assert r.status_code == 422
    assert r.json()["detail"] == (
        "Falta cargar el tipo de cambio de hoy: sin TC no se registra la venta."
    )
    assert session.exec(select(Venta)).all() == []


def test_vender_actualiza_el_stock_y_congela_el_tc(client, admin, datos, tc, session):
    r = vender(
        client,
        admin,
        venta(
            datos,
            [
                item(datos.iphone, "950"),
                item(datos.cable_x5, "12", cantidad=2),
                item(datos.cable_x5, "12", es_regalo=True),
            ],
            garantia_meses=6,
        ),
    )
    assert r.status_code == 201, r.json()
    v = r.json()
    assert v["tc_ars"] == "1000.00"
    assert v["garantia_meses"] == 6
    assert v["usuario"]["nombre"] == "admin"
    assert v["cliente"] == {"id": datos.cliente, "nombre": "Juan Pérez"}
    assert v["metodo_pago"]["nombre"] == "Transferencia"  # el predeterminado
    assert (v["total_usd"], v["total_ars"], v["saldo_usd"]) == ("974.00", "974000.00", "974.00")
    assert v["costo_usd"] == "712.00"  # 700 + 3 × 4, regalo incluido
    assert v["ganancia_usd"] == "262.00"
    regalo = v["items"][2]
    assert (regalo["precio_usd"], regalo["es_regalo"], regalo["costo_usd"]) == (
        "0.00",
        True,
        "4.00",
    )
    assert v["items"][0]["producto"]["imei"] == IMEI_1

    session.expire_all()
    iphone = session.get(Producto, datos.iphone)
    cable = session.get(Producto, datos.cable_x5)
    assert iphone.estado == EstadoProductoEnum.vendido
    assert (cable.estado, cable.cantidad) == (EstadoProductoEnum.disponible, 2)

    # El TC de hoy se corrige: la venta ya hecha no cambia.
    client.put("/tipo-cambio/hoy", json={"valor_ars": 1200}, headers=auth_header(admin))
    v = client.get("/ventas", headers=auth_header(admin)).json()["items"][0]
    assert v["total_ars"] == "974000.00"


def test_el_vendedor_no_ve_costos(client, vendedor, datos, tc):
    r = vender(client, vendedor, venta(datos, [item(datos.iphone, "1000")]))
    assert r.status_code == 201
    v = r.json()
    assert not {"costo_usd", "ganancia_usd", "margen_pct"} & set(v)
    assert not {"costo_usd", "bajo_costo"} & set(v["items"][0])


def test_cliente_y_metodo_de_pago(client, vendedor, datos, tc):
    r = vender(client, vendedor, {"items": [item(datos.iphone, "1000")]})
    assert errores(r) == {"cliente_id": "Este campo es obligatorio."}
    r = vender(client, vendedor, venta(datos, [item(datos.iphone, "1000")], metodo_pago_id=99))
    assert errores(r) == {"metodo_pago_id": "Elegí un método de pago."}
    r = vender(client, vendedor, venta(datos, [item(datos.iphone, "1000")], metodo_pago_id=4))
    assert r.json()["metodo_pago"]["nombre"] == "Efectivo"


def test_vendedor_por_numero(client, vendedor, datos, tc):
    r = vender(client, vendedor, venta(datos, [item(datos.iphone, "1000")], vendedor_numero=8))
    assert errores(r) == {"vendedor_numero": "Vendedor no registrado."}
    r = vender(client, vendedor, venta(datos, [item(datos.iphone, "1000")], vendedor_numero=7))
    assert r.json()["vendedor"]["nombre"] == "Ana"


def test_canje_entra_al_stock(client, admin, datos, tc, session):
    r = vender(
        client,
        admin,
        venta(
            datos,
            [item(datos.iphone, "1000")],
            canje_valor_usd="300",
            canje=canje(datos, bateria=82),  # sin IMEI: es opcional
        ),
    )
    assert r.status_code == 201, r.json()
    v = r.json()
    assert v["saldo_usd"] == "700.00"
    assert v["canje"]["valor_usd"] == "300.00"
    entregado = session.get(Producto, v["canje"]["producto"]["id"])
    assert entregado.estado == EstadoProductoEnum.disponible
    assert (entregado.precio_usd, entregado.costo_usd) == (Decimal(300), Decimal(300))
    assert entregado.proveedor.nombre == "Plan canje"
    assert (entregado.condicion, entregado.bateria) == (Condicion.usado, 82)


def test_canje_invalido_no_graba_nada(client, admin, datos, tc, session):
    # El IMEI del canje ya está en el stock: el iPhone que se vende todavía no salió.
    body = venta(
        datos,
        [item(datos.iphone, "1000")],
        canje_valor_usd="300",
        canje=canje(datos, imei=IMEI_1),
    )
    r = vender(client, admin, body)
    assert errores(r) == {"canje.imei": f"Ese IMEI ya está en el stock: producto #{datos.iphone}."}
    assert session.exec(select(Venta)).all() == []

    r = vender(client, admin, venta(datos, [item(datos.iphone, "1000")], canje_valor_usd="300"))
    assert errores(r) == {"canje": "Faltan los datos del equipo que entrega el cliente."}
    r = vender(client, admin, venta(datos, [item(datos.iphone, "1000")], canje=canje(datos)))
    assert errores(r) == {"canje_valor_usd": "Cargá el valor del canje."}


def test_si_falla_un_paso_no_queda_nada(client, admin, datos, tc, session, monkeypatch):
    original = Producto.vender

    def falla_con_el_cable(self, cantidad=1):
        if self.id == datos.cable_x5:
            raise RuntimeError("falla a mitad de la venta")
        original(self, cantidad)

    monkeypatch.setattr(Producto, "vender", falla_con_el_cable)
    body = venta(
        datos,
        [item(datos.iphone, "1000"), item(datos.cable_x5, "10")],
        canje_valor_usd="300",
        canje=canje(datos, imei=IMEI_2),
    )
    with pytest.raises(RuntimeError):
        vender(client, admin, body)

    session.expire_all()
    assert session.exec(select(Venta)).all() == []
    assert session.get(Producto, datos.iphone).estado == EstadoProductoEnum.disponible
    assert session.exec(select(Producto).where(Producto.imei == IMEI_2)).all() == []


# ─── Historial ───────────────────────────────────────────────────────────────
def test_historial_por_rol(client, admin, vendedor, datos, tc):
    vender(client, admin, venta(datos, [item(datos.iphone, "1000")]))
    vender(client, vendedor, venta(datos, [item(datos.sin_costo, "20")]))

    r = client.get("/ventas", headers=auth_header(vendedor)).json()
    assert [v["usuario"]["nombre"] for v in r["items"]] == ["vendedor"]  # solo las suyas
    assert "ganancia_total_usd" not in r

    r = client.get("/ventas", headers=auth_header(admin)).json()
    assert r["total"] == 2
    assert [v["ganancia_usd"] for v in r["items"]] == [None, "300.00"]  # las últimas primero
    assert r["ganancia_total_usd"] == "300.00"  # solo las ventas con costo


# ─── Borrar ──────────────────────────────────────────────────────────────────
def test_borrar_devuelve_el_stock_y_saca_el_canje(client, admin, vendedor, datos, tc, session):
    v = vender(
        client,
        admin,
        venta(
            datos,
            [item(datos.iphone, "1000"), item(datos.cable_x5, "10", cantidad=5)],
            canje_valor_usd="300",
            canje=canje(datos),
        ),
    ).json()
    # El cable se vendió entero: sigue disponible, sin stock.
    cable = session.get(Producto, datos.cable_x5)
    assert (cable.estado, cable.cantidad) == (EstadoProductoEnum.disponible, 0)
    url = f"/ventas/{v['id']}"
    assert client.delete(url, headers=auth_header(vendedor)).status_code == 403

    assert client.delete(url, headers=auth_header(admin)).status_code == 204
    session.expire_all()
    assert session.get(Producto, datos.iphone).estado == EstadoProductoEnum.disponible
    cable = session.get(Producto, datos.cable_x5)
    assert (cable.estado, cable.cantidad) == (EstadoProductoEnum.disponible, 5)
    assert session.get(Producto, v["canje"]["producto"]["id"]) is None
    assert session.exec(select(Venta)).all() == []


def test_no_se_borra_si_el_canje_ya_se_vendio(client, admin, datos, tc):
    v = vender(
        client,
        admin,
        venta(datos, [item(datos.iphone, "1000")], canje_valor_usd="300", canje=canje(datos)),
    ).json()
    entregado = v["canje"]["producto"]["id"]
    vender(client, admin, venta(datos, [item(entregado, "400")]))

    r = client.delete(f"/ventas/{v['id']}", headers=auth_header(admin))
    assert r.status_code == 409
    assert r.json()["detail"] == (
        f"No se puede borrar la venta: el equipo que entró por canje (producto #{entregado}) "
        "ya está vendido."
    )


def test_no_se_borra_si_el_equipo_volvio_con_el_mismo_imei(client, admin, datos, tc):
    primera = vender(client, admin, venta(datos, [item(datos.iphone, "1000")])).json()
    # El mismo iPhone vuelve por canje en otra venta.
    segunda = vender(
        client,
        admin,
        venta(
            datos,
            [item(datos.cable_x5, "10")],
            canje_valor_usd="5",
            canje=canje(datos, imei=IMEI_1),
        ),
    ).json()
    r = client.delete(f"/ventas/{primera['id']}", headers=auth_header(admin))
    assert r.status_code == 409
    assert r.json()["detail"] == (
        f"No se puede borrar la venta: el iPhone 15 #{datos.iphone} volvió a entrar con el "
        f"mismo IMEI (producto #{segunda['canje']['producto']['id']})."
    )


def test_no_se_borra_si_el_equipo_volvio_y_se_revendio(client, admin, datos, tc, session):
    primera = vender(client, admin, venta(datos, [item(datos.iphone, "1000")])).json()
    segunda = vender(
        client,
        admin,
        venta(
            datos,
            [item(datos.cable_x5, "10")],
            canje_valor_usd="5",
            canje=canje(datos, imei=IMEI_1),
        ),
    ).json()
    vuelto = segunda["canje"]["producto"]["id"]
    # El equipo que volvió se vende otra vez: ya no está en el stock, pero lo tiene otro
    # cliente, así que el de la primera venta no puede volver a estar disponible.
    assert vender(client, admin, venta(datos, [item(vuelto, "900")])).status_code == 201

    r = client.delete(f"/ventas/{primera['id']}", headers=auth_header(admin))
    assert r.status_code == 409
    assert f"(producto #{vuelto})" in r.json()["detail"]
    session.expire_all()
    assert session.get(Producto, datos.iphone).estado == EstadoProductoEnum.vendido


def test_un_accesorio_no_entra_por_canje(client, admin, datos, tc, session):
    cable = session.exec(select(Modelo).where(Modelo.nombre == "USB-C 1 m")).one()
    r = vender(
        client,
        admin,
        venta(
            datos,
            [item(datos.iphone, "1000")],
            canje_valor_usd="5",
            canje={"modelo_id": cable.id, "condicion": "usado"},
        ),
    )
    assert errores(r) == {"canje.modelo_id": "Cable no se toma en canje: solo equipos y consolas."}
    assert session.exec(select(Venta)).all() == []


def test_un_producto_con_ventas_no_se_borra(client, admin, datos, tc):
    vender(client, admin, venta(datos, [item(datos.cable_x5, "10", cantidad=2)]))
    r = client.delete(f"/productos/{datos.cable_x5}", headers=auth_header(admin))
    assert r.status_code == 409
    assert r.json()["detail"] == (
        "Tiene ventas: no se puede borrar. Para sacarlo del stock, poné la cantidad en 0."
    )


# ─── Resumen ─────────────────────────────────────────────────────────────────
def test_resumen_de_ventas(client, admin, vendedor, datos, tc, session):
    vender(client, admin, venta(datos, [item(datos.iphone, "1000")]))
    vender(client, admin, venta(datos, [item(datos.cable_x5, "10", cantidad=2)]))
    vieja = vender(client, admin, venta(datos, [item(datos.sin_costo, "20")])).json()
    # Una de hace 3 días y otra de hace 8: la segunda queda afuera de los 7 días.
    original = session.get(Venta, vieja["id"])
    original.fecha = datetime.now(UTC) - timedelta(days=3)
    session.add(
        Venta(
            **original.model_dump(exclude={"id", "fecha"}), fecha=original.fecha - timedelta(days=5)
        )
    )
    session.commit()

    ventas = client.get("/resumen", headers=auth_header(admin)).json()["ventas"]
    assert ventas == {
        "hoy": {"cantidad": 2, "total_usd": "1020.00", "total_ars": "1020000.00"},
        "ultimos_7_dias": {"cantidad": 3, "total_usd": "1040.00", "total_ars": "1040000.00"},
        "solo_propias": False,
    }

    # El Vendedor ve solo las que registró él, igual que en el historial.
    vender(client, vendedor, venta(datos, [item(datos.cable_x5, "10")]))
    ventas = client.get("/resumen", headers=auth_header(vendedor)).json()["ventas"]
    assert ventas == {
        "hoy": {"cantidad": 1, "total_usd": "10.00", "total_ars": "10000.00"},
        "ultimos_7_dias": {"cantidad": 1, "total_usd": "10.00", "total_ars": "10000.00"},
        "solo_propias": True,
    }
