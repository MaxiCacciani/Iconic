import { EncabezadoPagina } from "@/shared/ui/encabezado-pagina"
import { ModuloPendiente } from "@/shared/ui/modulo-pendiente"

export function ReservasPage() {
  return (
    <>
      <EncabezadoPagina
        titulo="Reservas"
        descripcion="Carritos apartados con seña."
      />
      <ModuloPendiente endpoint="GET /reservas" />
    </>
  )
}
