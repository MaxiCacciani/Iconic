// Lo que el usuario va cargando en el wizard, crudo y sin cuentas: los totales, el saldo y
// las validaciones salen de la API (`POST /ventas/cotizar` y `POST /ventas`).
import { createContext, useContext, type Dispatch } from "react"

import type { Cliente } from "@/features/clientes"
import { EQUIPO_VACIO, type Equipo, type Producto } from "@/features/productos"

import type { Cotizacion } from "../api"

export type Linea = {
  /** Identifica el renglón en pantalla (un producto puede ir con precio y de regalo). */
  clave: number
  producto: Producto
  precio: string
  cantidad: string
  esRegalo: boolean
}

export type Borrador = {
  lineas: Linea[]
  ultimaClave: number
  cliente: Cliente | null
  /** Vacío: el método de pago predeterminado del catálogo. */
  metodoPagoId: string
  conCanje: boolean
  canjeValor: string
  canje: Equipo
  vendedorNumero: string
  garantiaMeses: string
}

export const BORRADOR_VACIO: Borrador = {
  lineas: [],
  ultimaClave: 0,
  cliente: null,
  metodoPagoId: "",
  conCanje: false,
  canjeValor: "",
  canje: { ...EQUIPO_VACIO, condicion: "usado" },
  vendedorNumero: "",
  garantiaMeses: "3",
}

type NuevaLinea = Pick<Linea, "producto" | "cantidad" | "esRegalo">

export type Accion =
  | { tipo: "agregar"; lineas: NuevaLinea[] }
  | { tipo: "linea"; clave: number; cambios: Partial<Linea> }
  | { tipo: "quitar"; clave: number }
  | { tipo: "cambiar"; cambios: Partial<Borrador> }

const precioDe = (p: Producto) =>
  Number(p.precio_usd).toString().replace(".", ",")

export function reducir(b: Borrador, accion: Accion): Borrador {
  switch (accion.tipo) {
    case "agregar": {
      let clave = b.ultimaClave
      // El mismo producto en el mismo tipo de renglón ya está: no se repite.
      const nuevas = accion.lineas
        .filter(
          (n) =>
            !b.lineas.some(
              (l) =>
                l.producto.id === n.producto.id && l.esRegalo === n.esRegalo
            )
        )
        .map((n) => ({ ...n, clave: ++clave, precio: precioDe(n.producto) }))
      return { ...b, lineas: [...b.lineas, ...nuevas], ultimaClave: clave }
    }
    case "linea":
      return {
        ...b,
        lineas: b.lineas.map((l) =>
          l.clave === accion.clave ? { ...l, ...accion.cambios } : l
        ),
      }
    case "quitar":
      return { ...b, lineas: b.lineas.filter((l) => l.clave !== accion.clave) }
    case "cambiar":
      return { ...b, ...accion.cambios }
  }
}

export type Venta = {
  b: Borrador
  despachar: Dispatch<Accion>
  /** La última cotización (la anterior mientras llega la nueva). */
  cotizacion: Cotizacion | undefined
  /** Errores de la API por campo (`items.0.cantidad`, `canje.imei`…). */
  campos: Record<string, string>
}

export const VentaContext = createContext<Venta | null>(null)

export function useVenta(): Venta {
  const venta = useContext(VentaContext)
  if (!venta) throw new Error("useVenta va dentro de NuevaVentaPage")
  return venta
}
