import { pedir, type Schemas } from "@/shared/api"

/** El Vendedor recibe la venta y la cotización sin costos, ganancia ni "bajo costo". */
export type Venta = Schemas["VentaReadAdmin"] | Schemas["VentaReadVendedor"]
export type VentaAdmin = Schemas["VentaReadAdmin"]
export type PaginaVentas =
  Schemas["PaginaVentasAdmin"] | Schemas["Pagina_VentaReadVendedor_"]
export type Cotizacion =
  Schemas["CotizacionAdmin"] | Schemas["CotizacionVendedor"]
export type CotizacionAdmin = Schemas["CotizacionAdmin"]

/** Lo que se manda al cotizar o registrar. Los números van como los escribió el usuario
 * (`"1.250,50"`): los interpreta y valida la API. */
export type DatosVenta = Record<string, unknown>

export const TAMANIO_PAGINA = 50

export function esAdmin<T extends object>(
  x: T
): x is Extract<T, { costo_usd: unknown }> {
  return "costo_usd" in x
}

export const ventasApi = {
  listar: (pagina: number, signal?: AbortSignal) =>
    pedir<PaginaVentas>(`/ventas?pagina=${pagina}&tamanio=${TAMANIO_PAGINA}`, {
      signal,
    }),
  cotizar: (datos: DatosVenta, signal?: AbortSignal) =>
    pedir<Cotizacion>("/ventas/cotizar", {
      method: "POST",
      body: datos,
      signal,
    }),
  crear: (datos: DatosVenta) =>
    pedir<Venta>("/ventas", { method: "POST", body: datos }),
  eliminar: (id: number) => pedir<null>(`/ventas/${id}`, { method: "DELETE" }),
}
