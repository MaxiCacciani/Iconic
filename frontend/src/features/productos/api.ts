import { pedir, type Schemas } from "@/shared/api"

export type ProductoVendedor = Schemas["ProductoReadVendedor"]
export type ProductoAdmin = Schemas["ProductoReadAdmin"]
/** El Vendedor recibe el producto sin costo, ganancia ni margen. */
export type Producto = ProductoVendedor | ProductoAdmin
export type PaginaProductos =
  Schemas["Pagina_ProductoReadAdmin_"] | Schemas["Pagina_ProductoReadVendedor_"]
export type EstadoProducto = Schemas["EstadoProductoEnum"]
export type Condicion = Schemas["Condicion"]
export type NivelBateria = Schemas["NivelBateria"]

export type FiltrosStock = {
  estado?: EstadoProducto
  categoriaId?: number
  condicion?: Condicion
  buscar?: string
  pagina: number
}

/** Lo que se manda al cargar o editar. Los números van como los escribió el usuario
 * (`"1.250,50"`): los interpreta y valida la API. */
export type DatosProducto = Record<string, unknown>

export const TAMANIO_PAGINA = 50

export function tieneCostos(p: Producto): p is ProductoAdmin {
  return "costo_usd" in p
}

function consulta(f: FiltrosStock, tamanio: number): string {
  const params = new URLSearchParams({
    pagina: String(f.pagina),
    tamanio: String(tamanio),
  })
  if (f.estado) params.set("estado", f.estado)
  if (f.categoriaId) params.set("categoria_id", String(f.categoriaId))
  if (f.condicion) params.set("condicion", f.condicion)
  if (f.buscar?.trim()) params.set("buscar", f.buscar.trim())
  return params.toString()
}

export const productosApi = {
  listar: (
    filtros: FiltrosStock,
    signal?: AbortSignal,
    tamanio = TAMANIO_PAGINA
  ) =>
    pedir<PaginaProductos>(`/productos?${consulta(filtros, tamanio)}`, {
      signal,
    }),
  crear: (datos: DatosProducto) =>
    pedir<ProductoAdmin>("/productos", { method: "POST", body: datos }),
  actualizar: (id: number, datos: DatosProducto) =>
    pedir<ProductoAdmin>(`/productos/${id}`, { method: "PATCH", body: datos }),
  eliminar: (id: number) =>
    pedir<null>(`/productos/${id}`, { method: "DELETE" }),
}
