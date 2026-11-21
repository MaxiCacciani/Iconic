import {
  DotsThreeVerticalIcon,
  PencilSimpleIcon,
  ProhibitIcon,
  CheckCircleIcon,
} from "@phosphor-icons/react"

import { formatearFecha } from "@/shared/lib/formato"
import { Badge } from "@/shared/ui/badge"
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

import type { Usuario } from "../api"
import { NOMBRE_ROL } from "../roles"

type Props = {
  usuarios: Usuario[]
  idPropio: number | undefined
  onEditar: (usuario: Usuario) => void
  onCambiarActivo: (usuario: Usuario) => void
}

export function TablaUsuarios({
  usuarios,
  idPropio,
  onEditar,
  onCambiarActivo,
}: Props) {
  return (
    <div className="overflow-hidden rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Nombre</TableHead>
            <TableHead className="hidden md:table-cell">Email</TableHead>
            <TableHead>Rol</TableHead>
            <TableHead>Estado</TableHead>
            <TableHead className="hidden text-right lg:table-cell">
              Alta
            </TableHead>
            <TableHead className="w-12">
              <span className="sr-only">Acciones</span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {usuarios.map((usuario) => (
            <TableRow
              key={usuario.id}
              className={usuario.activo ? undefined : "text-muted-foreground"}
            >
              <TableCell>
                <div className="flex flex-col">
                  <span className="font-medium">
                    {usuario.nombre}
                    {usuario.id === idPropio && (
                      <span className="ml-1.5 text-xs font-normal text-muted-foreground">
                        (vos)
                      </span>
                    )}
                  </span>
                  <span className="text-xs text-muted-foreground md:hidden">
                    {usuario.email}
                  </span>
                </div>
              </TableCell>
              <TableCell className="hidden md:table-cell">
                {usuario.email}
              </TableCell>
              <TableCell>
                <Badge
                  variant={usuario.rol === "admin" ? "secondary" : "outline"}
                >
                  {NOMBRE_ROL[usuario.rol]}
                </Badge>
              </TableCell>
              <TableCell>
                {usuario.activo ? (
                  <Badge variant="outline">Activo</Badge>
                ) : (
                  <Badge variant="destructive">Inactivo</Badge>
                )}
              </TableCell>
              <TableCell className="hidden text-right tabular-nums lg:table-cell">
                {formatearFecha(usuario.creado_en)}
              </TableCell>
              <TableCell>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      aria-label={`Acciones para ${usuario.nombre}`}
                    >
                      <DotsThreeVerticalIcon />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onSelect={() => onEditar(usuario)}>
                      <PencilSimpleIcon />
                      Editar
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    {usuario.activo ? (
                      <DropdownMenuItem
                        variant="destructive"
                        onSelect={() => onCambiarActivo(usuario)}
                      >
                        <ProhibitIcon />
                        Desactivar
                      </DropdownMenuItem>
                    ) : (
                      <DropdownMenuItem onSelect={() => onCambiarActivo(usuario)}>
                        <CheckCircleIcon />
                        Activar
                      </DropdownMenuItem>
                    )}
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
