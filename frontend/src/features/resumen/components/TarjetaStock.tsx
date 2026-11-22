import { ArrowRightIcon } from "@phosphor-icons/react"
import { Link } from "react-router"

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

const unidades = (n: number) =>
  n === 1 ? "1 unidad" : `${n.toLocaleString("es-AR")} unidades`

const cuantas = (n: number, palabra: string) =>
  `${n.toLocaleString("es-AR")} ${palabra}${n === 1 ? "" : "s"}`

/** Stock disponible en unidades (un accesorio por cantidad suma todas las suyas). */
export function TarjetaStock({ stock }: { stock: Resumen["stock"] }) {
  return (
    <Card className="max-w-md">
      <CardHeader>
        <CardDescription>Stock a la venta</CardDescription>
        <CardTitle className="font-heading text-4xl tabular-nums">
          {unidades(stock.disponibles)}
        </CardTitle>
        <CardAction>
          <Button variant="outline" size="sm" asChild>
            <Link to="/productos">
              Ver stock
              <ArrowRightIcon />
            </Link>
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground tabular-nums">
          {stock.disponibles === 0
            ? "No hay productos disponibles."
            : stock.nuevas === stock.disponibles
              ? "Todas nuevas."
              : stock.nuevas === 0
                ? "Todas usadas."
                : `${cuantas(stock.nuevas, "nueva")} y ${cuantas(stock.disponibles - stock.nuevas, "usada")}.`}
        </p>
      </CardContent>
    </Card>
  )
}
