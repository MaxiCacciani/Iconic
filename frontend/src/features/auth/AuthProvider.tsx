import { useQueryClient } from "@tanstack/react-query"
import {
  createContext,
  use,
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"

import {
  borrarToken,
  guardarToken,
  leerToken,
  registrarAlPerderSesion,
} from "@/shared/api"

import type { Sesion } from "./api"
import { useSesionQuery } from "./queries"

type EstadoSesion = "anonimo" | "cargando" | "activa" | "error"

type AuthContexto = {
  estado: EstadoSesion
  /** Viene de `GET /auth/me` (TanStack Query). No se copia a estado local. */
  sesion: Sesion | undefined
  iniciarSesion: (token: string) => void
  cerrarSesion: () => void
  /** El backend decide los permisos; el front solo pregunta si está en la lista. */
  puede: (permiso: string) => boolean
}

const Contexto = createContext<AuthContexto | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [token, setToken] = useState<string | null>(leerToken)
  const sesionQuery = useSesionQuery(token)

  const cerrarSesion = useCallback(() => {
    borrarToken()
    setToken(null)
    queryClient.clear()
  }, [queryClient])

  const iniciarSesion = useCallback((nuevo: string) => {
    guardarToken(nuevo)
    setToken(nuevo)
  }, [])

  // Cualquier 401 con token (sesión vencida) limpia todo; las rutas protegidas mandan al login.
  useEffect(() => registrarAlPerderSesion(cerrarSesion), [cerrarSesion])

  const valor = useMemo<AuthContexto>(() => {
    const sesion = sesionQuery.data
    const estado: EstadoSesion =
      token === null
        ? "anonimo"
        : sesion
          ? "activa"
          : sesionQuery.isError
            ? "error"
            : "cargando"
    return {
      estado,
      sesion,
      iniciarSesion,
      cerrarSesion,
      puede: (permiso) => sesion?.permisos.includes(permiso) ?? false,
    }
  }, [
    token,
    sesionQuery.data,
    sesionQuery.isError,
    iniciarSesion,
    cerrarSesion,
  ])

  return <Contexto value={valor}>{children}</Contexto>
}

export function useAuth(): AuthContexto {
  const contexto = use(Contexto)
  if (!contexto)
    throw new Error("useAuth tiene que usarse dentro de <AuthProvider>")
  return contexto
}
