import { useQuery, useQueryClient } from "@tanstack/react-query"

import { resumenApi } from "./api"

export const resumenKeys = {
  todo: ["resumen"] as const,
}

export function useResumen() {
  return useQuery({
    queryKey: resumenKeys.todo,
    queryFn: ({ signal }) => resumenApi.obtener(signal),
    // Los avisos cambian por lo que hacen otras computadoras (por ejemplo, cargar el TC).
    refetchInterval: 2 * 60_000,
  })
}

/** Para pedir el resumen de nuevo cuando algo de la pantalla cambia sus avisos. */
export function useRefrescarResumen() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: resumenKeys.todo })
}
