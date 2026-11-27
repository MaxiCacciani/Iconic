import { Link } from "react-router"

import {
  useCatalogoQuery,
  useOpcionesDeModeloQuery,
} from "@/features/catalogos"
import { Alert, AlertDescription } from "@/shared/ui/alert"
import {
  Field,
  FieldDescription,
  FieldError,
  FieldLabel,
} from "@/shared/ui/field"
import { Input } from "@/shared/ui/input"
import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput,
  InputGroupText,
} from "@/shared/ui/input-group"
import { RadioGroup, RadioGroupItem } from "@/shared/ui/radio-group"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select"
import { Textarea } from "@/shared/ui/textarea"

import type { Condicion } from "../api"
import { CONDICION } from "./etiquetas"

/** El valor de "Sin capacidad" y "Sin color" en los selects. */
export const NINGUNO = "ninguno"

/** Lo que el usuario va cargando de un equipo, tal como lo escribe. */
export type Equipo = {
  categoriaId: string
  modeloId: string
  capacidadId: string
  colorId: string
  condicion: Condicion
  imei: string
  bateria: string
  controles: string
  extras: string
}

export const EQUIPO_VACIO: Equipo = {
  categoriaId: "",
  modeloId: "",
  capacidadId: "",
  colorId: "",
  condicion: "nuevo",
  imei: "",
  bateria: "",
  controles: "",
  extras: "",
}

const limpio = (v: string) => (v.trim() === "" ? null : v.trim())
const idDe = (v: string) => (v && v !== NINGUNO ? Number(v) : null)

/** La categoría elegida y su tipo, tal como los guarda el catálogo: de ahí sale qué
 * datos se piden (IMEI y batería, controles o cantidad). */
export function useTipoDeCategoria(categoriaId: string) {
  const categorias = useCatalogoQuery("categorias")
  const tipos = useCatalogoQuery("tipos-categoria")
  const categoria = categorias.data?.find((c) => c.id === Number(categoriaId))
  const tipo = tipos.data?.find((t) => t.id === categoria?.tipo_categoria_id)
  const porCantidad = new Set(
    tipos.data?.filter((t) => t.por_cantidad).map((t) => t.id)
  )
  return { categorias, categoria, tipo, porCantidad }
}

type Tipo = ReturnType<typeof useTipoDeCategoria>["tipo"]

/** Los datos para la API. Lo que el tipo no lleva va en null: si quedó algo escrito de
 * otra categoría, no se manda. */
export function datosDeEquipo(e: Equipo, tipo: Tipo) {
  return {
    modelo_id: idDe(e.modeloId),
    capacidad_id: idDe(e.capacidadId),
    color_id: idDe(e.colorId),
    condicion: e.condicion,
    imei: tipo?.usa_imei ? limpio(e.imei) : null,
    bateria: tipo?.usa_bateria ? limpio(e.bateria) : null,
    controles: tipo?.usa_controles ? limpio(e.controles) : null,
    extras: tipo?.usa_controles ? limpio(e.extras) : null,
  }
}

type Props = {
  equipo: Equipo
  onCambiar: (cambios: Partial<Equipo>) => void
  /** Errores de la API por campo. */
  campos: Record<string, string>
  /** Prefijo de los `id` de los inputs. */
  id: string
  /** Prefijo de los campos en los errores de la API (`"canje."`). */
  campo?: string
  imeiOpcional?: boolean
  /** Sin las categorías por cantidad (accesorios): el canje solo toma equipos y
   * consolas. La API lo valida igual. */
  sinAccesorios?: boolean
}

/** Categoría, modelo, capacidad, color, condición y los datos que pide el tipo de la
 * categoría. Lo usan el alta de productos y el canje de la venta. */
