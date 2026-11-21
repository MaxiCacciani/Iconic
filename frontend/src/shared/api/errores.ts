// Traduce las respuestas de error de FastAPI a algo que la UI pueda mostrar.
// El front no valida: los mensajes y los campos inválidos vienen del backend.

type ErrorValidacion = { loc: (string | number)[]; msg: string }

export class ApiError extends Error {
  readonly status: number
  /** Mensaje por campo cuando la API responde 422 (clave: nombre del campo). */
  readonly campos: Record<string, string>

  constructor(
    status: number,
    mensaje: string,
    campos: Record<string, string> = {}
  ) {
    super(mensaje)
    this.name = "ApiError"
    this.status = status
    this.campos = campos
  }
}

export function errorDesdeRespuesta(status: number, cuerpo: unknown): ApiError {
  const detalle = (cuerpo as { detail?: unknown } | null)?.detail

  if (typeof detalle === "string") return new ApiError(status, detalle)

  if (Array.isArray(detalle)) {
    const campos: Record<string, string> = {}
    for (const error of detalle as ErrorValidacion[]) {
      // loc viene como ["body", "campo", ...]; nos quedamos con la ruta del campo.
      const campo = error.loc.filter((parte) => parte !== "body").join(".")
      if (campo && !(campo in campos)) campos[campo] = error.msg
    }
    return new ApiError(status, "Revisá los datos marcados.", campos)
  }

  return new ApiError(status, mensajePorStatus(status))
}

function mensajePorStatus(status: number): string {
  if (status === 0) return "No se pudo conectar con el servidor."
  if (status === 401) return "Tu sesión venció. Volvé a ingresar."
  if (status === 403) return "No tenés permiso para hacer esto."
  if (status === 404) return "No se encontró lo que buscabas."
  if (status >= 500)
    return "El servidor tuvo un problema. Probá de nuevo en un rato."
  return "Algo salió mal."
}

export function mensajeDeError(error: unknown): string {
  return error instanceof Error ? error.message : "Algo salió mal."
}
