import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"

import { clientesApi, type DatosCliente, type FiltrosClientes } from "./api"

/** Cuántos resultados muestra el buscador: si no está, se sigue escribiendo. */
const RESULTADOS_BUSCADOR = 8

export const clientesKeys = {
  todo: ["clientes"] as const,
  lista: (filtros: FiltrosClientes) =>
    [...clientesKeys.todo, "lista", filtros] as const,
  buscador: (texto: string) =>
    [...clientesKeys.todo, "buscador", texto] as const,
  ficha: (id: number) => [...clientesKeys.todo, "ficha", id] as const,
}

export function useClientesQuery(filtros: FiltrosClientes) {
  return useQuery({
    queryKey: clientesKeys.lista(filtros),
    queryFn: ({ signal }) => clientesApi.listar(filtros, signal),
    placeholderData: keepPreviousData,
  })
}

/** Para el buscador: los primeros que coinciden con lo escrito. */
export function useBuscarClientesQuery(texto: string, habilitado: boolean) {
  return useQuery({
    queryKey: clientesKeys.buscador(texto),
    queryFn: ({ signal }) =>
      clientesApi.listar(
        { buscar: texto, pagina: 1 },
        signal,
        RESULTADOS_BUSCADOR
      ),
    enabled: habilitado,
    placeholderData: keepPreviousData,
  })
}

export function useClienteQuery(id: number) {
  return useQuery({
    queryKey: clientesKeys.ficha(id),
    queryFn: ({ signal }) => clientesApi.obtener(id, signal),
    enabled: Number.isInteger(id) && id > 0,
  })
}

function useAlGuardar() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: clientesKeys.todo })
}

export function useCrearCliente() {
  const alGuardar = useAlGuardar()
  return useMutation({
    mutationFn: (datos: DatosCliente) => clientesApi.crear(datos),
    onSuccess: alGuardar,
  })
}

export function useActualizarCliente() {
  const alGuardar = useAlGuardar()
  return useMutation({
    mutationFn: ({ id, datos }: { id: number; datos: DatosCliente }) =>
      clientesApi.actualizar(id, datos),
    onSuccess: alGuardar,
  })
}

export function useEliminarCliente() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => clientesApi.eliminar(id),
    onSuccess: (_, id) => {
      // La ficha ya no existe: se saca de la caché en vez de pedirla de nuevo (daría 404).
      queryClient.removeQueries({ queryKey: clientesKeys.ficha(id) })
      return queryClient.invalidateQueries({ queryKey: clientesKeys.todo })
    },
  })
}
