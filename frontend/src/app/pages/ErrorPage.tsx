import { ArrowClockwiseIcon, WarningCircleIcon } from "@phosphor-icons/react"
import {
  createPath,
  isRouteErrorResponse,
  Link,
  useLocation,
  useRouteError,
} from "react-router"

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

import { esVersionVieja, recargarPorVersionNueva } from "../version-nueva"
import { NoEncontradoPage } from "./NoEncontradoPage"

/** Errores de las rutas: una versión nueva publicada, una ruta que no existe o un fallo. */
export function ErrorPage() {
  const error = useRouteError()
  // La ruta a la que se estaba yendo: después de recargar, se abre esa.
  const destino = createPath(useLocation())

  if (isRouteErrorResponse(error) && error.status === 404)
    return <NoEncontradoPage />

  // La pestaña tenía la versión anterior: se recarga sola (una vez).
  if (esVersionVieja(error) && recargarPorVersionNueva(destino))
    return (
      <Empty>
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <Spinner />
          </EmptyMedia>
          <EmptyTitle>Hay una versión nueva</EmptyTitle>
          <EmptyDescription>Actualizando la página…</EmptyDescription>
        </EmptyHeader>
      </Empty>
    )

  return (
    <Empty>
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <WarningCircleIcon />
        </EmptyMedia>
        <EmptyTitle>No se pudo abrir esta pantalla</EmptyTitle>
        <EmptyDescription>
          {esVersionVieja(error)
            ? "No se pudo descargar la pantalla. Revisá la conexión y recargá."
            : "Ocurrió un error inesperado. Recargá la página y, si sigue pasando, avisá."}
        </EmptyDescription>
      </EmptyHeader>
      <EmptyContent className="flex-row justify-center">
        <Button onClick={() => window.location.reload()}>
          <ArrowClockwiseIcon />
          Recargar
        </Button>
        <Button asChild variant="outline">
          <Link to="/">Ir al resumen</Link>
        </Button>
      </EmptyContent>
    </Empty>
  )
}
