import { EncabezadoPagina } from "@/shared/ui/encabezado-pagina"
import { ModuloPendiente } from "@/shared/ui/modulo-pendiente"

export function GarantiasPage() {
  return (
    <>
      <EncabezadoPagina
        titulo="Garantías"
        descripcion="Comprobantes de garantía de cada venta."
      />
      <ModuloPendiente endpoint="GET /garantias" />
    </>
  )
}
