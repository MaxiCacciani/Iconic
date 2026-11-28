import {
  ArrowClockwiseIcon,
  CaretLeftIcon,
  CaretRightIcon,
} from "@phosphor-icons/react"
import { useState } from "react"
import { useSearchParams } from "react-router"
import { toast } from "sonner"

import { mensajeDeError } from "@/shared/api"
import { formatearMes, formatearUSD } from "@/shared/lib/formato"
import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/alert"
import { Button } from "@/shared/ui/button"
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/shared/ui/empty"
import { EncabezadoPagina } from "@/shared/ui/encabezado-pagina"
import { Skeleton } from "@/shared/ui/skeleton"

import type { Agenda, CobroAgenda, Mes } from "../api"
import { ConfirmarCobro } from "../components/ConfirmarCobro"
import { TablaAgenda } from "../components/TablaAgenda"
import { useAgendaQuery, useCobrar } from "../queries"

/** `?mes=2026-11`. Sin mes (o uno mal escrito), el actual. */
function leerMes(texto: string | null): Mes {
  const partes = /^(\d{4})-(\d{1,2})$/.exec(texto ?? "")
  if (!partes) return null
  const [anio, mes] = [Number(partes[1]), Number(partes[2])]
  return mes >= 1 && mes <= 12 ? { anio, mes } : null
}

function mover(anio: number, mes: number, delta: number): string {
  const indice = anio * 12 + mes - 1 + delta
  return `${Math.floor(indice / 12)}-${(indice % 12) + 1}`
}

export function CobrosPage() {
  const [params, setParams] = useSearchParams()
  const agenda = useAgendaQuery(leerMes(params.get("mes")))
  const cobrar = useCobrar()
  const [aCobrar, setACobrar] = useState<CobroAgenda | null>(null)

  function confirmar(cuota: CobroAgenda) {
    setACobrar(null)
    cobrar.mutate(cuota.id, {
      onSuccess: () =>
        toast.success(
          `Se cobró la cuota ${cuota.numero} de ${cuota.cliente.nombre}.`
        ),
      onError: (error) => toast.error(mensajeDeError(error)),
    })
  }

  return (
    <>
      <EncabezadoPagina
        titulo="Cobros"
        descripcion="Las cuotas que vencen en el mes. Desde acá se marcan como cobradas."
      />

      {agenda.isPending ? (
        <div className="flex flex-col gap-2" aria-busy="true">
          <span className="sr-only">Cargando la agenda…</span>
          <Skeleton className="h-10 w-72" />
          {Array.from({ length: 5 }, (_, i) => (
            <Skeleton key={i} className="h-14 w-full" />
          ))}
        </div>
      ) : agenda.isError ? (
        <Alert variant="destructive">
          <AlertTitle>No se pudo cargar la agenda</AlertTitle>
          <AlertDescription className="flex flex-col items-start gap-3">
            {mensajeDeError(agenda.error)}
            <Button
              variant="outline"
              size="sm"
              onClick={() => agenda.refetch()}
            >
              <ArrowClockwiseIcon />
              Reintentar
            </Button>
          </AlertDescription>
        </Alert>
      ) : (
        <MesDeAgenda
          agenda={agenda.data}
          actualizando={agenda.isPlaceholderData}
          onIrA={(delta) =>
            setParams({ mes: mover(agenda.data.anio, agenda.data.mes, delta) })
          }
          onCobrar={setACobrar}
          cobrando={cobrar.isPending ? (cobrar.variables ?? null) : null}
        />
      )}

      <ConfirmarCobro
        cuota={aCobrar}
        onCancelar={() => setACobrar(null)}
        onConfirmar={() => aCobrar && confirmar(aCobrar)}
      />
    </>
  )
}

function MesDeAgenda({
  agenda: a,
  actualizando,
  onIrA,
  onCobrar,
  cobrando,
}: {
  agenda: Agenda
  actualizando: boolean
  onIrA: (delta: number) => void
  onCobrar: (cuota: CobroAgenda) => void
  cobrando: number | null
}) {
  const titulo = formatearMes(a.anio, a.mes)
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <nav aria-label="Meses" className="flex items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            aria-label="Mes anterior"
            onClick={() => onIrA(-1)}
          >
            <CaretLeftIcon />
          </Button>
          <h2
            aria-live="polite"
            className="min-w-48 text-center font-heading text-2xl first-letter:uppercase"
          >
            {titulo}
          </h2>
          <Button
            variant="outline"
            size="icon"
            aria-label="Mes siguiente"
            onClick={() => onIrA(1)}
          >
            <CaretRightIcon />
          </Button>
        </nav>
        {a.cobros.length > 0 && (
          <p className="text-sm text-muted-foreground tabular-nums">
            {formatearUSD(a.total_usd)} en el mes · cobrado{" "}
            {formatearUSD(a.cobrado_usd)} · falta{" "}
            <span className="font-medium text-foreground">
              {formatearUSD(a.pendiente_usd)}
            </span>
          </p>
        )}
      </div>

      <div
        aria-busy={actualizando || undefined}
        className={actualizando ? "opacity-60 transition-opacity" : undefined}
      >
        {a.cobros.length === 0 ? (
          <Empty className="border">
            <EmptyHeader>
              <EmptyTitle>Sin cuotas en {titulo}</EmptyTitle>
              <EmptyDescription>
                Las cuotas de las ventas en cuotas aparecen en el mes en que
                vencen.
              </EmptyDescription>
            </EmptyHeader>
          </Empty>
        ) : (
          <TablaAgenda
            cobros={a.cobros}
            onCobrar={onCobrar}
            cobrando={cobrando}
          />
        )}
      </div>
    </div>
  )
}
