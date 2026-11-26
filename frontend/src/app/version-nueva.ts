// Cuando se publica una versión nueva, los archivos de cada pantalla cambian de nombre
// (llevan un hash) y los de la versión anterior dejan de existir. Una pestaña que quedó
// abierta con la versión vieja falla al abrir una sección que todavía no había cargado.
// Se arregla recargando: se baja el index.html nuevo, que apunta a los archivos nuevos.

const CLAVE = "iconic:recarga-por-version"
// Si en este lapso vuelve a fallar después de recargar, no es una versión nueva:
// se muestra el error en vez de recargar en bucle.
const VENTANA_MS = 10_000

const PATRONES = [
  "Failed to fetch dynamically imported module", // Chrome, Edge
  "error loading dynamically imported module", // Firefox
  "Importing a module script failed", // Safari
  "Unable to preload CSS",
]

export function esVersionVieja(error: unknown): boolean {
  const mensaje = error instanceof Error ? error.message : String(error ?? "")
  return PATRONES.some((p) => mensaje.includes(p))
}

/** Abre `destino` desde el servidor (con el index.html nuevo), una sola vez por versión
 * nueva. Devuelve `false` si ya se intentó hace poco. */
let enCurso = false

export function recargarPorVersionNueva(destino?: string): boolean {
  // Un segundo render mientras la página se va no tiene que contar como reintento.
  if (enCurso) return true
  let ultima = 0
  try {
    ultima = Number(sessionStorage.getItem(CLAVE)) || 0
  } catch {
    // Sin sessionStorage (modo privado estricto): igual se recarga una vez.
  }
  if (Date.now() - ultima < VENTANA_MS) return false
  try {
    sessionStorage.setItem(CLAVE, String(Date.now()))
  } catch {
    // Ídem.
  }
  enCurso = true
  if (
    destino &&
    destino !== location.pathname + location.search + location.hash
  )
    location.assign(destino)
  else location.reload()
  return true
}
