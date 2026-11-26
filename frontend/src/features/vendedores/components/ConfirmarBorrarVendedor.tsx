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

import type { Vendedor } from "../api"

type Props = {
  /** A quién se va a borrar; `null` cierra el diálogo. */
  vendedor: Vendedor | null
  onCancelar: () => void
  onConfirmar: () => void
}

export function ConfirmarBorrarVendedor({
  vendedor,
  onCancelar,
  onConfirmar,
}: Props) {
  return (
    <AlertDialog
      open={vendedor !== null}
      onOpenChange={(abierto) => !abierto && onCancelar()}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>¿Borrar a {vendedor?.nombre}?</AlertDialogTitle>
          <AlertDialogDescription>
            Vendedor n.º {vendedor?.numero}. Se elimina de la lista y no se
            puede deshacer. Si ya tiene ventas, no se puede borrar.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancelar</AlertDialogCancel>
          <AlertDialogAction variant="destructive" onClick={onConfirmar}>
            Borrar vendedor
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
