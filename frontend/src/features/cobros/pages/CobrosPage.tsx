import { EncabezadoPagina } from "@/shared/ui/encabezado-pagina"
import { ModuloPendiente } from "@/shared/ui/modulo-pendiente"

export function CobrosPage() {
  return (
    <>
      <EncabezadoPagina
        titulo="Cobros"
        descripcion="Agenda de cuotas pendientes, vencidas y cobradas."
      />
      <ModuloPendiente endpoint="GET /cobros" />
    </>
  )
}
