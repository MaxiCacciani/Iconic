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

import type { Pack } from "../api"

type Props = {
  /** El pack a borrar; `null` cierra el diálogo. */
  pack: Pack | null
  onCancelar: () => void
  onConfirmar: () => void
}

export function ConfirmarBorrarPack({ pack, onCancelar, onConfirmar }: Props) {
  return (
    <AlertDialog
      open={pack !== null}
      onOpenChange={(abierto) => !abierto && onCancelar()}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>¿Borrar «{pack?.nombre}»?</AlertDialogTitle>
          <AlertDialogDescription>
            Deja de aparecer al armar una venta. Los productos siguen en el
            stock y las ventas ya hechas no cambian. No se puede deshacer.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancelar</AlertDialogCancel>
          <AlertDialogAction variant="destructive" onClick={onConfirmar}>
            Borrar pack
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
