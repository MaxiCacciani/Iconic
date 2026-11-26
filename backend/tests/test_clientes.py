"""API de clientes: alta y edición con DNI único, búsqueda, ficha, borrado y roles."""

import pytest
from sqlalchemy import Column, ForeignKey, Integer, Table
from sqlmodel import Session, SQLModel

from app.modules.catalogos.models import Localidad
from tests.conftest import auth_header


@pytest.fixture
def rosario(session: Session) -> int:
    localidad = Localidad(nombre="Rosario")
    session.add(localidad)
    session.commit()
    return localidad.id  # type: ignore[return-value]


def crear(client, usuario, **datos):
    return client.post("/clientes", json=datos, headers=auth_header(usuario))


def errores(r) -> dict[str, str]:
    return {e["loc"][-1]: e["msg"] for e in r.json()["detail"]}


# ─── Alta ────────────────────────────────────────────────────────────────────
def test_alta_completa(client, admin, rosario):
    r = crear(
        client,
        admin,
        nombre="  Juan Pérez ",
        dni="30.123.456",
        telefono="+54 9 (341) 555-1234",
        localidad_id=rosario,
    )
    assert r.status_code == 201
    cliente = r.json()
    assert cliente["id"] > 0
    assert cliente["nombre"] == "Juan Pérez"
    assert cliente["dni"] == "30123456"  # se guardan solo los dígitos
    assert cliente["telefono"] == "5493415551234"
    assert cliente["localidad"] == {"id": rosario, "nombre": "Rosario"}


def test_solo_el_nombre_es_obligatorio(client, vendedor):
    # Los opcionales en blanco son "sin dato", no un DNI inválido.
    r = crear(client, vendedor, nombre="Ana", dni="", telefono="  ")
    assert r.status_code == 201
    assert r.json() | {"id": 0, "creado_en": ""} == {
        "id": 0,
        "nombre": "Ana",
        "dni": None,
        "telefono": None,
        "localidad": None,
        "creado_en": "",
    }
    r = crear(client, vendedor, nombre="   ")
    assert r.status_code == 422
    assert "nombre" in errores(r)


SOLO_NUMEROS_TEL = (
    "El teléfono solo puede tener números (también se aceptan espacios, guiones, "
    "paréntesis y el +)."
)
SOLO_NUMEROS_DNI = (
    "El DNI solo puede tener números (también se aceptan puntos, espacios y guiones)."
)


@pytest.mark.parametrize(
    "campo,valor,mensaje",
    [
        # Con letras se avisa eso, no un error de longitud.
        ("dni", "30a12345", SOLO_NUMEROS_DNI),
        ("dni", "30/123/456", SOLO_NUMEROS_DNI),
        ("telefono", "341-CASA", SOLO_NUMEROS_TEL),
        ("telefono", "341 555 1234 int. 2", SOLO_NUMEROS_TEL),
        # Solo números (los separadores no cuentan), pero con otra longitud.
        ("dni", "123.456", "El DNI tiene que tener 7 u 8 dígitos y tiene 6."),
        ("dni", "123456789", "El DNI tiene que tener 7 u 8 dígitos y tiene 9."),
        ("telefono", "341 555", "El teléfono tiene que tener entre 8 y 15 dígitos y tiene 6."),
        (
            "telefono",
            "+54 9 (341) 555-1234-999",
            "El teléfono tiene que tener entre 8 y 15 dígitos y tiene 16.",
        ),
    ],
)
def test_dni_y_telefono_invalidos(client, admin, campo, valor, mensaje):
    r = crear(client, admin, nombre="Ana", **{campo: valor})
    assert r.status_code == 422
    assert errores(r)[campo] == mensaje


