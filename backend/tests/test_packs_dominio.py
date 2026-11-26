"""`packs.dominio.repartir`: aplicar un pack sin repetir equipos. Sin base ni API."""

from app.modules.packs.dominio import Asignacion, Candidato, Pedido, repartir


def equipos(*ids: int) -> list[Candidato]:
    return [Candidato(i, 1) for i in ids]


def test_cada_item_toma_el_primer_candidato_libre():
    r = repartir([Pedido(1, 1, equipos(10, 11)), Pedido(2, 1, equipos(20))])
    assert r.asignaciones == [Asignacion(1, 10, 1), Asignacion(2, 20, 1)]
    assert r.faltantes == {}


def test_no_repite_el_mismo_equipo():
    # Dos ítems de la misma categoría: el segundo se lleva el siguiente equipo.
    r = repartir([Pedido(1, 1, equipos(10, 11)), Pedido(2, 1, equipos(10, 11))])
    assert r.asignaciones == [Asignacion(1, 10, 1), Asignacion(2, 11, 1)]


def test_varias_unidades_de_una_categoria_son_equipos_distintos():
    r = repartir([Pedido(1, 3, equipos(10, 11))])
    assert r.asignaciones == [Asignacion(1, 10, 1), Asignacion(1, 11, 1)]
    assert r.faltantes == {1: 1}


def test_lo_del_carrito_no_se_vuelve_a_dar():
    r = repartir([Pedido(1, 1, equipos(10, 11))], ocupadas={10: 1})
    assert r.asignaciones == [Asignacion(1, 11, 1)]


def test_el_fijo_primero_no_se_lo_lleva_la_categoria():
    # El service manda los fijos antes: el 10 queda para el ítem que lo pidió.
    fijo = Pedido(1, 1, equipos(10))
    categoria = Pedido(2, 1, equipos(10, 11))
    r = repartir([fijo, categoria])
    assert r.asignaciones == [Asignacion(1, 10, 1), Asignacion(2, 11, 1)]


def test_accesorio_por_cantidad_reparte_sus_unidades():
    cables = [Candidato(30, 3), Candidato(31, 5)]
    r = repartir([Pedido(1, 2, cables), Pedido(2, 4, cables)])
    # El primero usa 2 de la fila 30; el segundo, la que queda de la 30 y 3 de la 31.
    assert r.asignaciones == [
        Asignacion(1, 30, 2),
        Asignacion(2, 30, 1),
        Asignacion(2, 31, 3),
    ]
    assert r.faltantes == {}


def test_accesorio_con_carrito_y_faltante():
    r = repartir([Pedido(1, 4, [Candidato(30, 3)])], ocupadas={30: 2})
    assert r.asignaciones == [Asignacion(1, 30, 1)]
    assert r.faltantes == {1: 3}


def test_sin_candidatos_falta_todo():
    r = repartir([Pedido(1, 2, [])])
    assert r.asignaciones == []
    assert r.faltantes == {1: 2}


def test_no_modifica_lo_ocupado_que_recibe():
    ocupadas = {10: 1}
    repartir([Pedido(1, 1, equipos(10, 11))], ocupadas)
    assert ocupadas == {10: 1}
