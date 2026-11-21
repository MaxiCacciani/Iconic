import { useMutation, useQuery } from "@tanstack/react-query"

import { authApi, type Credenciales } from "./api"

export const authKeys = {
  todo: ["auth"] as const,
  sesion: () => [...authKeys.todo, "me"] as const,
}

/** Sesión actual (`GET /auth/me`): nombre, rol y permisos. Solo corre si hay token. */
export function useSesionQuery(token: string | null) {
  return useQuery({
    queryKey: [...authKeys.sesion(), token],
    queryFn: ({ signal }) => authApi.me(signal),
    enabled: token !== null,
    staleTime: 5 * 60_000,
  })
}

export function useLoginMutation() {
  return useMutation({
    mutationFn: (datos: Credenciales) => authApi.login(datos),
  })
}