@pytest.mark.parametrize(
    "escrito,guardado",
    [
        ("juan pérez", "Juan Pérez"),
        ("JUAN   PÉREZ", "Juan Pérez"),  # también junta los espacios repetidos
        ("maría de los ángeles", "María de los Ángeles"),  # partículas en minúscula…
        ("de la fuente ana", "De la Fuente Ana"),  # …salvo al principio
        ("ana pérez-garcía", "Ana Pérez-García"),
        ("o'brien", "O'Brien"),
        ("ñandú", "Ñandú"),
    ],
)
def test_nombre_con_iniciales_en_mayuscula(client, vendedor, escrito, guardado):
    cliente = crear(client, vendedor, nombre=escrito).json()
    assert cliente["nombre"] == guardado
    # Al editar, igual.
    r = client.patch(
        f"/clientes/{cliente['id']}",
        json={"nombre": escrito.upper()},
        headers=auth_header(vendedor),
    )
    assert r.json()["nombre"] == guardado


def test_largo_del_nombre(client, admin):
    assert crear(client, admin, nombre="x" * 100).status_code == 201
    r = crear(client, admin, nombre="x" * 101)
    assert r.status_code == 422
    assert errores(r)["nombre"] == "El nombre puede tener hasta 100 caracteres y tiene 101."
    # Los espacios de los bordes no cuentan.
    assert crear(client, admin, nombre=f"  {'y' * 100}  ").status_code == 201


def test_dni_unico(client, admin, vendedor):
    juan = crear(client, admin, nombre="Juan", dni="30123456").json()
    r = crear(client, vendedor, nombre="Otro", dni="30.123.456")
    assert r.status_code == 422
    assert errores(r)["dni"] == f"Ya hay un cliente con ese DNI: Juan (#{juan['id']})."


def test_localidad_inexistente(client, admin):
    r = crear(client, admin, nombre="Ana", localidad_id=999)
    assert r.status_code == 422
    assert errores(r)["localidad_id"] == "Esa localidad no existe."


# ─── Edición ─────────────────────────────────────────────────────────────────
def test_edicion_parcial_y_borrar_opcionales(client, vendedor, rosario):
    h = auth_header(vendedor)
    cliente = crear(
        client, vendedor, nombre="Ana", dni="30123456", telefono="3415551234", localidad_id=rosario
    ).json()
    url = f"/clientes/{cliente['id']}"

    r = client.patch(url, json={"telefono": "341 555 0000"}, headers=h)
    assert r.status_code == 200
    assert r.json()["telefono"] == "3415550000"
    assert r.json()["dni"] == "30123456"  # lo que no se manda queda igual

    # Su propio DNI no cuenta como repetido.
    assert client.patch(url, json={"dni": "30123456"}, headers=h).status_code == 200

    r = client.patch(url, json={"dni": None, "telefono": "", "localidad_id": None}, headers=h)
    assert r.status_code == 200
    assert (r.json()["dni"], r.json()["telefono"], r.json()["localidad"]) == (None, None, None)


def test_edicion_no_borra_el_nombre_ni_repite_dni(client, admin):
    h = auth_header(admin)
    crear(client, admin, nombre="Juan", dni="30123456")
    ana = crear(client, admin, nombre="Ana").json()
    url = f"/clientes/{ana['id']}"

    r = client.patch(url, json={"nombre": None}, headers=h)
    assert r.status_code == 422
    assert "nombre" in errores(r)

    r = client.patch(url, json={"dni": "30123456"}, headers=h)
    assert r.status_code == 422
    assert "dni" in errores(r)

    assert client.patch("/clientes/999", json={}, headers=h).status_code == 404


# ─── Búsqueda y ficha ────────────────────────────────────────────────────────
@pytest.fixture
def varios(client, admin):
    for nombre, dni in [
        ("Juan Pérez", "30123456"),
        ("ana gómez", "28999111"),
        ("Pedro Juárez", None),
        ("Juana 100%", "7123456"),
    ]:
        assert crear(client, admin, nombre=nombre, dni=dni).status_code == 201


def nombres(client, usuario, **params) -> list[str]:
    r = client.get("/clientes", params=params, headers=auth_header(usuario))
    assert r.status_code == 200
    return [c["nombre"] for c in r.json()["items"]]


def test_lista_por_nombre_sin_distinguir_mayusculas(client, vendedor, varios):
    assert nombres(client, vendedor) == ["Ana Gómez", "Juan Pérez", "Juana 100%", "Pedro Juárez"]


