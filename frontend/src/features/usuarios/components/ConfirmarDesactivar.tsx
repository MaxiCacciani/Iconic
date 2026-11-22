import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/shared/ui/alert-dialog"

import type { Usuario } from "../api"

type Props = {
  usuario: Usuario | null
  onCancelar: () => void
  onConfirmar: (usuario: Usuario) => void
}

export function ConfirmarDesactivar({
  usuario,
  onCancelar,
  onConfirmar,
}: Props) {
  return (
    <AlertDialog
      open={usuario !== null}
      onOpenChange={(abierto) => !abierto && onCancelar()}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>¿Desactivar a {usuario?.nombre}?</AlertDialogTitle>
          <AlertDialogDescription>
            No va a poder ingresar y, si tiene la sesión abierta, se le cierra.
            Sus ventas y reservas quedan como están. Lo podés volver a activar
            cuando quieras.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancelar</AlertDialogCancel>
          <AlertDialogAction
            variant="destructive"
            onClick={() => usuario && onConfirmar(usuario)}
          >
            Desactivar
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
