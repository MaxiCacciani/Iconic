import { EncabezadoPagina } from "@/shared/ui/encabezado-pagina"
import { ModuloPendiente } from "@/shared/ui/modulo-pendiente"

export function PacksPage() {
  return (
    <>
      <EncabezadoPagina
        titulo="Packs"
        descripcion="Combos de productos para aplicar en una venta."
      />
      <ModuloPendiente endpoint="GET /packs" />
    </>
  )
}
