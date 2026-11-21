import type { ReactNode } from "react"

type Props = {
  titulo: string
  descripcion?: string
  /** Botones o acciones de la pantalla, alineados a la derecha. */
  acciones?: ReactNode
}

export function EncabezadoPagina({ titulo, descripcion, acciones }: Props) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-4">
      <div className="flex flex-col gap-1">
        <h1 className="font-heading text-3xl text-balance">{titulo}</h1>
        {descripcion && (
          <p className="text-sm text-muted-foreground">{descripcion}</p>
        )}
      </div>
      {acciones && <div className="flex items-center gap-2">{acciones}</div>}
    </header>
  )
}
