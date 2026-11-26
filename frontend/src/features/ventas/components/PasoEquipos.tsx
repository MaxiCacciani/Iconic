import { PackageIcon, TrashIcon, WarningIcon } from "@phosphor-icons/react"
import { toast } from "sonner"

import { useAplicarPack, usePacksQuery } from "@/features/packs"
import { BuscadorProducto, variante } from "@/features/productos"
import { mensajeDeError } from "@/shared/api"
import { Badge } from "@/shared/ui/badge"
import { Button } from "@/shared/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu"
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/shared/ui/empty"
import { Field, FieldError, FieldLabel } from "@/shared/ui/field"
import { Input } from "@/shared/ui/input"
import { InputUSD } from "@/shared/ui/input-usd"
import { Switch } from "@/shared/ui/switch"

import { esAdmin } from "../api"
import { useVenta, type Linea } from "./borrador"

export function PasoEquipos() {
  const { b, despachar, campos } = useVenta()
  const packs = usePacksQuery()
  const aplicar = useAplicarPack()

  function agregarPack(id: number, nombre: string) {
    const enCarrito = b.lineas.map((l) => ({
      producto_id: l.producto.id,
      cantidad: Number(l.cantidad) || 1,
    }))
    aplicar.mutate(
      { id, enCarrito },
      {
        onSuccess: (r) => {
          despachar({
            tipo: "agregar",
            lineas: r.lineas.map((l) => ({
              producto: l.producto,
              cantidad: String(l.cantidad),
              esRegalo: l.es_regalo,
            })),
          })
          toast.success(`Se agregó el pack ${nombre}.`)
        },
        // Sin stock para algún ítem, la API dice cuál y no agrega nada.
        onError: (error) => toast.error(mensajeDeError(error)),
      }
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-2">
        <div className="min-w-64 flex-1">
          <BuscadorProducto
            producto={null}
            placeholder="Agregar un producto por modelo o IMEI…"
            onElegir={(producto) =>
              despachar({
                tipo: "agregar",
                lineas: [{ producto, cantidad: "1", esRegalo: false }],
              })
            }
          />
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="outline"
              disabled={!packs.data?.length || aplicar.isPending}
            >
              <PackageIcon />
              Agregar un pack
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {packs.data?.map((p) => (
              <DropdownMenuItem
                key={p.id}
                onSelect={() => agregarPack(p.id, p.nombre)}
              >
                {p.nombre}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {campos.items && <FieldError>{campos.items}</FieldError>}

      {b.lineas.length === 0 ? (
        <Empty className="border">
          <EmptyHeader>
            <EmptyTitle>Todavía no hay productos en la venta</EmptyTitle>
            <EmptyDescription>
              Buscalos por modelo o IMEI, o agregá un pack. Solo aparecen los
              disponibles.
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      ) : (
        <ul className="flex flex-col divide-y rounded-lg border">
          {b.lineas.map((linea, n) => (
            <Renglon key={linea.clave} linea={linea} n={n} />
          ))}
        </ul>
      )}
    </div>
  )
}

function Renglon({ linea, n }: { linea: Linea; n: number }) {
  const { despachar, cotizacion, campos } = useVenta()
  const p = linea.producto
  const cambiar = (cambios: Partial<Linea>) =>
    despachar({ tipo: "linea", clave: linea.clave, cambios })
  const bajoCosto =
    cotizacion && esAdmin(cotizacion) && cotizacion.bajo_costo.includes(n)
  const error = (campo: string) => campos[`items.${n}.${campo}`]
  const detalle = [variante(p), p.imei && `IMEI …${p.imei.slice(-4)}`]
    .filter(Boolean)
    .join(" · ")

  return (
    <li className="flex flex-col gap-2 p-3">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
        <div className="flex min-w-0 flex-1 flex-col gap-1">
          <p className="font-medium">
            {p.modelo.nombre}{" "}
            <span className="text-muted-foreground tabular-nums">#{p.id}</span>
          </p>
          {detalle && (
            <p className="text-xs text-muted-foreground tabular-nums">
              {detalle}
            </p>
          )}
          {bajoCosto && (
            <Badge
              variant="outline"
              className="border-warning/50 bg-warning/10 text-warning-foreground"
            >
              <WarningIcon weight="fill" aria-hidden />
              Bajo costo
            </Badge>
          )}
          {error("producto_id") && (
            <FieldError>{error("producto_id")}</FieldError>
          )}
        </div>

        <div className="flex flex-wrap items-start gap-3">
          {/* Solo un accesorio por cantidad tiene más de una unidad en su fila. */}
          {p.cantidad > 1 && (
            <Field
              data-invalid={error("cantidad") ? true : undefined}
              className="w-20"
            >
              <FieldLabel htmlFor={`linea-${linea.clave}-cantidad`}>
                Cant.
              </FieldLabel>
              <Input
                id={`linea-${linea.clave}-cantidad`}
                inputMode="numeric"
                autoComplete="off"
                className="tabular-nums"
                value={linea.cantidad}
                onChange={(e) => cambiar({ cantidad: e.target.value })}
                aria-invalid={error("cantidad") ? true : undefined}
              />
            </Field>
          )}
          <Field
            data-invalid={error("precio_usd") ? true : undefined}
            className="w-36"
          >
            <FieldLabel htmlFor={`linea-${linea.clave}-precio`}>
              Precio
            </FieldLabel>
            <InputUSD
              id={`linea-${linea.clave}-precio`}
              value={linea.esRegalo ? "0" : linea.precio}
              disabled={linea.esRegalo}
              onChange={(e) => cambiar({ precio: e.target.value })}
              aria-invalid={error("precio_usd") ? true : undefined}
            />
          </Field>
          <Field orientation="horizontal" className="w-auto sm:pt-7">
            <Switch
              id={`linea-${linea.clave}-regalo`}
              checked={linea.esRegalo}
              onCheckedChange={(esRegalo) => cambiar({ esRegalo })}
            />
            <FieldLabel
              htmlFor={`linea-${linea.clave}-regalo`}
              className="font-normal"
            >
              Regalo
            </FieldLabel>
          </Field>
          <Button
            variant="ghost"
            size="icon"
            className="sm:mt-6"
            aria-label={`Quitar ${p.modelo.nombre} #${p.id}`}
            onClick={() => despachar({ tipo: "quitar", clave: linea.clave })}
          >
            <TrashIcon />
          </Button>
        </div>
      </div>
      {error("cantidad") && <FieldError>{error("cantidad")}</FieldError>}
      {error("precio_usd") && <FieldError>{error("precio_usd")}</FieldError>}
    </li>
  )
}
