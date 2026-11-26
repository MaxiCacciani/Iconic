"""Carga datos de prueba: usuarios, TC de hoy, catálogos ampliados, ~90 productos,
vendedores y packs.

    uv run python -m app.scripts.datos_prueba                   # local (la base del .env)
    docker compose exec api python -m app.scripts.datos_prueba

Se puede correr varias veces: los catálogos se completan por nombre (no se duplican), los
usuarios y el TC solo se cargan si faltan, y los productos solo si la tabla está vacía
(con `--productos-igual` se suman otra tanda). Los vendedores se completan por número y
los packs solo se cargan si no hay ninguno. Productos y packs se crean con sus services,
así que pasan por las mismas validaciones que el alta de la pantalla.

Usuarios (contraseña `iconic123`, o la de `--password`):
- admin@iconic.com    Administrador
- vendedor@iconic.com Vendedor

Todos los productos quedan `disponible`: reservados y vendidos salen de reservas y ventas
(Fases 7 y 9), no se marcan a mano.
"""

import argparse
import random
from decimal import Decimal

from sqlmodel import Session, SQLModel, select

from app.common.enums import Condicion, Rol
from app.common.tipos import luhn_valido
from app.core import reloj
from app.core.config import get_settings
from app.core.db import crear_tablas_sqlite, engine
from app.core.security import hashear_password
from app.core.uow import UnidadDeTrabajo
from app.modules.catalogos.models import (
    Capacidad,
    Categoria,
    Color,
    Defecto,
    EstadoReclamo,
    Localidad,
    Modelo,
    Proveedor,
    TipoCategoria,
)
from app.modules.catalogos.semilla import sembrar_catalogos
from app.modules.catalogos.service import AsignacionService
from app.modules.packs.models import Pack
from app.modules.packs.schemas import PackCreate, PackItemCreate
from app.modules.packs.service import PackService
from app.modules.productos.models import Producto
from app.modules.productos.schemas import ProductoCreate
from app.modules.productos.service import ProductoService
from app.modules.tipo_cambio.models import TipoCambio
from app.modules.usuarios.models import Usuario
from app.modules.vendedores.models import Vendedor

TC_HOY = Decimal("1180.50")

VENDEDORES = [(1, "Martín Ríos"), (2, "Sofía Herrera"), (3, "Lucas Bertorello"), (7, "Camila Paz")]

# ─── Catálogos ───────────────────────────────────────────────────────────────
PROVEEDORES = ["Distribuidora Norte", "Apple Store Miami", "Gamer Point"]
LOCALIDADES = [
    "Córdoba", "Villa Carlos Paz", "Río Cuarto", "Villa María", "Alta Gracia",
    "Jesús María", "Rosario", "Buenos Aires", "Mendoza", "San Francisco",
]  # fmt: skip
DEFECTOS = ["Batería de servicio", "Cámara con mancha", "Tapa trasera astillada", "Sin caja"]
ESTADOS_RECLAMO = ["Esperando repuesto", "En servicio técnico", "Resuelto", "Rechazado"]

# Categorías nuevas, además de las de la semilla: (nombre, tipo).
CATEGORIAS_NUEVAS = [("Samsung", "Equipo con IMEI"), ("Parlantes", "Equipo sin IMEI")]

