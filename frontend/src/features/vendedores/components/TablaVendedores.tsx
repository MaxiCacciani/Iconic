import {
  DotsThreeVerticalIcon,
  PencilSimpleIcon,
  TrashIcon,
} from "@phosphor-icons/react"

import { Button } from "@/shared/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table"

import type { Vendedor } from "../api"

type Props = {
  vendedores: Vendedor[]
  onEditar: (vendedor: Vendedor) => void
  onBorrar: (vendedor: Vendedor) => void
}

/** Ordenados por número, que es lo que se carga en la venta. */
export function TablaVendedores({ vendedores, onEditar, onBorrar }: Props) {
  return (
    <div className="overflow-hidden rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-24">N.º</TableHead>
            <TableHead>Nombre</TableHead>
            <TableHead className="w-12">
              <span className="sr-only">Acciones</span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {vendedores.map((v) => (
            <TableRow key={v.id}>
              <TableCell className="font-medium tabular-nums">
                {v.numero}
              </TableCell>
              <TableCell className="whitespace-normal">{v.nombre}</TableCell>
              <TableCell>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      aria-label={`Acciones para ${v.nombre}`}
                    >
                      <DotsThreeVerticalIcon />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onSelect={() => onEditar(v)}>
                      <PencilSimpleIcon />
                      Editar
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      variant="destructive"
                      onSelect={() => onBorrar(v)}
                    >
                      <TrashIcon />
                      Borrar
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
