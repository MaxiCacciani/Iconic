import { FilePdfIcon, TrashIcon, WarningIcon } from "@phosphor-icons/react"
import { useState, type FormEvent, type ReactNode } from "react"
import { Link } from "react-router"
import { toast } from "sonner"

import { ApiError, mensajeDeError } from "@/shared/api"
import {
  formatearARS,
  formatearDiaDe,
  formatearFecha,
  formatearUSD,
} from "@/shared/lib/formato"
import { Badge } from "@/shared/ui/badge"
import { Button } from "@/shared/ui/button"
import { EstadoCuota } from "@/shared/ui/estado-cuota"
import { Field, FieldError, FieldLabel } from "@/shared/ui/field"
import { InputUSD } from "@/shared/ui/input-usd"
import { Separator } from "@/shared/ui/separator"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/shared/ui/sheet"
import { Spinner } from "@/shared/ui/spinner"

import { esAdmin, type Venta, type VentaAdmin } from "../api"
import { useCambiarComision, useDescargarComprobante } from "../queries"
import { MODALIDAD, nombreProducto } from "./etiquetas"

type Props = {
  /** La venta a mostrar; `null` cierra el panel. */
  venta: Venta | null
  onCerrar: () => void
  /** Sin esta función (sin permiso), no se ofrece borrar. */
  onBorrar?: (venta: Venta) => void
  /** La venta como quedó después de cambiar la comisión. */
  onActualizada: (venta: Venta) => void
}

export function DetalleVentaSheet({
  venta,
  onCerrar,
  onBorrar,
  onActualizada,
}: Props) {
  return (
    <Sheet open={venta !== null} onOpenChange={(a) => !a && onCerrar()}>
      <SheetContent className="flex flex-col sm:max-w-lg">
        {venta && (
          <Detalle
            venta={venta}
            onBorrar={onBorrar}
            onActualizada={onActualizada}
          />
        )}
      </SheetContent>
    </Sheet>
  )
}

