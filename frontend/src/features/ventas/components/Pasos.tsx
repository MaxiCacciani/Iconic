import { useEffect, useState } from "react"

import { useAuth } from "@/features/auth"
import { useCatalogoQuery } from "@/features/catalogos"
import { BuscadorCliente } from "@/features/clientes"
import { CamposEquipo, type Equipo } from "@/features/productos"
import { useVendedorPorNumeroQuery } from "@/features/vendedores"
import { mensajeDeError } from "@/shared/api"
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSet,
} from "@/shared/ui/field"
import { Input } from "@/shared/ui/input"
import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput,
  InputGroupText,
} from "@/shared/ui/input-group"
import { InputUSD } from "@/shared/ui/input-usd"
import { RadioGroup, RadioGroupItem } from "@/shared/ui/radio-group"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select"
import { Spinner } from "@/shared/ui/spinner"
import { Switch } from "@/shared/ui/switch"

import { useVenta } from "./borrador"

export function PasoCliente() {
  const { b, despachar, campos } = useVenta()
  return (
    <Field data-invalid={campos.cliente_id ? true : undefined}>
      <FieldLabel htmlFor="venta-cliente">Cliente</FieldLabel>
      <BuscadorCliente
        id="venta-cliente"
        cliente={b.cliente}
        onElegir={(cliente) =>
          despachar({ tipo: "cambiar", cambios: { cliente } })
        }
        invalido={campos.cliente_id ? true : undefined}
      />
      <FieldDescription>
        Toda venta necesita un cliente. Si no está, se da de alta desde acá.
      </FieldDescription>
      {campos.cliente_id && <FieldError>{campos.cliente_id}</FieldError>}
    </Field>
  )
}

export function PasoModalidad() {
  const { campos } = useVenta()
  return (
    <Field data-invalid={campos.modalidad ? true : undefined}>
      <FieldLabel id="venta-modalidad">Modalidad</FieldLabel>
      <RadioGroup aria-labelledby="venta-modalidad" value="contado">
        <Field orientation="horizontal">
          <RadioGroupItem value="contado" id="venta-contado" />
          <FieldLabel htmlFor="venta-contado" className="font-normal">
            Contado: pago único. El canje se descuenta del saldo.
          </FieldLabel>
        </Field>
        <Field orientation="horizontal" data-disabled>
          <RadioGroupItem value="cuotas" id="venta-cuotas" disabled />
          <FieldLabel htmlFor="venta-cuotas" className="font-normal">
            En cuotas (todavía no disponible)
          </FieldLabel>
        </Field>
      </RadioGroup>
      {campos.modalidad && <FieldError>{campos.modalidad}</FieldError>}
    </Field>
  )
}

