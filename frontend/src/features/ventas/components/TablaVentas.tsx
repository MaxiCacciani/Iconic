import {
  formatearARS,
  formatearDiaDe,
  formatearUSD,
} from "@/shared/lib/formato"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table"

import { esAdmin, type Venta } from "../api"
import { resumenProductos } from "./etiquetas"

type Props = {
  ventas: Venta[]
  onAbrir: (venta: Venta) => void
}

/** Una fila por venta con lo justo para reconocerla. El detalle se abre al tocarla. */
export function TablaVentas({ ventas, onAbrir }: Props) {
  // La ganancia solo llega para el Administrador.
  const conGanancia = ventas.some(esAdmin)

  return (
    <div className="overflow-x-auto rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-28">Venta</TableHead>
            <TableHead>Cliente</TableHead>
            <TableHead>Productos</TableHead>
            <TableHead className="text-right">Total</TableHead>
            {conGanancia && (
              <TableHead className="text-right">Ganancia</TableHead>
            )}
          </TableRow>
        </TableHeader>
        <TableBody>
          {ventas.map((v) => (
            <TableRow
              key={v.id}
              className="cursor-pointer"
              onClick={() => onAbrir(v)}
            >
              <TableCell className="tabular-nums">
                {/* El botón es para el teclado; con el mouse alcanza la fila. */}
                <button
                  type="button"
                  className="rounded-sm font-medium underline-offset-4 hover:underline focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
                  onClick={(e) => {
                    e.stopPropagation()
                    onAbrir(v)
                  }}
                >
                  #{v.id}
                  <span className="sr-only">: ver el detalle</span>
                </button>
                <span className="block text-xs text-muted-foreground">
                  {formatearDiaDe(v.fecha)}
                </span>
              </TableCell>
              <TableCell className="whitespace-normal">
                {v.cliente.nombre}
              </TableCell>
              <TableCell className="whitespace-normal">
                {resumenProductos(v)}
                {v.canje && (
                  <span className="block text-xs text-muted-foreground">
                    Con canje
                  </span>
                )}
              </TableCell>
              <TableCell className="text-right tabular-nums">
                {formatearUSD(v.total_usd)}
                <span className="block text-xs text-muted-foreground">
                  {formatearARS(v.total_ars)}
                </span>
              </TableCell>
              {conGanancia && (
                <TableCell className="text-right tabular-nums">
                  {esAdmin(v) && v.ganancia_usd !== null ? (
                    formatearUSD(v.ganancia_usd)
                  ) : (
                    <span className="text-muted-foreground">Sin costo</span>
                  )}
                </TableCell>
              )}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
