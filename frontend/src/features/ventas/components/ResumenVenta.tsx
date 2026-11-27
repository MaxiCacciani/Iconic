import { CheckIcon } from "@phosphor-icons/react"

import { AvisoTipoCambio, useTipoCambioHoy } from "@/features/tipo-cambio"
import { formatearARS, formatearUSD } from "@/shared/lib/formato"
import { cn } from "@/shared/lib/utils"
import { Alert, AlertDescription } from "@/shared/ui/alert"
import { Button } from "@/shared/ui/button"
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card"
import { Separator } from "@/shared/ui/separator"
import { Spinner } from "@/shared/ui/spinner"

import { esAdmin, type Cotizacion } from "../api"

type Props = {
  cotizacion: Cotizacion | undefined
  sinProductos: boolean
  /** Mientras llega la cotización nueva se ve la anterior, atenuada. */
  actualizando: boolean
  /** Un error que no es de un campo (por ejemplo, la venta sin TC). */
  error: string | null
  onTcCargado: () => void
  onConfirmar: () => void
  confirmando: boolean
}

/** Lo que devuelve `POST /ventas/cotizar`, tal cual. El front no suma nada. */
export function ResumenVenta({
  cotizacion: c,
  sinProductos,
  actualizando,
  error,
  onTcCargado,
  onConfirmar,
  confirmando,
}: Props) {
  const tc = useTipoCambioHoy()

  return (
    <Card className="xl:sticky xl:top-4">
      <CardHeader>
        <CardTitle className="font-heading text-xl">Resumen</CardTitle>
      </CardHeader>
      <CardContent
        aria-live="polite"
        aria-busy={actualizando || undefined}
        className={cn(
          "flex flex-col gap-3",
          actualizando && "opacity-60 transition-opacity"
        )}
      >
        {!c ? (
          <p className="text-sm text-muted-foreground">
            {sinProductos
              ? "Agregá productos para ver el total."
              : "Corregí los datos marcados para ver el total."}
          </p>
        ) : (
          <>
            <Monto etiqueta="Total" usd={c.total_usd} ars={c.total_ars} />
            {Number(c.canje_usd) > 0 && (
              <Monto etiqueta="Canje" usd={c.canje_usd} restar />
            )}
            <Separator />
            <div className="flex flex-col gap-0.5">
              <span className="text-sm text-muted-foreground">
                Saldo a pagar
              </span>
              <span className="font-heading text-3xl tabular-nums">
                {formatearUSD(c.saldo_usd)}
              </span>
              {c.saldo_ars !== null && (
                <span className="text-sm text-muted-foreground tabular-nums">
                  {formatearARS(c.saldo_ars)}
                </span>
              )}
            </div>
            {esAdmin(c) && (
              <>
                <Separator />
                <Monto etiqueta="Costo" usd={c.costo_usd} />
                <Monto etiqueta="Ganancia" usd={c.ganancia_usd} />
                {c.margen_pct !== null && (
                  <p className="flex justify-between text-sm tabular-nums">
                    <span className="text-muted-foreground">Margen</span>
                    {c.margen_pct.replace(".", ",")} %
                  </p>
                )}
              </>
            )}
          </>
        )}

        {tc.data?.valor_ars === null && (
          <AvisoTipoCambio
            mensaje="Sin el tipo de cambio de hoy no se puede registrar la venta."
            onCargado={onTcCargado}
          />
        )}
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
      </CardContent>
      <CardFooter>
        <Button className="w-full" onClick={onConfirmar} disabled={confirmando}>
          {confirmando ? <Spinner /> : <CheckIcon />}
          {confirmando ? "Registrando…" : "Confirmar venta"}
        </Button>
      </CardFooter>
    </Card>
  )
}

function Monto({
  etiqueta,
  usd,
  ars,
  restar = false,
}: {
  etiqueta: string
  usd: string | null
  ars?: string | null
  restar?: boolean
}) {
  return (
    <p className="flex justify-between gap-4 text-sm tabular-nums">
      <span className="text-muted-foreground">{etiqueta}</span>
      <span className="text-right">
        {usd === null
          ? "Sin costo cargado"
          : `${restar ? "− " : ""}${formatearUSD(usd)}`}
        {ars && (
          <span className="block text-xs text-muted-foreground">
            {formatearARS(ars)}
          </span>
        )}
      </span>
    </p>
  )
}
