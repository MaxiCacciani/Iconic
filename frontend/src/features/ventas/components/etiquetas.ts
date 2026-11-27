// Solo textos para mostrar lo que devuelve la API.
import { variante } from "@/features/productos"

import type { Venta } from "../api"

export const MODALIDAD: Record<Venta["modalidad"], string> = {
  contado: "Contado",
  cuotas: "En cuotas",
}

/** "iPhone 15 · 128 GB · Negro" */
export function nombreProducto(p: Venta["items"][number]["producto"]): string {
  return [p.modelo.nombre, variante(p)].filter(Boolean).join(" · ")
}

/** "iPhone 15 · 128 GB · Negro y 2 más": lo que se ve de la venta en el historial. */
export function resumenProductos(v: Venta): string {
  const [primero, ...resto] = v.items
  const nombre = nombreProducto(primero.producto)
  return resto.length === 0 ? nombre : `${nombre} y ${resto.length} más`
}
