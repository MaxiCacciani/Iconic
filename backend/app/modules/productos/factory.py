"""Factory de `Producto`: arma el producto según el tipo de su categoría y lo valida entero.

Reglas 2.1 y 2.2:
- Equipos con IMEI: IMEI obligatorio (15 dígitos, Luhn, sin duplicados en el stock, es
  decir, entre lo no vendido) y batería opcional.
- Consolas: cantidad de controles (0 a 4) y extras.
- Accesorios: por cantidad, varias unidades por fila.
- Lo que el tipo no lleva no se acepta: un AirPods no tiene IMEI ni un cargador, batería.
- Capacidad y color tienen que estar entre las opciones del modelo: sus asignados o, si
  no tiene, los de su categoría (`CatalogoService.opciones_de_modelo`). Al editar, solo
  si cambian o cambia el modelo.
- Precio mayor a 0 y costo entre 0 y el precio.

`desde_canje`: el equipo que entra por plan canje (reglas 4.5). Solo equipos y consolas:
un accesorio por cantidad no se toma en canje.
"""

from decimal import Decimal
from typing import Any

from sqlmodel import func, select

from app.core.excepciones import ErrorDeCampo, ReglaInvalida
from app.core.uow import UnidadDeTrabajo
from app.modules.catalogos.definiciones import POR_SLUG
from app.modules.catalogos.models import Defecto, Modelo, Proveedor
from app.modules.catalogos.semilla import PROVEEDOR_CANJE
from app.modules.catalogos.service import CatalogoService
from app.modules.productos.models import Producto
from app.modules.productos.repository import DefectoRepository, ProductoRepository

# Los campos del producto que se copian tal cual de los datos validados.
CAMPOS = (
    "modelo_id", "capacidad_id", "color_id", "proveedor_id", "condicion", "imei", "bateria",
    "controles", "extras", "cantidad", "precio_usd", "costo_usd",
)  # fmt: skip
_OBLIGATORIOS = ("modelo_id", "proveedor_id", "condicion", "precio_usd", "cantidad")
_OPCIONES = ("capacidad_id", "color_id")  # tienen que estar entre las opciones del modelo


