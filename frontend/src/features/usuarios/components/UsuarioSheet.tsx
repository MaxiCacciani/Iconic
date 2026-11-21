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
  Select,
  SelectContent,
  SelectItem,
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

import type { Rol, Usuario } from "../api"
import { useActualizarUsuario, useCrearUsuario } from "../queries"
import { NOMBRE_ROL } from "../roles"

type Props = {
  abierto: boolean
  onAbiertoChange: (abierto: boolean) => void
  /** Sin usuario es un alta; con usuario, una edición. */
  usuario: Usuario | null
}

const FORM_ID = "form-usuario"

export function UsuarioSheet({ abierto, onAbiertoChange, usuario }: Props) {
  const crear = useCrearUsuario()
  const actualizar = useActualizarUsuario()
  const mutacion = usuario ? actualizar : crear
  const { reset } = mutacion

  // Cada vez que se abre, arranca sin los errores del intento anterior.
  useEffect(() => {
    if (abierto) reset()
  }, [abierto, reset])

  const campos = mutacion.error instanceof ApiError ? mutacion.error.campos : {}
  const errorGeneral =
    mutacion.error && Object.keys(campos).length === 0
      ? mensajeDeError(mutacion.error)
      : null

  const alTerminar = (mensaje: string) => () => {
    toast.success(mensaje)
    onAbiertoChange(false)
  }

  function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const datos = new FormData(evento.currentTarget)
    const nombre = String(datos.get("nombre") ?? "")
    const email = String(datos.get("email") ?? "")
    const rol = String(datos.get("rol") ?? "") as Rol
    const password = String(datos.get("password") ?? "")

    if (usuario) {
      actualizar.mutate(
        {
          id: usuario.id,
          // La contraseña vacía significa "no cambiarla".
          cambios: { nombre, email, rol, ...(password ? { password } : {}) },
        },
        { onSuccess: alTerminar(`Se guardaron los cambios de ${nombre}.`) }
      )
    } else {
      crear.mutate(
        { nombre, email, rol, password },
        { onSuccess: alTerminar(`${nombre} ya puede ingresar.`) }
      )
    }
  }

  const invalido = (campo: string) => (campos[campo] ? true : undefined)

  return (
    <Sheet open={abierto} onOpenChange={onAbiertoChange}>
      <SheetContent className="flex flex-col sm:max-w-md">
        <SheetHeader>
          <SheetTitle className="font-heading text-2xl">
            {usuario ? "Editar usuario" : "Nuevo usuario"}
          </SheetTitle>
          <SheetDescription>
            {usuario
              ? `Usuario #${usuario.id}. Los cambios de rol valen desde su próximo ingreso.`
              : "Va a ingresar con este email y contraseña."}
          </SheetDescription>
        </SheetHeader>

        <form
          id={FORM_ID}
          key={usuario?.id ?? "nuevo"}
          onSubmit={enviar}
          noValidate
          className="flex-1 overflow-y-auto px-4"
        >
          <FieldGroup>
            <Field data-invalid={invalido("nombre")}>
              <FieldLabel htmlFor="usuario-nombre">Nombre</FieldLabel>
              <Input
                id="usuario-nombre"
                name="nombre"
                autoComplete="off"
                defaultValue={usuario?.nombre}
                aria-invalid={invalido("nombre")}
              />
              {campos.nombre && <FieldError>{campos.nombre}</FieldError>}
            </Field>

            <Field data-invalid={invalido("email")}>
              <FieldLabel htmlFor="usuario-email">Email</FieldLabel>
              <Input
                id="usuario-email"
                name="email"
                type="email"
                autoComplete="off"
                spellCheck={false}
                defaultValue={usuario?.email}
                aria-invalid={invalido("email")}
              />
              {campos.email && <FieldError>{campos.email}</FieldError>}
            </Field>

            <Field data-invalid={invalido("rol")}>
              <FieldLabel htmlFor="usuario-rol">Rol</FieldLabel>
              <Select name="rol" defaultValue={usuario?.rol ?? "vendedor"}>
                <SelectTrigger
                  id="usuario-rol"
                  className="w-full"
                  aria-invalid={invalido("rol")}
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="vendedor">{NOMBRE_ROL.vendedor}</SelectItem>
                  <SelectItem value="admin">{NOMBRE_ROL.admin}</SelectItem>
                </SelectContent>
              </Select>
              <FieldDescription>
                El Vendedor no ve costos, ganancias ni las pantallas de
                administración.
              </FieldDescription>
              {campos.rol && <FieldError>{campos.rol}</FieldError>}
            </Field>

            <Field data-invalid={invalido("password")}>
              <FieldLabel htmlFor="usuario-password">
                {usuario ? "Nueva contraseña" : "Contraseña"}
              </FieldLabel>
              <Input
                id="usuario-password"
                name="password"
                type="password"
                autoComplete="new-password"
                aria-invalid={invalido("password")}
              />
              <FieldDescription>
                {usuario
                  ? "Dejala vacía para no cambiarla. Si la blanqueás, pasásela a la persona."
                  : "Al menos 8 caracteres."}
              </FieldDescription>
              {campos.password && <FieldError>{campos.password}</FieldError>}
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
              : usuario
                ? "Guardar cambios"
                : "Crear usuario"}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}
