import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"

import { clientesKeys } from "@/features/clientes"

import { cobrosApi, type Mes } from "./api"

export const cobrosKeys = {
  todo: ["cobros"] as const,
  agenda: (mes: Mes) => [...cobrosKeys.todo, "agenda", mes] as const,
}

export function useAgendaQuery(mes: Mes) {
  return useQuery({
    queryKey: cobrosKeys.agenda(mes),
    queryFn: ({ signal }) => cobrosApi.agenda(mes, signal),
    placeholderData: keepPreviousData,
  })
}

export function useCobrar() {
  const queryClient = useQueryClient()
  // Cobrar cambia la agenda, el Resumen (cobros del mes y vencidas), la ficha del cliente
  // y las cuotas en el detalle de la venta.
  return useMutation({
    mutationFn: (id: number) => cobrosApi.cobrar(id),
    onSuccess: () =>
      Promise.all(
        [cobrosKeys.todo, ["resumen"], clientesKeys.todo, ["ventas"]].map(
          (queryKey) => queryClient.invalidateQueries({ queryKey })
        )
      ),
  })
}
