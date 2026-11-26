import { ArrowClockwiseIcon, PlusIcon } from "@phosphor-icons/react"
import { useState } from "react"
import { toast } from "sonner"

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
import { Skeleton } from "@/shared/ui/skeleton"

import type { Vendedor } from "../api"
import { ConfirmarBorrarVendedor } from "../components/ConfirmarBorrarVendedor"
import { TablaVendedores } from "../components/TablaVendedores"
import { VendedorSheet } from "../components/VendedorSheet"
import { useEliminarVendedor, useVendedoresQuery } from "../queries"

export function VendedoresPage() {
  const vendedores = useVendedoresQuery()
  const eliminar = useEliminarVendedor()

  const [sheet, setSheet] = useState({
    abierto: false,
    apertura: 0,
    vendedor: null as Vendedor | null,
  })
  const [aBorrar, setABorrar] = useState<Vendedor | null>(null)

  const abrir = (vendedor: Vendedor | null) =>
    setSheet((s) => ({ abierto: true, apertura: s.apertura + 1, vendedor }))

  function borrar(vendedor: Vendedor) {
    setABorrar(null)
    eliminar.mutate(vendedor.id, {
      onSuccess: () => toast.success(`Se borró a ${vendedor.nombre}.`),
      // Con ventas no se borra: el motivo lo da la API.
      onError: (error) => toast.error(mensajeDeError(error)),
    })
  }

  return (
    <>
      <EncabezadoPagina
        titulo="Vendedores"
        descripcion="Números y nombres de los vendedores. En cada venta se carga el número."
        acciones={
          <Button onClick={() => abrir(null)}>
            <PlusIcon />
            Nuevo vendedor
          </Button>
        }
      />

      {vendedores.isPending ? (
        <div className="flex flex-col gap-2" aria-busy="true">
          <span className="sr-only">Cargando los vendedores…</span>
          {Array.from({ length: 4 }, (_, i) => (
            <Skeleton key={i} className="h-11 w-full" />
          ))}
        </div>
      ) : vendedores.isError ? (
        <Alert variant="destructive">
          <AlertTitle>No se pudieron cargar los vendedores</AlertTitle>
          <AlertDescription className="flex flex-col items-start gap-3">
            {mensajeDeError(vendedores.error)}
            <Button
              variant="outline"
              size="sm"
              onClick={() => vendedores.refetch()}
            >
              <ArrowClockwiseIcon />
              Reintentar
            </Button>
          </AlertDescription>
        </Alert>
      ) : vendedores.data.length === 0 ? (
        <Empty className="border">
          <EmptyHeader>
            <EmptyTitle>Todavía no hay vendedores</EmptyTitle>
            <EmptyDescription>
              Cargalos con su número para elegirlos al registrar una venta. Es
              opcional: una venta puede no tener vendedor.
            </EmptyDescription>
          </EmptyHeader>
          <EmptyContent>
            <Button onClick={() => abrir(null)}>
              <PlusIcon />
              Nuevo vendedor
            </Button>
          </EmptyContent>
        </Empty>
      ) : (
        <div className="flex max-w-2xl flex-col gap-3">
          <TablaVendedores
            vendedores={vendedores.data}
            onEditar={abrir}
            onBorrar={setABorrar}
          />
          <p className="text-sm text-muted-foreground tabular-nums">
            {vendedores.data.length === 1
              ? "1 vendedor"
              : `${vendedores.data.length} vendedores`}
          </p>
        </div>
      )}

      <VendedorSheet
        abierto={sheet.abierto}
        onAbiertoChange={(abierto) => setSheet((s) => ({ ...s, abierto }))}
        vendedor={sheet.vendedor}
        apertura={sheet.apertura}
      />
      <ConfirmarBorrarVendedor
        vendedor={aBorrar}
        onCancelar={() => setABorrar(null)}
        onConfirmar={() => aBorrar && borrar(aBorrar)}
      />
    </>
  )
}
