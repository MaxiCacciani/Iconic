import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { usuariosApi, type UsuarioCambios, type UsuarioNuevo } from "./api"

export const usuariosKeys = {
  todo: ["usuarios"] as const,
  lista: () => [...usuariosKeys.todo, "lista"] as const,
}

export function useUsuariosQuery() {
  return useQuery({
    queryKey: usuariosKeys.lista(),
    queryFn: ({ signal }) => usuariosApi.listar(signal),
  })
}

export function useCrearUsuario() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (datos: UsuarioNuevo) => usuariosApi.crear(datos),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: usuariosKeys.todo }),
  })
}

export function useActualizarUsuario() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, cambios }: { id: number; cambios: UsuarioCambios }) =>
      usuariosApi.actualizar(id, cambios),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: usuariosKeys.todo }),
  })
}