# Por categoría: capacidades, colores y modelos. Cada modelo: (nombre, capacidades, colores,
# rango de precio en USD). Capacidades o colores en `None`: el modelo no los asigna y ofrece
# todos los de su categoría (sirve para probar ese caso). Lista vacía: el producto va sin eso.
CATALOGO: dict[str, dict] = {
    "iPhone": {
        "capacidades": ["64 GB", "128 GB", "256 GB", "512 GB", "1 TB"],
        "colores": [
            "Negro",
            "Blanco",
            "Azul",
            "Rojo",
            "Verde",
            "Rosa",
            "Violeta",
            "Titanio natural",
            "Titanio negro",
            "Titanio desierto",
            "Grafito",
            "Dorado",
        ],  # fmt: skip
        "modelos": [
            ("iPhone 11", ["64 GB", "128 GB"], ["Negro", "Blanco", "Rojo", "Violeta"], (220, 300)),
            ("iPhone 12", ["64 GB", "128 GB", "256 GB"], ["Negro", "Blanco", "Azul"], (300, 380)),
            (
                "iPhone 13",
                ["128 GB", "256 GB"],
                ["Negro", "Blanco", "Azul", "Rosa", "Rojo"],
                (380, 480),
            ),
            (
                "iPhone 13 Pro",
                ["128 GB", "256 GB", "512 GB"],
                ["Grafito", "Dorado", "Azul"],
                (480, 600),
            ),
            ("iPhone 14", ["128 GB", "256 GB"], ["Negro", "Blanco", "Azul", "Violeta"], (500, 620)),
            (
                "iPhone 14 Pro Max",
                ["128 GB", "256 GB", "512 GB"],
                ["Negro", "Dorado", "Violeta"],
                (750, 900),
            ),
            (
                "iPhone 15",
                ["128 GB", "256 GB", "512 GB"],
                ["Negro", "Azul", "Verde", "Rosa"],
                (700, 820),
            ),
            (
                "iPhone 15 Pro",
                ["128 GB", "256 GB", "512 GB", "1 TB"],
                ["Titanio natural", "Titanio negro", "Blanco", "Azul"],
                (850, 1050),
            ),
            ("iPhone 16", ["128 GB", "256 GB"], None, (850, 950)),
            (
                "iPhone 16 Pro Max",
                ["256 GB", "512 GB", "1 TB"],
                ["Titanio natural", "Titanio negro", "Titanio desierto", "Blanco"],
                (1250, 1550),
            ),
        ],  # fmt: skip
    },
    "iPad": {
        "capacidades": ["64 GB", "128 GB", "256 GB", "512 GB"],
        "colores": ["Gris espacial", "Plata", "Azul", "Rosa", "Violeta"],
        "modelos": [
            ("iPad 10ª gen", ["64 GB", "256 GB"], ["Plata", "Azul", "Rosa"], (330, 420)),
            (
                "iPad Air M2",
                ["128 GB", "256 GB", "512 GB"],
                ["Gris espacial", "Azul", "Violeta"],
                (580, 750),
            ),
            ('iPad Pro 11" M4', ["256 GB", "512 GB"], ["Gris espacial", "Plata"], (950, 1200)),
            ("iPad mini 6", ["64 GB", "256 GB"], None, (380, 480)),
        ],  # fmt: skip
    },
    "Mac": {
        "capacidades": ["256 GB", "512 GB", "1 TB"],
        "colores": ["Gris espacial", "Plata", "Medianoche", "Blanco estelar"],
        "modelos": [
            ("MacBook Air M1", ["256 GB", "512 GB"], ["Gris espacial", "Plata"], (650, 780)),
            (
                'MacBook Air M3 13"',
                ["256 GB", "512 GB"],
                ["Medianoche", "Blanco estelar", "Plata"],
                (1000, 1250),
            ),
            ('MacBook Pro 14" M3', ["512 GB", "1 TB"], ["Gris espacial", "Plata"], (1650, 2100)),
        ],  # fmt: skip
    },
    "Samsung": {
        "capacidades": ["128 GB", "256 GB", "512 GB"],
        "colores": ["Negro", "Gris", "Violeta", "Crema"],
        "modelos": [
            ("Galaxy S23", ["128 GB", "256 GB"], ["Negro", "Crema", "Violeta"], (450, 560)),
            ("Galaxy S24 Ultra", ["256 GB", "512 GB"], ["Negro", "Gris", "Violeta"], (950, 1150)),
            ("Galaxy A55", ["128 GB", "256 GB"], None, (330, 400)),
        ],  # fmt: skip
    },
    "Apple Watch": {
        "capacidades": [],
        "colores": ["Medianoche", "Blanco estelar", "Plata", "Rojo", "Titanio natural"],
        "modelos": [
            ("Apple Watch SE 40 mm", [], ["Medianoche", "Blanco estelar", "Plata"], (200, 260)),
            (
                "Apple Watch Series 9 45 mm",
                [],
                ["Medianoche", "Blanco estelar", "Rojo"],
                (360, 450),
            ),
            ("Apple Watch Ultra 2", [], ["Titanio natural"], (700, 850)),
        ],  # fmt: skip
    },
    "AirPods": {
        "capacidades": [],
        "colores": ["Blanco"],
        "modelos": [
            ("AirPods 3ª gen", [], ["Blanco"], (140, 180)),
            ("AirPods Pro 2", [], ["Blanco"], (200, 260)),
            ("AirPods Max", [], None, (480, 580)),
        ],  # fmt: skip
    },
    "Parlantes": {
        "capacidades": [],
        "colores": ["Negro", "Blanco", "Azul"],
        "modelos": [
            ("JBL Flip 6", [], ["Negro", "Azul"], (110, 150)),
            ("HomePod mini", [], ["Blanco", "Negro", "Azul"], (110, 140)),
        ],  # fmt: skip
    },
    "PlayStation": {
        "capacidades": ["825 GB", "1 TB", "2 TB"],
        "colores": ["Blanco", "Negro"],
        "modelos": [
            ("PS4 Slim", ["1 TB"], ["Negro"], (230, 300)),
            ("PS5 Slim Digital", ["1 TB"], ["Blanco"], (480, 560)),
            ("PS5 Slim Lectora", ["1 TB"], ["Blanco"], (560, 650)),
            ("PS5 Pro", ["2 TB"], ["Blanco"], (850, 980)),
        ],  # fmt: skip
    },
    "Xbox": {
        "capacidades": ["512 GB", "1 TB"],
        "colores": ["Blanco", "Negro"],
        "modelos": [
            ("Xbox Series S", ["512 GB", "1 TB"], ["Blanco", "Negro"], (330, 420)),
            ("Xbox Series X", ["1 TB"], ["Negro"], (580, 680)),
        ],  # fmt: skip
    },
    "Nintendo": {
        "capacidades": ["32 GB", "64 GB", "256 GB"],
        "colores": ["Neón", "Gris", "Blanco OLED"],
        "modelos": [
            ("Switch V2", ["32 GB"], ["Neón", "Gris"], (280, 340)),
            ("Switch OLED", ["64 GB"], ["Blanco OLED", "Neón"], (380, 450)),
            ("Switch Lite", ["32 GB"], None, (200, 250)),
        ],  # fmt: skip
    },
    "Vidrio templado": {
        "capacidades": [],
        "colores": [],
        "modelos": [
            ("Vidrio iPhone 13/14", [], [], (8, 12)),
            ("Vidrio iPhone 15", [], [], (8, 12)),
            ("Vidrio iPhone 16 Pro Max", [], [], (10, 15)),
        ],  # fmt: skip
    },
    "Cargador": {
        "capacidades": [],
        "colores": ["Blanco", "Negro"],
        "modelos": [
            ("Cargador Apple 20 W USB-C", [], ["Blanco"], (25, 35)),
            ("Cargador Samsung 25 W", [], ["Negro", "Blanco"], (20, 28)),
            ("Cargador MagSafe", [], ["Blanco"], (40, 55)),
        ],  # fmt: skip
    },
    "Cable": {
        "capacidades": [],
        "colores": ["Blanco", "Negro"],
        "modelos": [
            ("Cable USB-C a Lightning 1 m", [], ["Blanco"], (15, 22)),
            ("Cable USB-C a USB-C 1 m", [], ["Blanco", "Negro"], (12, 20)),
        ],  # fmt: skip
    },
    "Funda/Case": {
        "capacidades": [],
        "colores": ["Transparente", "Negro", "Azul", "Rosa", "Verde"],
        "modelos": [
            ("Funda silicona iPhone 15", [], ["Negro", "Azul", "Rosa", "Verde"], (18, 28)),
            ("Funda MagSafe transparente iPhone 16", [], ["Transparente"], (25, 35)),
            ("Funda iPad Air Smart Folio", [], ["Negro", "Azul"], (35, 50)),
        ],  # fmt: skip
    },
    "Otro accesorio": {
        "capacidades": [],
        "colores": ["Negro", "Blanco"],
        "modelos": [
            ("Joystick DualSense", [], ["Blanco", "Negro"], (65, 85)),
            ("AirTag", [], ["Blanco"], (30, 40)),
            ("Soporte auto magnético", [], None, (12, 20)),
        ],  # fmt: skip
    },
}

