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

import type { Cliente } from "../api"

type Props = {
  /** A quién se va a borrar; `null` cierra el diálogo. */
  cliente: Cliente | null
  onCancelar: () => void
  onConfirmar: () => void
}

export function ConfirmarBorrarCliente({
  cliente,
  onCancelar,
  onConfirmar,
}: Props) {
  return (
    <AlertDialog
      open={cliente !== null}
      onOpenChange={(abierto) => !abierto && onCancelar()}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>¿Borrar a {cliente?.nombre}?</AlertDialogTitle>
          <AlertDialogDescription>
            Cliente #{cliente?.id}. Se elimina y no se puede deshacer. Si tiene
            compras, reservas o reclamos, no se puede borrar.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancelar</AlertDialogCancel>
          <AlertDialogAction variant="destructive" onClick={onConfirmar}>
            Borrar cliente
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
