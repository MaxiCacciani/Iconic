"""Lógica de negocio de packs: lista, alta, edición, borrado y aplicar un pack al carrito.

Reglas 4.2: cada ítem es un producto fijo o una categoría. Al aplicar el pack, los fijos
se agregan tal cual (si están disponibles) y, por cada categoría, el primer producto
disponible, sin repetir el mismo equipo. El reparto lo hace `dominio.repartir`.

Decisiones:
- El nombre del pack no se repite, sin distinguir mayúsculas (se elige de una lista).
- Un producto fijo no se repite dentro del pack; uno vendido no se puede sumar (si ya
  estaba, puede quedar: al aplicar se avisa que ya se vendió). Un equipo es una sola
  unidad; de un accesorio no se piden más unidades de las que tiene.
- Aplicar un pack que no se puede completar no es un error: se agrega lo que hay y se
  devuelve lo que falta, para que el front lo avise.
- "El primer disponible" de una categoría es el que lleva más tiempo en el stock.
"""

from collections import defaultdict
from collections.abc import Sequence

from app.common.enums import EstadoProductoEnum
from app.core.excepciones import ErrorDeCampo, NoEncontrado
from app.core.uow import UnidadDeTrabajo
from app.modules.catalogos.models import Capacidad, Categoria, Color, Modelo
from app.modules.packs import dominio
from app.modules.packs.models import Pack, PackItem
from app.modules.packs.repository import PackRepository
from app.modules.packs.schemas import (
    Faltante,
    LineaPackAdmin,
    LineaPackVendedor,
    PackAplicadoAdmin,
    PackAplicadoVendedor,
    PackAplicar,
    PackCreate,
    PackItemCreate,
    PackItemRead,
    PackRead,
    PackUpdate,
    ProductoEnPack,
    Referencia,
)
from app.modules.productos.models import Producto
from app.modules.productos.repository import ProductoRepository
from app.modules.productos.service import ProductoService
from app.modules.tipo_cambio.service import TipoCambioService

_DISPONIBLE = EstadoProductoEnum.disponible


def _ref(x: Categoria | Modelo | Capacidad | Color) -> Referencia:
    return Referencia(id=x.id, nombre=x.nombre)  # type: ignore[arg-type]


def _faltan(n: int) -> str:
    return "falta 1" if n == 1 else f"faltan {n}"


