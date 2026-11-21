import { pedir, type Schemas } from "@/shared/api"

export type Resumen = Schemas["ResumenRead"]
export type Aviso = Schemas["AvisoRead"]

export const resumenApi = {
  obtener: (signal?: AbortSignal) => pedir<Resumen>("/resumen", { signal }),
}
