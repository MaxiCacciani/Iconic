import { FloppyDiskIcon } from "@phosphor-icons/react"
import { useState, type FormEvent } from "react"
import { toast } from "sonner"

import { ApiError, mensajeDeError } from "@/shared/api"
import { Alert, AlertDescription } from "@/shared/ui/alert"
import { Button } from "@/shared/ui/button"
import { Checkbox } from "@/shared/ui/checkbox"
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSet,
} from "@/shared/ui/field"
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/shared/ui/sheet"
import { Skeleton } from "@/shared/ui/skeleton"
import { Spinner } from "@/shared/ui/spinner"

import type { Asignaciones, Modelo } from "../api"
import { useAsignarAModelo, useCatalogoQuery } from "../queries"

type Props = {
  abierto: boolean
  onAbiertoChange: (abierto: boolean) => void
  /** Se mantiene al cerrar, así el contenido no desaparece durante la animación. */
  modelo: Modelo | null
  categoria?: string
  /** Cambia en cada apertura: el formulario arranca de nuevo con lo guardado. */
  apertura: number
}

const FORM_ID = "form-asignaciones"
type Asignable = "colores" | "capacidades"
/** El campo de cada lista en `ModeloRead` y en lo que se manda. */
const CAMPO = { colores: "color_ids", capacidades: "capacidad_ids" } as const

/** Qué colores y capacidades de su categoría tiene un modelo. */
export function AsignacionesSheet({
  abierto,
  onAbiertoChange,
  modelo,
  categoria,
  apertura,
}: Props) {
  return (
    <Sheet open={abierto} onOpenChange={onAbiertoChange}>
      <SheetContent className="flex flex-col sm:max-w-md">
        {modelo && (
          <Contenido
            key={`${modelo.id}-${apertura}`}
            modelo={modelo}
            categoria={categoria}
            onCerrar={() => onAbiertoChange(false)}
          />
        )}
      </SheetContent>
    </Sheet>
  )
}

