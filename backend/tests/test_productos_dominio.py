"""Funciones puras y State de productos: sin base ni API."""

from decimal import Decimal

import pytest

from app.common.enums import EstadoProductoEnum as E
from app.common.enums import NivelBateria
from app.core.excepciones import TransicionInvalida
from app.modules.productos import dominio
from app.modules.productos.estados import estado_de


# ─── Batería ─────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "bateria,nivel",
    [
        (100, NivelBateria.alta),
        (85, NivelBateria.alta),
        (84, NivelBateria.media),
        (80, NivelBateria.media),
        (79, NivelBateria.baja),
        (1, NivelBateria.baja),
        (None, None),
    ],
)
def test_nivel_bateria_por_intervalos(bateria, nivel):
    assert dominio.nivel_bateria(bateria) == nivel


# ─── Ganancia y margen ───────────────────────────────────────────────────────
def test_ganancia_y_margen():
    assert dominio.ganancia(Decimal("1000"), Decimal("800")) == Decimal("200")
    assert dominio.margen_pct(Decimal("1000"), Decimal("800")) == Decimal("25.0")
    assert dominio.margen_pct(Decimal("100"), Decimal("30")) == Decimal("233.3")


def test_sin_costo_no_hay_ganancia_ni_margen():
    assert dominio.ganancia(Decimal("1000"), None) is None
    assert dominio.margen_pct(Decimal("1000"), None) is None


def test_costo_cero_tiene_ganancia_pero_no_margen():
    # El margen divide por el costo.
    assert dominio.ganancia(Decimal("50"), Decimal("0")) == Decimal("50")
    assert dominio.margen_pct(Decimal("50"), Decimal("0")) is None


def test_en_pesos_redondea_a_centavos():
    assert dominio.en_pesos(Decimal("10.01"), Decimal("1180.55")) == Decimal("11817.31")
    assert dominio.en_pesos(Decimal("10"), None) is None
    assert dominio.en_pesos(None, Decimal("1180")) is None


# ─── State ───────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "desde,accion,hasta",
    [
        (E.disponible, "reservar", E.reservado),
        (E.disponible, "vender", E.vendido),
        (E.reservado, "liberar", E.disponible),
        (E.reservado, "vender", E.vendido),
        (E.vendido, "devolver", E.disponible),
    ],
)
def test_transiciones_permitidas(desde, accion, hasta):
    assert getattr(estado_de(desde), accion)() == hasta


@pytest.mark.parametrize(
    "desde,accion",
    [
        (E.disponible, "liberar"),
        (E.disponible, "devolver"),
        (E.reservado, "reservar"),
        (E.reservado, "devolver"),
        (E.vendido, "reservar"),
        (E.vendido, "vender"),
        (E.vendido, "liberar"),
    ],
)
def test_transiciones_no_permitidas(desde, accion):
    with pytest.raises(TransicionInvalida):
        getattr(estado_de(desde), accion)()


def test_solo_se_edita_y_borra_lo_disponible():
    estado_de(E.disponible).editar()
    estado_de(E.disponible).eliminar()
    for estado in (E.reservado, E.vendido):
        with pytest.raises(TransicionInvalida):
            estado_de(estado).editar()
        with pytest.raises(TransicionInvalida):
            estado_de(estado).eliminar()


def test_el_producto_delega_en_su_estado():
    from app.modules.catalogos.models import Categoria, Modelo, TipoCategoria
    from app.modules.productos.models import Producto

    equipo = Categoria(nombre="iPhone", tipo=TipoCategoria(nombre="Equipo con IMEI"))
    modelo = Modelo(nombre="iPhone 15", categoria=equipo)
    p = Producto(modelo=modelo, proveedor_id=1, condicion="nuevo", precio_usd=Decimal("10"))
    assert p.estado == E.disponible
    p.reservar()
    assert p.estado == E.reservado
    with pytest.raises(TransicionInvalida):
        p.reservar()
    p.liberar()
    p.vender()
    assert p.estado == E.vendido
    p.devolver()
    assert p.estado == E.disponible
