import { ArrowClockwiseIcon, WarningCircleIcon } from "@phosphor-icons/react"
import { useQueryClient } from "@tanstack/react-query"

import { useAuth } from "@/features/auth"
import { Button } from "@/shared/ui/button"
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/shared/ui/empty"
import { Spinner } from "@/shared/ui/spinner"

export function CargandoSesion() {
  return (
    <div className="flex min-h-svh items-center justify-center" role="status">
      <Spinner className="size-6" />
      <span className="sr-only">Cargando sesión…</span>
    </div>
  )
}

/** `GET /auth/me` falló por algo que no es un 401 (servidor caído, sin red). */
export function ErrorSesion() {
  const queryClient = useQueryClient()
  const { cerrarSesion } = useAuth()

  return (
    <div className="flex min-h-svh items-center justify-center p-4">
      <Empty>
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <WarningCircleIcon />
          </EmptyMedia>
          <EmptyTitle>No se pudo cargar tu sesión</EmptyTitle>
          <EmptyDescription>
            El servidor no respondió. Revisá la conexión y probá de nuevo.
          </EmptyDescription>
        </EmptyHeader>
        <EmptyContent className="flex-row justify-center">
          <Button
            onClick={() => queryClient.refetchQueries({ queryKey: ["auth"] })}
          >
            <ArrowClockwiseIcon />
            Reintentar
          </Button>
          <Button variant="ghost" onClick={cerrarSesion}>
            Salir
          </Button>
        </EmptyContent>
      </Empty>
    </div>
  )
}
