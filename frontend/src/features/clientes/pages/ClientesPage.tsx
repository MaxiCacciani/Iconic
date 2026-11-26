import {
  ArrowClockwiseIcon,
  CaretLeftIcon,
  CaretRightIcon,
  MagnifyingGlassIcon,
  PlusIcon,
} from "@phosphor-icons/react"
import { useCallback, useEffect, useState } from "react"
import { useNavigate, useSearchParams } from "react-router"

import { mensajeDeError } from "@/shared/api"
import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/alert"
import { Button } from "@/shared/ui/button"
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/shared/ui/empty"
import { EncabezadoPagina } from "@/shared/ui/encabezado-pagina"
import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput,
} from "@/shared/ui/input-group"
import { Skeleton } from "@/shared/ui/skeleton"

import { TAMANIO_PAGINA, type FiltrosClientes } from "../api"
import { ClienteSheet } from "../components/ClienteSheet"
import { TablaClientes } from "../components/TablaClientes"
import { useClientesQuery } from "../queries"

const ESPERA_BUSQUEDA = 300

/** La búsqueda y la página van en la URL: se pueden compartir y sobreviven a un F5. */
function filtrosDe(params: URLSearchParams): FiltrosClientes {
  return {
    buscar: params.get("buscar") ?? undefined,
    pagina: Math.max(1, Number(params.get("pagina")) || 1),
  }
}

