import { CurrencyDollarIcon, WarningIcon } from "@phosphor-icons/react"
import { Link } from "react-router"

import { formatearARS } from "@/shared/lib/formato"
import { Badge } from "@/shared/ui/badge"

import { useTipoCambioHoy } from "../queries"

/** TC de hoy en el encabezado, visible desde cualquier pantalla. Si falta, lleva a Resumen. */
export function IndicadorTipoCambio() {
  const tc = useTipoCambioHoy()
  // Cargando o con error no se muestra nada: mejor nada que un valor dudoso.
  if (!tc.data) return null

  if (!tc.data.valor_ars)
    return (
      <Badge
        asChild
        variant="outline"
        className="h-7 border-warning/50 bg-warning/10 px-2.5 text-warning-foreground"
      >
        <Link to="/">
          <WarningIcon weight="fill" aria-hidden />
          Falta el TC de hoy
        </Link>
      </Badge>
    )

  return (
    <Badge variant="outline" className="h-7 px-2.5 tabular-nums">
      <CurrencyDollarIcon aria-hidden />
      <span className="text-muted-foreground">TC</span>
      {formatearARS(tc.data.valor_ars)}
    </Badge>
  )
}