# Cuántos productos (filas) por categoría. Suman 92.
PRODUCTOS_POR_CATEGORIA = {
    "iPhone": 26, "iPad": 6, "Mac": 4, "Samsung": 6,
    "Apple Watch": 5, "AirPods": 5, "Parlantes": 3,
    "PlayStation": 7, "Xbox": 4, "Nintendo": 5,
    "Vidrio templado": 3, "Cargador": 4, "Cable": 3, "Funda/Case": 5, "Otro accesorio": 6,
}  # fmt: skip

EXTRAS_CONSOLA = [
    "Caja original y cable HDMI", "Incluye 2 juegos físicos", "Sin caja", "Con base vertical",
    "Joy-Con con leve drift", None,
]  # fmt: skip
DEFECTOS_ESCRITOS = ["Botón de volumen duro", "Altavoz bajo", "Rayón en la tapa"]


# ─── Ayudas ──────────────────────────────────────────────────────────────────
def _por_nombre(session: Session, modelo: type[SQLModel], campo: str, valor: str, **filtro):
    consulta = select(modelo).where(getattr(modelo, campo) == valor)
    for k, v in filtro.items():
        consulta = consulta.where(getattr(modelo, k) == v)
    return session.exec(consulta).first()


def _asegurar(session: Session, modelo: type[SQLModel], campo: str = "nombre", **datos):
    """Lo busca por su nombre (y categoría, si la lleva) y, si no está, lo crea."""
    filtro = {"categoria_id": datos["categoria_id"]} if "categoria_id" in datos else {}
    existente = _por_nombre(session, modelo, campo, datos[campo], **filtro)
    if existente is not None:
        return existente
    nuevo = modelo(**datos)
    session.add(nuevo)
    session.flush()
    return nuevo


