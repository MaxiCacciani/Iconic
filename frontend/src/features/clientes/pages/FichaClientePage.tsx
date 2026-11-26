import {
  ArrowClockwiseIcon,
  ArrowLeftIcon,
  PencilSimpleIcon,
  TrashIcon,
} from "@phosphor-icons/react"
import { useState } from "react"
import { Link, useNavigate, useParams } from "react-router"
import { toast } from "sonner"

import { useAuth } from "@/features/auth"
import { ApiError, mensajeDeError } from "@/shared/api"
import { formatearDiaDe, formatearDNI } from "@/shared/lib/formato"
import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/alert"
import { Button } from "@/shared/ui/button"
import { Card, CardContent } from "@/shared/ui/card"
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/shared/ui/empty"
import { EncabezadoPagina } from "@/shared/ui/encabezado-pagina"
import { Skeleton } from "@/shared/ui/skeleton"

import type { Cliente } from "../api"
import { ClienteSheet } from "../components/ClienteSheet"
import { ConfirmarBorrarCliente } from "../components/ConfirmarBorrarCliente"
import { useClienteQuery, useEliminarCliente } from "../queries"

function Volver() {
  return (
    <Button variant="ghost" size="sm" asChild className="-ml-2 self-start">
      <Link to="/clientes">
        <ArrowLeftIcon />
        Clientes
      </Link>
    </Button>
  )
}

function Dato({ titulo, valor }: { titulo: string; valor: string | null }) {
  return (
    <div className="flex flex-col gap-1">
      <dt className="text-sm text-muted-foreground">{titulo}</dt>
      <dd className="tabular-nums">
        {valor ?? <span className="text-muted-foreground">Sin cargar</span>}
      </dd>
    </div>
  )
}

/** La ficha arranca con los datos básicos. Compras, cuotas, reservas y reclamos se suman
 * en las fases siguientes. */
export function FichaClientePage() {
  const id = Number(useParams().id)
  const { puede } = useAuth()
  const navigate = useNavigate()
  const ficha = useClienteQuery(id)
  const eliminar = useEliminarCliente()
  const [edicion, setEdicion] = useState({ abierta: false, apertura: 0 })
  const [aBorrar, setABorrar] = useState<Cliente | null>(null)

  function borrar(cliente: Cliente) {
    setABorrar(null)
    eliminar.mutate(cliente.id, {
      onSuccess: () => {
        toast.success(`Se borró a ${cliente.nombre}.`)
        navigate("/clientes", { replace: true })
      },
      onError: (error) => toast.error(mensajeDeError(error)),
    })
  }

  const noExiste =
    !Number.isInteger(id) ||
    id <= 0 ||
    (ficha.error instanceof ApiError && ficha.error.status === 404)

  if (noExiste)
    return (
      <div className="flex flex-col gap-4">
        <Volver />
        <Empty className="border">
          <EmptyHeader>
            <EmptyTitle>Ese cliente no existe</EmptyTitle>
            <EmptyDescription>
              Puede que lo hayan borrado. Buscalo en la lista.
            </EmptyDescription>
          </EmptyHeader>
          <EmptyContent>
            <Button asChild>
              <Link to="/clientes">Ir a Clientes</Link>
            </Button>
          </EmptyContent>
        </Empty>
      </div>
    )

  if (ficha.isError)
    return (
      <div className="flex flex-col gap-4">
        <Volver />
        <Alert variant="destructive">
          <AlertTitle>No se pudo cargar el cliente</AlertTitle>
          <AlertDescription className="flex flex-col items-start gap-3">
            {mensajeDeError(ficha.error)}
            <Button variant="outline" size="sm" onClick={() => ficha.refetch()}>
              <ArrowClockwiseIcon />
              Reintentar
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    )

  if (ficha.isPending)
    return (
      <div className="flex flex-col gap-4" aria-busy="true">
        <span className="sr-only">Cargando el cliente…</span>
        <Volver />
        <Skeleton className="h-9 w-64" />
        <Skeleton className="h-32 w-full max-w-2xl" />
      </div>
    )

  const cliente = ficha.data

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <Volver />
        <EncabezadoPagina
          titulo={cliente.nombre}
          descripcion={`Cliente #${cliente.id} · desde el ${formatearDiaDe(cliente.creado_en)}`}
          acciones={
            <>
              <Button
                variant="outline"
                onClick={() =>
                  setEdicion((e) => ({
                    abierta: true,
                    apertura: e.apertura + 1,
                  }))
                }
              >
                <PencilSimpleIcon />
                Editar
              </Button>
              {puede("clientes:borrar") && (
                <Button
                  variant="outline"
                  onClick={() => setABorrar(cliente)}
                  disabled={eliminar.isPending}
                >
                  <TrashIcon />
                  Borrar…
                </Button>
              )}
            </>
          }
        />
      </div>

      <Card className="max-w-2xl">
        <CardContent>
          <dl className="grid gap-4 sm:grid-cols-3">
            <Dato
              titulo="DNI"
              valor={cliente.dni ? formatearDNI(cliente.dni) : null}
            />
            <Dato titulo="Teléfono" valor={cliente.telefono} />
            <Dato
              titulo="Localidad"
              valor={cliente.localidad?.nombre ?? null}
            />
          </dl>
        </CardContent>
      </Card>

      <ClienteSheet
        abierto={edicion.abierta}
        onAbiertoChange={(abierta) => setEdicion((e) => ({ ...e, abierta }))}
        cliente={cliente}
        apertura={edicion.apertura}
      />
      {puede("clientes:borrar") && (
        <ConfirmarBorrarCliente
          cliente={aBorrar}
          onCancelar={() => setABorrar(null)}
          onConfirmar={() => aBorrar && borrar(aBorrar)}
        />
      )}
    </div>
  )
}
