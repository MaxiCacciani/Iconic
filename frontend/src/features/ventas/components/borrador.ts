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
  /** Solo la carga el Administrador; vacía no se manda. */
  comision: string
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
  comision: "",
}

type NuevaLinea = Pick<Linea, "producto" | "cantidad" | "esRegalo">

export type Accion =
  /** `sumar`: si el producto ya está, se le suman las unidades (packs). Si no, el
   * que ya está queda como está (el buscador). */
  | { tipo: "agregar"; lineas: NuevaLinea[]; sumar?: boolean }
  | { tipo: "linea"; clave: number; cambios: Partial<Linea> }
  | { tipo: "quitar"; clave: number }
  | { tipo: "cambiar"; cambios: Partial<Borrador> }

const precioDe = (p: Producto) =>
  Number(p.precio_usd).toString().replace(".", ",")

export function reducir(b: Borrador, accion: Accion): Borrador {
  switch (accion.tipo) {
    case "agregar": {
      let clave = b.ultimaClave
      const lineas = [...b.lineas]
      for (const n of accion.lineas) {
        // El mismo producto en el mismo tipo de renglón va en un solo renglón.
        const i = lineas.findIndex(
          (l) => l.producto.id === n.producto.id && l.esRegalo === n.esRegalo
        )
        if (i === -1) {
          lineas.push({ ...n, clave: ++clave, precio: precioDe(n.producto) })
        } else if (accion.sumar) {
          // Un pack puede traer más unidades de un accesorio que ya está en el
          // carrito (la API ya descontó las del carrito): se suman a ese renglón.
          const l = lineas[i]
          lineas[i] = {
            ...l,
            cantidad: String((Number(l.cantidad) || 1) + Number(n.cantidad)),
          }
        }
      }
      return { ...b, lineas, ultimaClave: clave }
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
