import { FloppyDiskIcon } from "@phosphor-icons/react"
import { useEffect, useId, useRef, type FormEvent } from "react"
import { toast } from "sonner"

import { ApiError, mensajeDeError } from "@/shared/api"
import { formatearARS } from "@/shared/lib/formato"
import { Button } from "@/shared/ui/button"
import {
  Field,
  FieldDescription,
  FieldError,
  FieldLabel,
} from "@/shared/ui/field"
import { Input } from "@/shared/ui/input"
import { Spinner } from "@/shared/ui/spinner"

import type { TipoCambioHoy } from "../api"
import { useCargarTipoCambio } from "../queries"

type Props = {
  /** Al corregir un TC ya cargado, arranca con ese valor. */
  valorActual?: string | null
  onCargado?: (hoy: TipoCambioHoy) => void
  onCancelar?: () => void
}

/** Carga o corrige el TC de hoy. El backend valida el valor y entiende `1.180,50`. */
export function FormTipoCambio({ valorActual, onCargado, onCancelar }: Props) {
  const id = useId()
  const cargar = useCargarTipoCambio()
  const input = useRef<HTMLInputElement>(null)
  const corrigiendo = valorActual !== undefined

  // Al abrir "Corregir" el foco va al valor, que es lo único que se edita.
  useEffect(() => {
    if (corrigiendo) input.current?.select()
  }, [corrigiendo])

  const error =
    cargar.error instanceof ApiError
      ? (cargar.error.campos.valor_ars ?? cargar.error.message)
      : cargar.error
        ? mensajeDeError(cargar.error)
        : null

  function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const valor = String(
      new FormData(evento.currentTarget).get("valor_ars") ?? ""
    )
    cargar.mutate(
      { valor_ars: valor },
      {
        onSuccess: (hoy) => {
          if (hoy.valor_ars)
            toast.success(
              `TC de hoy: ${formatearARS(hoy.valor_ars)} por dólar.`
            )
          onCargado?.(hoy)
        },
      }
    )
  }

  return (
    <form onSubmit={enviar} noValidate className="flex flex-col gap-3">
      <Field data-invalid={error ? true : undefined}>
        <FieldLabel htmlFor={id}>Pesos por dólar</FieldLabel>
        <div className="flex flex-wrap gap-2">
          <Input
            ref={input}
            id={id}
            name="valor_ars"
            inputMode="decimal"
            autoComplete="off"
            placeholder="Ej.: 1.180,50"
            defaultValue={valorActual ? valorActual.replace(".", ",") : ""}
            aria-invalid={error ? true : undefined}
            className="w-40 tabular-nums"
          />
          <Button type="submit" disabled={cargar.isPending}>
            {cargar.isPending ? <Spinner /> : <FloppyDiskIcon />}
            {cargar.isPending ? "Guardando…" : "Guardar TC"}
          </Button>
          {onCancelar && (
            <Button type="button" variant="ghost" onClick={onCancelar}>
              Cancelar
            </Button>
          )}
        </div>
        {error ? (
          <FieldError>{error}</FieldError>
        ) : (
          <FieldDescription>
            Vale para todas las computadoras hasta que termine el día.
          </FieldDescription>
        )}
      </Field>
    </form>
  )
}