export function ClientesPage() {
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const filtros = filtrosDe(params)
  const clientes = useClientesQuery(filtros)

  const [busqueda, setBusqueda] = useState(filtros.buscar ?? "")
  const [alta, setAlta] = useState({ abierta: false, apertura: 0 })

  const filtrar = useCallback(
    (clave: "buscar" | "pagina", valor: string | undefined) =>
      setParams(
        (actual) => {
          const nuevos = new URLSearchParams(actual)
          if (valor) nuevos.set(clave, valor)
          else nuevos.delete(clave)
          if (clave !== "pagina") nuevos.delete("pagina")
          return nuevos
        },
        { replace: clave === "buscar" }
      ),
    [setParams]
  )

  // La búsqueda pasa a la URL cuando se deja de escribir, y el campo sigue a la URL
  // si cambia por otro lado (Atrás, Adelante, un link).
  const buscarEnUrl = params.get("buscar") ?? ""
  const [buscarVisto, setBuscarVisto] = useState(buscarEnUrl)
  if (buscarEnUrl !== buscarVisto) {
    setBuscarVisto(buscarEnUrl)
    if (buscarEnUrl !== busqueda.trim()) setBusqueda(buscarEnUrl)
  }
  useEffect(() => {
    if (busqueda.trim() === buscarEnUrl) return
    const espera = setTimeout(
      () => filtrar("buscar", busqueda.trim() || undefined),
      ESPERA_BUSQUEDA
    )
    return () => clearTimeout(espera)
  }, [busqueda, buscarEnUrl, filtrar])

  const abrirAlta = () =>
    setAlta((a) => ({ abierta: true, apertura: a.apertura + 1 }))

  const paginas = clientes.data
    ? Math.max(1, Math.ceil(clientes.data.total / TAMANIO_PAGINA))
    : 1
  // Una página que ya no existe (vino así en un link o se borró lo último): a la última.
  const fueraDeRango =
    clientes.data !== undefined &&
    !clientes.isPlaceholderData &&
    filtros.pagina > paginas
  useEffect(() => {
    if (!fueraDeRango) return
    setParams(
      (actual) => {
        const nuevos = new URLSearchParams(actual)
        if (paginas > 1) nuevos.set("pagina", String(paginas))
        else nuevos.delete("pagina")
        return nuevos
      },
      { replace: true }
    )
  }, [fueraDeRango, paginas, setParams])

  return (
    <>
      <EncabezadoPagina
        titulo="Clientes"
        descripcion="Buscá por nombre o DNI y abrí la ficha de cada cliente."
        acciones={
          <Button onClick={abrirAlta}>
            <PlusIcon />
            Nuevo cliente
          </Button>
        }
      />

      <div className="flex flex-col gap-4">
        <div role="search" className="max-w-xl">
          <InputGroup>
            <InputGroupAddon>
              <MagnifyingGlassIcon aria-hidden />
            </InputGroupAddon>
            <InputGroupInput
              type="search"
              placeholder="Buscar por nombre o DNI…"
              aria-label="Buscar por nombre o DNI"
              autoComplete="off"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
            />
          </InputGroup>
        </div>

        {clientes.isError ? (
          <Alert variant="destructive">
            <AlertTitle>No se pudieron cargar los clientes</AlertTitle>
            <AlertDescription className="flex flex-col items-start gap-3">
              {mensajeDeError(clientes.error)}
              <Button
                variant="outline"
                size="sm"
                onClick={() => clientes.refetch()}
              >
                <ArrowClockwiseIcon />
                Reintentar
              </Button>
            </AlertDescription>
          </Alert>
        ) : clientes.isPending || fueraDeRango ? (
          <div className="flex flex-col gap-2" aria-busy="true">
            <span className="sr-only">Cargando los clientes…</span>
            {Array.from({ length: 6 }, (_, i) => (
              <Skeleton key={i} className="h-11 w-full" />
            ))}
          </div>
        ) : clientes.data.items.length === 0 ? (
          <Empty className="border">
            <EmptyHeader>
              <EmptyTitle>
                {filtros.buscar
                  ? `No hay clientes con «${filtros.buscar}»`
                  : "Todavía no hay clientes"}
              </EmptyTitle>
              <EmptyDescription>
                {filtros.buscar
                  ? "Revisá cómo está escrito o dalo de alta."
                  : "Se cargan acá o al registrar una venta."}
              </EmptyDescription>
            </EmptyHeader>
            <EmptyContent className="flex-row justify-center">
              {filtros.buscar && (
                <Button
                  variant="outline"
                  onClick={() => {
                    setBusqueda("")
                    setParams({})
                  }}
                >
                  Ver todos
                </Button>
              )}
              <Button onClick={abrirAlta}>
                <PlusIcon />
                Nuevo cliente
              </Button>
            </EmptyContent>
          </Empty>
        ) : (
          <>
            <div
              aria-busy={clientes.isPlaceholderData || undefined}
              className={
                clientes.isPlaceholderData
                  ? "opacity-60 transition-opacity"
                  : undefined
              }
            >
              <TablaClientes clientes={clientes.data.items} />
            </div>
            <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-muted-foreground">
              <p aria-live="polite" className="tabular-nums">
                {clientes.data.total === 1
                  ? "1 cliente"
                  : `${clientes.data.total.toLocaleString("es-AR")} clientes`}
                {paginas > 1 && ` · página ${filtros.pagina} de ${paginas}`}
              </p>
              {paginas > 1 && (
                <nav aria-label="Páginas" className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={filtros.pagina <= 1}
                    onClick={() =>
                      filtrar("pagina", String(filtros.pagina - 1))
                    }
                  >
                    <CaretLeftIcon />
                    Anterior
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={filtros.pagina >= paginas}
                    onClick={() =>
                      filtrar("pagina", String(filtros.pagina + 1))
                    }
                  >
                    Siguiente
                    <CaretRightIcon />
                  </Button>
                </nav>
              )}
            </div>
          </>
        )}
      </div>

      <ClienteSheet
        abierto={alta.abierta}
        onAbiertoChange={(abierta) => setAlta((a) => ({ ...a, abierta }))}
        cliente={null}
        apertura={alta.apertura}
        // Lo que se buscó y no estaba suele ser el nombre del cliente nuevo.
        nombreInicial={
          clientes.data?.items.length === 0 ? filtros.buscar : undefined
        }
        onGuardado={(c) => navigate(`/clientes/${c.id}`)}
      />
    </>
  )
}
