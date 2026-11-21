import { ArrowClockwiseIcon, PencilSimpleIcon } from "@phosphor-icons/react"
import { useState } from "react"

import { useAuth } from "@/features/auth"
import { mensajeDeError } from "@/shared/api"
import { formatearARS, formatearFecha } from "@/shared/lib/formato"
import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/alert"
import { Button } from "@/shared/ui/button"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card"
import { Skeleton } from "@/shared/ui/skeleton"

import type { TipoCambioHoy } from "../api"
import { useTipoCambioHoy } from "../queries"
import { FormTipoCambio } from "./FormTipoCambio"

type Props = { onCargado?: (hoy: TipoCambioHoy) => void }

/** TC de hoy ya cargado. Si falta, no se muestra: de eso se ocupa `AvisoTipoCambio`. */
export function TarjetaTipoCambio({ onCargado }: Props) {
  const { puede } = useAuth()
  const tc = useTipoCambioHoy()
  const [editando, setEditando] = useState(false)

  if (tc.isPending)
    return (
      <Card className="max-w-md" aria-busy="true">
        <span className="sr-only">Cargando el tipo de cambio…</span>
        <CardHeader>
          <Skeleton className="h-4 w-32" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-9 w-40" />
        </CardContent>
      </Card>
    )

  if (tc.isError)
    return (
      <Alert variant="destructive" className="max-w-md">
        <AlertTitle>No se pudo leer el tipo de cambio</AlertTitle>
        <AlertDescription className="flex flex-col items-start gap-3">
          {mensajeDeError(tc.error)}
          <Button variant="outline" size="sm" onClick={() => tc.refetch()}>
            <ArrowClockwiseIcon />
            Reintentar
          </Button>
        </AlertDescription>
      </Alert>
    )

  const { valor_ars, fecha, cargado_por } = tc.data
  if (!valor_ars) return null

  return (
    <Card className="max-w-md">
      <CardHeader>
        <CardDescription>
          Tipo de cambio · {formatearFecha(fecha)}
        </CardDescription>
        <CardTitle className="font-heading text-4xl tabular-nums">
          {formatearARS(valor_ars)}
        </CardTitle>
        {puede("tipo_cambio:editar") && !editando && (
          <CardAction>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setEditando(true)}
            >
              <PencilSimpleIcon />
              Corregir
            </Button>
          </CardAction>
        )}
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <p className="text-sm text-muted-foreground">
          Pesos por cada dólar
          {cargado_por && <> · Lo cargó {cargado_por}</>}
        </p>
        {editando && (
          <div className="flex flex-col gap-3 border-t pt-4">
            <p className="text-sm text-muted-foreground">
              Las ventas ya registradas conservan el TC con el que se hicieron.
            </p>
            <FormTipoCambio
              valorActual={valor_ars}
              onCancelar={() => setEditando(false)}
              onCargado={(hoy) => {
                setEditando(false)
                onCargado?.(hoy)
              }}
            />
          </div>
        )}
      </CardContent>
    </Card>
  )
}
