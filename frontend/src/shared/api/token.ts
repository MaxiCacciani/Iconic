// El token es la sesión, no un dato del negocio: es lo único que guarda el navegador.
const CLAVE = "iconic.token"

export function leerToken(): string | null {
  try {
    return localStorage.getItem(CLAVE)
  } catch {
    return null
  }
}

export function guardarToken(token: string): void {
  try {
    localStorage.setItem(CLAVE, token)
  } catch {
    // Sin storage la sesión dura lo que dure la pestaña (queda en memoria en AuthContext).
  }
}

export function borrarToken(): void {
  try {
    localStorage.removeItem(CLAVE)
  } catch {
    // nada que borrar
  }
}
