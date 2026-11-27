import {
  DotsThreeVerticalIcon,
  PencilSimpleIcon,
  TrashIcon,
} from "@phosphor-icons/react"

import { formatearARS, formatearUSD } from "@/shared/lib/formato"
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

import { tieneCostos, type Producto } from "../api"
import { Bateria } from "./Bateria"
import { CONDICION, ESTADO, variante } from "./etiquetas"

type Props = {
  productos: Producto[]
  /** Se muestra la columna de estado cuando la lista no está filtrada por uno. */
  conEstado: boolean
  /** Sin estas acciones (Vendedor), la fila no tiene menú. */
  onEditar?: (producto: Producto) => void
  onBorrar?: (producto: Producto) => void
}

/** Lo propio de cada tipo: IMEI, controles o unidades. */
function identificacion(p: Producto) {
  if (p.imei)
    return <span className="font-mono text-xs tracking-wide">{p.imei}</span>
  if (p.controles !== null)
    return p.controles === 1 ? "1 control" : `${p.controles} controles`
  if (p.cantidad > 1) return `${p.cantidad} unidades`
  return <span className="text-muted-foreground">—</span>
}

export function TablaStock({
  productos,
  conEstado,
  onEditar,
  onBorrar,
}: Props) {
  // Si la API mandó costos, se muestran; si no, la columna no existe.
  const conCostos = productos.some(tieneCostos)
  const conAcciones = Boolean(onEditar && onBorrar)

  return (
    <div className="overflow-hidden rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-16">N.º</TableHead>
            <TableHead>Producto</TableHead>
            <TableHead className="hidden md:table-cell">
              IMEI o detalle
            </TableHead>
            <TableHead className="hidden sm:table-cell">Condición</TableHead>
            <TableHead className="hidden lg:table-cell">Batería</TableHead>
            <TableHead className="text-right">Precio</TableHead>
            {conCostos && (
              <TableHead className="hidden text-right lg:table-cell">
                Costo y margen
              </TableHead>
            )}
            {conEstado && <TableHead>Estado</TableHead>}
            {conAcciones && (
              <TableHead className="w-12">
                <span className="sr-only">Acciones</span>
              </TableHead>
            )}
          </TableRow>
        </TableHeader>
        <TableBody>
          {productos.map((p) => (
            <TableRow key={p.id}>
              <TableCell className="text-muted-foreground tabular-nums">
                #{p.id}
              </TableCell>
              <TableCell className="whitespace-normal">
                <div className="flex flex-col gap-0.5">
                  <span className="flex items-center gap-2 font-medium">
                    {p.modelo.nombre}
                    {/* Solo un accesorio por cantidad llega a 0: se repone editándolo. */}
                    {p.cantidad === 0 && (
                      <Badge variant="destructive">Sin stock</Badge>
                    )}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {[p.categoria.nombre, variante(p)]
                      .filter(Boolean)
                      .join(" · ")}
                  </span>
                  {p.defectos.length > 0 && (
                    <span className="text-xs text-warning-foreground">
                      {p.defectos.map((d) => d.descripcion).join(", ")}
                    </span>
                  )}
                </div>
              </TableCell>
              <TableCell className="hidden md:table-cell">
                {identificacion(p)}
              </TableCell>
              <TableCell className="hidden sm:table-cell">
                <Badge
                  variant={p.condicion === "nuevo" ? "default" : "outline"}
                >
                  {CONDICION[p.condicion]}
                </Badge>
              </TableCell>
              <TableCell className="hidden lg:table-cell">
                <Bateria bateria={p.bateria} nivel={p.bateria_nivel} />
              </TableCell>
              <TableCell className="text-right tabular-nums">
                <div className="flex flex-col items-end gap-0.5">
                  <span className="font-medium">
                    {formatearUSD(p.precio_usd)}
                  </span>
                  {p.precio_ars !== null && (
                    <span className="text-xs text-muted-foreground">
                      {formatearARS(p.precio_ars)}
                    </span>
                  )}
                </div>
              </TableCell>
              {conCostos && (
                <TableCell className="hidden text-right tabular-nums lg:table-cell">
                  {tieneCostos(p) && p.costo_usd !== null ? (
                    <div className="flex flex-col items-end gap-0.5">
                      <span>{formatearUSD(p.costo_usd)}</span>
                      <span className="text-xs text-muted-foreground">
                        {p.margen_pct !== null
                          ? `Margen ${Number(p.margen_pct).toLocaleString("es-AR")} %`
                          : "Sin margen"}
                      </span>
                    </div>
                  ) : (
                    <span className="text-muted-foreground">Sin costo</span>
                  )}
                </TableCell>
              )}
              {conEstado && (
                <TableCell>
                  <Badge
                    variant={
                      p.estado === "disponible" ? "secondary" : "outline"
                    }
                  >
                    {ESTADO[p.estado]}
                  </Badge>
                </TableCell>
              )}
              {conAcciones && (
                <TableCell>
                  {/* Si se puede editar en su estado lo dice la API. */}
                  {p.editable && (
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label={`Acciones para el producto #${p.id}`}
                        >
                          <DotsThreeVerticalIcon />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onSelect={() => onEditar?.(p)}>
                          <PencilSimpleIcon />
                          Editar
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          variant="destructive"
                          onSelect={() => onBorrar?.(p)}
                        >
                          <TrashIcon />
                          Borrar…
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
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
