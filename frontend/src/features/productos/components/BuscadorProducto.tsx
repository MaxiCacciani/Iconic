import { CaretUpDownIcon, WarningCircleIcon } from "@phosphor-icons/react"
import { useEffect, useId, useState } from "react"

import { formatearUSD } from "@/shared/lib/formato"
import { cn } from "@/shared/lib/utils"
import { Button } from "@/shared/ui/button"
import {
  Command,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/shared/ui/command"
import { Popover, PopoverContent, PopoverTrigger } from "@/shared/ui/popover"
import { Spinner } from "@/shared/ui/spinner"

import type { Producto } from "../api"
import { useBuscarProductosQuery } from "../queries"
import { variante } from "./etiquetas"

/** Lo mínimo para mostrar el producto elegido: un producto del stock o el que ya tenía
 * guardado otra pantalla (por ejemplo, el producto fijo de un pack). */
export type ProductoElegido = {
  id: number
  modelo: { nombre: string }
  capacidad: { nombre: string } | null
  color: { nombre: string } | null
  imei: string | null
}

type Props = {
  producto: ProductoElegido | null
  onElegir: (producto: Producto) => void
  id?: string
  /** Para marcarlo cuando la API rechaza el producto (un 422 en ese campo). */
  invalido?: boolean
  placeholder?: string
}

const ESPERA = 250

/** "128 GB · Negro · IMEI …4521": lo que distingue a dos productos del mismo modelo. */
function detalle(p: ProductoElegido & { cantidad?: number }): string {
  return [
    variante(p),
    p.imei && `IMEI …${p.imei.slice(-4)}`,
    p.cantidad !== undefined && p.cantidad > 1 && `${p.cantidad} unidades`,
  ]
    .filter(Boolean)
    .join(" · ")
}

/** Busca un producto disponible por modelo o IMEI. Lo usan los packs (producto fijo) y,
 * después, el carrito de la venta. */
export function BuscadorProducto({
  producto,
  onElegir,
  id,
  invalido,
  placeholder = "Buscar por modelo o IMEI…",
}: Props) {
  const [abierto, setAbierto] = useState(false)
  const listaId = useId()
  const [texto, setTexto] = useState("")
  const [buscado, setBuscado] = useState("")

  useEffect(() => {
    const espera = setTimeout(() => setBuscado(texto.trim()), ESPERA)
    return () => clearTimeout(espera)
  }, [texto])

  const resultados = useBuscarProductosQuery(buscado, abierto && buscado !== "")
  const esperando = texto.trim() !== buscado || resultados.isFetching
  const items = buscado && resultados.data ? resultados.data.items : []
  const hayMas = resultados.data ? resultados.data.total > items.length : false

  return (
    <Popover
      open={abierto}
      onOpenChange={(a) => {
        setAbierto(a)
        if (!a) setTexto("")
      }}
    >
      <PopoverTrigger asChild>
        <Button
          id={id}
          variant="outline"
          role="combobox"
          aria-expanded={abierto}
          aria-controls={listaId}
          aria-invalid={invalido}
          className="h-auto min-h-9 w-full justify-between py-1.5 font-normal"
        >
          {producto ? (
            <span className="flex min-w-0 flex-col items-start text-left">
              <span className="truncate font-medium">
                {producto.modelo.nombre}{" "}
                <span className="text-muted-foreground tabular-nums">
                  #{producto.id}
                </span>
              </span>
              {detalle(producto) && (
                <span className="truncate text-xs text-muted-foreground tabular-nums">
                  {detalle(producto)}
                </span>
              )}
            </span>
          ) : (
            <span className="text-muted-foreground">{placeholder}</span>
          )}
          <CaretUpDownIcon className="opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        id={listaId}
        className="w-(--radix-popover-trigger-width) min-w-72 p-0"
        align="start"
      >
        {/* El filtro lo hace la API: cmdk solo maneja el teclado. */}
        <Command shouldFilter={false}>
          <CommandInput
            value={texto}
            onValueChange={setTexto}
            placeholder="Modelo o IMEI…"
            aria-label="Buscar producto por modelo o IMEI"
          />
          <CommandList>
            <div aria-live="polite" className="text-sm text-muted-foreground">
              {!texto.trim() ? (
                <p className="px-3 py-4">
                  Escribí el modelo o parte del IMEI. Solo aparecen los
                  disponibles.
                </p>
              ) : resultados.isError ? (
                <p className="flex items-center gap-2 px-3 py-4 text-destructive">
                  <WarningCircleIcon aria-hidden />
                  No se pudo buscar. Probá de nuevo.
                </p>
              ) : esperando && items.length === 0 ? (
                <p className="flex items-center gap-2 px-3 py-4">
                  <Spinner />
                  Buscando…
                </p>
              ) : items.length === 0 ? (
                <p className="px-3 py-4">
                  No hay productos disponibles con «{texto.trim()}».
                </p>
              ) : null}
            </div>
            {items.length > 0 && (
              <CommandGroup
                className={cn(esperando && "opacity-60 transition-opacity")}
              >
                {items.map((p) => (
                  <CommandItem
                    key={p.id}
                    value={String(p.id)}
                    data-checked={p.id === producto?.id}
                    onSelect={() => {
                      onElegir(p)
                      setAbierto(false)
                      setTexto("")
                    }}
                  >
                    <span className="flex min-w-0 flex-1 flex-col">
                      <span className="truncate">
                        {p.modelo.nombre}{" "}
                        <span className="text-muted-foreground tabular-nums">
                          #{p.id}
                        </span>
                      </span>
                      {detalle(p) && (
                        <span className="truncate text-xs text-muted-foreground tabular-nums">
                          {detalle(p)}
                        </span>
                      )}
                    </span>
                    <span className="text-xs text-muted-foreground tabular-nums">
                      {formatearUSD(p.precio_usd)}
                    </span>
                  </CommandItem>
                ))}
                {hayMas && (
                  <p className="px-2 py-1.5 text-xs text-muted-foreground">
                    Hay más: seguí escribiendo para acotar.
                  </p>
                )}
              </CommandGroup>
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
