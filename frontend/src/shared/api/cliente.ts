// Cliente HTTP único. Los componentes nunca lo usan directo:
// cada feature lo envuelve en su `api.ts` y lo expone con hooks en `queries.ts`.
import { ApiError, errorDesdeRespuesta } from "./errores"
import { leerToken } from "./token"

// Nginx (Docker) y el proxy de Vite (dev) reenvían /api al backend: mismo origen, sin CORS.
const BASE = "/api"

let alPerderSesion: () => void = () => {}

/** Lo registra AuthProvider: qué hacer cuando la API responde 401 con un token puesto. */
export function registrarAlPerderSesion(fn: () => void): void {
  alPerderSesion = fn
}

type Opciones = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE"
  body?: unknown
  signal?: AbortSignal
}

export async function pedir<T>(
  ruta: string,
  { method = "GET", body, signal }: Opciones = {}
): Promise<T> {
  const token = leerToken()
  const headers: Record<string, string> = { Accept: "application/json" }
  if (body !== undefined) headers["Content-Type"] = "application/json"
  if (token) headers.Authorization = `Bearer ${token}`

  let respuesta: Response
  try {
    respuesta = await fetch(`${BASE}${ruta}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError")
      throw error
    throw errorDesdeRespuesta(0, null)
  }

  const cuerpo: unknown =
    respuesta.status === 204 ? null : await respuesta.json().catch(() => null)

  if (!respuesta.ok) {
    // 401 con token = sesión vencida o inválida → se limpia y se vuelve al login.
    // 401 sin token (por ejemplo, login con datos incorrectos) es un error común.
    if (respuesta.status === 401 && token) alPerderSesion()
    throw errorDesdeRespuesta(respuesta.status, cuerpo)
  }

  return cuerpo as T
}

export { ApiError }
