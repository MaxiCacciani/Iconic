import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { packsApi, type DatosPack, type EnCarrito } from "./api"

export const packsKeys = {
  todo: ["packs"] as const,
  lista: () => [...packsKeys.todo, "lista"] as const,
}

export function usePacksQuery() {
  return useQuery({
    queryKey: packsKeys.lista(),
    queryFn: ({ signal }) => packsApi.listar(signal),
  })
}

function useAlGuardar() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: packsKeys.todo })
}

export function useCrearPack() {
  const alGuardar = useAlGuardar()
  return useMutation({
    mutationFn: (datos: DatosPack) => packsApi.crear(datos),
    onSuccess: alGuardar,
  })
}

export function useActualizarPack() {
  const alGuardar = useAlGuardar()
  return useMutation({
    mutationFn: ({ id, datos }: { id: number; datos: DatosPack }) =>
      packsApi.actualizar(id, datos),
    onSuccess: alGuardar,
  })
}

export function useEliminarPack() {
  const alGuardar = useAlGuardar()
  return useMutation({
    mutationFn: (id: number) => packsApi.eliminar(id),
    onSuccess: alGuardar,
  })
}

/** Para el carrito de la venta (Fase 7): no guarda nada, solo devuelve qué agregar. Si falta
 * stock de algún ítem falla con un 409 y no hay nada que agregar: el mensaje de la API
 * ("No se pudo agregar el pack por falta de stock de …") va tal cual al usuario. */
export function useAplicarPack() {
  return useMutation({
    mutationFn: ({ id, enCarrito }: { id: number; enCarrito?: EnCarrito[] }) =>
      packsApi.aplicar(id, enCarrito),
  })
}
