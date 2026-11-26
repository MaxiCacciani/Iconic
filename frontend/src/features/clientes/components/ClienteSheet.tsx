import { FloppyDiskIcon } from "@phosphor-icons/react"
import { useEffect, type FormEvent } from "react"
import { Link } from "react-router"
import { toast } from "sonner"

import { useAuth } from "@/features/auth"
import { useCatalogoQuery } from "@/features/catalogos"
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
  Select,
  SelectContent,
  SelectItem,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select"
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

import type { Cliente, DatosCliente } from "../api"
import { useActualizarCliente, useCrearCliente } from "../queries"

type Props = {
  abierto: boolean
  onAbiertoChange: (abierto: boolean) => void
  /** Sin cliente es un alta; con cliente, una edición. */
  cliente: Cliente | null
  /** En un alta, el nombre con el que arranca (lo que se escribió en el buscador). */
  nombreInicial?: string
  /** En un alta, el DNI con el que arranca (si en el buscador se escribió un número). */
  dniInicial?: string
  /** Cambia en cada apertura, así el formulario arranca de cero. */
  apertura?: number
  onGuardado?: (cliente: Cliente) => void
}

const FORM_ID = "form-cliente"
const SIN_LOCALIDAD = "ninguna"

/** Un opcional en blanco se manda como `null`: "sin dato". */
function opcional(datos: FormData, campo: string): string | null {
  const valor = String(datos.get(campo) ?? "").trim()
  return valor || null
}

export function ClienteSheet({
  abierto,
  onAbiertoChange,
  cliente,
  nombreInicial,
  dniInicial,
  apertura = 0,
  onGuardado,
}: Props) {
  const { puede } = useAuth()
  const crear = useCrearCliente()
  const actualizar = useActualizarCliente()
  const mutacion = cliente ? actualizar : crear
  const { reset } = mutacion
  const localidades = useCatalogoQuery("localidades", undefined, {
    habilitado: abierto,
  })

  // Cada vez que se abre, arranca sin los errores del intento anterior.
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
    const localidad = String(form.get("localidad_id") ?? SIN_LOCALIDAD)
    const datos: DatosCliente = {
      nombre: String(form.get("nombre") ?? ""),
      dni: opcional(form, "dni"),
      telefono: opcional(form, "telefono"),
      localidad_id: localidad === SIN_LOCALIDAD ? null : Number(localidad),
    }
    const alTerminar = (guardado: Cliente) => {
      toast.success(
        cliente
          ? `Se guardaron los cambios de ${guardado.nombre}.`
          : `Se dio de alta a ${guardado.nombre} (cliente #${guardado.id}).`
      )
      onAbiertoChange(false)
      onGuardado?.(guardado)
    }
    if (cliente)
      actualizar.mutate({ id: cliente.id, datos }, { onSuccess: alTerminar })
    else crear.mutate(datos, { onSuccess: alTerminar })
  }

  const sinLocalidades = localidades.isSuccess && localidades.data.length === 0

  return (
    <Sheet open={abierto} onOpenChange={onAbiertoChange}>
      <SheetContent className="flex flex-col sm:max-w-md">
        <SheetHeader>
          <SheetTitle className="font-heading text-2xl">
            {cliente ? "Editar cliente" : "Nuevo cliente"}
          </SheetTitle>
          <SheetDescription>
            {cliente
              ? `Cliente #${cliente.id}.`
              : "Solo el nombre es obligatorio. El resto se puede completar después."}
          </SheetDescription>
        </SheetHeader>

        <form
          id={FORM_ID}
          key={`${cliente?.id ?? "nuevo"}-${apertura}`}
          onSubmit={enviar}
          noValidate
          className="flex-1 overflow-y-auto px-4"
        >
          <FieldGroup>
            <Field data-invalid={invalido("nombre")}>
              <FieldLabel htmlFor="cliente-nombre">
                Nombre y apellido
              </FieldLabel>
              <Input
                id="cliente-nombre"
                name="nombre"
                autoComplete="off"
                defaultValue={cliente?.nombre ?? nombreInicial}
                aria-invalid={invalido("nombre")}
              />
              {campos.nombre && <FieldError>{campos.nombre}</FieldError>}
            </Field>

            <Field data-invalid={invalido("dni")}>
              <FieldLabel htmlFor="cliente-dni">DNI</FieldLabel>
              <Input
                id="cliente-dni"
                name="dni"
                inputMode="numeric"
                autoComplete="off"
                spellCheck={false}
                placeholder="30.123.456"
                defaultValue={cliente ? (cliente.dni ?? "") : dniInicial}
                aria-invalid={invalido("dni")}
              />
              <FieldDescription>
                Opcional. Con o sin puntos; no puede repetirse.
              </FieldDescription>
              {campos.dni && <FieldError>{campos.dni}</FieldError>}
            </Field>

            <Field data-invalid={invalido("telefono")}>
              <FieldLabel htmlFor="cliente-telefono">Teléfono</FieldLabel>
              <Input
                id="cliente-telefono"
                name="telefono"
                type="tel"
                inputMode="tel"
                autoComplete="off"
                placeholder="341 555 1234"
                defaultValue={cliente?.telefono ?? ""}
                aria-invalid={invalido("telefono")}
              />
              <FieldDescription>
                Opcional. Con característica, de 8 a 15 dígitos.
              </FieldDescription>
              {campos.telefono && <FieldError>{campos.telefono}</FieldError>}
            </Field>

            <Field data-invalid={invalido("localidad_id")}>
              <FieldLabel htmlFor="cliente-localidad">Localidad</FieldLabel>
              <Select
                name="localidad_id"
                defaultValue={
                  cliente?.localidad
                    ? String(cliente.localidad.id)
                    : SIN_LOCALIDAD
                }
                disabled={localidades.isPending || sinLocalidades}
              >
                <SelectTrigger
                  id="cliente-localidad"
                  className="w-full"
                  aria-invalid={invalido("localidad_id")}
                >
                  <SelectValue
                    placeholder={
                      localidades.isPending ? "Cargando…" : "Sin localidad"
                    }
                  />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={SIN_LOCALIDAD}>Sin localidad</SelectItem>
                  <SelectSeparator />
                  {localidades.data?.map((l) => (
                    <SelectItem key={l.id} value={String(l.id)}>
                      {l.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {sinLocalidades && (
                <FieldDescription>
                  Todavía no hay localidades cargadas.{" "}
                  {puede("catalogos") ? (
                    <Link to="/catalogos?lista=localidades">
                      Cargalas en Catálogos.
                    </Link>
                  ) : (
                    "Las carga un Administrador en Catálogos."
                  )}
                </FieldDescription>
              )}
              {localidades.isError && (
                <FieldDescription>
                  No se pudieron cargar las localidades.
                </FieldDescription>
              )}
              {campos.localidad_id && (
                <FieldError>{campos.localidad_id}</FieldError>
              )}
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
              : cliente
                ? "Guardar cambios"
                : "Dar de alta"}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}
