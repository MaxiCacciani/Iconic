"""Catálogos iniciales, sacados de las reglas de negocio (secciones 2, 3 y 4).

Es la única fuente: la API los carga al arrancar, tanto en PostgreSQL como en SQLite.
Cada tabla se carga solo si está vacía, así que no pisa lo que el negocio ya cambió.
Las reglas no traen modelos, capacidades, colores ni localidades: se cargan desde la app.
"""

from sqlmodel import Session, SQLModel, select

from app.modules.catalogos.models import (
    Categoria,
    Defecto,
    Diagnostico,
    EstadoReclamo,
    MetodoPago,
    Proveedor,
    TipoCategoria,
)

TIPOS_CATEGORIA: list[dict] = [
    {"nombre": "Equipo con IMEI", "usa_imei": True, "usa_bateria": True},
    {"nombre": "Equipo sin IMEI"},
    {"nombre": "Consola", "usa_controles": True},
    {"nombre": "Accesorio", "por_cantidad": True},
]

CATEGORIAS = {
    "Equipo con IMEI": ["iPhone", "iPad", "Mac"],
    "Equipo sin IMEI": ["Apple Watch", "AirPods"],
    "Consola": ["Xbox", "PlayStation", "Nintendo"],
    "Accesorio": ["Vidrio templado", "Cargador", "Cable", "Funda/Case", "Otro accesorio"],
}

PROVEEDORES = ["Plan canje", "Importación personal", "Mariano Camara", "Lucas Bertorello"]

METODOS_PAGO = ["Transferencia", "Débito", "Crédito", "Efectivo"]  # el primero, predeterminado

DIAGNOSTICOS = [
    "Pantalla", "Batería", "Cámara", "Botones", "Señal", "No enciende", "Audio", "Carga",
    "Humedad", "Face ID / Touch ID", "Reinicios", "Sobrecalentamiento", "Otro",
]  # fmt: skip

ESTADO_RECLAMO_INICIAL = "En gestión"

DEFECTOS_COMUNES = ["Pantalla con micro-rayones", "Marco desgastado", "Puerto de carga flojo"]


def _vacia(session: Session, modelo: type[SQLModel]) -> bool:
    return session.exec(select(modelo)).first() is None


def sembrar_catalogos(session: Session) -> None:
    if _vacia(session, TipoCategoria):
        session.add_all(TipoCategoria(**t) for t in TIPOS_CATEGORIA)
        session.flush()

    if _vacia(session, Categoria):
        tipos = {t.nombre: t.id for t in session.exec(select(TipoCategoria)).all()}
        for tipo, categorias in CATEGORIAS.items():
            if tipo in tipos:
                session.add_all(
                    Categoria(nombre=c, tipo_categoria_id=tipos[tipo]) for c in categorias
                )

    if _vacia(session, Proveedor):
        session.add_all(Proveedor(nombre=p) for p in PROVEEDORES)

    if _vacia(session, MetodoPago):
        session.add_all(
            MetodoPago(nombre=m, predeterminado=i == 0) for i, m in enumerate(METODOS_PAGO)
        )

    if _vacia(session, Diagnostico):
        session.add_all(Diagnostico(nombre=d) for d in DIAGNOSTICOS)

    if _vacia(session, EstadoReclamo):
        session.add(EstadoReclamo(nombre=ESTADO_RECLAMO_INICIAL, es_inicial=True))

    if _vacia(session, Defecto):
        session.add_all(Defecto(descripcion=d, es_comun=True) for d in DEFECTOS_COMUNES)

    session.commit()
