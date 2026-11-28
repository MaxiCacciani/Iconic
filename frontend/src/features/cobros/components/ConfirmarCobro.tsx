import { formatearUSD } from "@/shared/lib/formato"
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

import type { CobroAgenda } from "../api"

type Props = {
  /** La cuota a cobrar; `null` cierra el diálogo. */
  cuota: CobroAgenda | null
  onCancelar: () => void
  onConfirmar: () => void
}

/** Se confirma porque no se puede deshacer. */
export function ConfirmarCobro({ cuota, onCancelar, onConfirmar }: Props) {
  return (
    <AlertDialog
      open={cuota !== null}
      onOpenChange={(abierto) => !abierto && onCancelar()}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            ¿Cobrar {cuota && formatearUSD(cuota.monto_usd)}?
          </AlertDialogTitle>
          <AlertDialogDescription>
            Cuota {cuota?.numero} de {cuota?.cantidad_cuotas} de{" "}
            {cuota?.cliente.nombre} (venta #{cuota?.venta_id}). Queda marcada
            como cobrada y no se puede deshacer.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancelar</AlertDialogCancel>
          <AlertDialogAction onClick={onConfirmar}>
            Marcar como cobrada
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
