import { EncabezadoPagina } from "@/shared/ui/encabezado-pagina"
import { ModuloPendiente } from "@/shared/ui/modulo-pendiente"

export function VentasPage() {
  return (
    <>
      <EncabezadoPagina
        titulo="Ventas"
        descripcion="Registrar ventas y ver las ya registradas."
      />
      <ModuloPendiente endpoint="GET /ventas" />
    </>
  )
}
