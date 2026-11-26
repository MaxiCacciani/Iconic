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
