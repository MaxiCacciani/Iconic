import { Link } from "react-router"

import { formatearDNI } from "@/shared/lib/formato"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table"

import type { Cliente } from "../api"

const SIN_DATO = <span className="text-muted-foreground">—</span>

/** Cada fila lleva a la ficha del cliente. */
export function TablaClientes({ clientes }: { clientes: Cliente[] }) {
  return (
    <div className="overflow-hidden rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-16">N.º</TableHead>
            <TableHead>Nombre</TableHead>
            <TableHead>DNI</TableHead>
            <TableHead className="hidden sm:table-cell">Teléfono</TableHead>
            <TableHead className="hidden md:table-cell">Localidad</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {clientes.map((c) => (
            <TableRow key={c.id} className="relative">
              <TableCell className="text-muted-foreground tabular-nums">
                #{c.id}
              </TableCell>
              <TableCell className="font-medium whitespace-normal">
                {/* El link cubre toda la fila (after:inset-0), pero se lee una sola vez. */}
                <Link
                  to={`/clientes/${c.id}`}
                  className="after:absolute after:inset-0 hover:underline focus-visible:outline-none"
                >
                  {c.nombre}
                </Link>
              </TableCell>
              <TableCell className="tabular-nums">
                {c.dni ? formatearDNI(c.dni) : SIN_DATO}
              </TableCell>
              <TableCell className="hidden tabular-nums sm:table-cell">
                {c.telefono ?? SIN_DATO}
              </TableCell>
              <TableCell className="hidden md:table-cell">
                {c.localidad?.nombre ?? SIN_DATO}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
