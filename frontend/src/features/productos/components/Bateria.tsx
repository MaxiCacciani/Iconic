import {
  BatteryFullIcon,
  BatteryLowIcon,
  BatteryMediumIcon,
} from "@phosphor-icons/react"

import { cn } from "@/shared/lib/utils"

import type { NivelBateria } from "../api"

// El nivel lo decide la API (`bateria_nivel`); acá solo se pinta. Sin alertas.
const NIVEL = {
  alta: { icono: BatteryFullIcon, clase: "text-success", texto: "alta" },
  media: { icono: BatteryMediumIcon, clase: "text-info", texto: "media" },
  baja: { icono: BatteryLowIcon, clase: "text-destructive", texto: "baja" },
} as const

export function Bateria({
  bateria,
  nivel,
}: {
  bateria: number | null
  nivel: NivelBateria | null
}) {
  if (bateria === null || nivel === null)
    return <span className="text-muted-foreground">—</span>
  const { icono: Icono, clase, texto } = NIVEL[nivel]
  return (
    <span
      className={cn("inline-flex items-center gap-1 tabular-nums", clase)}
      title={`Batería ${texto}`}
    >
      <Icono weight="fill" aria-hidden className="size-4" />
      {bateria}%<span className="sr-only">, batería {texto}</span>
    </span>
  )
}
