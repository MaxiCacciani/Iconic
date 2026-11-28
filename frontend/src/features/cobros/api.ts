import { pedir, type Schemas } from "@/shared/api"

export type Agenda = Schemas["AgendaRead"]
export type CobroAgenda = Schemas["CobroAgendaRead"]

/** Sin mes, la API devuelve el actual (en Argentina). */
export type Mes = { anio: number; mes: number } | null

export const cobrosApi = {
  agenda: (mes: Mes, signal?: AbortSignal) =>
    pedir<Agenda>(mes ? `/cobros?anio=${mes.anio}&mes=${mes.mes}` : "/cobros", {
      signal,
    }),
  cobrar: (id: number) =>
    pedir<CobroAgenda>(`/cobros/${id}/cobrar`, { method: "POST" }),
}
