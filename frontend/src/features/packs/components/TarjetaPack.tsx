import {
  DotsThreeVerticalIcon,
  GiftIcon,
  PencilSimpleIcon,
  TrashIcon,
  WarningIcon,
} from "@phosphor-icons/react"

import { variante } from "@/features/productos"
import { Badge } from "@/shared/ui/badge"
import { Button } from "@/shared/ui/button"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu"

import type { ItemPack, Pack } from "../api"

type Props = {
  pack: Pack
  onEditar: (pack: Pack) => void
  onBorrar: (pack: Pack) => void
}

/** Si hoy no alcanza el stock para el ítem, por qué. Sin aviso, alcanza. */
function aviso(item: ItemPack): string | null {
  if (item.unidades_disponibles >= item.cantidad) return null
  const p = item.producto
  if (p?.estado === "vendido") return "Ya se vendió"
  if (p?.estado === "reservado") return "Está reservado"
  if (item.unidades_disponibles === 0) return "Sin stock"
  return item.unidades_disponibles === 1
    ? "Hay 1 sola unidad"
    : `Hay ${item.unidades_disponibles} unidades`
}

function Item({ item }: { item: ItemPack }) {
  const p = item.producto
  const motivo = aviso(item)
  return (
    <li className="flex items-start gap-3 py-2">
      <span className="w-8 shrink-0 text-right text-muted-foreground tabular-nums">
        {item.cantidad}&nbsp;×
      </span>
      <div className="flex min-w-0 flex-1 flex-col">
        {p ? (
          <>
            <span className="truncate">
              {p.modelo.nombre}{" "}
              <span className="text-muted-foreground tabular-nums">
                #{p.id}
              </span>
            </span>
            <span className="truncate text-xs text-muted-foreground">
              {[p.categoria.nombre, variante(p)].filter(Boolean).join(" · ")}
            </span>
          </>
        ) : (
          <>
            <span className="truncate">{item.categoria?.nombre}</span>
            <span className="text-xs text-muted-foreground">
              El primero disponible
            </span>
          </>
        )}
        {motivo && (
          <span className="mt-0.5 flex items-center gap-1 text-xs text-warning-foreground">
            <WarningIcon aria-hidden />
            {motivo}
          </span>
        )}
      </div>
      {item.es_regalo && (
        <Badge variant="secondary" className="shrink-0">
          <GiftIcon aria-hidden />
          Regalo
        </Badge>
      )}
    </li>
  )
}

export function TarjetaPack({ pack, onEditar, onBorrar }: Props) {
  return (
    <Card className="gap-3">
      <CardHeader>
        <CardTitle className="font-heading text-xl">{pack.nombre}</CardTitle>
        {pack.descripcion && (
          <CardDescription className="text-pretty">
            {pack.descripcion}
          </CardDescription>
        )}
        <CardAction>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                aria-label={`Acciones para ${pack.nombre}`}
              >
                <DotsThreeVerticalIcon />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onSelect={() => onEditar(pack)}>
                <PencilSimpleIcon />
                Editar
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                variant="destructive"
                onSelect={() => onBorrar(pack)}
              >
                <TrashIcon />
                Borrar
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </CardAction>
      </CardHeader>
      <CardContent>
        {pack.items.length > 0 ? (
          <ul className="divide-y text-sm">
            {pack.items.map((item) => (
              <Item key={item.id} item={item} />
            ))}
          </ul>
        ) : (
          // Sus productos fijos se borraron del stock y se fueron con ellos.
          <p className="flex items-center gap-1.5 text-sm text-warning-foreground">
            <WarningIcon aria-hidden />
            Se quedó sin productos. Editalo para agregarle.
          </p>
        )}
      </CardContent>
    </Card>
  )
}
