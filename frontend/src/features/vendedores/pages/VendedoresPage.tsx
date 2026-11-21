import { EncabezadoPagina } from "@/shared/ui/encabezado-pagina"
import { ModuloPendiente } from "@/shared/ui/modulo-pendiente"

export function VendedoresPage() {
  return (
    <>
      <EncabezadoPagina
        titulo="Vendedores"
        descripcion="Números y nombres de los vendedores."
      />
      <ModuloPendiente endpoint="GET /vendedores" />
    </>
  )
}
