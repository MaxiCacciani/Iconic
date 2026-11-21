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

type Props = {
  /** Lo que se va a borrar; `null` cierra el diálogo. */
  texto: string | null
  onCancelar: () => void
  onConfirmar: () => void
}

export function ConfirmarBorrar({ texto, onCancelar, onConfirmar }: Props) {
  return (
    <AlertDialog
      open={texto !== null}
      onOpenChange={(abierto) => !abierto && onCancelar()}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>¿Borrar «{texto}»?</AlertDialogTitle>
          <AlertDialogDescription>
            Deja de aparecer para elegir y no se puede deshacer. Si ya se usa en
            algún producto, cliente, venta o reclamo, no se va a poder borrar.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancelar</AlertDialogCancel>
          <AlertDialogAction variant="destructive" onClick={onConfirmar}>
            Borrar
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
