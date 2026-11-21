import { EncabezadoPagina } from "@/shared/ui/encabezado-pagina"
import { ModuloPendiente } from "@/shared/ui/modulo-pendiente"

export function ResumenPage() {
  return (
    <>
      <EncabezadoPagina
        titulo="Resumen"
        descripcion="Lo más importante del día y el tipo de cambio."
      />
      <ModuloPendiente endpoint="GET /resumen" />
    </>
  )
}