def _imei(rng: random.Random, usados: set[str]) -> str:
    while True:
        base = "35" + "".join(str(rng.randint(0, 9)) for _ in range(12))
        imei = next(base + str(d) for d in range(10) if luhn_valido(base + str(d)))
        if imei not in usados:
            usados.add(imei)
            return imei


def _precio(rng: random.Random, rango: tuple[int, int], usado: bool) -> Decimal:
    bajo, alto = rango
    precio = rng.uniform(bajo, alto) * (0.85 if usado else 1)
    return Decimal(str(round(precio / 5) * 5 if precio > 50 else round(precio)))


# ─── Pasos ───────────────────────────────────────────────────────────────────
def _usuarios(session: Session, password: str) -> Usuario:
    for nombre, email, rol in [
        ("Admin", "admin@iconic.com", Rol.admin),
        ("Valentina Vendedora", "vendedor@iconic.com", Rol.vendedor),
    ]:
        if _por_nombre(session, Usuario, "email", email) is None:
            session.add(
                Usuario(
                    nombre=nombre, email=email, password_hash=hashear_password(password), rol=rol
                )
            )
            print(f"  usuario {email} ({rol.value})")
    session.commit()
    admin = session.exec(select(Usuario).where(Usuario.rol == Rol.admin)).first()
    assert admin is not None
    return admin


def _tipo_cambio(session: Session, admin: Usuario) -> None:
    hoy = reloj.hoy()
    if _por_nombre(session, TipoCambio, "fecha", hoy) is None:  # type: ignore[arg-type]
        session.add(TipoCambio(fecha=hoy, valor_ars=TC_HOY, usuario_id=admin.id))  # type: ignore[arg-type]
        session.commit()
        print(f"  TC de hoy: $ {TC_HOY}")


