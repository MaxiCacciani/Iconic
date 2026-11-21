import { HammerIcon } from "@phosphor-icons/react"

import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/shared/ui/empty"

/** Marcador del esqueleto: la pantalla existe en el router pero su endpoint todavía no. */
export function ModuloPendiente({ endpoint }: { endpoint: string }) {
  return (
    <Empty className="border border-dashed">
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <HammerIcon />
        </EmptyMedia>
        <EmptyTitle>Pantalla en construcción</EmptyTitle>
        <EmptyDescription>
          Se arma cuando el backend tenga{" "}
          <code className="font-mono">{endpoint}</code>.
        </EmptyDescription>
      </EmptyHeader>
    </Empty>
  )
}
