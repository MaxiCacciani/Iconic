import { pedir, type Schemas } from "@/shared/api"

export type Cliente = Schemas["ClienteRead"]
export type PaginaClientes = Schemas["Pagina_ClienteRead_"]
export type CuotasCliente = Schemas["CuotasClienteRead"]

/** Lo que se manda al dar de alta o editar. El DNI y el teléfono van como los escribió
 * el usuario (`30.123.456`): los limpia y valida la API. */
export type DatosCliente = {
  nombre: string
  dni: string | null
  telefono: string | null
  localidad_id: number | null
}

export type FiltrosClientes = { buscar?: string; pagina: number }

export const TAMANIO_PAGINA = 50

function consulta({ buscar, pagina }: FiltrosClientes, tamanio: number) {
  const params = new URLSearchParams({
    pagina: String(pagina),
    tamanio: String(tamanio),
  })
  if (buscar?.trim()) params.set("buscar", buscar.trim())
  return params.toString()
}

export const clientesApi = {
  listar: (
    filtros: FiltrosClientes,
    signal?: AbortSignal,
    tamanio = TAMANIO_PAGINA
  ) =>
    pedir<PaginaClientes>(`/clientes?${consulta(filtros, tamanio)}`, {
      signal,
    }),
  obtener: (id: number, signal?: AbortSignal) =>
    pedir<Cliente>(`/clientes/${id}`, { signal }),
  cuotas: (id: number, signal?: AbortSignal) =>
    pedir<CuotasCliente>(`/clientes/${id}/cuotas`, { signal }),
  crear: (datos: DatosCliente) =>
    pedir<Cliente>("/clientes", { method: "POST", body: datos }),
  actualizar: (id: number, datos: DatosCliente) =>
    pedir<Cliente>(`/clientes/${id}`, { method: "PATCH", body: datos }),
  eliminar: (id: number) =>
    pedir<null>(`/clientes/${id}`, { method: "DELETE" }),
}
