import { WarningIcon } from "@phosphor-icons/react"

import { useAuth } from "@/features/auth"
import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/alert"

import type { TipoCambioHoy } from "../api"
import { FormTipoCambio } from "./FormTipoCambio"

type Props = {
  /** El texto del aviso lo manda el backend (`GET /resumen`). */
  mensaje: string
  onCargado?: (hoy: TipoCambioHoy) => void
}

/** Aviso de TC sin cargar. El Administrador lo carga ahí mismo; el Vendedor solo lo ve. */
export function AvisoTipoCambio({ mensaje, onCargado }: Props) {
  const { puede } = useAuth()
  const puedeCargar = puede("tipo_cambio:editar")

  return (
    <Alert className="border-warning/50 bg-warning/10 px-4 py-3 text-warning-foreground">
      <WarningIcon weight="fill" aria-hidden />
      <AlertTitle className="text-base">{mensaje}</AlertTitle>
      <AlertDescription className="flex flex-col gap-4 text-foreground/80">
        <p>
          {puedeCargar
            ? "Sin TC no se pueden mostrar los montos en pesos. No se arrastra el de ayer: cargá el de hoy."
            : "Lo tiene que cargar un Administrador. Hasta entonces no se muestran los montos en pesos."}
        </p>
        {puedeCargar && <FormTipoCambio onCargado={onCargado} />}
      </AlertDescription>
    </Alert>
  )
}
