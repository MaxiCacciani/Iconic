import { CheckIcon, WarningIcon } from "@phosphor-icons/react"

import { Badge } from "@/shared/ui/badge"

type Props = { estado: "pendiente" | "vencida" | "cobrada" }

/** El estado de una cuota tal como lo manda la API (la vencida la calcula ella). */
export function EstadoCuota({ estado }: Props) {
  if (estado === "cobrada")
    return (
      <Badge variant="secondary">
        <CheckIcon aria-hidden />
        Cobrada
      </Badge>
    )
  if (estado === "vencida")
    return (
      <Badge variant="destructive">
        <WarningIcon weight="fill" aria-hidden />
        Vencida
      </Badge>
    )
  return <Badge variant="outline">Pendiente</Badge>
}
