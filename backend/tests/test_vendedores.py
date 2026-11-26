"""API de vendedores: ABM del Administrador, número único, búsqueda por número y roles."""

from sqlalchemy import Column, ForeignKey, Integer, Table
from sqlmodel import Session, SQLModel

from tests.conftest import auth_header


def crear(client, usuario, **datos):
    return client.post("/vendedores", json=datos, headers=auth_header(usuario))


def errores(r) -> dict[str, str]:
    return {e["loc"][-1]: e["msg"] for e in r.json()["detail"]}


def test_sin_sesion_401(client):
    assert client.get("/vendedores").status_code == 401
    assert client.get("/vendedores/numero/1").status_code == 401


def test_alta_y_lista_por_numero(client, admin):
    assert crear(client, admin, numero=7, nombre="  juan PÉREZ ").status_code == 201
    r = crear(client, admin, numero=2, nombre="Ana")
    assert r.json() == {"id": r.json()["id"], "numero": 2, "nombre": "Ana"}
    lista = client.get("/vendedores", headers=auth_header(admin)).json()
    assert [(v["numero"], v["nombre"]) for v in lista] == [(2, "Ana"), (7, "Juan Pérez")]


def test_numero_y_nombre_obligatorios_y_validos(client, admin):
    r = crear(client, admin, numero=0, nombre="  ")
    assert r.status_code == 422
    assert set(errores(r)) == {"numero", "nombre"}
    assert errores(crear(client, admin, numero="tres", nombre="Ana"))["numero"] == (
        "Tiene que ser un número entero."
    )


def test_numero_unico_nombra_al_otro(client, admin):
    crear(client, admin, numero=3, nombre="Ana Gómez")
    r = crear(client, admin, numero=3, nombre="Luis")
    assert r.status_code == 422
    assert errores(r) == {"numero": "El número 3 ya es de Ana Gómez."}


def test_editar(client, admin):
    ana = crear(client, admin, numero=3, nombre="Ana").json()
    crear(client, admin, numero=4, nombre="Luis")
    h = auth_header(admin)
    # Su propio número no cuenta como repetido.
    r = client.patch(f"/vendedores/{ana['id']}", json={"numero": 3, "nombre": "ana lía"}, headers=h)
    assert r.status_code == 200
    assert r.json()["nombre"] == "Ana Lía"
    r = client.patch(f"/vendedores/{ana['id']}", json={"numero": 4}, headers=h)
    assert errores(r) == {"numero": "El número 4 ya es de Luis."}
    r = client.patch(f"/vendedores/{ana['id']}", json={"nombre": None}, headers=h)
    assert errores(r) == {"nombre": "Este campo es obligatorio."}
    assert client.patch("/vendedores/999", json={}, headers=h).status_code == 404


def test_buscar_por_numero(client, admin, vendedor):
    crear(client, admin, numero=12, nombre="Ana")
    h = auth_header(vendedor)
    r = client.get("/vendedores/numero/12", headers=h)
    assert r.status_code == 200
    assert r.json()["nombre"] == "Ana"
    r = client.get("/vendedores/numero/13", headers=h)
    assert r.status_code == 404
    assert r.json() == {"detail": "Vendedor no registrado."}


def test_vendedor_lee_pero_no_modifica(client, admin, vendedor):
    vid = crear(client, admin, numero=1, nombre="Ana").json()["id"]
    h = auth_header(vendedor)
    assert client.get("/vendedores", headers=h).status_code == 200
    assert crear(client, vendedor, numero=2, nombre="Luis").status_code == 403
    assert client.patch(f"/vendedores/{vid}", json={}, headers=h).status_code == 403
    assert client.delete(f"/vendedores/{vid}", headers=h).status_code == 403


def test_borrar(client, admin):
    vid = crear(client, admin, numero=1, nombre="Ana").json()["id"]
    h = auth_header(admin)
    assert client.delete(f"/vendedores/{vid}", headers=h).status_code == 204
    assert client.get("/vendedores", headers=h).json() == []
    assert client.delete(f"/vendedores/{vid}", headers=h).status_code == 404


def test_con_ventas_no_se_borra(client, admin, session: Session):
    """Las ventas llegan en la Fase 7: una tabla que apunta a vendedores alcanza para ver
    que el chequeo sale de las claves foráneas."""
    ventas = Table(
        "ventas_de_prueba",
        SQLModel.metadata,
        Column("id", Integer, primary_key=True),
        Column("vendedor_id", Integer, ForeignKey("vendedores.id")),
    )
    try:
        ventas.create(session.connection())
        vid = crear(client, admin, numero=1, nombre="Ana").json()["id"]
        session.execute(ventas.insert().values(vendedor_id=vid))
        session.execute(ventas.insert().values(vendedor_id=vid))
        session.commit()
        r = client.delete(f"/vendedores/{vid}", headers=auth_header(admin))
        assert r.status_code == 409
        assert r.json()["detail"] == (
            "No se puede borrar a Ana: tiene 2 ventas. Quedan como historial."
        )
    finally:
        SQLModel.metadata.remove(ventas)
