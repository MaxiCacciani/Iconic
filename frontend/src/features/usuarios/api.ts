import { pedir, type Schemas } from "@/shared/api"

export type Usuario = Schemas["UsuarioRead"]
export type UsuarioNuevo = Schemas["UsuarioCreate"]
export type UsuarioCambios = Schemas["UsuarioUpdate"]
export type Rol = Usuario["rol"]

export const usuariosApi = {
  listar: (signal?: AbortSignal) => pedir<Usuario[]>("/usuarios", { signal }),
  crear: (datos: UsuarioNuevo) =>
    pedir<Usuario>("/usuarios", { method: "POST", body: datos }),
  actualizar: (id: number, cambios: UsuarioCambios) =>
    pedir<Usuario>(`/usuarios/${id}`, { method: "PATCH", body: cambios }),
}
