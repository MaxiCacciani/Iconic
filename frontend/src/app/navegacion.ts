import {
  BookmarkSimpleIcon,
  CalendarCheckIcon,
  DeviceMobileIcon,
  HouseIcon,
  IdentificationBadgeIcon,
  type Icon,
  PackageIcon,
  ReceiptIcon,
  ShieldCheckIcon,
  UserGearIcon,
  UsersIcon,
  WrenchIcon,
} from "@phosphor-icons/react"
import type { ComponentType } from "react"

export type Seccion = {
  /** Permiso que devuelve `GET /auth/me`. Sin él, la sección no aparece ni se puede abrir. */
  permiso: string
  ruta: string
  titulo: string
  icono: Icon
  grupo: "Operación" | "Administración"
  cargar: () => Promise<ComponentType>
}

// El orden de esta lista es el orden del menú.
export const SECCIONES: Seccion[] = [
  {
    permiso: "resumen",
    ruta: "/",
    titulo: "Resumen",
    icono: HouseIcon,
    grupo: "Operación",
    cargar: () => import("@/features/resumen").then((m) => m.ResumenPage),
  },
  {
    permiso: "ventas",
    ruta: "/ventas",
    titulo: "Ventas",
    icono: ReceiptIcon,
    grupo: "Operación",
    cargar: () => import("@/features/ventas").then((m) => m.VentasPage),
  },
  {
    permiso: "productos",
    ruta: "/productos",
    titulo: "Productos",
    icono: DeviceMobileIcon,
    grupo: "Operación",
    cargar: () => import("@/features/productos").then((m) => m.ProductosPage),
  },
  {
    permiso: "clientes",
    ruta: "/clientes",
    titulo: "Clientes",
    icono: UsersIcon,
    grupo: "Operación",
    cargar: () => import("@/features/clientes").then((m) => m.ClientesPage),
  },
  {
    permiso: "reservas",
    ruta: "/reservas",
    titulo: "Reservas",
    icono: BookmarkSimpleIcon,
    grupo: "Operación",
    cargar: () => import("@/features/reservas").then((m) => m.ReservasPage),
  },
  {
    permiso: "cobros",
    ruta: "/cobros",
    titulo: "Cobros",
    icono: CalendarCheckIcon,
    grupo: "Operación",
    cargar: () => import("@/features/cobros").then((m) => m.CobrosPage),
  },
  {
    permiso: "garantias",
    ruta: "/garantias",
    titulo: "Garantías",
    icono: ShieldCheckIcon,
    grupo: "Operación",
    cargar: () => import("@/features/garantias").then((m) => m.GarantiasPage),
  },
  {
    permiso: "reclamos",
    ruta: "/reclamos",
    titulo: "Reclamos",
    icono: WrenchIcon,
    grupo: "Operación",
    cargar: () => import("@/features/reclamos").then((m) => m.ReclamosPage),
  },
  {
    permiso: "packs",
    ruta: "/packs",
    titulo: "Packs",
    icono: PackageIcon,
    grupo: "Administración",
    cargar: () => import("@/features/packs").then((m) => m.PacksPage),
  },
  {
    permiso: "vendedores",
    ruta: "/vendedores",
    titulo: "Vendedores",
    icono: IdentificationBadgeIcon,
    grupo: "Administración",
    cargar: () => import("@/features/vendedores").then((m) => m.VendedoresPage),
  },
  {
    permiso: "usuarios",
    ruta: "/usuarios",
    titulo: "Usuarios",
    icono: UserGearIcon,
    grupo: "Administración",
    cargar: () => import("@/features/usuarios").then((m) => m.UsuariosPage),
  },
]
