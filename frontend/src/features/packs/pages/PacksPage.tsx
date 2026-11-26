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

import type { Pack } from "../api"
import { ConfirmarBorrarPack } from "../components/ConfirmarBorrarPack"
import { PackSheet } from "../components/PackSheet"
import { TarjetaPack } from "../components/TarjetaPack"
import { useEliminarPack, usePacksQuery } from "../queries"

export function PacksPage() {
  const packs = usePacksQuery()
  const eliminar = useEliminarPack()

  const [sheet, setSheet] = useState({
    abierto: false,
    apertura: 0,
    pack: null as Pack | null,
  })
  const [aBorrar, setABorrar] = useState<Pack | null>(null)

  const abrir = (pack: Pack | null) =>
    setSheet((s) => ({ abierto: true, apertura: s.apertura + 1, pack }))

  function borrar(pack: Pack) {
    setABorrar(null)
    eliminar.mutate(pack.id, {
      onSuccess: () => toast.success(`Se borró el pack «${pack.nombre}».`),
      onError: (error) => toast.error(mensajeDeError(error)),
    })
  }

  return (
    <>
      <EncabezadoPagina
        titulo="Packs"
        descripcion="Combos para sumar de una vez al carrito de una venta."
        acciones={
          <Button onClick={() => abrir(null)}>
            <PlusIcon />
            Nuevo pack
          </Button>
        }
      />

      {packs.isPending ? (
        <div
          className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3"
          aria-busy="true"
        >
          <span className="sr-only">Cargando los packs…</span>
          {Array.from({ length: 3 }, (_, i) => (
            <Skeleton key={i} className="h-48 w-full rounded-xl" />
          ))}
        </div>
      ) : packs.isError ? (
        <Alert variant="destructive">
          <AlertTitle>No se pudieron cargar los packs</AlertTitle>
          <AlertDescription className="flex flex-col items-start gap-3">
            {mensajeDeError(packs.error)}
            <Button variant="outline" size="sm" onClick={() => packs.refetch()}>
              <ArrowClockwiseIcon />
              Reintentar
            </Button>
          </AlertDescription>
        </Alert>
      ) : packs.data.length === 0 ? (
        <Empty className="border">
          <EmptyHeader>
            <EmptyTitle>Todavía no hay packs</EmptyTitle>
            <EmptyDescription>
              Por ejemplo, «iPhone + accesorios de regalo»: un iPhone, un vidrio
              templado y una funda de regalo. Al vender se agregan de una vez.
            </EmptyDescription>
          </EmptyHeader>
          <EmptyContent>
            <Button onClick={() => abrir(null)}>
              <PlusIcon />
              Nuevo pack
            </Button>
          </EmptyContent>
        </Empty>
      ) : (
        <div className="grid items-start gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {packs.data.map((pack) => (
            <TarjetaPack
              key={pack.id}
              pack={pack}
              onEditar={abrir}
              onBorrar={setABorrar}
            />
          ))}
        </div>
      )}

      <PackSheet
        abierto={sheet.abierto}
        onAbiertoChange={(abierto) => setSheet((s) => ({ ...s, abierto }))}
        pack={sheet.pack}
        apertura={sheet.apertura}
      />
      <ConfirmarBorrarPack
        pack={aBorrar}
        onCancelar={() => setABorrar(null)}
        onConfirmar={() => aBorrar && borrar(aBorrar)}
      />
    </>
  )
}