class ProductoFactory:
    def __init__(self, uow: UnidadDeTrabajo) -> None:
        self.session = uow.session
        self.uow = uow
        self.productos = ProductoRepository(uow.session)
        self.defectos = DefectoRepository(uow.session)

    def crear(self, datos: dict[str, Any]) -> Producto:
        """Un producto nuevo, disponible. Todavía no está en la sesión."""
        producto = Producto(**self._validados(datos, producto_id=None, opciones=_OPCIONES))
        producto.defectos = self._defectos(datos)
        return producto

    def desde_canje(self, datos: dict[str, Any], valor: Decimal) -> Producto:
        """El equipo que entrega el cliente: entra disponible, con precio = costo = valor
        del canje y proveedor "Plan canje". El IMEI es opcional, pero si se carga se valida
        igual. Un accesorio por cantidad no entra por canje. Todavía no está en la sesión."""
        modelo = self.session.get(Modelo, datos.get("modelo_id"))
        if modelo is not None and modelo.categoria.tipo.por_cantidad:
            raise ErrorDeCampo(
                "modelo_id",
                f"{modelo.categoria.nombre} no se toma en canje: solo equipos y consolas.",
            )
        proveedor = self.session.exec(
            select(Proveedor).where(func.lower(Proveedor.nombre) == PROVEEDOR_CANJE.lower())
        ).first()
        if proveedor is None:
            raise ReglaInvalida(f"Falta el proveedor «{PROVEEDOR_CANJE}» en Catálogos.")
        datos = datos | {
            "proveedor_id": proveedor.id,
            "precio_usd": valor,
            "costo_usd": valor,
            "cantidad": 1,
        }
        return Producto(
            **self._validados(datos, producto_id=None, opciones=_OPCIONES, imei_obligatorio=False)
        )

    def actualizar(self, producto: Producto, cambios: dict[str, Any]) -> Producto:
        """Aplica los cambios y valida el producto resultante completo."""
        datos = {campo: getattr(producto, campo) for campo in CAMPOS} | {
            k: v for k, v in cambios.items() if k in CAMPOS
        }
        # Color y capacidad se controlan contra las opciones del modelo solo si cambian (o
        # cambia el modelo): si después el admin le sacó esa opción al modelo, el equipo que
        # ya la tiene se sigue pudiendo editar sin tocarla.
        if datos["modelo_id"] != producto.modelo_id:
            opciones = _OPCIONES
        else:
            opciones = tuple(c for c in _OPCIONES if datos[c] != getattr(producto, c))
        validados = self._validados(datos, producto_id=producto.id, opciones=opciones)
        # Sin autoflush: si una consulta grabara antes de tiempo, chocaría con los CHECK.
        with self.session.no_autoflush:
            for campo, valor in validados.items():
                setattr(producto, campo, valor)
            if "defecto_ids" in cambios or "defectos_nuevos" in cambios:
                producto.defectos = self._defectos(cambios)
        return producto

    # ─── Validación ──────────────────────────────────────────────────────────
    def _validados(
        self,
        datos: dict[str, Any],
        producto_id: int | None,
        opciones: tuple[str, ...],
        imei_obligatorio: bool = True,
    ) -> dict[str, Any]:
        d = {campo: datos.get(campo) for campo in CAMPOS}
        for campo in _OBLIGATORIOS:
            if d[campo] is None:
                raise ErrorDeCampo(campo, "Este campo es obligatorio.")
        if isinstance(d["extras"], str) and not d["extras"]:
            d["extras"] = None

        modelo = self.session.get(Modelo, d["modelo_id"])
        if modelo is None:
            raise ErrorDeCampo("modelo_id", "Ese modelo no existe.")
        if self.session.get(Proveedor, d["proveedor_id"]) is None:
            raise ErrorDeCampo("proveedor_id", "Ese proveedor no existe.")

        if "capacidad_id" in opciones:
            self._opcion_del_modelo(d, "capacidad_id", "capacidades", modelo, "Esa capacidad")
        if "color_id" in opciones:
            self._opcion_del_modelo(d, "color_id", "colores", modelo, "Ese color")
        self._segun_tipo(d, modelo, producto_id, imei_obligatorio)

        if d["costo_usd"] is not None and d["costo_usd"] > d["precio_usd"]:
            raise ErrorDeCampo("costo_usd", "El costo no puede ser mayor al precio de venta.")
        return d

    def _opcion_del_modelo(
        self, d: dict[str, Any], campo: str, slug: str, modelo: Modelo, que: str
    ) -> None:
        if d[campo] is None:
            return
        opciones = CatalogoService(self.uow, POR_SLUG[slug]).opciones_de_modelo(modelo.id)  # type: ignore[arg-type]
        if d[campo] not in {o.id for o in opciones}:  # type: ignore[attr-defined]
            raise ErrorDeCampo(campo, f"{que} no está entre las opciones de {modelo.nombre}.")

    def _segun_tipo(
        self, d: dict[str, Any], modelo: Modelo, producto_id: int | None, imei_obligatorio: bool
    ) -> None:
        tipo = modelo.categoria.tipo
        categoria = modelo.categoria.nombre

        if tipo.usa_imei:
            if d["imei"] is None:
                if imei_obligatorio:
                    raise ErrorDeCampo("imei", f"El IMEI es obligatorio en {categoria}.")
            elif (repetido := self.productos.en_stock_por_imei(d["imei"])) and (
                repetido.id != producto_id
            ):
                raise ErrorDeCampo(
                    "imei", f"Ese IMEI ya está en el stock: producto #{repetido.id}."
                )
        elif d["imei"] is not None:
            raise ErrorDeCampo("imei", f"{categoria} no lleva IMEI.")

        if not tipo.usa_bateria and d["bateria"] is not None:
            raise ErrorDeCampo("bateria", f"{categoria} no lleva batería.")

        if not tipo.usa_controles:
            if d["controles"] is not None:
                raise ErrorDeCampo("controles", f"{categoria} no lleva controles.")
            if d["extras"] is not None:
                raise ErrorDeCampo("extras", f"{categoria} no lleva extras.")

        if not tipo.por_cantidad and d["cantidad"] != 1:
            raise ErrorDeCampo(
                "cantidad", f"{categoria} va de a una unidad por fila: la cantidad es 1."
            )

    # ─── Defectos ────────────────────────────────────────────────────────────
    def _defectos(self, datos: dict[str, Any]) -> list[Defecto]:
        """Los elegidos de la lista más los escritos a mano. Uno escrito a mano que ya está
        en la lista (sin distinguir mayúsculas) es ese; si no, se agrega como no común,
        así no aparece para elegir pero queda en el producto."""
        ids = set(datos.get("defecto_ids") or [])
        elegidos = list(self.defectos.por_ids(ids))
        if len(elegidos) != len(ids):
            raise ErrorDeCampo("defecto_ids", "Uno de los defectos no existe.")
        for texto in datos.get("defectos_nuevos") or []:
            defecto = self.defectos.por_descripcion(texto) or self.defectos.crear(
                Defecto(descripcion=texto, es_comun=False)
            )
            if defecto not in elegidos:
                elegidos.append(defecto)
        return sorted(elegidos, key=lambda x: x.descripcion.lower())
