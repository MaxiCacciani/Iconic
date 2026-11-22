import { ArrowClockwiseIcon, InfoIcon } from "@phosphor-icons/react"

import { AvisoTipoCambio, TarjetaTipoCambio } from "@/features/tipo-cambio"
import { mensajeDeError } from "@/shared/api"
import { formatearFecha } from "@/shared/lib/formato"
import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/alert"
import { Button } from "@/shared/ui/button"
import { EncabezadoPagina } from "@/shared/ui/encabezado-pagina"
import { Skeleton } from "@/shared/ui/skeleton"

import { TarjetaStock } from "../components/TarjetaStock"
import { useRefrescarResumen, useResumen } from "../queries"

export function ResumenPage() {
  const resumen = useResumen()
  const refrescar = useRefrescarResumen()

  return (
    <>
      <EncabezadoPagina
        titulo="Resumen"
        descripcion={
          resumen.data
            ? `Lo más importante de hoy, ${formatearFecha(resumen.data.fecha)}.`
            : "Lo más importante de hoy."
        }
      />

      {resumen.isPending ? (
        <div className="flex max-w-2xl flex-col gap-3" aria-busy="true">
          <span className="sr-only">Cargando el resumen…</span>
          <Skeleton className="h-28 w-full" />
        </div>
      ) : resumen.isError ? (
        <Alert variant="destructive" className="max-w-2xl">
          <AlertTitle>No se pudo cargar el resumen</AlertTitle>
          <AlertDescription className="flex flex-col items-start gap-3">
            {mensajeDeError(resumen.error)}
            <Button
              variant="outline"
              size="sm"
              onClick={() => resumen.refetch()}
            >
              <ArrowClockwiseIcon />
              Reintentar
            </Button>
          </AlertDescription>
        </Alert>
      ) : (
        <div className="flex max-w-2xl flex-col gap-4">
          {resumen.data.avisos.map((aviso) =>
            aviso.tipo === "tc_sin_cargar" ? (
              <AvisoTipoCambio
                key={aviso.tipo}
                mensaje={aviso.mensaje}
                onCargado={refrescar}
              />
            ) : (
              <Alert key={aviso.tipo}>
                <InfoIcon aria-hidden />
                <AlertTitle>{aviso.mensaje}</AlertTitle>
              </Alert>
            )
          )}
          {!resumen.data.avisos.some((a) => a.tipo === "tc_sin_cargar") && (
            <TarjetaTipoCambio onCargado={refrescar} />
          )}
          <TarjetaStock stock={resumen.data.stock} />
        </div>
      )}
    </>
  )
}
