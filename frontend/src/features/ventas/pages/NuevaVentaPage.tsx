import { ArrowLeftIcon, ArrowRightIcon } from "@phosphor-icons/react"
import { useEffect, useReducer, useState, type Dispatch } from "react"
import { useNavigate } from "react-router"
import { toast } from "sonner"

import { useAuth } from "@/features/auth"
import { datosDeEquipo, useTipoDeCategoria } from "@/features/productos"
import { ApiError, mensajeDeError } from "@/shared/api"
import { cn } from "@/shared/lib/utils"
import { Button } from "@/shared/ui/button"
import { Card, CardContent, CardFooter } from "@/shared/ui/card"
import { EncabezadoPagina } from "@/shared/ui/encabezado-pagina"

import type { DatosVenta } from "../api"
import {
  BORRADOR_VACIO,
  reducir,
  VentaContext,
  type Accion,
} from "../components/borrador"
import { PasoEquipos } from "../components/PasoEquipos"
import {
  PasoCliente,
  PasoModalidad,
  PasoPago,
  PasoVendedor,
} from "../components/Pasos"
import { ResumenVenta } from "../components/ResumenVenta"
import { useCotizacionQuery, useCrearVenta } from "../queries"

// Reglas 4.1: Equipos → Cliente → Modalidad → Método de pago / Canje → Vendedor.
const PASOS = [
  { titulo: "Equipos", Paso: PasoEquipos },
  { titulo: "Cliente", Paso: PasoCliente },
  { titulo: "Modalidad", Paso: PasoModalidad },
  { titulo: "Pago y canje", Paso: PasoPago },
  { titulo: "Vendedor", Paso: PasoVendedor },
]

/** En qué paso se carga cada campo, para llevar al usuario al error. */
function pasoDe(campo: string): number {
  if (campo.startsWith("items")) return 0
  if (campo === "cliente_id") return 1
  if (campo === "modalidad") return 2
  if (campo.startsWith("canje") || campo === "metodo_pago_id") return 3
  return 4
}

const limpio = (v: string) => (v.trim() === "" ? null : v.trim())

/** Lo vacío no se manda: la API responde "Este campo es obligatorio." donde corresponde. */
const sinVacios = (datos: Record<string, unknown>) =>
  Object.fromEntries(Object.entries(datos).filter(([, v]) => v !== null))

const ESPERA_COTIZACION = 300

