import { FloppyDiskIcon } from "@phosphor-icons/react"
import { useEffect, type FormEvent } from "react"
import { toast } from "sonner"

import { ApiError, mensajeDeError } from "@/shared/api"
import { Alert, AlertDescription } from "@/shared/ui/alert"
import { Button } from "@/shared/ui/button"
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/shared/ui/field"
import { Input } from "@/shared/ui/input"
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/shared/ui/sheet"
import { Spinner } from "@/shared/ui/spinner"

import type { DatosVendedor, Vendedor } from "../api"
import { useActualizarVendedor, useCrearVendedor } from "../queries"

type Props = {
  abierto: boolean
  onAbiertoChange: (abierto: boolean) => void
  /** Sin vendedor es un alta; con vendedor, una edición. */
  vendedor: Vendedor | null
  /** Cambia en cada apertura, así el formulario arranca de cero. */
  apertura: number
}

const FORM_ID = "form-vendedor"

export function VendedorSheet({
  abierto,
  onAbiertoChange,
  vendedor,
  apertura,
}: Props) {
  const crear = useCrearVendedor()
  const actualizar = useActualizarVendedor()
  const mutacion = vendedor ? actualizar : crear
  const { reset } = mutacion

  useEffect(() => {
    if (abierto) reset()
  }, [abierto, reset])

  const campos = mutacion.error instanceof ApiError ? mutacion.error.campos : {}
  const errorGeneral =
    mutacion.error && Object.keys(campos).length === 0
      ? mensajeDeError(mutacion.error)
      : null
  const invalido = (campo: string) => (campos[campo] ? true : undefined)

  function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const form = new FormData(evento.currentTarget)
    const numero = String(form.get("numero") ?? "").trim()
    const datos: DatosVendedor = { nombre: String(form.get("nombre") ?? "") }
    // En blanco: en un alta no se manda (la API dice que es obligatorio); en una edición
    // va `null`, así no queda el número de antes sin avisar.
    if (numero) datos.numero = numero
    else if (vendedor) datos.numero = null

    const alTerminar = (guardado: Vendedor) => {
      toast.success(
        vendedor
          ? `Se guardaron los cambios de ${guardado.nombre}.`
          : `${guardado.nombre} quedó como vendedor n.º ${guardado.numero}.`
      )
      onAbiertoChange(false)
    }
    if (vendedor)
      actualizar.mutate({ id: vendedor.id, datos }, { onSuccess: alTerminar })
    else crear.mutate(datos, { onSuccess: alTerminar })
  }

  return (
    <Sheet open={abierto} onOpenChange={onAbiertoChange}>
      <SheetContent className="flex flex-col sm:max-w-md">
        <SheetHeader>
          <SheetTitle className="font-heading text-2xl">
            {vendedor ? "Editar vendedor" : "Nuevo vendedor"}
          </SheetTitle>
          <SheetDescription>
            En cada venta se carga el número y el nombre sale de esta lista.
          </SheetDescription>
        </SheetHeader>

        <form
          id={FORM_ID}
          key={`${vendedor?.id ?? "nuevo"}-${apertura}`}
          onSubmit={enviar}
          noValidate
          className="flex-1 overflow-y-auto px-4"
        >
          <FieldGroup>
            <Field data-invalid={invalido("numero")}>
              <FieldLabel htmlFor="vendedor-numero">Número</FieldLabel>
              <Input
                id="vendedor-numero"
                name="numero"
                inputMode="numeric"
                autoComplete="off"
                className="max-w-32 tabular-nums"
                defaultValue={vendedor?.numero ?? ""}
                aria-invalid={invalido("numero")}
              />
              <FieldDescription>No puede repetirse.</FieldDescription>
              {campos.numero && <FieldError>{campos.numero}</FieldError>}
            </Field>

            <Field data-invalid={invalido("nombre")}>
              <FieldLabel htmlFor="vendedor-nombre">
                Nombre y apellido
              </FieldLabel>
              <Input
                id="vendedor-nombre"
                name="nombre"
                autoComplete="off"
                defaultValue={vendedor?.nombre ?? ""}
                aria-invalid={invalido("nombre")}
              />
              {campos.nombre && <FieldError>{campos.nombre}</FieldError>}
            </Field>

            {errorGeneral && (
              <Alert variant="destructive" aria-live="polite">
                <AlertDescription>{errorGeneral}</AlertDescription>
              </Alert>
            )}
          </FieldGroup>
        </form>

        <SheetFooter className="flex-row justify-end">
          <SheetClose asChild>
            <Button variant="outline">Cancelar</Button>
          </SheetClose>
          <Button type="submit" form={FORM_ID} disabled={mutacion.isPending}>
            {mutacion.isPending ? <Spinner /> : <FloppyDiskIcon />}
            {mutacion.isPending
              ? "Guardando…"
              : vendedor
                ? "Guardar cambios"
                : "Dar de alta"}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}
