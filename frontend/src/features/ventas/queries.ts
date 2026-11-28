import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"

import { clientesKeys } from "@/features/clientes"
import { productosKeys } from "@/features/productos"

import { ventasApi, type DatosVenta } from "./api"

export const ventasKeys = {
  todo: ["ventas"] as const,
  lista: (pagina: number) => [...ventasKeys.todo, "lista", pagina] as const,
  // Fuera de `todo`: al vender se invalida `todo`, y volver a cotizar productos que
  // ya se vendieron daría un 422.
  cotizacion: (datos: DatosVenta) => ["cotizacion-venta", datos] as const,
}

export function useVentasQuery(pagina: number) {
  return useQuery({
    queryKey: ventasKeys.lista(pagina),
    queryFn: ({ signal }) => ventasApi.listar(pagina, signal),
    placeholderData: keepPreviousData,
  })
}

/** Total, canje y saldo del carrito. No graba nada: se pide en cada cambio. */
export function useCotizacionQuery(datos: DatosVenta, habilitada: boolean) {
  return useQuery({
    queryKey: ventasKeys.cotizacion(datos),
    queryFn: ({ signal }) => ventasApi.cotizar(datos, signal),
    enabled: habilitada,
    placeholderData: keepPreviousData,
    staleTime: 0,
  })
}

function useAlGuardar() {
  const queryClient = useQueryClient()
  // Vender o borrar una venta cambia el stock, los packs (unidades), el Resumen y las
  // cuotas (agenda y ficha del cliente).
  return () =>
    Promise.all(
      [
        ventasKeys.todo,
        productosKeys.todo,
        ["packs"],
        ["resumen"],
        ["cobros"],
        clientesKeys.todo,
      ].map((queryKey) => queryClient.invalidateQueries({ queryKey }))
    )
}

export function useCrearVenta() {
  const alGuardar = useAlGuardar()
  return useMutation({
    mutationFn: (datos: DatosVenta) => ventasApi.crear(datos),
    onSuccess: alGuardar,
  })
}

/** Solo del Administrador. Cambia la ganancia de la venta y la del historial. */
export function useCambiarComision() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, comision }: { id: number; comision: string }) =>
      ventasApi.cambiarComision(id, comision),
    onSuccess: () =>
      Promise.all(
        [ventasKeys.todo, ["resumen"]].map((queryKey) =>
          queryClient.invalidateQueries({ queryKey })
        )
      ),
  })
}

export function useEliminarVenta() {
  const alGuardar = useAlGuardar()
  return useMutation({
    mutationFn: (id: number) => ventasApi.eliminar(id),
    onSuccess: alGuardar,
  })
}

/** Genera el PDF en la API y lo guarda como `venta-<id>.pdf`. */
export function useDescargarComprobante() {
  return useMutation({
    mutationFn: (id: number) => ventasApi.comprobante(id),
    onSuccess: (archivo, id) => {
      const url = URL.createObjectURL(archivo)
      const enlace = document.createElement("a")
      enlace.href = url
      enlace.download = `venta-${id}.pdf`
      enlace.click()
      URL.revokeObjectURL(url)
    },
  })
}