export function PasoPago() {
  const { b, despachar, campos } = useVenta()
  const metodos = useCatalogoQuery("metodos-pago")
  const predeterminado = metodos.data?.find((m) => m.predeterminado)
  const metodoPagoId = b.metodoPagoId || String(predeterminado?.id ?? "")
  const cambiarCanje = (cambios: Partial<Equipo>) =>
    despachar({
      tipo: "cambiar",
      cambios: { canje: { ...b.canje, ...cambios } },
    })

  return (
    <FieldGroup>
      <Field data-invalid={campos.metodo_pago_id ? true : undefined}>
        <FieldLabel htmlFor="venta-metodo">Método de pago</FieldLabel>
        <Select
          value={metodoPagoId}
          onValueChange={(v) =>
            despachar({ tipo: "cambiar", cambios: { metodoPagoId: v } })
          }
          disabled={metodos.isPending}
        >
          <SelectTrigger
            id="venta-metodo"
            className="w-full sm:w-64"
            aria-invalid={campos.metodo_pago_id ? true : undefined}
          >
            <SelectValue placeholder="Elegí un método" />
          </SelectTrigger>
          <SelectContent>
            {metodos.data?.map((m) => (
              <SelectItem key={m.id} value={String(m.id)}>
                {m.nombre}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {campos.metodo_pago_id && (
          <FieldError>{campos.metodo_pago_id}</FieldError>
        )}
      </Field>

      <Field orientation="horizontal">
        <Switch
          id="venta-con-canje"
          checked={b.conCanje}
          onCheckedChange={(conCanje) =>
            despachar({ tipo: "cambiar", cambios: { conCanje } })
          }
        />
        <FieldLabel htmlFor="venta-con-canje" className="font-normal">
          El cliente entrega un equipo en canje
        </FieldLabel>
      </Field>

      {b.conCanje && (
        <FieldSet>
          <FieldLegend>Plan canje</FieldLegend>
          <FieldDescription>
            El equipo entra al stock como disponible, con precio y costo iguales
            al valor del canje.
          </FieldDescription>
          <FieldGroup>
            <Field
              data-invalid={campos.canje_valor_usd ? true : undefined}
              className="sm:w-1/2"
            >
              <FieldLabel htmlFor="canje-valor">Valor del canje</FieldLabel>
              <InputUSD
                id="canje-valor"
                value={b.canjeValor}
                onChange={(e) =>
                  despachar({
                    tipo: "cambiar",
                    cambios: { canjeValor: e.target.value },
                  })
                }
                aria-invalid={campos.canje_valor_usd ? true : undefined}
              />
              {campos.canje_valor_usd && (
                <FieldError>{campos.canje_valor_usd}</FieldError>
              )}
            </Field>
            <CamposEquipo
              equipo={b.canje}
              onCambiar={cambiarCanje}
              campos={campos}
              id="canje"
              campo="canje."
              imeiOpcional
              sinAccesorios
            />
            {campos.canje && <FieldError>{campos.canje}</FieldError>}
          </FieldGroup>
        </FieldSet>
      )}
    </FieldGroup>
  )
}

const ESPERA = 300

export function PasoVendedor() {
  const { b, despachar, campos } = useVenta()
  const { puede } = useAuth()
  const escrito = b.vendedorNumero.trim()
  const [buscado, setBuscado] = useState(escrito)
  useEffect(() => {
    const espera = setTimeout(() => setBuscado(escrito), ESPERA)
    return () => clearTimeout(espera)
  }, [escrito])
  const numero = /^\d+$/.test(buscado) ? Number(buscado) : undefined
  const vendedor = useVendedorPorNumeroQuery(numero)

  return (
    <FieldGroup>
      <Field
        data-invalid={campos.vendedor_numero ? true : undefined}
        className="sm:w-1/2"
      >
        <FieldLabel htmlFor="venta-vendedor">
          Número de vendedor (opcional)
        </FieldLabel>
        <Input
          id="venta-vendedor"
          inputMode="numeric"
          autoComplete="off"
          className="tabular-nums"
          value={b.vendedorNumero}
          onChange={(e) =>
            despachar({
              tipo: "cambiar",
              cambios: { vendedorNumero: e.target.value },
            })
          }
          aria-invalid={campos.vendedor_numero ? true : undefined}
          aria-describedby="venta-vendedor-nombre"
        />
        <p
          id="venta-vendedor-nombre"
          aria-live="polite"
          className="text-sm text-muted-foreground"
        >
          {!escrito ? null : escrito !== buscado || vendedor.isFetching ? (
            <Spinner />
          ) : vendedor.isError ? (
            mensajeDeError(vendedor.error)
          ) : (
            vendedor.data?.nombre
          )}
        </p>
        {campos.vendedor_numero && (
          <FieldError>{campos.vendedor_numero}</FieldError>
        )}
      </Field>

      <Field
        data-invalid={campos.garantia_meses ? true : undefined}
        className="sm:w-1/2"
      >
        <FieldLabel htmlFor="venta-garantia">Garantía</FieldLabel>
        <InputGroup>
          <InputGroupInput
            id="venta-garantia"
            inputMode="numeric"
            autoComplete="off"
            className="tabular-nums"
            value={b.garantiaMeses}
            onChange={(e) =>
              despachar({
                tipo: "cambiar",
                cambios: { garantiaMeses: e.target.value },
              })
            }
            aria-invalid={campos.garantia_meses ? true : undefined}
          />
          <InputGroupAddon align="inline-end">
            <InputGroupText>meses</InputGroupText>
          </InputGroupAddon>
        </InputGroup>
        <FieldDescription>Desde la fecha de venta.</FieldDescription>
        {campos.garantia_meses && (
          <FieldError>{campos.garantia_meses}</FieldError>
        )}
      </Field>

      {puede("ver_costos") && (
        <Field
          data-invalid={campos.comision_usd ? true : undefined}
          className="sm:w-1/2"
        >
          <FieldLabel htmlFor="venta-comision">Comisión (opcional)</FieldLabel>
          <InputUSD
            id="venta-comision"
            placeholder="0"
            value={b.comision}
            onChange={(e) =>
              despachar({
                tipo: "cambiar",
                cambios: { comision: e.target.value },
              })
            }
            aria-invalid={campos.comision_usd ? true : undefined}
          />
          <FieldDescription>
            Se descuenta de la ganancia. Se puede cargar después, desde el
            historial.
          </FieldDescription>
          {campos.comision_usd && (
            <FieldError>{campos.comision_usd}</FieldError>
          )}
        </Field>
      )}
    </FieldGroup>
  )
}
