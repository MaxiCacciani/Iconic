import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { vendedoresApi, type DatosVendedor } from "./api"

export const vendedoresKeys = {
  todo: ["vendedores"] as const,
  lista: () => [...vendedoresKeys.todo, "lista"] as const,
}

export function useVendedoresQuery() {
  return useQuery({
    queryKey: vendedoresKeys.lista(),
    queryFn: ({ signal }) => vendedoresApi.listar(signal),
  })
}

function useAlGuardar() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: vendedoresKeys.todo })
}

export function useCrearVendedor() {
  const alGuardar = useAlGuardar()
  return useMutation({
    mutationFn: (datos: DatosVendedor) => vendedoresApi.crear(datos),
    onSuccess: alGuardar,
  })
}

export function useActualizarVendedor() {
  const alGuardar = useAlGuardar()
  return useMutation({
    mutationFn: ({ id, datos }: { id: number; datos: DatosVendedor }) =>
      vendedoresApi.actualizar(id, datos),
    onSuccess: alGuardar,
  })
}

export function useEliminarVendedor() {
  const alGuardar = useAlGuardar()
  return useMutation({
    mutationFn: (id: number) => vendedoresApi.eliminar(id),
    onSuccess: alGuardar,
  })
}
