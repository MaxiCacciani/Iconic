import { Link } from "react-router"

import {
  formatearARS,
  formatearFecha,
  formatearUSD,
} from "@/shared/lib/formato"
import { Button } from "@/shared/ui/button"
import { EstadoCuota } from "@/shared/ui/estado-cuota"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table"

import type { CobroAgenda } from "../api"

type Props = {
  cobros: CobroAgenda[]
  onCobrar: (cuota: CobroAgenda) => void
  /** La cuota que se está marcando, para no cobrarla dos veces. */
  cobrando: number | null
}

export function TablaAgenda({ cobros, onCobrar, cobrando }: Props) {
  return (
    <div className="overflow-x-auto rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Vencimiento</TableHead>
            <TableHead>Cliente</TableHead>
            <TableHead>Cuota</TableHead>
            <TableHead className="text-right">Monto</TableHead>
            <TableHead>Estado</TableHead>
            <TableHead className="w-32">
              <span className="sr-only">Acciones</span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody className="tabular-nums">
          {cobros.map((c) => (
            <TableRow key={c.id}>
              <TableCell>{formatearFecha(c.vencimiento)}</TableCell>
              <TableCell className="whitespace-normal">
                <Link
                  to={`/clientes/${c.cliente.id}`}
                  className="underline-offset-4 hover:underline"
                >
                  {c.cliente.nombre}
                </Link>
              </TableCell>
              <TableCell>
                {c.numero} de {c.cantidad_cuotas}
                <span className="block text-xs text-muted-foreground">
                  Venta #{c.venta_id}
                </span>
              </TableCell>
              <TableCell className="text-right">
                {formatearUSD(c.monto_usd)}
                {c.monto_ars !== null && (
                  <span className="block text-xs text-muted-foreground">
                    {formatearARS(c.monto_ars)}
                  </span>
                )}
              </TableCell>
              <TableCell>
                <EstadoCuota estado={c.estado} />
              </TableCell>
              <TableCell className="text-right">
                {c.estado !== "cobrada" && (
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={cobrando === c.id}
                    onClick={() => onCobrar(c)}
                  >
                    Cobrar…
                  </Button>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
