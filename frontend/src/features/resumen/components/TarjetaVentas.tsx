import { ArrowRightIcon } from "@phosphor-icons/react"
import { Link } from "react-router"

import { formatearARS, formatearUSD } from "@/shared/lib/formato"
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

const cuantas = (n: number) => (n === 1 ? "1 venta" : `${n} ventas`)

/** Ventas de hoy y de los últimos 7 días. En pesos, cada una con su TC congelado. Al
 * Vendedor la API le manda solo las suyas (`solo_propias`). */
export function TarjetaVentas({ ventas }: { ventas: Resumen["ventas"] }) {
  const { hoy, ultimos_7_dias: semana, solo_propias: propias } = ventas
  return (
    <Card className="max-w-md">
      <CardHeader>
        <CardDescription>
          {propias ? "Tus ventas de hoy" : "Ventas de hoy"}
        </CardDescription>
        <CardTitle className="font-heading text-4xl tabular-nums">
          {formatearUSD(hoy.total_usd)}
        </CardTitle>
        <CardAction>
          <Button variant="outline" size="sm" asChild>
            <Link to="/ventas">
              Ver ventas
              <ArrowRightIcon />
            </Link>
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent className="flex flex-col gap-1 text-sm text-muted-foreground tabular-nums">
        <p>
          {hoy.cantidad === 0
            ? propias
              ? "Todavía no registraste ventas hoy."
              : "Todavía no hubo ventas hoy."
            : `${cuantas(hoy.cantidad)} · ${formatearARS(hoy.total_ars)}`}
        </p>
        <p>
          Últimos 7 días: {formatearUSD(semana.total_usd)} en{" "}
          {cuantas(semana.cantidad)}
        </p>
      </CardContent>
    </Card>
  )
}
