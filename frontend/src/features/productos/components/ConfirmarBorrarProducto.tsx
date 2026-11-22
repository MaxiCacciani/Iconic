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

import type { Producto } from "../api"

type Props = {
  /** Lo que se va a borrar; `null` cierra el diálogo. */
  producto: Producto | null
  onCancelar: () => void
  onConfirmar: () => void
}

export function ConfirmarBorrarProducto({
  producto,
  onCancelar,
  onConfirmar,
}: Props) {
  return (
    <AlertDialog
      open={producto !== null}
      onOpenChange={(abierto) => !abierto && onCancelar()}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            ¿Borrar el producto #{producto?.id}?
          </AlertDialogTitle>
          <AlertDialogDescription>
            {producto?.categoria.nombre} {producto?.modelo.nombre}
            {producto?.imei ? `, IMEI ${producto.imei}` : ""}. Se elimina del
            stock y no se puede deshacer.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancelar</AlertDialogCancel>
          <AlertDialogAction variant="destructive" onClick={onConfirmar}>
            Borrar producto
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
