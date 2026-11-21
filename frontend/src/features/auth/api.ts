import { pedir, type Schemas } from "@/shared/api"

export type Credenciales = Schemas["LoginCreate"]
export type Sesion = Schemas["SesionRead"]
export type Token = Schemas["TokenRead"]

export const authApi = {
  login: (datos: Credenciales) =>
    pedir<Token>("/auth/login", { method: "POST", body: datos }),
  me: (signal?: AbortSignal) => pedir<Sesion>("/auth/me", { signal }),
}
