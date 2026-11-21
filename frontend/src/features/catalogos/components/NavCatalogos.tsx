import { Button } from "@/shared/ui/button"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select"

import type { Slug } from "../api"
import { CATALOGOS, type DefinicionCatalogo } from "../catalogos"

type Props = {
  actual: Slug
  onElegir: (slug: Slug) => void
}

// Los grupos en el orden en que aparecen en CATALOGOS.
const GRUPOS = [...new Set(CATALOGOS.map((c) => c.grupo))].map(
  (grupo) =>
    [grupo, CATALOGOS.filter((c) => c.grupo === grupo)] as [
      string,
      DefinicionCatalogo[],
    ]
)

/** Lista de catálogos: a la izquierda en pantallas anchas, un desplegable en el celular. */
export function NavCatalogos({ actual, onElegir }: Props) {
  return (
    <>
      <div className="md:hidden">
        <Select value={actual} onValueChange={(v) => onElegir(v as Slug)}>
          <SelectTrigger className="w-full" aria-label="Catálogo">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {GRUPOS.map(([grupo, catalogos]) => (
              <SelectGroup key={grupo}>
                <SelectLabel>{grupo}</SelectLabel>
                {catalogos.map((c) => (
                  <SelectItem key={c.slug} value={c.slug}>
                    {c.titulo}
                  </SelectItem>
                ))}
              </SelectGroup>
            ))}
          </SelectContent>
        </Select>
      </div>

      <nav aria-label="Catálogos" className="hidden flex-col gap-5 md:flex">
        {GRUPOS.map(([grupo, catalogos]) => (
          <div key={grupo} className="flex flex-col gap-1">
            <h2 className="px-2.5 text-xs font-medium text-muted-foreground">
              {grupo}
            </h2>
            {catalogos.map((c) => {
              const activo = c.slug === actual
              return (
                <Button
                  key={c.slug}
                  variant={activo ? "secondary" : "ghost"}
                  className="justify-start"
                  aria-current={activo ? "page" : undefined}
                  onClick={() => onElegir(c.slug)}
                >
                  {c.titulo}
                </Button>
              )
            })}
          </div>
        ))}
      </nav>
    </>
  )
}
