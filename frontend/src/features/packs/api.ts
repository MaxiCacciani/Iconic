import { pedir, type Schemas } from "@/shared/api"

export type Pack = Schemas["PackRead"]
export type ItemPack = Schemas["PackItemRead"]
export type ProductoEnPack = Schemas["ProductoEnPack"]
/** El Vendedor recibe los productos sin costo, ganancia ni margen. */
export type PackAplicado =
  Schemas["PackAplicadoAdmin"] | Schemas["PackAplicadoVendedor"]
export type EnCarrito = Schemas["EnCarrito"]

/** Lo que se manda al guardar. La cantidad va como la escribió el usuario: la valida la API,
 * igual que "producto o categoría, uno de los dos". */
export type DatosItemPack = {
  producto_id: number | null
  categoria_id: number | null
  cantidad: string
  es_regalo: boolean
}
export type DatosPack = {
  nombre: string
  descripcion: string | null
  items: DatosItemPack[]
}

export const packsApi = {
  listar: (signal?: AbortSignal) => pedir<Pack[]>("/packs", { signal }),
  crear: (datos: DatosPack) =>
    pedir<Pack>("/packs", { method: "POST", body: datos }),
  actualizar: (id: number, datos: DatosPack) =>
    pedir<Pack>(`/packs/${id}`, { method: "PATCH", body: datos }),
  eliminar: (id: number) => pedir<null>(`/packs/${id}`, { method: "DELETE" }),
  /** Los productos del pack que hay hoy, sin repetir lo que ya está en el carrito. */
  aplicar: (id: number, enCarrito: EnCarrito[] = []) =>
    pedir<PackAplicado>(`/packs/${id}/aplicar`, {
      method: "POST",
      body: { en_carrito: enCarrito },
    }),
}