export function NuevaVentaPage() {
  const navigate = useNavigate()
  const { puede } = useAuth()
  const [b, despacharBorrador] = useReducer(reducir, BORRADOR_VACIO)
  const [paso, setPaso] = useState(0)
  const crear = useCrearVenta()
  const { tipo: tipoCanje } = useTipoDeCategoria(b.canje.categoriaId)

  // Con un cambio, el error de la venta anterior ya no aplica: la cotización dice el actual.
  const despachar: Dispatch<Accion> = (accion) => {
    if (crear.error) crear.reset()
    despacharBorrador(accion)
  }

  const venta: DatosVenta = {
    items: b.lineas.map((l) => ({
      producto_id: l.producto.id,
      cantidad: l.cantidad,
      precio_usd: l.esRegalo ? "0" : l.precio,
      es_regalo: l.esRegalo,
    })),
    modalidad: "contado",
    canje_valor_usd: b.conCanje ? limpio(b.canjeValor) : null,
    // La comisión entra en la ganancia de la cotización; el Vendedor no la manda.
    ...(puede("ver_costos") &&
      limpio(b.comision) !== null && { comision_usd: limpio(b.comision) }),
  }
  const cotizacion = useCotizacionQuery(
    useDemorado(venta, ESPERA_COTIZACION),
    b.lineas.length > 0
  )

  function confirmar() {
    const datos = sinVacios({
      ...venta,
      canje: b.conCanje ? sinVacios(datosDeEquipo(b.canje, tipoCanje)) : null,
      cliente_id: b.cliente?.id ?? null,
      metodo_pago_id: b.metodoPagoId ? Number(b.metodoPagoId) : null,
      vendedor_numero: limpio(b.vendedorNumero),
      garantia_meses: limpio(b.garantiaMeses),
    })
    crear.mutate(datos, {
      onSuccess: (v) => {
        toast.success(`Se registró la venta #${v.id}.`)
        navigate("/ventas")
      },
      onError: (error) => {
        const primero =
          error instanceof ApiError && Object.keys(error.campos)[0]
        if (primero) setPaso(pasoDe(primero))
      },
    })
  }

  const errorCotizacion =
    b.lineas.length > 0 && cotizacion.error instanceof ApiError
      ? cotizacion.error
      : null
  const campos = {
    ...(crear.error instanceof ApiError ? crear.error.campos : {}),
    ...errorCotizacion?.campos,
  }
  const errorGeneral = [crear.error, errorCotizacion].find(
    (e) => e && !(e instanceof ApiError && Object.keys(e.campos).length > 0)
  )
  const conError = new Set(Object.keys(campos).map(pasoDe))
  const cotizado = b.lineas.length > 0 ? cotizacion.data : undefined
  const { Paso, titulo } = PASOS[paso]

  return (
    <VentaContext
      value={{
        b,
        despachar,
        cotizacion: cotizado,
        campos,
      }}
    >
      <EncabezadoPagina
        titulo="Nueva venta"
        descripcion="Los totales y el saldo se calculan con cada cambio."
      />

      <div className="grid items-start gap-6 xl:grid-cols-[1fr_20rem]">
        <div className="flex min-w-0 flex-col gap-4">
          <nav aria-label="Pasos de la venta">
            <ol className="flex flex-wrap gap-2">
              {PASOS.map((p, n) => (
                <li key={p.titulo}>
                  <Button
                    variant={n === paso ? "secondary" : "ghost"}
                    size="sm"
                    aria-current={n === paso ? "step" : undefined}
                    className={cn(conError.has(n) && "text-destructive")}
                    onClick={() => setPaso(n)}
                  >
                    <span className="tabular-nums">{n + 1}.</span>
                    {p.titulo}
                    {conError.has(n) && (
                      <span className="sr-only"> (tiene errores)</span>
                    )}
                  </Button>
                </li>
              ))}
            </ol>
          </nav>

          <Card>
            <CardContent className="flex flex-col gap-4">
              <h2 className="font-heading text-2xl">{titulo}</h2>
              <Paso />
            </CardContent>
            <CardFooter className="justify-between">
              <Button
                variant="outline"
                disabled={paso === 0}
                onClick={() => setPaso(paso - 1)}
              >
                <ArrowLeftIcon />
                Anterior
              </Button>
              {paso < PASOS.length - 1 && (
                <Button variant="outline" onClick={() => setPaso(paso + 1)}>
                  Siguiente
                  <ArrowRightIcon />
                </Button>
              )}
            </CardFooter>
          </Card>
        </div>

        <ResumenVenta
          cotizacion={errorCotizacion ? undefined : cotizado}
          sinProductos={b.lineas.length === 0}
          actualizando={cotizacion.isFetching}
          error={errorGeneral ? mensajeDeError(errorGeneral) : null}
          onTcCargado={() => cotizacion.refetch()}
          onConfirmar={confirmar}
          confirmando={crear.isPending}
        />
      </div>
    </VentaContext>
  )
}

/** El valor, recién cuando deja de cambiar por un rato: no se cotiza en cada tecla. */
function useDemorado<T>(valor: T, ms: number): T {
  const [demorado, setDemorado] = useState(valor)
  const clave = JSON.stringify(valor)
  useEffect(() => {
    const espera = setTimeout(() => setDemorado(JSON.parse(clave)), ms)
    return () => clearTimeout(espera)
  }, [clave, ms])
  return demorado
}
