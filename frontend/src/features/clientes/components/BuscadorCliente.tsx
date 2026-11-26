import {
  CaretUpDownIcon,
  UserCirclePlusIcon,
  WarningCircleIcon,
} from "@phosphor-icons/react"
import { useEffect, useId, useState } from "react"

import { formatearDNI } from "@/shared/lib/formato"
import { cn } from "@/shared/lib/utils"
import { Button } from "@/shared/ui/button"
import {
  Command,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/shared/ui/command"
import { Popover, PopoverContent, PopoverTrigger } from "@/shared/ui/popover"
import { Spinner } from "@/shared/ui/spinner"

import type { Cliente } from "../api"
import { useBuscarClientesQuery } from "../queries"
import { ClienteSheet } from "./ClienteSheet"

type Props = {
  /** El cliente elegido. */
  cliente: Cliente | null
  onElegir: (cliente: Cliente) => void
  id?: string
  /** Para marcarlo cuando la API rechaza el cliente (un 422 en `cliente_id`). */
  invalido?: boolean
}

const ESPERA = 250
const ALTA = "__alta__"
const SOLO_NUMERO = /^[\d.\s-]+$/

/** "DNI 30.123.456 · Rosario": lo que distingue a dos clientes con el mismo nombre. */
function detalle(c: Cliente): string {
  return [c.dni && `DNI ${formatearDNI(c.dni)}`, c.localidad?.nombre]
    .filter(Boolean)
    .join(" · ")
}

/** Busca un cliente por nombre o DNI y, si no está, lo da de alta en el momento.
 * Lo usan la venta y la reserva (toda venta necesita un cliente). */
export function BuscadorCliente({ cliente, onElegir, id, invalido }: Props) {
  const [abierto, setAbierto] = useState(false)
  const listaId = useId()
  const [texto, setTexto] = useState("")
  const [buscado, setBuscado] = useState("")
  const [alta, setAlta] = useState({ abierta: false, apertura: 0, texto: "" })

  // Se busca cuando se deja de escribir.
  useEffect(() => {
    const espera = setTimeout(() => setBuscado(texto.trim()), ESPERA)
    return () => clearTimeout(espera)
  }, [texto])

  const resultados = useBuscarClientesQuery(buscado, abierto && buscado !== "")
  const esperando = texto.trim() !== buscado || resultados.isFetching
  const items = buscado && resultados.data ? resultados.data.items : []
  const hayMas = resultados.data ? resultados.data.total > items.length : false

  // Al llegar resultados se resalta el primero: un Enter elige al cliente, no da de alta
  // un duplicado (cmdk se queda con lo que resaltó mientras la lista estaba vacía).
  const primero = items[0] ? String(items[0].id) : ALTA
  const [resaltado, setResaltado] = useState(primero)
  const [primeroVisto, setPrimeroVisto] = useState(primero)
  if (primero !== primeroVisto) {
    setPrimeroVisto(primero)
    setResaltado(primero)
  }

  function darDeAlta() {
    setAbierto(false)
    setAlta((a) => ({
      abierta: true,
      apertura: a.apertura + 1,
      texto: texto.trim(),
    }))
  }

  const esNumero = SOLO_NUMERO.test(alta.texto)

  return (
    <>
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
            {cliente ? (
              <span className="flex min-w-0 flex-col items-start text-left">
                <span className="truncate font-medium">
                  {cliente.nombre}{" "}
                  <span className="text-muted-foreground tabular-nums">
                    #{cliente.id}
                  </span>
                </span>
                {detalle(cliente) && (
                  <span className="truncate text-xs text-muted-foreground tabular-nums">
                    {detalle(cliente)}
                  </span>
                )}
              </span>
            ) : (
              <span className="text-muted-foreground">
                Buscar por nombre o DNI…
              </span>
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
          <Command
            shouldFilter={false}
            value={resaltado}
            onValueChange={setResaltado}
          >
            <CommandInput
              value={texto}
              onValueChange={setTexto}
              placeholder="Nombre o DNI…"
              aria-label="Buscar cliente por nombre o DNI"
            />
            <CommandList>
              <div aria-live="polite" className="text-sm text-muted-foreground">
                {!texto.trim() ? (
                  <p className="px-3 py-4">Escribí el nombre o el DNI.</p>
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
                    No hay clientes con «{texto.trim()}».
                  </p>
                ) : null}
              </div>
              {items.length > 0 && (
                <CommandGroup
                  className={cn(esperando && "opacity-60 transition-opacity")}
                >
                  {items.map((c) => (
                    <CommandItem
                      key={c.id}
                      value={String(c.id)}
                      data-checked={c.id === cliente?.id}
                      onSelect={() => {
                        onElegir(c)
                        setAbierto(false)
                        setTexto("")
                      }}
                    >
                      <span className="flex min-w-0 flex-col">
                        <span className="truncate">
                          {c.nombre}{" "}
                          <span className="text-muted-foreground tabular-nums">
                            #{c.id}
                          </span>
                        </span>
                        {detalle(c) && (
                          <span className="truncate text-xs text-muted-foreground tabular-nums">
                            {detalle(c)}
                          </span>
                        )}
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
              <CommandSeparator />
              <CommandGroup>
                <CommandItem value={ALTA} onSelect={darDeAlta}>
                  <UserCirclePlusIcon />
                  {texto.trim()
                    ? `Dar de alta «${texto.trim()}»`
                    : "Dar de alta un cliente nuevo"}
                </CommandItem>
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>

      <ClienteSheet
        abierto={alta.abierta}
        onAbiertoChange={(abierta) => setAlta((a) => ({ ...a, abierta }))}
        cliente={null}
        apertura={alta.apertura}
        nombreInicial={esNumero ? undefined : alta.texto}
        dniInicial={esNumero ? alta.texto : undefined}
        onGuardado={onElegir}
      />
    </>
  )
}