def _catalogos(session: Session) -> dict[str, list[tuple[Modelo, tuple[int, int]]]]:
    for p in PROVEEDORES:
        _asegurar(session, Proveedor, nombre=p)
    for loc in LOCALIDADES:
        _asegurar(session, Localidad, nombre=loc)
    for d in DEFECTOS:
        _asegurar(session, Defecto, "descripcion", descripcion=d, es_comun=True)
    for e in ESTADOS_RECLAMO:
        _asegurar(session, EstadoReclamo, nombre=e)

    tipos = {t.nombre: t for t in session.exec(select(TipoCategoria)).all()}
    for nombre, tipo in CATEGORIAS_NUEVAS:
        _asegurar(session, Categoria, nombre=nombre, tipo_categoria_id=tipos[tipo].id)

    modelos_por_categoria: dict[str, list[tuple[Modelo, tuple[int, int]]]] = {}
    asignaciones: list[tuple[int, dict[str, list[int]]]] = []
    for cat_nombre, datos in CATALOGO.items():
        categoria = _por_nombre(session, Categoria, "nombre", cat_nombre)
        if categoria is None:  # la borraron desde la app
            print(f"  ! no está la categoría {cat_nombre}: se saltea")
            continue
        cid = categoria.id
        caps = {
            c: _asegurar(session, Capacidad, nombre=c, categoria_id=cid)
            for c in datos["capacidades"]
        }
        cols = {c: _asegurar(session, Color, nombre=c, categoria_id=cid) for c in datos["colores"]}
        lista = []
        for nombre, mcaps, mcols, rango in datos["modelos"]:
            modelo = _asegurar(session, Modelo, nombre=nombre, categoria_id=cid)
            cambios = {}
            if mcaps:
                cambios["capacidad_ids"] = [caps[c].id for c in mcaps]
            if mcols:
                cambios["color_ids"] = [cols[c].id for c in mcols]
            if cambios:
                asignaciones.append((modelo.id, cambios))  # type: ignore[arg-type]
            lista.append((modelo, rango))
        modelos_por_categoria[cat_nombre] = lista
    session.commit()

    for modelo_id, cambios in asignaciones:
        AsignacionService(UnidadDeTrabajo(session)).asignar(modelo_id, cambios)
    print(f"  catálogos: {sum(len(m) for m in modelos_por_categoria.values())} modelos en "
          f"{len(modelos_por_categoria)} categorías")  # fmt: skip
    return modelos_por_categoria


def _opciones(session: Session, modelo: Modelo, clase: type[SQLModel], relacion: str) -> list:
    asignadas = getattr(modelo, relacion)
    if asignadas:
        return list(asignadas)
    return list(session.exec(select(clase).where(clase.categoria_id == modelo.categoria_id)).all())  # type: ignore[attr-defined]


def _productos(session: Session, modelos: dict, rng: random.Random) -> int:
    proveedores = list(session.exec(select(Proveedor)).all())
    comunes = list(session.exec(select(Defecto).where(Defecto.es_comun)).all())
    usados_imei = {p.imei for p in session.exec(select(Producto)).all() if p.imei}
    creados = 0

    for cat_nombre, cantidad in PRODUCTOS_POR_CATEGORIA.items():
        lista = modelos.get(cat_nombre)
        if not lista:
            continue
        for i in range(cantidad):
            modelo, rango = lista[i % len(lista)]
            session.refresh(modelo)
            tipo = modelo.categoria.tipo
            capacidades = _opciones(session, modelo, Capacidad, "capacidades")
            colores = _opciones(session, modelo, Color, "colores")
            # Accesorios nuevos; del resto, cerca de 4 de cada 10 usados.
            usado = not tipo.por_cantidad and rng.random() < 0.4

            datos: dict = {
                "modelo_id": modelo.id,
                "capacidad_id": rng.choice(capacidades).id if capacidades else None,
                "color_id": rng.choice(colores).id if colores else None,
                "proveedor_id": rng.choice(proveedores).id,
                "condicion": Condicion.usado if usado else Condicion.nuevo,
                "precio_usd": _precio(rng, rango, usado),
            }
            # Costo: casi siempre, entre el 60 y el 85 % del precio; algunos sin costo.
            if rng.random() < 0.9:
                datos["costo_usd"] = (
                    datos["precio_usd"] * Decimal(str(rng.uniform(0.6, 0.85)))
                ).quantize(Decimal("1"))
            if tipo.usa_imei:
                datos["imei"] = _imei(rng, usados_imei)
            if tipo.usa_bateria:
                # Nuevos al 100; usados repartidos entre alta, media y baja (y alguno sin dato).
                datos["bateria"] = (
                    100 if not usado else rng.choice([95, 91, 88, 86, 84, 82, 80, 78, 74, None])
                )
            if tipo.usa_controles:
                datos["controles"] = rng.choice([0, 1, 1, 2, 2, 3])
                datos["extras"] = rng.choice(EXTRAS_CONSOLA)
            if tipo.por_cantidad:
                datos["cantidad"] = rng.choice([1, 3, 5, 10, 12, 20, 25])
            if usado and rng.random() < 0.5:
                datos["defecto_ids"] = [
                    d.id for d in rng.sample(comunes, k=min(len(comunes), rng.randint(1, 2)))
                ]
                if rng.random() < 0.3:
                    datos["defectos_nuevos"] = [rng.choice(DEFECTOS_ESCRITOS)]

            ProductoService(UnidadDeTrabajo(session)).crear(ProductoCreate(**datos))
            creados += 1
    return creados


