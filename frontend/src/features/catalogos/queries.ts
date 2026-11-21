import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { catalogosApi, type DatosItem, type Slug } from "./api"

export const catalogosKeys = {
  todo: ["catalogos"] as const,
  catalogo: (slug: Slug) => [...catalogosKeys.todo, slug] as const,
  lista: (slug: Slug, categoriaId?: number) =>
    [...catalogosKeys.catalogo(slug), { categoriaId }] as const,
}

/** Un catálogo completo o, en modelos, capacidades y colores, solo los de una categoría. */
export function useCatalogoQuery<S extends Slug>(
  slug: S,
  categoriaId?: number,
  { habilitado = true }: { habilitado?: boolean } = {}
) {
  return useQuery({
    queryKey: catalogosKeys.lista(slug, categoriaId),
    queryFn: ({ signal }) => catalogosApi.listar(slug, categoriaId, signal),
    enabled: habilitado,
    // Cambian poco: no hace falta pedirlos cada vez que se abre una pantalla.
    staleTime: 5 * 60_000,
  })
}

function useInvalidar(slug: Slug) {
  const queryClient = useQueryClient()
  return () =>
    queryClient.invalidateQueries({ queryKey: catalogosKeys.catalogo(slug) })
}

export function useCrearItem(slug: Slug) {
  const invalidar = useInvalidar(slug)
  return useMutation({
    mutationFn: (datos: DatosItem) => catalogosApi.crear(slug, datos),
    onSuccess: invalidar,
  })
}

export function useActualizarItem(slug: Slug) {
  const invalidar = useInvalidar(slug)
  return useMutation({
    mutationFn: ({ id, cambios }: { id: number; cambios: DatosItem }) =>
      catalogosApi.actualizar(slug, id, cambios),
    onSuccess: invalidar,
  })
}

export function useEliminarItem(slug: Slug) {
  const invalidar = useInvalidar(slug)
  return useMutation({
    mutationFn: (id: number) => catalogosApi.eliminar(slug, id),
    onSuccess: invalidar,
  })
}
