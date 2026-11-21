import { EncabezadoPagina } from "@/shared/ui/encabezado-pagina"
import { ModuloPendiente } from "@/shared/ui/modulo-pendiente"

export function ReclamosPage() {
  return (
    <>
      <EncabezadoPagina
        titulo="Reclamos"
        descripcion="Reclamos de clientes y su seguimiento."
      />
      <ModuloPendiente endpoint="GET /reclamos" />
    </>
  )
}
