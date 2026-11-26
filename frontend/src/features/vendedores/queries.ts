import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { vendedoresApi, type DatosVendedor } from "./api"

export const vendedoresKeys = {
  todo: ["vendedores"] as const,
  lista: () => [...vendedoresKeys.todo, "lista"] as const,
  numero: (numero: number) =>
    [...vendedoresKeys.todo, "numero", numero] as const,
}

export function useVendedoresQuery() {
  return useQuery({
    queryKey: vendedoresKeys.lista(),
    queryFn: ({ signal }) => vendedoresApi.listar(signal),
  })
}

/** Para la venta: el nombre del vendedor con ese número. */
export function useVendedorPorNumeroQuery(numero: number | undefined) {
  return useQuery({
    queryKey: vendedoresKeys.numero(numero as number),
    queryFn: ({ signal }) => vendedoresApi.porNumero(numero as number, signal),
    enabled: numero !== undefined,
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
