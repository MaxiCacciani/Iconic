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

import type { Venta } from "../api"

type Props = {
  /** La venta a borrar; `null` cierra el diálogo. */
  venta: Venta | null
  onCancelar: () => void
  onConfirmar: () => void
}

export function ConfirmarBorrarVenta({
  venta,
  onCancelar,
  onConfirmar,
}: Props) {
  return (
    <AlertDialog
      open={venta !== null}
      onOpenChange={(abierto) => !abierto && onCancelar()}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>¿Borrar la venta #{venta?.id}?</AlertDialogTitle>
          <AlertDialogDescription>
            Los productos vuelven al stock
            {venta?.canje && " y el equipo del canje sale del stock"}. No se
            puede deshacer.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancelar</AlertDialogCancel>
          <AlertDialogAction variant="destructive" onClick={onConfirmar}>
            Borrar venta
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
