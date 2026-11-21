import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { tipoCambioApi, type TipoCambioCarga } from "./api"

export const tipoCambioKeys = {
  todo: ["tipo-cambio"] as const,
  hoy: () => [...tipoCambioKeys.todo, "hoy"] as const,
}

// Otra computadora puede cargarlo, y a la medianoche vuelve a faltar: se revisa seguido.
const REVISAR_CADA = 2 * 60_000

export function useTipoCambioHoy() {
  return useQuery({
    queryKey: tipoCambioKeys.hoy(),
    queryFn: ({ signal }) => tipoCambioApi.hoy(signal),
    refetchInterval: REVISAR_CADA,
  })
}

export function useCargarTipoCambio() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (datos: TipoCambioCarga) => tipoCambioApi.cargarHoy(datos),
    onSuccess: (hoy) => {
      queryClient.setQueryData(tipoCambioKeys.hoy(), hoy)
      return queryClient.invalidateQueries({ queryKey: tipoCambioKeys.todo })
    },
  })
}
