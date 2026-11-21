import { EncabezadoPagina } from "@/shared/ui/encabezado-pagina"
import { ModuloPendiente } from "@/shared/ui/modulo-pendiente"

export function ProductosPage() {
  return (
    <>
      <EncabezadoPagina
        titulo="Productos"
        descripcion="Stock de equipos y accesorios."
      />
      <ModuloPendiente endpoint="GET /productos" />
    </>
  )
}