function Detalle({
  venta: v,
  onBorrar,
  onActualizada,
}: {
  venta: Venta
  onBorrar?: (venta: Venta) => void
  onActualizada: (venta: Venta) => void
}) {
  return (
    <>
      <SheetHeader>
        <SheetTitle className="font-heading text-2xl">Venta #{v.id}</SheetTitle>
        <SheetDescription className="tabular-nums">
          {formatearDiaDe(v.fecha)} · TC {formatearARS(v.tc_ars)}
        </SheetDescription>
      </SheetHeader>

      <div className="flex flex-1 flex-col gap-6 overflow-y-auto px-4 text-sm">
        <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2">
          <Dato termino="Cliente">
            <Link
              to={`/clientes/${v.cliente.id}`}
              className="underline-offset-4 hover:underline"
            >
              {v.cliente.nombre}
            </Link>
          </Dato>
          <Dato termino="Pago">
            {v.cantidad_cuotas
              ? `${v.cantidad_cuotas} cuotas`
              : MODALIDAD[v.modalidad]}{" "}
            · {v.metodo_pago.nombre}
          </Dato>
          <Dato termino="Vendedor">
            {v.vendedor ? (
              `${v.vendedor.nombre} (n.º ${v.vendedor.numero})`
            ) : (
              <span className="text-muted-foreground">Sin vendedor</span>
            )}
          </Dato>
          <Dato termino="Registró">{v.usuario.nombre}</Dato>
          <Dato termino="Garantía">
            {v.garantia_meses === 1 ? "1 mes" : `${v.garantia_meses} meses`}
          </Dato>
        </dl>

        <section className="flex flex-col gap-2">
          <h3 className="font-medium">Productos</h3>
          <ul className="flex flex-col divide-y rounded-lg border">
            {v.items.map((i, n) => (
              <li key={n} className="flex justify-between gap-4 p-3">
                <div className="flex min-w-0 flex-col gap-1">
                  <span>
                    {nombreProducto(i.producto)}{" "}
                    <span className="text-muted-foreground tabular-nums">
                      #{i.producto.id}
                    </span>
                  </span>
                  {i.producto.imei && (
                    <span className="font-mono text-xs text-muted-foreground">
                      IMEI {i.producto.imei}
                    </span>
                  )}
                  <span className="flex flex-wrap gap-1.5">
                    {i.es_regalo && <Badge variant="secondary">Regalo</Badge>}
                    {"bajo_costo" in i && i.bajo_costo && (
                      <Badge
                        variant="outline"
                        className="border-warning/50 bg-warning/10 text-warning-foreground"
                      >
                        <WarningIcon weight="fill" aria-hidden />
                        Bajo costo
                      </Badge>
                    )}
                  </span>
                </div>
                <div className="shrink-0 text-right tabular-nums">
                  {i.cantidad > 1 && (
                    <span className="text-muted-foreground">
                      {i.cantidad} ×{" "}
                    </span>
                  )}
                  {formatearUSD(i.precio_usd)}
                  {"costo_usd" in i && i.costo_usd !== null && (
                    <span className="block text-xs text-muted-foreground">
                      Costo {formatearUSD(i.costo_usd)}
                    </span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </section>

        {v.canje && (
          <section className="flex flex-col gap-2">
            <h3 className="font-medium">Plan canje</h3>
            <p className="flex justify-between gap-4 rounded-lg border p-3">
              <span>
                {v.canje.producto ? (
                  <>
                    {nombreProducto(v.canje.producto)}{" "}
                    <span className="text-muted-foreground tabular-nums">
                      #{v.canje.producto.id}
                    </span>
                  </>
                ) : (
                  "Equipo entregado"
                )}
              </span>
              <span className="tabular-nums">
                {formatearUSD(v.canje.valor_usd)}
              </span>
            </p>
          </section>
        )}

        <section className="flex flex-col gap-2 tabular-nums">
          <Fila etiqueta="Total">
            {formatearUSD(v.total_usd)} · {formatearARS(v.total_ars)}
          </Fila>
          {v.canje && (
            <Fila etiqueta="Canje">− {formatearUSD(v.canje.valor_usd)}</Fila>
          )}
          {Number(v.anticipo_usd) > 0 && (
            <Fila etiqueta="Anticipo">− {formatearUSD(v.anticipo_usd)}</Fila>
          )}
          <Separator />
          <Fila etiqueta={v.cuotas.length > 0 ? "A financiar" : "Saldo"}>
            <span className="font-medium">
              {formatearUSD(v.saldo_usd)} · {formatearARS(v.saldo_ars)}
            </span>
          </Fila>
          {esAdmin(v) && (
            <>
              <Separator />
              <Fila etiqueta="Costo">
                {v.costo_usd === null
                  ? "Sin costo cargado"
                  : formatearUSD(v.costo_usd)}
              </Fila>
              {Number(v.comision_usd) > 0 && (
                <Fila etiqueta="Comisión">
                  − {formatearUSD(v.comision_usd)}
                </Fila>
              )}
              {v.ganancia_usd !== null && (
                <Fila etiqueta="Ganancia">
                  {formatearUSD(v.ganancia_usd)}
                  {v.margen_pct !== null &&
                    ` · ${v.margen_pct.replace(".", ",")} %`}
                </Fila>
              )}
            </>
          )}
        </section>

        {v.cuotas.length > 0 && (
          <section className="flex flex-col gap-2">
            <h3 className="font-medium">Cuotas</h3>
            <ol className="flex flex-col divide-y rounded-lg border tabular-nums">
              {v.cuotas.map((c) => (
                <li
                  key={c.id}
                  className="flex items-center justify-between gap-4 px-3 py-2"
                >
                  <span>
                    {c.numero} de {v.cuotas.length}
                    <span className="block text-xs text-muted-foreground">
                      {formatearFecha(c.vencimiento)}
                    </span>
                  </span>
                  <span className="flex items-center gap-3">
                    <EstadoCuota estado={c.estado} />
                    {formatearUSD(c.monto_usd)}
                  </span>
                </li>
              ))}
            </ol>
          </section>
        )}

        {esAdmin(v) && (
          <Comision key={v.id} venta={v} onGuardada={onActualizada} />
        )}
      </div>

      <SheetFooter>
        <DescargarComprobante ventaId={v.id} />
        {onBorrar && (
          <Button variant="destructive" onClick={() => onBorrar(v)}>
            <TrashIcon />
            Borrar venta
          </Button>
        )}
      </SheetFooter>
    </>
  )
}

function DescargarComprobante({ ventaId }: { ventaId: number }) {
  const descargar = useDescargarComprobante()
  return (
    <Button
      variant="outline"
      disabled={descargar.isPending}
      onClick={() =>
        descargar.mutate(ventaId, {
          onError: (error) => toast.error(mensajeDeError(error)),
        })
      }
    >
      {descargar.isPending ? <Spinner /> : <FilePdfIcon />}
      Descargar comprobante
    </Button>
  )
}

/** Montos de la API (`"50.00"`) como los escribe el usuario (`"50"`, `"80,5"`). */
const comoTexto = (usd: string) => Number(usd).toString().replace(".", ",")

function Comision({
  venta,
  onGuardada,
}: {
  venta: VentaAdmin
  onGuardada: (venta: VentaAdmin) => void
}) {
  const [valor, setValor] = useState(comoTexto(venta.comision_usd))
  const cambiar = useCambiarComision()
  // El 422 del campo o, si no, el motivo general (por ejemplo, la venta ya no existe).
  const error =
    cambiar.error &&
    ((cambiar.error instanceof ApiError && cambiar.error.campos.comision_usd) ||
      mensajeDeError(cambiar.error))

  function guardar(e: FormEvent) {
    e.preventDefault()
    cambiar.mutate(
      { id: venta.id, comision: valor.trim() },
      {
        onSuccess: (v) => {
          onGuardada(v)
          toast.success(`Se guardó la comisión de la venta #${v.id}.`)
        },
      }
    )
  }

  return (
    <form onSubmit={guardar}>
      <Field data-invalid={error ? true : undefined}>
        <FieldLabel htmlFor="detalle-comision">Comisión</FieldLabel>
        <div className="flex gap-2">
          <InputUSD
            id="detalle-comision"
            placeholder="0"
            className="sm:w-48"
            value={valor}
            onChange={(e) => {
              if (cambiar.error) cambiar.reset()
              setValor(e.target.value)
            }}
            aria-invalid={error ? true : undefined}
          />
          <Button type="submit" variant="outline" disabled={cambiar.isPending}>
            {cambiar.isPending && <Spinner />}
            Guardar
          </Button>
        </div>
        {error && <FieldError>{error}</FieldError>}
      </Field>
    </form>
  )
}

function Dato({ termino, children }: { termino: string; children: ReactNode }) {
  return (
    <>
      <dt className="text-muted-foreground">{termino}</dt>
      <dd>{children}</dd>
    </>
  )
}

function Fila({
  etiqueta,
  children,
}: {
  etiqueta: string
  children: ReactNode
}) {
  return (
    <p className="flex justify-between gap-4">
      <span className="text-muted-foreground">{etiqueta}</span>
      <span className="text-right">{children}</span>
    </p>
  )
}