class PackService:
    def __init__(self, uow: UnidadDeTrabajo) -> None:
        self.uow = uow
        self.packs = PackRepository(uow.session)
        self.productos = ProductoRepository(uow.session)

    # ─── Lectura ─────────────────────────────────────────────────────────────
    def listar(self) -> list[PackRead]:
        packs = self.packs.todos()
        return self._leer(packs)

    def obtener(self, id: int) -> PackRead:
        return self._leer([self._detalle(id)])[0]

    # ─── Escritura (solo Administrador; lo resuelve el router) ───────────────
    def crear(self, datos: PackCreate) -> PackRead:
        with self.uow:
            self._nombre_libre(datos.nombre)
            self._validar_items(datos.items, ya_estaban=set())
            pack = self.packs.crear(Pack(nombre=datos.nombre, descripcion=datos.descripcion))
            self._guardar_items(pack, datos.items)
        return self.obtener(pack.id)  # type: ignore[arg-type]

    def actualizar(self, id: int, datos: PackUpdate) -> PackRead:
        with self.uow:
            pack = self._detalle(id)
            cambios = datos.model_dump(exclude_unset=True, exclude={"items"})
            if "nombre" in cambios:
                if cambios["nombre"] is None:
                    raise ErrorDeCampo("nombre", "Este campo es obligatorio.")
                self._nombre_libre(cambios["nombre"], id_en_edicion=id)
            if datos.items is not None:
                ya_estaban = {i.producto_id for i in pack.items if i.producto_id is not None}
                self._validar_items(datos.items, ya_estaban)
            for campo, valor in cambios.items():
                setattr(pack, campo, valor)
            self.packs.actualizar(pack)
            if datos.items is not None:
                for item in list(pack.items):
                    self.uow.session.delete(item)
                self.uow.session.flush()
                self._guardar_items(pack, datos.items)
        self.uow.session.expire_all()
        return self.obtener(id)

    def eliminar(self, id: int) -> None:
        """Lo borra con sus ítems. Las ventas no apuntan a los packs: no hay historial."""
        with self.uow:
            self.packs.eliminar(self._detalle(id))

    # ─── Aplicar ─────────────────────────────────────────────────────────────
    def aplicar(
        self, id: int, datos: PackAplicar, con_costos: bool
    ) -> PackAplicadoAdmin | PackAplicadoVendedor:
        pack = self._detalle(id)
        items = {item.id: item for item in pack.items}
        fijos = [i for i in pack.items if i.producto is not None]
        de_categoria = [i for i in pack.items if i.categoria_id is not None]

        por_categoria: dict[int, list[Producto]] = defaultdict(list)
        if de_categoria:
            categorias = {i.categoria_id for i in de_categoria}
            for p in self.productos.disponibles_por_categoria(categorias):  # type: ignore[arg-type]
                por_categoria[p.modelo.categoria_id].append(p)

        def candidatos(productos: Sequence[Producto]) -> list[dominio.Candidato]:
            return [
                dominio.Candidato(p.id, p.cantidad)  # type: ignore[arg-type]
                for p in productos
                if p.estado == _DISPONIBLE
            ]

        # Primero los fijos: así una categoría no se lleva el producto que un fijo pidió.
        pedidos = [
            dominio.Pedido(i.id, i.cantidad, candidatos([i.producto]))  # type: ignore[arg-type, list-item]
            for i in fijos
        ] + [
            dominio.Pedido(i.id, i.cantidad, candidatos(por_categoria[i.categoria_id]))  # type: ignore[arg-type, index]
            for i in de_categoria
        ]
        ocupadas: dict[int, int] = defaultdict(int)
        for linea in datos.en_carrito:
            ocupadas[linea.producto_id] += linea.cantidad
        reparto = dominio.repartir(pedidos, ocupadas)

        # Las líneas, en el orden del pack.
        orden = {item_id: n for n, item_id in enumerate(items)}
        asignaciones = sorted(reparto.asignaciones, key=lambda a: orden[a.clave])
        productos = {p.id: p for p in self.productos.por_ids({a.producto_id for a in asignaciones})}
        tc = TipoCambioService(self.uow).valor_hoy()
        Linea = LineaPackAdmin if con_costos else LineaPackVendedor
        lineas = [
            Linea(
                pack_item_id=a.clave,
                producto=ProductoService.leer(productos[a.producto_id], tc, con_costos),  # type: ignore[arg-type]
                cantidad=a.cantidad,
                es_regalo=items[a.clave].es_regalo,
            )
            for a in asignaciones
        ]
        faltantes = [
            Faltante(
                pack_item_id=item_id,
                faltan=faltan,
                mensaje=self._por_que_falta(items[item_id], faltan, ocupadas),
            )
            for item_id, faltan in sorted(reparto.faltantes.items(), key=lambda f: orden[f[0]])
        ]
        Aplicado = PackAplicadoAdmin if con_costos else PackAplicadoVendedor
        return Aplicado(
            pack=Referencia(id=pack.id, nombre=pack.nombre),  # type: ignore[arg-type]
            lineas=lineas,  # type: ignore[arg-type]
            faltantes=faltantes,
        )

    @staticmethod
    def _por_que_falta(item: PackItem, faltan: int, ocupadas: dict[int, int]) -> str:
        if item.producto is None:
            nombre = item.categoria.nombre  # type: ignore[union-attr]
            if faltan == item.cantidad:
                return f"{nombre}: no hay disponibles."
            return f"{nombre}: {_faltan(faltan)}, no hay más disponibles."
        p = item.producto
        nombre = f"{p.modelo.nombre} #{p.id}"
        if p.estado == EstadoProductoEnum.vendido:
            return f"{nombre}: ya se vendió."
        if p.estado == EstadoProductoEnum.reservado:
            return f"{nombre}: está reservado."
        if ocupadas.get(p.id, 0) >= p.cantidad:
            return f"{nombre}: ya está en el carrito."
        return f"{nombre}: {_faltan(faltan)}, no hay más disponibles."

    # ─── Reglas ──────────────────────────────────────────────────────────────
    def _detalle(self, id: int) -> Pack:
        pack = self.packs.con_detalle(id)
        if pack is None:
            raise NoEncontrado(f"El pack #{id} no existe.")
        return pack

    def _nombre_libre(self, nombre: str, id_en_edicion: int | None = None) -> None:
        otro = self.packs.por_nombre(nombre)
        if otro is not None and otro.id != id_en_edicion:
            raise ErrorDeCampo("nombre", "Ya hay un pack con ese nombre.")

    def _validar_items(self, items: list[PackItemCreate], ya_estaban: set[int]) -> None:
        """`ya_estaban`: productos fijos que el pack ya tenía. Si se vendieron, pueden
        quedar (al aplicarlo se avisa); lo que no se puede es sumar uno vendido."""
        session = self.uow.session
        vistos: set[int] = set()
        for n, item in enumerate(items):
            if item.categoria_id is not None:
                if session.get(Categoria, item.categoria_id) is None:
                    raise ErrorDeCampo(f"items.{n}.categoria_id", "Esa categoría no existe.")
                continue
            campo = f"items.{n}.producto_id"
            producto = session.get(Producto, item.producto_id)
            if producto is None:
                raise ErrorDeCampo(campo, f"El producto #{item.producto_id} no existe.")
            if producto.id in vistos:
                raise ErrorDeCampo(campo, "Ese producto ya está en el pack.")
            vistos.add(producto.id)  # type: ignore[arg-type]
            vendido = producto.estado == EstadoProductoEnum.vendido
            if vendido and producto.id not in ya_estaban:
                raise ErrorDeCampo(campo, f"El producto #{producto.id} ya se vendió.")
            if not producto.modelo.categoria.tipo.por_cantidad:
                if item.cantidad != 1:
                    raise ErrorDeCampo(
                        f"items.{n}.cantidad",
                        "Es un equipo: va una sola unidad. Para sumar otro, agregá otro ítem.",
                    )
            elif not vendido and item.cantidad > producto.cantidad:
                raise ErrorDeCampo(
                    f"items.{n}.cantidad",
                    f"Del producto #{producto.id} hay {producto.cantidad} "
                    f"{'unidad' if producto.cantidad == 1 else 'unidades'}.",
                )

    def _guardar_items(self, pack: Pack, items: list[PackItemCreate]) -> None:
        for item in items:
            self.uow.session.add(PackItem(pack_id=pack.id, **item.model_dump()))  # type: ignore[arg-type]
        self.uow.session.flush()

    # ─── Armado de las lecturas ──────────────────────────────────────────────
    def _leer(self, packs: Sequence[Pack]) -> list[PackRead]:
        categorias = {i.categoria_id for p in packs for i in p.items if i.categoria_id is not None}
        unidades = self.packs.unidades_disponibles_por_categoria(categorias)

        def item(i: PackItem) -> PackItemRead:
            p = i.producto
            if p is not None:
                disponibles = p.cantidad if p.estado == _DISPONIBLE else 0
            else:
                disponibles = unidades.get(i.categoria_id, 0)  # type: ignore[arg-type]
            return PackItemRead(
                id=i.id,  # type: ignore[arg-type]
                producto=None
                if p is None
                else ProductoEnPack(
                    id=p.id,  # type: ignore[arg-type]
                    categoria=_ref(p.modelo.categoria),
                    modelo=_ref(p.modelo),
                    capacidad=_ref(p.capacidad) if p.capacidad else None,
                    color=_ref(p.color) if p.color else None,
                    imei=p.imei,
                    condicion=p.condicion,
                    estado=p.estado,
                ),
                categoria=None if i.categoria is None else _ref(i.categoria),
                cantidad=i.cantidad,
                es_regalo=i.es_regalo,
                unidades_disponibles=disponibles,
            )

        return [
            PackRead(
                id=p.id,  # type: ignore[arg-type]
                nombre=p.nombre,
                descripcion=p.descripcion,
                items=[item(i) for i in p.items],
            )
            for p in packs
        ]
