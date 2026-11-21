import type { ReactNode } from "react"
import { Navigate, useLocation } from "react-router"

import { useAuth } from "@/features/auth"

import { CargandoSesion, ErrorSesion } from "./pages/EstadosSesion"
import { SinPermisoPage } from "./pages/SinPermisoPage"

/** Sin sesión no hay acceso: manda al login y recuerda a dónde quería ir. */
export function RequiereSesion({ children }: { children: ReactNode }) {
  const { estado } = useAuth()
  const location = useLocation()

  if (estado === "anonimo")
    return <Navigate to="/login" replace state={{ desde: location.pathname }} />
  if (estado === "cargando") return <CargandoSesion />
  if (estado === "error") return <ErrorSesion />
  return children
}

export function RequierePermiso({
  permiso,
  children,
}: {
  permiso: string
  children: ReactNode
}) {
  const { puede } = useAuth()
  return puede(permiso) ? children : <SinPermisoPage />
}
