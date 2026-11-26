import {
  ArrowClockwiseIcon,
  CaretLeftIcon,
  CaretRightIcon,
  MagnifyingGlassIcon,
  PlusIcon,
} from "@phosphor-icons/react"
import { useCallback, useEffect, useState } from "react"
import { useSearchParams } from "react-router"
import { toast } from "sonner"

import { useAuth } from "@/features/auth"
import { useCatalogoQuery } from "@/features/catalogos"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select"
import { Skeleton } from "@/shared/ui/skeleton"

import {
  TAMANIO_PAGINA,
  type Condicion,
  type EstadoProducto,
  type FiltrosStock,
  type Producto,
} from "../api"
import { ConfirmarBorrarProducto } from "../components/ConfirmarBorrarProducto"
import { CONDICION, ESTADO } from "../components/etiquetas"
import { ProductoSheet } from "../components/ProductoSheet"
import { TablaStock } from "../components/TablaStock"
import { useEliminarProducto, useStockQuery } from "../queries"

const TODOS = "todos"
const ESPERA_BUSQUEDA = 300

/** Los filtros van en la URL: se pueden compartir y sobreviven a un F5. Por defecto,
 * lo que está a la venta. */
function filtrosDe(params: URLSearchParams): FiltrosStock {
  const estado = params.get("estado")
  const condicion = params.get("condicion")
  return {
    estado:
      estado === TODOS
        ? undefined
        : estado && estado in ESTADO
          ? (estado as EstadoProducto)
          : "disponible",
    categoriaId: Number(params.get("categoria")) || undefined,
    condicion:
      condicion && condicion in CONDICION
        ? (condicion as Condicion)
        : undefined,
    buscar: params.get("buscar") ?? undefined,
    pagina: Math.max(1, Number(params.get("pagina")) || 1),
  }
}

