"""Cuotas: división con ajuste en la última, fechas a fin de mes, `EnCuotas` y el State
de `Cobro`."""

from datetime import date
from decimal import Decimal

import pytest

from app.common.enums import EstadoCobroEnum
from app.core.excepciones import ErrorDeCampo, TransicionInvalida
from app.modules.cobros.estados import EstadoCuota, estado_de
from app.modules.cobros.models import Cobro
from app.modules.ventas.dominio import dividir, plan_de_cuotas, sumar_meses
from app.modules.ventas.modalidades import EnCuotas, Pago

D = Decimal
HOY = date(2026, 11, 28)


def test_ejemplo_de_las_reglas_1000_en_6():
    assert dividir(D(1000), 6) == [D(167)] * 5 + [D(165)]


@pytest.mark.parametrize(
    ("monto", "cuotas", "esperado"),
    [
        (D(1000), 3, [D(333), D(333), D(334)]),
        (D(900), 2, [D(450), D(450)]),
        (D("1000.50"), 6, [D(167)] * 5 + [D("165.50")]),
        (D(10), 4, [D(3), D(3), D(3), D(1)]),  # 2,50 redondea a 3
    ],
)
def test_dividir_suma_exacta(monto, cuotas, esperado):
    partes = dividir(monto, cuotas)
    assert partes == esperado
    assert sum(partes) == monto


@pytest.mark.parametrize(
    ("dia", "meses", "esperado"),
    [
        (date(2026, 1, 31), 1, date(2026, 2, 28)),
        (date(2026, 1, 31), 2, date(2026, 3, 31)),  # desde el día original, no el 28
        (date(2028, 1, 30), 1, date(2028, 2, 29)),  # bisiesto
        (date(2026, 11, 15), 2, date(2027, 1, 15)),  # cambio de año
        (date(2026, 12, 31), 12, date(2027, 12, 31)),
    ],
)
def test_sumar_meses_a_fin_de_mes(dia, meses, esperado):
    assert sumar_meses(dia, meses) == esperado


def test_la_primera_vence_al_mes_siguiente():
    plan = plan_de_cuotas(D(300), 3, date(2026, 1, 31), primera_hoy=False)
    assert [c.vencimiento for c in plan] == [
        date(2026, 2, 28),
        date(2026, 3, 31),
        date(2026, 4, 30),
    ]
    assert not any(c.cobrada for c in plan)


def test_primera_cuota_hoy_queda_cobrada():
    plan = plan_de_cuotas(D(300), 3, HOY, primera_hoy=True)
    assert [(c.numero, c.vencimiento, c.cobrada) for c in plan] == [
        (1, HOY, True),
        (2, date(2026, 12, 28), False),
        (3, date(2027, 1, 28), False),
    ]


def test_en_cuotas_financia_total_menos_anticipo_y_canje():
    plan = EnCuotas().planear(D(1300), D(200), Pago(D(100), 6), HOY)
    assert plan.anticipo == D(100)
    assert plan.cantidad_cuotas == 6
    assert [c.monto for c in plan.cuotas] == [D(167)] * 5 + [D(165)]


@pytest.mark.parametrize(
    ("canje", "pago", "campo"),
    [
        (D(0), Pago(), "cantidad_cuotas"),
        (D(0), Pago(D(1000), 6), "anticipo_usd"),
        (D(600), Pago(D(400), 6), "anticipo_usd"),
        (D(1000), Pago(D(0), 6), "canje_valor_usd"),
        (D(990), Pago(D(0), 12), "cantidad_cuotas"),  # 10 en 12: alguna queda por debajo de 1
    ],
)
def test_en_cuotas_rechaza(canje, pago, campo):
    with pytest.raises(ErrorDeCampo) as e:
        EnCuotas().planear(D(1000), canje, pago, HOY)
    assert e.value.campo == campo


def test_vencida_se_calcula_y_no_se_guarda():
    assert estado_de(EstadoCobroEnum.pendiente, HOY, HOY).valor == EstadoCuota.pendiente
    assert (
        estado_de(EstadoCobroEnum.pendiente, date(2026, 11, 27), HOY).valor == EstadoCuota.vencida
    )
    assert estado_de(EstadoCobroEnum.cobrada, date(2026, 11, 1), HOY).valor == EstadoCuota.cobrada


def test_cobrar_una_vencida_y_no_dos_veces():
    cobro = Cobro(numero_cuota=1, fecha_vencimiento=date(2020, 1, 1), monto_usd=D(10))
    cobro.cobrar()
    assert cobro.estado == EstadoCobroEnum.cobrada
    with pytest.raises(TransicionInvalida):
        cobro.cobrar()
