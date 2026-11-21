import {
  DotsThreeVerticalIcon,
  PencilSimpleIcon,
  TrashIcon,
} from "@phosphor-icons/react"

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

import type { ItemCatalogo } from "../api"
import { valorDe, type DefinicionCatalogo } from "../catalogos"

type Props = {
  definicion: DefinicionCatalogo
  items: ItemCatalogo[]
  /** Nombre de cada categoría por id, para la columna "Categoría". Sin él, no se muestra. */
  categorias?: Map<number, string>
  /** Nombre de cada tipo de categoría por id, para la columna "Tipo". */
  tipos?: Map<number, string>
  onEditar: (item: ItemCatalogo) => void
  onBorrar: (item: ItemCatalogo) => void
}

export function TablaCatalogo({
  definicion,
  items,
  categorias,
  tipos,
  onEditar,
  onBorrar,
}: Props) {
  const texto = (item: ItemCatalogo) =>
    String(valorDe(item, definicion.campoTexto))

  return (
    <div className="overflow-hidden rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>{definicion.etiquetaTexto}</TableHead>
            {categorias && <TableHead>Categoría</TableHead>}
            {tipos && <TableHead>Tipo</TableHead>}
            <TableHead className="w-12">
              <span className="sr-only">Acciones</span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((item) => (
            <TableRow key={item.id}>
              <TableCell className="whitespace-normal">
                <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                  <span className="font-medium">{texto(item)}</span>
                  {definicion.interruptores
                    ?.filter((i) => valorDe(item, i.campo) === true)
                    .map((i) => (
                      <Badge key={i.campo} variant="secondary">
                        {i.insignia}
                      </Badge>
                    ))}
                </div>
              </TableCell>
              {categorias && (
                <TableCell className="text-muted-foreground">
                  {categorias.get(Number(valorDe(item, "categoria_id")))}
                </TableCell>
              )}
              {tipos && (
                <TableCell className="text-muted-foreground">
                  {tipos.get(Number(valorDe(item, "tipo_categoria_id")))}
                </TableCell>
              )}
              <TableCell>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      aria-label={`Acciones para ${texto(item)}`}
                    >
                      <DotsThreeVerticalIcon />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onSelect={() => onEditar(item)}>
                      <PencilSimpleIcon />
                      Editar
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      variant="destructive"
                      onSelect={() => onBorrar(item)}
                    >
                      <TrashIcon />
                      Borrar…
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
