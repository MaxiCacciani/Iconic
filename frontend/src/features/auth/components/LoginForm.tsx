import { SignInIcon } from "@phosphor-icons/react"
import type { FormEvent } from "react"

import { ApiError, mensajeDeError } from "@/shared/api"
import { Alert, AlertDescription } from "@/shared/ui/alert"
import { Button } from "@/shared/ui/button"
import { Field, FieldError, FieldGroup, FieldLabel } from "@/shared/ui/field"
import { Input } from "@/shared/ui/input"
import { Spinner } from "@/shared/ui/spinner"

import { useAuth } from "../AuthProvider"
import { useLoginMutation } from "../queries"

export function LoginForm() {
  const { iniciarSesion } = useAuth()
  const login = useLoginMutation()

  const campos = login.error instanceof ApiError ? login.error.campos : {}
  // Los errores por campo (422) van junto a cada input; el resto, arriba del botón.
  const errorGeneral =
    login.error && Object.keys(campos).length === 0
      ? mensajeDeError(login.error)
      : null

  function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const datos = new FormData(evento.currentTarget)
    login.mutate(
      {
        email: String(datos.get("email") ?? ""),
        password: String(datos.get("password") ?? ""),
      },
      { onSuccess: (token) => iniciarSesion(token.access_token) }
    )
  }

  return (
    <form onSubmit={enviar} noValidate>
      <FieldGroup>
        <Field data-invalid={campos.email ? true : undefined}>
          <FieldLabel htmlFor="email">Email</FieldLabel>
          <Input
            id="email"
            name="email"
            type="email"
            autoComplete="username"
            spellCheck={false}
            required
            aria-invalid={campos.email ? true : undefined}
          />
          {campos.email && <FieldError>{campos.email}</FieldError>}
        </Field>
        <Field data-invalid={campos.password ? true : undefined}>
          <FieldLabel htmlFor="password">Contraseña</FieldLabel>
          <Input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            aria-invalid={campos.password ? true : undefined}
          />
          {campos.password && <FieldError>{campos.password}</FieldError>}
        </Field>
        {errorGeneral && (
          <Alert variant="destructive" aria-live="polite">
            <AlertDescription>{errorGeneral}</AlertDescription>
          </Alert>
        )}
        <Button type="submit" disabled={login.isPending}>
          {login.isPending ? <Spinner /> : <SignInIcon />}
          {login.isPending ? "Ingresando…" : "Ingresar"}
        </Button>
      </FieldGroup>
    </form>
  )
}
