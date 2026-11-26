import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"

import { catalogosKeys } from "@/features/catalogos"

import { productosApi, type DatosProducto, type FiltrosStock } from "./api"

export const productosKeys = {
  todo: ["productos"] as const,
  lista: (filtros: FiltrosStock) =>
    [...productosKeys.todo, "lista", filtros] as const,
}

export function useStockQuery(filtros: FiltrosStock) {
  return useQuery({
    queryKey: productosKeys.lista(filtros),
    queryFn: ({ signal }) => productosApi.listar(filtros, signal),
    // Al cambiar de página o de filtro se sigue viendo la lista anterior hasta que llega.
    placeholderData: keepPreviousData,
  })
}

function useAlGuardar() {
  const queryClient = useQueryClient()
  return () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: productosKeys.todo }),
      // Un defecto escrito a mano se agrega al catálogo; el stock cambia el Resumen.
      queryClient.invalidateQueries({
        queryKey: catalogosKeys.catalogo("defectos"),
      }),
      queryClient.invalidateQueries({ queryKey: ["resumen"] }),
    ])
}

export function useCrearProducto() {
  const alGuardar = useAlGuardar()
  return useMutation({
    mutationFn: (datos: DatosProducto) => productosApi.crear(datos),
    onSuccess: alGuardar,
  })
}

export function useActualizarProducto() {
  const alGuardar = useAlGuardar()
  return useMutation({
    mutationFn: ({ id, datos }: { id: number; datos: DatosProducto }) =>
      productosApi.actualizar(id, datos),
    onSuccess: alGuardar,
  })
}

export function useEliminarProducto() {
  const alGuardar = useAlGuardar()
  return useMutation({
    mutationFn: (id: number) => productosApi.eliminar(id),
    onSuccess: alGuardar,
  })
}
