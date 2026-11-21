import { EncabezadoPagina } from "@/shared/ui/encabezado-pagina"
import { ModuloPendiente } from "@/shared/ui/modulo-pendiente"

export function UsuariosPage() {
  return (
    <>
      <EncabezadoPagina
        titulo="Usuarios"
        descripcion="Accesos al sistema y sus roles."
      />
      <ModuloPendiente endpoint="GET /usuarios" />
    </>
  )
}