export function CamposEquipo({
  equipo: e,
  onCambiar,
  campos,
  id,
  campo = "",
  imeiOpcional = false,
  sinAccesorios = false,
}: Props) {
  const categoriaId = Number(e.categoriaId) || undefined
  const modeloId = Number(e.modeloId) || undefined
  const { categorias, categoria, tipo, porCantidad } = useTipoDeCategoria(
    e.categoriaId
  )
  const ofrecidas = sinAccesorios
    ? categorias.data?.filter((c) => !porCantidad.has(c.tipo_categoria_id))
    : categorias.data
  const modelos = useCatalogoQuery("modelos", categoriaId, {
    habilitado: categoriaId !== undefined,
  })
  // Lo que se ofrece depende del modelo: sus colores y capacidades, o los de la categoría.
  const capacidades = useOpcionesDeModeloQuery("capacidades", modeloId)
  const colores = useOpcionesDeModeloQuery("colores", modeloId)

  const mensaje = (nombre: string) => campos[campo + nombre]
  const invalido = (nombre: string) => (mensaje(nombre) ? true : undefined)
  const error = (nombre: string) =>
    mensaje(nombre) ? <FieldError>{mensaje(nombre)}</FieldError> : null

  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field>
          <FieldLabel htmlFor={`${id}-categoria`}>Categoría</FieldLabel>
          <Select
            value={e.categoriaId}
            onValueChange={(v) =>
              onCambiar({
                categoriaId: v,
                modeloId: "",
                capacidadId: NINGUNO,
                colorId: NINGUNO,
              })
            }
            disabled={categorias.isPending}
          >
            <SelectTrigger id={`${id}-categoria`} className="w-full">
              <SelectValue placeholder="Elegí una categoría" />
            </SelectTrigger>
            <SelectContent>
              {ofrecidas?.map((c) => (
                <SelectItem key={c.id} value={String(c.id)}>
                  {c.nombre}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </Field>

        <Field data-invalid={invalido("modelo_id")}>
          <FieldLabel htmlFor={`${id}-modelo`}>Modelo</FieldLabel>
          <Select
            value={e.modeloId}
            onValueChange={(v) =>
              onCambiar({ modeloId: v, capacidadId: NINGUNO, colorId: NINGUNO })
            }
            disabled={!categoriaId || modelos.isPending}
          >
            <SelectTrigger
              id={`${id}-modelo`}
              className="w-full"
              aria-invalid={invalido("modelo_id")}
            >
              <SelectValue
                placeholder={
                  categoriaId ? "Elegí un modelo" : "Primero la categoría"
                }
              />
            </SelectTrigger>
            <SelectContent>
              {modelos.data?.map((m) => (
                <SelectItem key={m.id} value={String(m.id)}>
                  {m.nombre}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {error("modelo_id")}
        </Field>
      </div>

      {categoriaId && modelos.data?.length === 0 && (
        <Alert>
          <AlertDescription>
            {categoria?.nombre} todavía no tiene modelos.{" "}
            <Link
              to={`/catalogos?lista=modelos&categoria=${categoriaId}`}
              className="font-medium text-foreground underline underline-offset-4"
            >
              Cargalos en Catálogos
            </Link>
            .
          </AlertDescription>
        </Alert>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <OpcionDeModelo
          id={`${id}-capacidad`}
          etiqueta="Capacidad"
          ninguna="Sin capacidad"
          valor={e.capacidadId}
          onCambiar={(v) => onCambiar({ capacidadId: v })}
          opciones={capacidades.data}
          habilitado={Boolean(modeloId)}
          error={mensaje("capacidad_id")}
        />
        <OpcionDeModelo
          id={`${id}-color`}
          etiqueta="Color"
          ninguna="Sin color"
          valor={e.colorId}
          onCambiar={(v) => onCambiar({ colorId: v })}
          opciones={colores.data}
          habilitado={Boolean(modeloId)}
          error={mensaje("color_id")}
        />
      </div>

      {tipo?.usa_imei && (
        <Field data-invalid={invalido("imei")}>
          <FieldLabel htmlFor={`${id}-imei`}>
            {imeiOpcional ? "IMEI (opcional)" : "IMEI"}
          </FieldLabel>
          <Input
            id={`${id}-imei`}
            inputMode="numeric"
            autoComplete="off"
            spellCheck={false}
            maxLength={15}
            className="font-mono tracking-wide"
            value={e.imei}
            onChange={(ev) => onCambiar({ imei: ev.target.value })}
            aria-invalid={invalido("imei")}
          />
          <FieldDescription>Los 15 dígitos, sin espacios.</FieldDescription>
          {error("imei")}
        </Field>
      )}

      {tipo?.usa_bateria && (
        <Field data-invalid={invalido("bateria")} className="sm:w-1/2">
          <FieldLabel htmlFor={`${id}-bateria`}>Batería (opcional)</FieldLabel>
          <InputGroup>
            <InputGroupInput
              id={`${id}-bateria`}
              inputMode="numeric"
              autoComplete="off"
              value={e.bateria}
              onChange={(ev) => onCambiar({ bateria: ev.target.value })}
              aria-invalid={invalido("bateria")}
            />
            <InputGroupAddon align="inline-end">
              <InputGroupText>%</InputGroupText>
            </InputGroupAddon>
          </InputGroup>
          {error("bateria")}
        </Field>
      )}

      {tipo?.usa_controles && (
        <>
          <Field data-invalid={invalido("controles")}>
            <FieldLabel htmlFor={`${id}-controles`}>Controles</FieldLabel>
            <Input
              id={`${id}-controles`}
              inputMode="numeric"
              autoComplete="off"
              className="sm:w-32"
              value={e.controles}
              onChange={(ev) => onCambiar({ controles: ev.target.value })}
              aria-invalid={invalido("controles")}
            />
            <FieldDescription>De 0 a 4.</FieldDescription>
            {error("controles")}
          </Field>
          <Field data-invalid={invalido("extras")}>
            <FieldLabel htmlFor={`${id}-extras`}>Extras (opcional)</FieldLabel>
            <Textarea
              id={`${id}-extras`}
              rows={2}
              placeholder="Caja original, juegos, cables…"
              value={e.extras}
              onChange={(ev) => onCambiar({ extras: ev.target.value })}
              aria-invalid={invalido("extras")}
            />
            {error("extras")}
          </Field>
        </>
      )}

      <Field data-invalid={invalido("condicion")}>
        <FieldLabel id={`${id}-condicion`}>Condición</FieldLabel>
        <RadioGroup
          aria-labelledby={`${id}-condicion`}
          value={e.condicion}
          onValueChange={(v) => onCambiar({ condicion: v as Condicion })}
          className="flex gap-6"
        >
          {(Object.keys(CONDICION) as Condicion[]).map((c) => (
            <Field key={c} orientation="horizontal" className="w-auto">
              <RadioGroupItem value={c} id={`${id}-condicion-${c}`} />
              <FieldLabel
                htmlFor={`${id}-condicion-${c}`}
                className="font-normal"
              >
                {CONDICION[c]}
                {c === "nuevo" && " (sellado)"}
              </FieldLabel>
            </Field>
          ))}
        </RadioGroup>
        {error("condicion")}
      </Field>
    </>
  )
}

function OpcionDeModelo({
  id,
  etiqueta,
  ninguna,
  valor,
  onCambiar,
  opciones,
  habilitado,
  error,
}: {
  id: string
  etiqueta: string
  ninguna: string
  valor: string
  onCambiar: (valor: string) => void
  opciones?: { id: number; nombre: string }[]
  habilitado: boolean
  error?: string
}) {
  return (
    <Field data-invalid={error ? true : undefined}>
      <FieldLabel htmlFor={id}>{etiqueta}</FieldLabel>
      <Select
        value={habilitado ? valor : ""}
        onValueChange={onCambiar}
        disabled={!habilitado || !opciones}
      >
        <SelectTrigger
          id={id}
          className="w-full"
          aria-invalid={error ? true : undefined}
        >
          <SelectValue
            placeholder={habilitado ? ninguna : "Primero el modelo"}
          />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={NINGUNO}>{ninguna}</SelectItem>
          {opciones && opciones.length > 0 && <SelectSeparator />}
          {opciones?.map((o) => (
            <SelectItem key={o.id} value={String(o.id)}>
              {o.nombre}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {error && <FieldError>{error}</FieldError>}
    </Field>
  )
}