function Contenido({
  modelo,
  categoria,
  onCerrar,
}: {
  modelo: Modelo
  categoria?: string
  onCerrar: () => void
}) {
  const asignar = useAsignarAModelo()
  const guardados: Record<Asignable, number[]> = {
    colores: modelo.color_ids,
    capacidades: modelo.capacidad_ids,
  }
  const [elegidos, setElegidos] = useState(() => ({
    colores: new Set(modelo.color_ids),
    capacidades: new Set(modelo.capacidad_ids),
  }))
  const colores = useCatalogoQuery("colores", modelo.categoria_id)
  const capacidades = useCatalogoQuery("capacidades", modelo.categoria_id)

  function alternar(que: Asignable, id: number, marcado: boolean) {
    setElegidos((actual) => {
      const ids = new Set(actual[que])
      if (marcado) ids.add(id)
      else ids.delete(id)
      return { ...actual, [que]: ids }
    })
  }

  function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const cambios: Asignaciones = {}
    for (const que of ["colores", "capacidades"] as const) {
      const ids = [...elegidos[que]].toSorted((a, b) => a - b)
      if (ids.join() !== guardados[que].join()) cambios[CAMPO[que]] = ids
    }
    if (Object.keys(cambios).length === 0) {
      onCerrar()
      return
    }
    asignar.mutate(
      { modeloId: modelo.id, cambios },
      {
        onSuccess: () => {
          toast.success(
            `Se guardaron los colores y capacidades de «${modelo.nombre}».`
          )
          onCerrar()
        },
      }
    )
  }

  // Un 422 viene por lista (`color_ids`, `capacidad_ids`) y se muestra en su grupo.
  const campos = asignar.error instanceof ApiError ? asignar.error.campos : {}
  const error =
    asignar.error && Object.keys(campos).length === 0
      ? mensajeDeError(asignar.error)
      : null
  const deLaCategoria = categoria ?? "Esta categoría"

  return (
    <>
      <SheetHeader>
        <SheetTitle className="font-heading text-2xl">
          Colores y capacidades
        </SheetTitle>
        <SheetDescription>
          {categoria ? `${categoria} ` : ""}
          {modelo.nombre}. Marcá los que vinieron en este modelo: son los que se
          ofrecen al cargarlo. Si no marcás ninguno, se ofrecen todos los de la
          categoría.
        </SheetDescription>
      </SheetHeader>

      <form
        id={FORM_ID}
        onSubmit={enviar}
        noValidate
        className="flex-1 overflow-y-auto px-4"
      >
        <FieldGroup>
          <Grupo
            titulo="Colores"
            vacio={`${deLaCategoria} todavía no tiene colores. Agregalos en el catálogo Colores.`}
            consulta={colores}
            elegidos={elegidos.colores}
            error={campos[CAMPO.colores]}
            onAlternar={(id, marcado) => alternar("colores", id, marcado)}
          />
          <Grupo
            titulo="Capacidades"
            femenino
            vacio={`${deLaCategoria} todavía no tiene capacidades. Agregalas en el catálogo Capacidades.`}
            consulta={capacidades}
            elegidos={elegidos.capacidades}
            error={campos[CAMPO.capacidades]}
            onAlternar={(id, marcado) => alternar("capacidades", id, marcado)}
          />

          {error && (
            <Alert variant="destructive" aria-live="polite">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </FieldGroup>
      </form>

      <SheetFooter className="flex-row justify-end">
        <SheetClose asChild>
          <Button variant="outline">Cancelar</Button>
        </SheetClose>
        <Button type="submit" form={FORM_ID} disabled={asignar.isPending}>
          {asignar.isPending ? <Spinner /> : <FloppyDiskIcon />}
          {asignar.isPending ? "Guardando…" : "Guardar"}
        </Button>
      </SheetFooter>
    </>
  )
}

type GrupoProps = {
  titulo: string
  /** Para los textos: "ninguna marcada" en capacidades. */
  femenino?: boolean
  vacio: string
  consulta: ReturnType<typeof useCatalogoQuery<"colores">>
  elegidos: Set<number>
  error?: string
  onAlternar: (id: number, marcado: boolean) => void
}

function Grupo({
  titulo,
  femenino,
  vacio,
  consulta,
  elegidos,
  error,
  onAlternar,
}: GrupoProps) {
  const items = consulta.data
  const id = `asignar-${titulo.toLowerCase()}`

  return (
    <FieldSet data-invalid={error ? true : undefined}>
      <FieldLegend variant="label">{titulo}</FieldLegend>
      {error && <FieldError>{error}</FieldError>}
      {consulta.isError ? (
        <FieldDescription>
          No se pudo cargar la lista: {mensajeDeError(consulta.error)}
        </FieldDescription>
      ) : !items ? (
        <div className="flex flex-col gap-2" aria-busy="true">
          <span className="sr-only">Cargando {titulo.toLowerCase()}…</span>
          {Array.from({ length: 3 }, (_, i) => (
            <Skeleton key={i} className="h-5 w-40" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <FieldDescription>{vacio}</FieldDescription>
      ) : (
        <>
          <FieldDescription>
            {elegidos.size === 0
              ? femenino
                ? "Ninguna marcada: se ofrecen todas."
                : "Ninguno marcado: se ofrecen todos."
              : `${elegidos.size} de ${items.length} ${femenino ? "marcadas" : "marcados"}.`}
          </FieldDescription>
          <FieldGroup data-slot="checkbox-group" className="gap-3">
            {items.map((item) => (
              <Field key={item.id} orientation="horizontal">
                <Checkbox
                  id={`${id}-${item.id}`}
                  checked={elegidos.has(item.id)}
                  onCheckedChange={(marcado) =>
                    onAlternar(item.id, marcado === true)
                  }
                />
                <FieldLabel
                  htmlFor={`${id}-${item.id}`}
                  className="font-normal"
                >
                  {item.nombre}
                </FieldLabel>
              </Field>
            ))}
          </FieldGroup>
        </>
      )}
    </FieldSet>
  )
}
