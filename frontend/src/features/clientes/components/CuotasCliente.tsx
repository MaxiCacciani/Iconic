import { ArrowClockwiseIcon } from "@phosphor-icons/react"

import { mensajeDeError } from "@/shared/api"
import {
  formatearARS,
  formatearDiaDe,
  formatearFecha,
  formatearUSD,
} from "@/shared/lib/formato"
import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/alert"
import { Badge } from "@/shared/ui/badge"
import { Button } from "@/shared/ui/button"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card"
import { EstadoCuota } from "@/shared/ui/estado-cuota"
import { Skeleton } from "@/shared/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table"

import type { CuotasCliente as Cuotas } from "../api"
import { useCuotasClienteQuery } from "../queries"

/** Saldo, mora y el plan de cada venta en cuotas. Sin ventas en cuotas, no se muestra. */
export function CuotasCliente({ clienteId }: { clienteId: number }) {
  const cuotas = useCuotasClienteQuery(clienteId)

  if (cuotas.isPending)
    return (
      <Skeleton
        className="h-40 w-full max-w-2xl"
        aria-label="Cargando cuotas"
      />
    )
  if (cuotas.isError)
    return (
      <Alert variant="destructive" className="max-w-2xl">
        <AlertTitle>No se pudieron cargar las cuotas</AlertTitle>
        <AlertDescription className="flex flex-col items-start gap-3">
          {mensajeDeError(cuotas.error)}
          <Button variant="outline" size="sm" onClick={() => cuotas.refetch()}>
            <ArrowClockwiseIcon />
            Reintentar
          </Button>
        </AlertDescription>
      </Alert>
    )
  if (cuotas.data.planes.length === 0) return null

  const { saldo_usd, saldo_ars, en_mora, planes } = cuotas.data
  return (
    <section className="flex max-w-2xl flex-col gap-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-heading text-2xl">Cuotas</h2>
        <p className="flex items-center gap-2 tabular-nums">
          {en_mora && <Badge variant="destructive">En mora</Badge>}
          <span className="text-muted-foreground">Saldo</span>
          <span className="font-medium">{formatearUSD(saldo_usd)}</span>
          {saldo_ars !== null && Number(saldo_usd) > 0 && (
            <span className="text-sm text-muted-foreground">
              {formatearARS(saldo_ars)}
            </span>
          )}
        </p>
      </div>
      {planes.map((plan) => (
        <Plan key={plan.venta_id} plan={plan} />
      ))}
    </section>
  )
}

function Plan({ plan }: { plan: Cuotas["planes"][number] }) {
  const { proxima, en_mora_desde: moraDesde } = plan
  return (
    <Card>
      <CardHeader>
        <CardTitle>Venta #{plan.venta_id}</CardTitle>
        <CardDescription className="tabular-nums">
          {formatearDiaDe(plan.fecha)} · {plan.pagadas} de{" "}
          {plan.cantidad_cuotas} pagadas
          {proxima &&
            ` · próxima: ${formatearUSD(proxima.monto_usd)} el ${formatearFecha(proxima.vencimiento)}`}
        </CardDescription>
        <CardAction>
          {moraDesde ? (
            <Badge variant="destructive">
              En mora desde el {formatearFecha(moraDesde)}
            </Badge>
          ) : (
            !proxima && <Badge variant="secondary">Pagado</Badge>
          )}
        </CardAction>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Cuota</TableHead>
                <TableHead>Vencimiento</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead className="text-right">Monto</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody className="tabular-nums">
              {plan.cuotas.map((c) => (
                <TableRow key={c.id}>
                  <TableCell>
                    {c.numero} de {plan.cantidad_cuotas}
                  </TableCell>
                  <TableCell>{formatearFecha(c.vencimiento)}</TableCell>
                  <TableCell>
                    <EstadoCuota estado={c.estado} />
                  </TableCell>
                  <TableCell className="text-right">
                    {formatearUSD(c.monto_usd)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}
