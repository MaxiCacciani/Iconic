import { EncabezadoPagina } from "@/shared/ui/encabezado-pagina"
import { ModuloPendiente } from "@/shared/ui/modulo-pendiente"

export function ClientesPage() {
  return (
    <>
      <EncabezadoPagina
        titulo="Clientes"
        descripcion="Clientes, saldos y reclamos."
      />
      <ModuloPendiente endpoint="GET /clientes" />
    </>
  )
}
