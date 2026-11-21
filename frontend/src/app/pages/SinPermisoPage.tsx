import { LockIcon } from "@phosphor-icons/react"
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

export function SinPermisoPage() {
  return (
    <Empty>
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <LockIcon />
        </EmptyMedia>
        <EmptyTitle>No tenés acceso a esta sección</EmptyTitle>
        <EmptyDescription>
          Si la necesitás, pedíselo al Administrador.
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
