from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

from app.core.db import tablas_faltantes


def test_sin_faltantes_con_el_esquema_completo(session):
    assert tablas_faltantes(session.get_bind()) == []


def test_avisa_las_tablas_que_faltan():
    motor = create_engine("sqlite://", poolclass=StaticPool)
    tablas = SQLModel.metadata.tables
    todas_menos = [t for nombre, t in tablas.items() if nombre != "modelo_colores"]
    SQLModel.metadata.create_all(motor, tables=todas_menos)
    assert tablas_faltantes(motor) == ["modelo_colores"]
