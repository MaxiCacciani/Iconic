import { pedir, type Schemas } from "@/shared/api"

export type Vendedor = Schemas["VendedorRead"]

/** Lo que se manda al dar de alta o editar. El número va como lo escribió el usuario: lo
 * valida la API. `null` en una edición es "lo borró" (la API responde que es obligatorio). */
export type DatosVendedor = { numero?: string | null; nombre: string }

export const vendedoresApi = {
  listar: (signal?: AbortSignal) =>
    pedir<Vendedor[]>("/vendedores", { signal }),
  crear: (datos: DatosVendedor) =>
    pedir<Vendedor>("/vendedores", { method: "POST", body: datos }),
  actualizar: (id: number, datos: DatosVendedor) =>
    pedir<Vendedor>(`/vendedores/${id}`, { method: "PATCH", body: datos }),
  eliminar: (id: number) =>
    pedir<null>(`/vendedores/${id}`, { method: "DELETE" }),
}
