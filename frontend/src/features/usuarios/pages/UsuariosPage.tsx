import { ArrowClockwiseIcon, UserPlusIcon } from "@phosphor-icons/react"
import { useState } from "react"
import { toast } from "sonner"

import { useAuth } from "@/features/auth"
import { ApiError, mensajeDeError } from "@/shared/api"
import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/alert"
import { Button } from "@/shared/ui/button"
import { EncabezadoPagina } from "@/shared/ui/encabezado-pagina"
import { Skeleton } from "@/shared/ui/skeleton"

import type { Usuario } from "../api"
import { ConfirmarDesactivar } from "../components/ConfirmarDesactivar"
import { TablaUsuarios } from "../components/TablaUsuarios"
import { UsuarioSheet } from "../components/UsuarioSheet"
import { useActualizarUsuario, useUsuariosQuery } from "../queries"

export function UsuariosPage() {
  const { sesion } = useAuth()
  const usuarios = useUsuariosQuery()
  const actualizar = useActualizarUsuario()

  const [sheetAbierto, setSheetAbierto] = useState(false)
  const [editando, setEditando] = useState<Usuario | null>(null)
  const [aDesactivar, setADesactivar] = useState<Usuario | null>(null)

  function abrirAlta() {
    setEditando(null)
    setSheetAbierto(true)
  }

  function abrirEdicion(usuario: Usuario) {
    setEditando(usuario)
    setSheetAbierto(true)
  }

  function cambiarActivo(usuario: Usuario, activo: boolean) {
    actualizar.mutate(
      { id: usuario.id, cambios: { activo } },
      {
        onSuccess: () =>
          toast.success(
            activo
              ? `${usuario.nombre} puede volver a ingresar.`
              : `${usuario.nombre} ya no puede ingresar.`
          ),
        // Las reglas (no desactivarse a uno mismo, siempre un admin activo) las decide la API.
        onError: (error) =>
          toast.error(
            error instanceof ApiError && Object.values(error.campos)[0]
              ? Object.values(error.campos)[0]
              : mensajeDeError(error)
          ),
      }
    )
  }

  return (
    <>
      <EncabezadoPagina
        titulo="Usuarios"
        descripcion="Quién puede ingresar al sistema y con qué rol."
        acciones={
          <Button onClick={abrirAlta}>
            <UserPlusIcon />
            Nuevo usuario
          </Button>
        }
      />

      {usuarios.isPending ? (
        <div className="flex flex-col gap-2" aria-busy="true">
          <span className="sr-only">Cargando usuarios…</span>
          {Array.from({ length: 4 }, (_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : usuarios.isError ? (
        <Alert variant="destructive">
          <AlertTitle>No se pudieron cargar los usuarios</AlertTitle>
          <AlertDescription className="flex flex-col items-start gap-3">
            {mensajeDeError(usuarios.error)}
            <Button
              variant="outline"
              size="sm"
              onClick={() => usuarios.refetch()}
            >
              <ArrowClockwiseIcon />
              Reintentar
            </Button>
          </AlertDescription>
        </Alert>
      ) : (
        <TablaUsuarios
          usuarios={usuarios.data}
          idPropio={sesion?.id}
          onEditar={abrirEdicion}
          onCambiarActivo={(usuario) =>
            usuario.activo
              ? setADesactivar(usuario)
              : cambiarActivo(usuario, true)
          }
        />
      )}

      <UsuarioSheet
        abierto={sheetAbierto}
        onAbiertoChange={setSheetAbierto}
        usuario={editando}
      />
      <ConfirmarDesactivar
        usuario={aDesactivar}
        onCancelar={() => setADesactivar(null)}
        onConfirmar={(usuario) => {
          setADesactivar(null)
          cambiarActivo(usuario, false)
        }}
      />
    </>
  )
}
