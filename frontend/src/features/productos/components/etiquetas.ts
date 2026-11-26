// Solo textos para mostrar los valores fijos que devuelve la API.
import type { Condicion, EstadoProducto } from "../api"

export const CONDICION: Record<Condicion, string> = {
  nuevo: "Nuevo",
  usado: "Usado",
}

export const ESTADO: Record<EstadoProducto, string> = {
  disponible: "Disponible",
  reservado: "Reservado",
  vendido: "Vendido",
}

type ConVariante = {
  capacidad: { nombre: string } | null
  color: { nombre: string } | null
}

/** "128 GB · Negro", lo que diferencia a dos equipos del mismo modelo. */
export function variante(p: ConVariante): string {
  return [p.capacidad?.nombre, p.color?.nombre].filter(Boolean).join(" · ")
}
