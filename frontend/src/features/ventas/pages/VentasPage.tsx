import {
  ArrowClockwiseIcon,
  CaretLeftIcon,
  CaretRightIcon,
  PlusIcon,
} from "@phosphor-icons/react"
import { useState } from "react"
import { Link, useSearchParams } from "react-router"
import { toast } from "sonner"

import { useAuth } from "@/features/auth"
import { mensajeDeError } from "@/shared/api"
import { formatearUSD } from "@/shared/lib/formato"
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
import { Skeleton } from "@/shared/ui/skeleton"

import { TAMANIO_PAGINA, type Venta } from "../api"
import { ConfirmarBorrarVenta } from "../components/ConfirmarBorrarVenta"
import { DetalleVentaSheet } from "../components/DetalleVentaSheet"
import { TablaVentas } from "../components/TablaVentas"
import { useEliminarVenta, useVentasQuery } from "../queries"

const NuevaVenta = () => (
  <Button asChild>
    <Link to="/ventas/nueva">
      <PlusIcon />
      Nueva venta
    </Link>
  </Button>
)

export function VentasPage() {
  const { puede } = useAuth()
  const [params, setParams] = useSearchParams()
  const pagina = Math.max(1, Number(params.get("pagina")) || 1)
  const ventas = useVentasQuery(pagina)
  const eliminar = useEliminarVenta()
  const [abierta, setAbierta] = useState<Venta | null>(null)
  const [aBorrar, setABorrar] = useState<Venta | null>(null)

  const irA = (n: number) => setParams(n > 1 ? { pagina: String(n) } : {})
  const paginas = ventas.data
    ? Math.max(1, Math.ceil(ventas.data.total / TAMANIO_PAGINA))
    : 1

  function borrar(venta: Venta) {
    setABorrar(null)
    eliminar.mutate(venta.id, {
      onSuccess: () => {
        setAbierta(null)
        // Era la última de la página: se vuelve a la anterior en vez de mostrarla vacía.
        if (pagina > 1 && ventas.data?.items.length === 1) irA(pagina - 1)
        toast.success(`Se borró la venta #${venta.id}.`)
      },
      // Si devolver el stock lo dejaría inconsistente, el motivo lo da la API.
      onError: (error) => toast.error(mensajeDeError(error)),
    })
  }

  return (
    <>
      <EncabezadoPagina
        titulo="Ventas"
        descripcion={
          puede("ver_costos")
            ? "Todas las ventas registradas, las últimas primero."
            : "Las ventas que registraste, las últimas primero."
        }
        acciones={<NuevaVenta />}
      />

      {ventas.isPending ? (
        <div className="flex flex-col gap-2" aria-busy="true">
          <span className="sr-only">Cargando las ventas…</span>
          {Array.from({ length: 6 }, (_, i) => (
            <Skeleton key={i} className="h-14 w-full" />
          ))}
        </div>
      ) : ventas.isError ? (
        <Alert variant="destructive">
          <AlertTitle>No se pudieron cargar las ventas</AlertTitle>
          <AlertDescription className="flex flex-col items-start gap-3">
            {mensajeDeError(ventas.error)}
            <Button
              variant="outline"
              size="sm"
              onClick={() => ventas.refetch()}
            >
              <ArrowClockwiseIcon />
              Reintentar
            </Button>
          </AlertDescription>
        </Alert>
      ) : ventas.data.items.length === 0 ? (
        <Empty className="border">
          <EmptyHeader>
            <EmptyTitle>Todavía no hay ventas</EmptyTitle>
            <EmptyDescription>
              Las ventas que se registren van a aparecer acá.
            </EmptyDescription>
          </EmptyHeader>
          <EmptyContent>
            <NuevaVenta />
          </EmptyContent>
        </Empty>
      ) : (
        <div className="flex flex-col gap-3">
          <div
            aria-busy={ventas.isPlaceholderData || undefined}
            className={
              ventas.isPlaceholderData
                ? "opacity-60 transition-opacity"
                : undefined
            }
          >
            <TablaVentas ventas={ventas.data.items} onAbrir={setAbierta} />
          </div>
          <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-muted-foreground">
            <p aria-live="polite" className="tabular-nums">
              {ventas.data.total === 1
                ? "1 venta"
                : `${ventas.data.total.toLocaleString("es-AR")} ventas`}
              {"ganancia_total_usd" in ventas.data &&
                ` · ganancia registrada ${formatearUSD(ventas.data.ganancia_total_usd)}`}
              {paginas > 1 && ` · página ${pagina} de ${paginas}`}
            </p>
            {paginas > 1 && (
              <nav aria-label="Páginas" className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={pagina <= 1}
                  onClick={() => irA(pagina - 1)}
                >
                  <CaretLeftIcon />
                  Anterior
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={pagina >= paginas}
                  onClick={() => irA(pagina + 1)}
                >
                  Siguiente
                  <CaretRightIcon />
                </Button>
              </nav>
            )}
          </div>
        </div>
      )}

      <DetalleVentaSheet
        venta={abierta}
        onCerrar={() => setAbierta(null)}
        onActualizada={setAbierta}
        onBorrar={puede("ventas:borrar") ? setABorrar : undefined}
      />
      <ConfirmarBorrarVenta
        venta={aBorrar}
        onCancelar={() => setABorrar(null)}
        onConfirmar={() => aBorrar && borrar(aBorrar)}
      />
    </>
  )
}
