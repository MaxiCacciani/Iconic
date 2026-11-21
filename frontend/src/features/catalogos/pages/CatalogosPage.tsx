import { ArrowClockwiseIcon, ListPlusIcon } from "@phosphor-icons/react"
import { useMemo, useState } from "react"
import { useSearchParams } from "react-router"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select"
import { Skeleton } from "@/shared/ui/skeleton"

import type { ItemCatalogo, Slug } from "../api"
import { definicionDe, valorDe } from "../catalogos"
import { ConfirmarBorrar } from "../components/ConfirmarBorrar"
import { ItemSheet } from "../components/ItemSheet"
import { NavCatalogos } from "../components/NavCatalogos"
import { TablaCatalogo } from "../components/TablaCatalogo"
import { useCatalogoQuery, useEliminarItem } from "../queries"

const TODAS = "todas"

export function CatalogosPage() {
  // El catálogo y la categoría van en la URL: se pueden compartir y sobreviven a un F5.
  const [params, setParams] = useSearchParams()
  const d = definicionDe(params.get("lista"))
  const categoriaId = d.porCategoria
    ? Number(params.get("categoria")) || undefined
    : undefined

  const items = useCatalogoQuery(d.slug, categoriaId)
  const categorias = useCatalogoQuery("categorias", undefined, {
    habilitado: Boolean(d.porCategoria),
  })
  const tipos = useCatalogoQuery("tipos-categoria", undefined, {
    habilitado: Boolean(d.conTipo),
  })
  const eliminar = useEliminarItem(d.slug)

  const [sheetAbierto, setSheetAbierto] = useState(false)
  const [editando, setEditando] = useState<ItemCatalogo | null>(null)
  const [aBorrar, setABorrar] = useState<ItemCatalogo | null>(null)

  const nombresCategoria = useMemo(
    () => new Map(categorias.data?.map((c) => [c.id, c.nombre])),
    [categorias.data]
  )
  const nombresTipo = useMemo(
    () => new Map(tipos.data?.map((t) => [t.id, t.nombre])),
    [tipos.data]
  )
  const categoriaActual = categoriaId
    ? nombresCategoria.get(categoriaId)
    : undefined
  const texto = (item: ItemCatalogo) => String(valorDe(item, d.campoTexto))

  function elegirCatalogo(slug: Slug) {
    setParams({ lista: slug })
    setSheetAbierto(false)
  }

  function elegirCategoria(valor: string) {
    setParams(
      valor === TODAS ? { lista: d.slug } : { lista: d.slug, categoria: valor }
    )
  }

  function abrirAlta() {
    setEditando(null)
    setSheetAbierto(true)
  }

  function abrirEdicion(item: ItemCatalogo) {
    setEditando(item)
    setSheetAbierto(true)
  }

  function borrar(item: ItemCatalogo) {
    setABorrar(null)
    eliminar.mutate(item.id, {
      onSuccess: () => toast.success(`Se borró «${texto(item)}».`),
      // Si está en uso, la API responde 409 con qué lo usa.
      onError: (error) => toast.error(mensajeDeError(error)),
    })
  }

  const cargando =
    items.isPending ||
    (d.porCategoria && categorias.isPending) ||
    (d.conTipo && tipos.isPending)
  const fallo = [items, categorias, tipos].find((q) => q.isError)

  return (
    <>
      <EncabezadoPagina
        titulo="Catálogos"
        descripcion="Las listas que se eligen al cargar productos, clientes, ventas y reclamos."
      />

      <div className="grid gap-6 md:grid-cols-[13rem_minmax(0,1fr)] md:gap-8">
        <NavCatalogos actual={d.slug} onElegir={elegirCatalogo} />

        <section
          aria-labelledby="titulo-catalogo"
          className="flex min-w-0 flex-col gap-4"
        >
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div className="flex max-w-prose flex-col gap-1">
              <h2 id="titulo-catalogo" className="font-heading text-2xl">
                {d.titulo}
              </h2>
              <p className="text-sm text-pretty text-muted-foreground">
                {d.descripcion}
              </p>
            </div>
            <Button onClick={abrirAlta} disabled={Boolean(cargando || fallo)}>
              <ListPlusIcon />
              {d.nuevo}
            </Button>
          </div>

          {d.porCategoria && (
            <Select
              value={categoriaId ? String(categoriaId) : TODAS}
              onValueChange={elegirCategoria}
              disabled={categorias.isPending}
            >
              <SelectTrigger
                className="w-full sm:w-64"
                aria-label="Filtrar por categoría"
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={TODAS}>Todas las categorías</SelectItem>
                <SelectSeparator />
                {categorias.data?.map((c) => (
                  <SelectItem key={c.id} value={String(c.id)}>
                    {c.nombre}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}

          {fallo ? (
            <Alert variant="destructive">
              <AlertTitle>No se pudo cargar la lista</AlertTitle>
              <AlertDescription className="flex flex-col items-start gap-3">
                {mensajeDeError(fallo.error)}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => fallo.refetch()}
                >
                  <ArrowClockwiseIcon />
                  Reintentar
                </Button>
              </AlertDescription>
            </Alert>
          ) : cargando || !items.data ? (
            <div className="flex flex-col gap-2" aria-busy="true">
              <span className="sr-only">
                Cargando {d.titulo.toLowerCase()}…
              </span>
              {Array.from({ length: 5 }, (_, i) => (
                <Skeleton key={i} className="h-11 w-full" />
              ))}
            </div>
          ) : items.data.length === 0 ? (
            <Empty className="border">
              <EmptyHeader>
                <EmptyTitle>
                  {categoriaActual
                    ? `${categoriaActual} todavía no tiene ${d.titulo.toLowerCase()}`
                    : `Todavía no hay ${d.titulo.toLowerCase()}`}
                </EmptyTitle>
                <EmptyDescription>
                  Lo que agregues acá se va a poder elegir al cargar los datos.
                </EmptyDescription>
              </EmptyHeader>
              <EmptyContent>
                <Button onClick={abrirAlta}>
                  <ListPlusIcon />
                  {d.nuevo}
                </Button>
              </EmptyContent>
            </Empty>
          ) : (
            <TablaCatalogo
              definicion={d}
              items={items.data}
              categorias={
                d.porCategoria && !categoriaId ? nombresCategoria : undefined
              }
              tipos={d.conTipo ? nombresTipo : undefined}
              onEditar={abrirEdicion}
              onBorrar={setABorrar}
            />
          )}
        </section>
      </div>

      <ItemSheet
        abierto={sheetAbierto}
        onAbiertoChange={setSheetAbierto}
        definicion={d}
        item={editando}
        categorias={categorias.data ?? []}
        categoriaInicial={categoriaId}
        tipos={tipos.data ?? []}
      />
      <ConfirmarBorrar
        texto={aBorrar ? texto(aBorrar) : null}
        onCancelar={() => setABorrar(null)}
        onConfirmar={() => aBorrar && borrar(aBorrar)}
      />
    </>
  )
}
