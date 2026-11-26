"""Funciones puras de ventas, la Strategy `Contado` y el stock al vender y devolver."""

from dataclasses import dataclass
from decimal import Decimal

import pytest

from app.common.enums import Condicion, EstadoProductoEnum, Modalidad
from app.core.excepciones import ErrorDeCampo, TransicionInvalida
from app.modules.productos.models import Producto
from app.modules.ventas import dominio
from app.modules.ventas.modalidades import Contado, modalidad_de


@dataclass
class L:
    precio_usd: Decimal
    costo_usd: Decimal | None
    cantidad: int = 1
    es_regalo: bool = False


def D(x) -> Decimal:
    return Decimal(str(x))


def test_total_sin_regalos_y_costo_con_regalos():
    lineas = [L(D(800), D(600)), L(D(10), D(4), cantidad=3), L(D(0), D(5), es_regalo=True)]
    assert dominio.total(lineas) == D(830)
    assert dominio.costo(lineas) == D(617)


def test_sin_costo_en_un_item_la_venta_no_tiene_costo():
    assert dominio.costo([L(D(800), D(600)), L(D(10), None)]) is None


def test_bajo_costo():
    assert dominio.bajo_costo(L(D(500), D(600)))
    assert not dominio.bajo_costo(L(D(600), D(600)))
    assert not dominio.bajo_costo(L(D(500), None))
    assert not dominio.bajo_costo(L(D(0), D(5), es_regalo=True))


def test_contado_el_canje_no_cubre_el_total():
    Contado().validar(D(1000), D(0))
    Contado().validar(D(1000), D("999.99"))
    with pytest.raises(ErrorDeCampo) as e:
        Contado().validar(D(1000), D(1000))
    assert e.value.campo == "canje_valor_usd"


def test_cuotas_todavia_no():
    assert isinstance(modalidad_de(Modalidad.contado), Contado)
    with pytest.raises(ErrorDeCampo):
        modalidad_de(Modalidad.cuotas)


def _producto(cantidad=1, estado=EstadoProductoEnum.disponible) -> Producto:
    return Producto(
        modelo_id=1,
        proveedor_id=1,
        condicion=Condicion.nuevo,
        cantidad=cantidad,
        precio_usd=D(10),
        estado=estado,
    )


def test_accesorio_se_descuenta_y_pasa_a_vendido_al_venderse_todo():
    cable = _producto(cantidad=5)
    cable.vender(2)
    assert (cable.estado, cable.cantidad) == (EstadoProductoEnum.disponible, 3)
    cable.vender(3)
    assert (cable.estado, cable.cantidad) == (EstadoProductoEnum.vendido, 3)


def test_devolver_en_cualquier_orden_deja_las_unidades_originales():
    # Dos ventas: A se lleva 2 y B las 3 que quedan. Se borran en los dos órdenes.
    for orden in ((2, 3), (3, 2)):
        cable = _producto(cantidad=5)
        cable.vender(2)
        cable.vender(3)
        for cantidad in orden:
            cable.devolver(cantidad)
        assert (cable.estado, cable.cantidad) == (EstadoProductoEnum.disponible, 5)


def test_un_equipo_vendido_no_se_vuelve_a_vender():
    equipo = _producto()
    equipo.vender()
    assert equipo.estado == EstadoProductoEnum.vendido
    with pytest.raises(TransicionInvalida):
        equipo.vender()
