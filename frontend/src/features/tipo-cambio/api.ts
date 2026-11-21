import { pedir, type Schemas } from "@/shared/api"

export type TipoCambioHoy = Schemas["TipoCambioHoyRead"]
export type TipoCambioCarga = Schemas["TipoCambioUpdate"]

export const tipoCambioApi = {
  hoy: (signal?: AbortSignal) =>
    pedir<TipoCambioHoy>("/tipo-cambio/hoy", { signal }),
  cargarHoy: (datos: TipoCambioCarga) =>
    pedir<TipoCambioHoy>("/tipo-cambio/hoy", { method: "PUT", body: datos }),
}
