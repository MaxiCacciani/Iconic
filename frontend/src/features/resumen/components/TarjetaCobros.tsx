import { ArrowRightIcon } from "@phosphor-icons/react"
import { Link } from "react-router"

import { formatearUSD } from "@/shared/lib/formato"
import { Button } from "@/shared/ui/button"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card"

import type { Resumen } from "../api"

type Cobros = NonNullable<Resumen["cobros_del_mes"]>

/** Las cuotas que vencen este mes. Solo le llega al Administrador. */
export function TarjetaCobros({ cobros }: { cobros: Cobros }) {
  const sinCuotas = Number(cobros.total_usd) === 0
  return (
    <Card className="max-w-md">
      <CardHeader>
        <CardDescription>Falta cobrar este mes</CardDescription>
        <CardTitle className="font-heading text-4xl tabular-nums">
          {formatearUSD(cobros.pendiente_usd)}
        </CardTitle>
        <CardAction>
          <Button variant="outline" size="sm" asChild>
            <Link to="/cobros">
              Ver agenda
              <ArrowRightIcon />
            </Link>
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground tabular-nums">
          {sinCuotas
            ? "No vencen cuotas este mes."
            : `Cobrado ${formatearUSD(cobros.cobrado_usd)} de ${formatearUSD(cobros.total_usd)}.`}
        </p>
      </CardContent>
    </Card>
  )
}
