import { CompassIcon } from "@phosphor-icons/react"
import { Link } from "react-router"

import { Button } from "@/shared/ui/button"
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/shared/ui/empty"

export function NoEncontradoPage() {
  return (
    <Empty>
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <CompassIcon />
        </EmptyMedia>
        <EmptyTitle>Esta página no existe</EmptyTitle>
        <EmptyDescription>
          Revisá la dirección o volvé al inicio.
        </EmptyDescription>
      </EmptyHeader>
      <EmptyContent>
        <Button asChild variant="outline">
          <Link to="/">Ir al resumen</Link>
        </Button>
      </EmptyContent>
    </Empty>
  )
}