def _vendedores(session: Session) -> None:
    for numero, nombre in VENDEDORES:
        if _por_nombre(session, Vendedor, "numero", numero) is None:  # type: ignore[arg-type]
            session.add(Vendedor(numero=numero, nombre=nombre))
            print(f"  vendedor {numero}: {nombre}")
    session.commit()


def _packs(session: Session) -> None:
    if session.exec(select(Pack)).first() is not None:
        print("  packs: ya hay, no se suman")
        return

    def categoria(nombre: str) -> int | None:
        c = _por_nombre(session, Categoria, "nombre", nombre)
        return c.id if c else None

    def items(*pedidos: tuple[str, int, bool]) -> list[PackItemCreate]:
        return [
            PackItemCreate(categoria_id=cid, cantidad=cantidad, es_regalo=regalo)
            for nombre, cantidad, regalo in pedidos
            if (cid := categoria(nombre)) is not None
        ]

    packs = [
        PackCreate(
            nombre="iPhone + accesorios de regalo",
            descripcion="Vidrio templado y funda sin cargo con cualquier iPhone.",
            items=items(
                ("iPhone", 1, False), ("Vidrio templado", 1, True), ("Funda/Case", 1, True)
            ),
        ),
        PackCreate(
            nombre="Kit de carga",
            items=items(("Cargador", 1, False), ("Cable", 1, True)),
        ),
    ]
    # Uno con producto fijo: el primer cargador del stock, con un cable de regalo.
    cargador = session.exec(
        select(Producto)
        .join(Modelo)
        .where(Modelo.categoria_id == categoria("Cargador"), Producto.cantidad >= 2)
        .order_by(Producto.id)  # type: ignore[arg-type]
    ).first()
    if cargador is not None:
        packs.append(
            PackCreate(
                nombre="Dos cargadores + cable",
                items=[
                    PackItemCreate(producto_id=cargador.id, cantidad=2),
                    *items(("Cable", 1, True)),
                ],
            )
        )
    for datos in packs:
        if datos.items:
            PackService(UnidadDeTrabajo(session)).crear(datos)
            print(f"  pack {datos.nombre}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--password", default="iconic123", help="Contraseña de los usuarios nuevos")
    parser.add_argument("--productos-igual", action="store_true",
                        help="Sumar productos aunque la tabla ya tenga")  # fmt: skip
    parser.add_argument("--semilla", type=int, default=42, help="Semilla del azar (mismos datos)")
    args = parser.parse_args()

    if get_settings().es_sqlite:
        crear_tablas_sqlite()

    with Session(engine) as session:
        sembrar_catalogos(session)
        print("Cargando datos de prueba…")
        admin = _usuarios(session, args.password)
        _tipo_cambio(session, admin)
        modelos = _catalogos(session)

        if session.exec(select(Producto)).first() is not None and not args.productos_igual:
            print("  productos: la tabla ya tiene, no se suman (usá --productos-igual)")
        else:
            creados = _productos(session, modelos, random.Random(args.semilla))
            print(f"  productos: {creados} creados")
        _vendedores(session)
        _packs(session)
    print("Listo.")


if __name__ == "__main__":
    main()