export function ProductosPage() {
  const { puede } = useAuth()
  const puedeEditar = puede("productos:editar")
  const [params, setParams] = useSearchParams()
  const filtros = filtrosDe(params)
  const stock = useStockQuery(filtros)
  const categorias = useCatalogoQuery("categorias")
  const eliminar = useEliminarProducto()

  const [busqueda, setBusqueda] = useState(filtros.buscar ?? "")
  const [sheet, setSheet] = useState<{
    abierto: boolean
    producto: Producto | null
    apertura: number
  }>({ abierto: false, producto: null, apertura: 0 })
  const [aBorrar, setABorrar] = useState<Producto | null>(null)

  /** Cambia un filtro y vuelve a la primera página. */
  const filtrar = useCallback(
    (clave: string, valor: string | undefined) =>
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

  // La búsqueda pasa a la URL cuando se deja de escribir.
  const buscarEnUrl = params.get("buscar") ?? ""
  // Y al revés: si la URL cambia por otro lado (Atrás, Adelante, un link), el campo la
  // sigue; si no, la espera de arriba volvería a pisar la URL con lo viejo.
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

  function abrir(producto: Producto | null) {
    setSheet((s) => ({ abierto: true, producto, apertura: s.apertura + 1 }))
  }

  function borrar(producto: Producto) {
    setABorrar(null)
    eliminar.mutate(producto.id, {
      onSuccess: () => toast.success(`Se borró el producto #${producto.id}.`),
      onError: (error) => toast.error(mensajeDeError(error)),
    })
  }

  const filtrado =
    Boolean(filtros.categoriaId || filtros.condicion || filtros.buscar) ||
    filtros.estado !== "disponible"
  const paginas = stock.data
    ? Math.max(1, Math.ceil(stock.data.total / TAMANIO_PAGINA))
    : 1
  // Una página que ya no existe (se borró o se vendió lo último de la última, o vino así
  // en un link): se pasa a la última que tiene productos, sin sumar una entrada al historial.
  const fueraDeRango =
    stock.data !== undefined &&
    !stock.isPlaceholderData &&
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
        titulo="Productos"
        descripcion="El stock de equipos, consolas y accesorios."
        acciones={
          puedeEditar && (
            <Button onClick={() => abrir(null)}>
              <PlusIcon />
              Cargar producto
            </Button>
          )
        }
      />

      <div className="flex flex-col gap-4">
        <div
          role="search"
          className="grid gap-2 sm:grid-cols-3 xl:grid-cols-[minmax(0,1fr)_12rem_12rem_11rem]"
        >
          <InputGroup className="sm:col-span-3 xl:col-span-1">
            <InputGroupAddon>
              <MagnifyingGlassIcon aria-hidden />
            </InputGroupAddon>
            <InputGroupInput
              type="search"
              placeholder="Buscar por modelo o IMEI…"
              aria-label="Buscar por modelo o IMEI"
              autoComplete="off"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
            />
          </InputGroup>

          <Select
            value={filtros.estado ?? TODOS}
            onValueChange={(v) =>
              filtrar("estado", v === "disponible" ? undefined : v)
            }
          >
            <SelectTrigger className="w-full" aria-label="Filtrar por estado">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {(Object.keys(ESTADO) as EstadoProducto[]).map((e) => (
                <SelectItem key={e} value={e}>
                  {e === "disponible" ? "A la venta" : `${ESTADO[e]}s`}
                </SelectItem>
              ))}
              <SelectSeparator />
              <SelectItem value={TODOS}>Todos los estados</SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={filtros.categoriaId ? String(filtros.categoriaId) : TODOS}
            onValueChange={(v) =>
              filtrar("categoria", v === TODOS ? undefined : v)
            }
            disabled={categorias.isPending}
          >
            <SelectTrigger
              className="w-full"
              aria-label="Filtrar por categoría"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={TODOS}>Todas las categorías</SelectItem>
              <SelectSeparator />
              {categorias.data?.map((c) => (
                <SelectItem key={c.id} value={String(c.id)}>
                  {c.nombre}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={filtros.condicion ?? TODOS}
            onValueChange={(v) =>
              filtrar("condicion", v === TODOS ? undefined : v)
            }
          >
            <SelectTrigger
              className="w-full"
              aria-label="Filtrar por condición"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={TODOS}>Nuevos y usados</SelectItem>
              <SelectSeparator />
              {(Object.keys(CONDICION) as Condicion[]).map((c) => (
                <SelectItem key={c} value={c}>
                  {`${CONDICION[c]}s`}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {stock.isError ? (
          <Alert variant="destructive">
            <AlertTitle>No se pudo cargar el stock</AlertTitle>
            <AlertDescription className="flex flex-col items-start gap-3">
              {mensajeDeError(stock.error)}
              <Button
                variant="outline"
                size="sm"
                onClick={() => stock.refetch()}
              >
                <ArrowClockwiseIcon />
                Reintentar
              </Button>
            </AlertDescription>
          </Alert>
        ) : stock.isPending || fueraDeRango ? (
          <div className="flex flex-col gap-2" aria-busy="true">
            <span className="sr-only">Cargando el stock…</span>
            {Array.from({ length: 6 }, (_, i) => (
              <Skeleton key={i} className="h-14 w-full" />
            ))}
          </div>
        ) : stock.data.items.length === 0 ? (
          <Empty className="border">
            <EmptyHeader>
              <EmptyTitle>
                {filtrado
                  ? "No hay productos con estos filtros"
                  : "Todavía no hay productos a la venta"}
              </EmptyTitle>
              <EmptyDescription>
                {filtrado
                  ? "Probá con otra búsqueda o sacá algún filtro."
                  : puedeEditar
                    ? "Cargá el primer equipo, consola o accesorio."
                    : "Cuando se cargue stock, va a aparecer acá."}
              </EmptyDescription>
            </EmptyHeader>
            <EmptyContent>
              {filtrado ? (
                <Button
                  variant="outline"
                  onClick={() => {
                    setBusqueda("")
                    setParams({})
                  }}
                >
                  Sacar los filtros
                </Button>
              ) : (
                puedeEditar && (
                  <Button onClick={() => abrir(null)}>
                    <PlusIcon />
                    Cargar producto
                  </Button>
                )
              )}
            </EmptyContent>
          </Empty>
        ) : (
          <>
            <div
              aria-busy={stock.isPlaceholderData || undefined}
              className={
                stock.isPlaceholderData
                  ? "opacity-60 transition-opacity"
                  : undefined
              }
            >
              <TablaStock
                productos={stock.data.items}
                conEstado={filtros.estado === undefined}
                onEditar={puedeEditar ? abrir : undefined}
                onBorrar={puedeEditar ? setABorrar : undefined}
              />
            </div>
            <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-muted-foreground">
              <p aria-live="polite" className="tabular-nums">
                {stock.data.total === 1
                  ? "1 producto"
                  : `${stock.data.total.toLocaleString("es-AR")} productos`}
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

      {puedeEditar && (
        <>
          <ProductoSheet
            abierto={sheet.abierto}
            onAbiertoChange={(abierto) => setSheet((s) => ({ ...s, abierto }))}
            producto={sheet.producto}
            apertura={sheet.apertura}
          />
          <ConfirmarBorrarProducto
            producto={aBorrar}
            onCancelar={() => setABorrar(null)}
            onConfirmar={() => aBorrar && borrar(aBorrar)}
          />
        </>
      )}
    </>
  )
}