@pytest.mark.parametrize(
    "buscar,esperados",
    [
        ("juan", ["Juan Pérez", "Juana 100%"]),
        ("pérez juan", ["Juan Pérez"]),  # cada palabra, en cualquier orden
        ("perez", ["Juan Pérez"]),  # sin distinguir tildes…
        ("JUÁREZ", ["Pedro Juárez"]),  # …ni mayúsculas, con o sin tilde
        ("GOMEZ", ["Ana Gómez"]),
        ("30.123", ["Juan Pérez"]),  # parte del DNI, con o sin puntos
        ("999", ["Ana Gómez"]),
        ("100%", ["Juana 100%"]),  # el % no es comodín
        ("zzz", []),
    ],
)
def test_busqueda_por_nombre_o_dni(client, vendedor, varios, buscar, esperados):
    assert nombres(client, vendedor, buscar=buscar) == esperados


def test_paginacion(client, admin, varios):
    r = client.get("/clientes", params={"tamanio": 3, "pagina": 2}, headers=auth_header(admin))
    pagina = r.json()
    assert (pagina["total"], pagina["pagina"], pagina["tamanio"]) == (4, 2, 3)
    assert [c["nombre"] for c in pagina["items"]] == ["Pedro Juárez"]


def test_ficha(client, vendedor, rosario):
    cliente = crear(client, vendedor, nombre="Ana", localidad_id=rosario).json()
    r = client.get(f"/clientes/{cliente['id']}", headers=auth_header(vendedor))
    assert r.status_code == 200
    assert r.json() == cliente
    r = client.get("/clientes/999", headers=auth_header(vendedor))
    assert r.status_code == 404
    assert r.json()["detail"] == "El cliente #999 no existe."


# ─── Borrado y roles ─────────────────────────────────────────────────────────
def test_borrar_solo_admin(client, admin, vendedor):
    cliente = crear(client, vendedor, nombre="Ana").json()
    url = f"/clientes/{cliente['id']}"
    assert client.delete(url, headers=auth_header(vendedor)).status_code == 403
    assert client.delete(url, headers=auth_header(admin)).status_code == 204
    assert client.get(url, headers=auth_header(admin)).status_code == 404
    assert client.delete(url, headers=auth_header(admin)).status_code == 404


def test_no_se_borra_un_cliente_con_historial(client, admin, session):
    """Las ventas, reservas y reclamos llegan en otras fases: el chequeo lee las claves
    foráneas, así que una tabla que apunta a clientes ya lo frena."""
    tabla = Table(
        "ventas_de_prueba",
        SQLModel.metadata,
        Column("id", Integer, primary_key=True),
        Column("cliente_id", Integer, ForeignKey("clientes.id"), nullable=False),
    )
    try:
        tabla.create(session.connection())
        cliente = crear(client, admin, nombre="Ana").json()
        session.execute(tabla.insert().values(cliente_id=cliente["id"]))
        session.execute(tabla.insert().values(cliente_id=cliente["id"]))
        session.commit()

        r = client.delete(f"/clientes/{cliente['id']}", headers=auth_header(admin))
        assert r.status_code == 409
        assert r.json()["detail"] == (
            "No se puede borrar a Ana: tiene ventas_de_prueba (2). Quedan como historial."
        )
    finally:
        SQLModel.metadata.remove(tabla)


def test_sin_sesion_no_hay_acceso(client):
    assert client.get("/clientes").status_code == 401
    assert client.post("/clientes", json={"nombre": "Ana"}).status_code == 401


def test_permisos(client, admin, vendedor):
    def permisos(u):
        return client.get("/auth/me", headers=auth_header(u)).json()["permisos"]

    assert "clientes" in permisos(vendedor)
    assert "clientes:borrar" not in permisos(vendedor)
    assert "clientes:borrar" in permisos(admin)


def test_localidad_en_uso_no_se_borra(client, admin, rosario):
    crear(client, admin, nombre="Ana", localidad_id=rosario)
    r = client.delete(f"/catalogos/localidades/{rosario}", headers=auth_header(admin))
    assert r.status_code == 409
    assert "clientes (1)" in r.json()["detail"]
