import { FloppyDiskIcon, PlusIcon, XIcon } from "@phosphor-icons/react"
import { useRef, useState, type FormEvent, type KeyboardEvent } from "react"
import { Link } from "react-router"
import { toast } from "sonner"

import {
  useCatalogoQuery,
  useOpcionesDeModeloQuery,
} from "@/features/catalogos"
import { ApiError, mensajeDeError } from "@/shared/api"
import { Alert, AlertDescription } from "@/shared/ui/alert"
import { Badge } from "@/shared/ui/badge"
import { Button } from "@/shared/ui/button"
import { Checkbox } from "@/shared/ui/checkbox"
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSeparator,
  FieldSet,
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
import { Textarea } from "@/shared/ui/textarea"

import {
  tieneCostos,
  type Condicion,
  type DatosProducto,
  type Producto,
} from "../api"
import { useActualizarProducto, useCrearProducto } from "../queries"
import { CONDICION } from "./etiquetas"

type Props = {
  abierto: boolean
  onAbiertoChange: (abierto: boolean) => void
  /** Sin producto es un alta; con producto, una edición. */
  producto: Producto | null
  /** Cambia en cada apertura: el formulario arranca de nuevo. */
  apertura: number
}

const FORM_ID = "form-producto"
const NINGUNO = "ninguno"

type Borrador = {
  categoriaId: string
  modeloId: string
  capacidadId: string
  colorId: string
  proveedorId: string
  condicion: Condicion
  imei: string
  bateria: string
  controles: string
  extras: string
  cantidad: string
  precio: string
  costo: string
  defectoIds: number[]
  defectosNuevos: string[]
}

const limpio = (v: string) => (v.trim() === "" ? null : v.trim())
const idDe = (v: string) => (v && v !== NINGUNO ? Number(v) : null)
const texto = (v: number | string | null | undefined) =>
  v === null || v === undefined ? "" : String(v)

function borradorDe(p: Producto | null): Borrador {
  return {
    categoriaId: texto(p?.categoria.id),
    modeloId: texto(p?.modelo.id),
    capacidadId: p ? texto(p.capacidad?.id) || NINGUNO : "",
    colorId: p ? texto(p.color?.id) || NINGUNO : "",
    proveedorId: texto(p?.proveedor.id),
    condicion: p?.condicion ?? "nuevo",
    imei: texto(p?.imei),
    bateria: texto(p?.bateria),
    controles: texto(p?.controles),
    extras: texto(p?.extras),
    cantidad: texto(p?.cantidad ?? 1),
    // Los montos se muestran como se escriben acá: `1250,5`, no `1250.50`.
    precio: p ? Number(p.precio_usd).toString().replace(".", ",") : "",
    costo:
      p && tieneCostos(p) && p.costo_usd !== null
        ? Number(p.costo_usd).toString().replace(".", ",")
        : "",
    defectoIds: p?.defectos.map((d) => d.id) ?? [],
    defectosNuevos: [],
  }
}

export function ProductoSheet({
  abierto,
  onAbiertoChange,
  producto,
  apertura,
}: Props) {
  return (
    <Sheet open={abierto} onOpenChange={onAbiertoChange}>
      <SheetContent className="flex flex-col sm:max-w-lg">
        <Formulario
          key={`${producto?.id ?? "nuevo"}-${apertura}`}
          producto={producto}
          onCerrar={() => onAbiertoChange(false)}
        />
      </SheetContent>
    </Sheet>
  )
}

function Formulario({
  producto,
  onCerrar,
}: {
  producto: Producto | null
  onCerrar: () => void
}) {
  const [b, setB] = useState(() => borradorDe(producto))
  const [defectoEscrito, setDefectoEscrito] = useState("")
  const formRef = useRef<HTMLFormElement>(null)
  // Si la API marca un campo, se lleva la vista hasta él (puede estar más abajo o arriba).
  const mostrarError = () =>
    requestAnimationFrame(() =>
      formRef.current
        ?.querySelector<HTMLElement>("[aria-invalid=true]")
        ?.scrollIntoView({ block: "center", behavior: "smooth" })
    )
  const cambiar = (cambios: Partial<Borrador>) =>
    setB((actual) => ({ ...actual, ...cambios }))

  const categoriaId = Number(b.categoriaId) || undefined
  const modeloId = Number(b.modeloId) || undefined
  const categorias = useCatalogoQuery("categorias")
  const tipos = useCatalogoQuery("tipos-categoria")
  const proveedores = useCatalogoQuery("proveedores")
  const defectos = useCatalogoQuery("defectos")
  const modelos = useCatalogoQuery("modelos", categoriaId, {
    habilitado: categoriaId !== undefined,
  })
  // Lo que se ofrece depende del modelo: sus colores y capacidades, o los de la categoría.
  const capacidades = useOpcionesDeModeloQuery("capacidades", modeloId)
  const colores = useOpcionesDeModeloQuery("colores", modeloId)

  const crear = useCrearProducto()
  const actualizar = useActualizarProducto()
  const mutacion = producto ? actualizar : crear

  // Qué datos se piden sale del tipo de la categoría, tal como lo guarda el catálogo.
  const categoria = categorias.data?.find((c) => c.id === categoriaId)
  const tipo = tipos.data?.find((t) => t.id === categoria?.tipo_categoria_id)
  const conCostos = !producto || tieneCostos(producto)

  const campos = mutacion.error instanceof ApiError ? mutacion.error.campos : {}
  const errorGeneral =
    mutacion.error && Object.keys(campos).length === 0
      ? mensajeDeError(mutacion.error)
      : null
  const invalido = (campo: string) => (campos[campo] ? true : undefined)
  const error = (campo: string) =>
    campos[campo] ? <FieldError>{campos[campo]}</FieldError> : null

  const opcionesDefectos =
    defectos.data?.filter((d) => d.es_comun || b.defectoIds.includes(d.id)) ??
    []

  function agregarDefecto() {
    const nuevo = defectoEscrito.trim()
    if (!nuevo) return
    if (!b.defectosNuevos.some((d) => d.toLowerCase() === nuevo.toLowerCase()))
      cambiar({ defectosNuevos: [...b.defectosNuevos, nuevo] })
    setDefectoEscrito("")
  }

  function alEscribirDefecto(evento: KeyboardEvent<HTMLInputElement>) {
    // Enter agrega el defecto en vez de enviar el formulario.
    if (evento.key === "Enter") {
      evento.preventDefault()
      agregarDefecto()
    }
  }

  function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    // Lo que el tipo no lleva va en null; si quedó algo escrito, no se manda.
    const datos: DatosProducto = {
      modelo_id: idDe(b.modeloId),
      capacidad_id: idDe(b.capacidadId),
      color_id: idDe(b.colorId),
      proveedor_id: idDe(b.proveedorId),
      condicion: b.condicion,
      imei: tipo?.usa_imei ? limpio(b.imei) : null,
      bateria: tipo?.usa_bateria ? limpio(b.bateria) : null,
      controles: tipo?.usa_controles ? limpio(b.controles) : null,
      extras: tipo?.usa_controles ? limpio(b.extras) : null,
      cantidad: tipo?.por_cantidad ? limpio(b.cantidad) : 1,
      precio_usd: limpio(b.precio),
      costo_usd: limpio(b.costo),
      defecto_ids: b.defectoIds,
      defectos_nuevos: [
        ...b.defectosNuevos,
        // Lo que quedó escrito sin apretar "Agregar" también cuenta.
        ...(defectoEscrito.trim() ? [defectoEscrito.trim()] : []),
      ],
    }
    const nombre =
      modelos.data?.find((m) => m.id === modeloId)?.nombre ?? "el producto"

    if (producto) {
      actualizar.mutate(
        { id: producto.id, datos },
        {
          onSuccess: () => {
            toast.success(
              `Se guardaron los cambios del producto #${producto.id}.`
            )
            onCerrar()
          },
          onError: mostrarError,
        }
      )
    } else {
      // En el alta, lo vacío no se manda: la API responde "Este campo es obligatorio."
      const alta = Object.fromEntries(
        Object.entries(datos).filter(([, v]) => v !== null)
      )
      crear.mutate(alta, {
        onSuccess: (nuevo) => {
          toast.success(`Se cargó ${nombre} como producto #${nuevo.id}.`)
          onCerrar()
        },
        onError: mostrarError,
      })
    }
  }

  return (
    <>
      <SheetHeader>
        <SheetTitle className="font-heading text-2xl">
          {producto ? `Editar producto #${producto.id}` : "Cargar producto"}
        </SheetTitle>
        <SheetDescription>
          {producto
            ? `${producto.categoria.nombre} ${producto.modelo.nombre}.`
            : "Los datos que se piden dependen de la categoría."}
        </SheetDescription>
      </SheetHeader>

      <form
        ref={formRef}
        id={FORM_ID}
        onSubmit={enviar}
        noValidate
        className="flex-1 overflow-y-auto px-4"
      >
        <FieldGroup>
          <FieldSet>
            <FieldLegend>Equipo</FieldLegend>
            <FieldGroup>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field>
                  <FieldLabel htmlFor="producto-categoria">
                    Categoría
                  </FieldLabel>
                  <Select
                    value={b.categoriaId}
                    onValueChange={(v) =>
                      cambiar({
                        categoriaId: v,
                        modeloId: "",
                        capacidadId: NINGUNO,
                        colorId: NINGUNO,
                      })
                    }
                    disabled={categorias.isPending}
                  >
                    <SelectTrigger id="producto-categoria" className="w-full">
                      <SelectValue placeholder="Elegí una categoría" />
                    </SelectTrigger>
                    <SelectContent>
                      {categorias.data?.map((c) => (
                        <SelectItem key={c.id} value={String(c.id)}>
                          {c.nombre}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </Field>

                <Field data-invalid={invalido("modelo_id")}>
                  <FieldLabel htmlFor="producto-modelo">Modelo</FieldLabel>
                  <Select
                    value={b.modeloId}
                    onValueChange={(v) =>
                      cambiar({
                        modeloId: v,
                        capacidadId: NINGUNO,
                        colorId: NINGUNO,
                      })
                    }
                    disabled={!categoriaId || modelos.isPending}
                  >
                    <SelectTrigger
                      id="producto-modelo"
                      className="w-full"
                      aria-invalid={invalido("modelo_id")}
                    >
                      <SelectValue
                        placeholder={
                          categoriaId
                            ? "Elegí un modelo"
                            : "Primero la categoría"
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
                  id="producto-capacidad"
                  etiqueta="Capacidad"
                  ninguna="Sin capacidad"
                  valor={b.capacidadId}
                  onCambiar={(v) => cambiar({ capacidadId: v })}
                  opciones={capacidades.data}
                  habilitado={Boolean(modeloId)}
                  error={campos.capacidad_id}
                />
                <OpcionDeModelo
                  id="producto-color"
                  etiqueta="Color"
                  ninguna="Sin color"
                  valor={b.colorId}
                  onCambiar={(v) => cambiar({ colorId: v })}
                  opciones={colores.data}
                  habilitado={Boolean(modeloId)}
                  error={campos.color_id}
                />
              </div>

              {tipo?.usa_imei && (
                <Field data-invalid={invalido("imei")}>
                  <FieldLabel htmlFor="producto-imei">IMEI</FieldLabel>
                  <Input
                    id="producto-imei"
                    inputMode="numeric"
                    autoComplete="off"
                    spellCheck={false}
                    maxLength={15}
                    className="font-mono tracking-wide"
                    value={b.imei}
                    onChange={(e) => cambiar({ imei: e.target.value })}
                    aria-invalid={invalido("imei")}
                  />
                  <FieldDescription>
                    Los 15 dígitos, sin espacios.
                  </FieldDescription>
                  {error("imei")}
                </Field>
              )}

              {(tipo?.usa_bateria || tipo?.por_cantidad) && (
                <div className="grid gap-4 sm:grid-cols-2">
                  {tipo.usa_bateria && (
                    <Field data-invalid={invalido("bateria")}>
                      <FieldLabel htmlFor="producto-bateria">
                        Batería (opcional)
                      </FieldLabel>
                      <InputGroup>
                        <InputGroupInput
                          id="producto-bateria"
                          inputMode="numeric"
                          autoComplete="off"
                          value={b.bateria}
                          onChange={(e) => cambiar({ bateria: e.target.value })}
                          aria-invalid={invalido("bateria")}
                        />
                        <InputGroupAddon align="inline-end">
                          <InputGroupText>%</InputGroupText>
                        </InputGroupAddon>
                      </InputGroup>
                      {error("bateria")}
                    </Field>
                  )}
                  {tipo.por_cantidad && (
                    <Field data-invalid={invalido("cantidad")}>
                      <FieldLabel htmlFor="producto-cantidad">
                        Cantidad
                      </FieldLabel>
                      <Input
                        id="producto-cantidad"
                        inputMode="numeric"
                        autoComplete="off"
                        value={b.cantidad}
                        onChange={(e) => cambiar({ cantidad: e.target.value })}
                        aria-invalid={invalido("cantidad")}
                      />
                      <FieldDescription>
                        Unidades en esta fila.
                      </FieldDescription>
                      {error("cantidad")}
                    </Field>
                  )}
                </div>
              )}

              {tipo?.usa_controles && (
                <>
                  <Field data-invalid={invalido("controles")}>
                    <FieldLabel htmlFor="producto-controles">
                      Controles
                    </FieldLabel>
                    <Input
                      id="producto-controles"
                      inputMode="numeric"
                      autoComplete="off"
                      className="sm:w-32"
                      value={b.controles}
                      onChange={(e) => cambiar({ controles: e.target.value })}
                      aria-invalid={invalido("controles")}
                    />
                    <FieldDescription>De 0 a 4.</FieldDescription>
                    {error("controles")}
                  </Field>
                  <Field data-invalid={invalido("extras")}>
                    <FieldLabel htmlFor="producto-extras">
                      Extras (opcional)
                    </FieldLabel>
                    <Textarea
                      id="producto-extras"
                      rows={2}
                      placeholder="Caja original, juegos, cables…"
                      value={b.extras}
                      onChange={(e) => cambiar({ extras: e.target.value })}
                      aria-invalid={invalido("extras")}
                    />
                    {error("extras")}
                  </Field>
                </>
              )}

              <Field data-invalid={invalido("condicion")}>
                <FieldLabel id="producto-condicion">Condición</FieldLabel>
                <RadioGroup
                  aria-labelledby="producto-condicion"
                  value={b.condicion}
                  onValueChange={(v) => cambiar({ condicion: v as Condicion })}
                  className="flex gap-6"
                >
                  {(Object.keys(CONDICION) as Condicion[]).map((c) => (
                    <Field key={c} orientation="horizontal" className="w-auto">
                      <RadioGroupItem
                        value={c}
                        id={`producto-condicion-${c}`}
                      />
                      <FieldLabel
                        htmlFor={`producto-condicion-${c}`}
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

              <Field data-invalid={invalido("proveedor_id")}>
                <FieldLabel htmlFor="producto-proveedor">Proveedor</FieldLabel>
                <Select
                  value={b.proveedorId}
                  onValueChange={(v) => cambiar({ proveedorId: v })}
                  disabled={proveedores.isPending}
                >
                  <SelectTrigger
                    id="producto-proveedor"
                    className="w-full"
                    aria-invalid={invalido("proveedor_id")}
                  >
                    <SelectValue placeholder="Elegí un proveedor" />
                  </SelectTrigger>
                  <SelectContent>
                    {proveedores.data?.map((p) => (
                      <SelectItem key={p.id} value={String(p.id)}>
                        {p.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {error("proveedor_id")}
              </Field>
            </FieldGroup>
          </FieldSet>

          <FieldSeparator />

          <FieldSet>
            <FieldLegend>Precio</FieldLegend>
            <div className="grid gap-4 sm:grid-cols-2">
              <Monto
                id="producto-precio"
                etiqueta="Precio de venta"
                valor={b.precio}
                onCambiar={(v) => cambiar({ precio: v })}
                error={campos.precio_usd}
              />
              {conCostos && (
                <Monto
                  id="producto-costo"
                  etiqueta="Costo (opcional)"
                  valor={b.costo}
                  onCambiar={(v) => cambiar({ costo: v })}
                  error={campos.costo_usd}
                />
              )}
            </div>
          </FieldSet>

          <FieldSeparator />

          <FieldSet>
            <FieldLegend>Defectos</FieldLegend>
            <FieldDescription>
              Marcá los de la lista o escribí uno que no esté.
            </FieldDescription>
            <FieldGroup className="gap-3">
              {opcionesDefectos.map((d) => (
                <Field key={d.id} orientation="horizontal">
                  <Checkbox
                    id={`producto-defecto-${d.id}`}
                    checked={b.defectoIds.includes(d.id)}
                    onCheckedChange={(marcado) =>
                      cambiar({
                        defectoIds: marcado
                          ? [...b.defectoIds, d.id]
                          : b.defectoIds.filter((x) => x !== d.id),
                      })
                    }
                  />
                  <FieldLabel
                    htmlFor={`producto-defecto-${d.id}`}
                    className="font-normal"
                  >
                    {d.descripcion}
                  </FieldLabel>
                </Field>
              ))}
              {error("defecto_ids")}

              {b.defectosNuevos.length > 0 && (
                <ul
                  className="flex flex-wrap gap-2"
                  aria-label="Defectos escritos"
                >
                  {b.defectosNuevos.map((d) => (
                    <li key={d}>
                      <Badge variant="secondary" className="gap-1 pr-1">
                        {d}
                        <button
                          type="button"
                          className="rounded-sm p-0.5 hover:bg-background/60 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
                          aria-label={`Quitar «${d}»`}
                          onClick={() =>
                            cambiar({
                              defectosNuevos: b.defectosNuevos.filter(
                                (x) => x !== d
                              ),
                            })
                          }
                        >
                          <XIcon className="size-3" />
                        </button>
                      </Badge>
                    </li>
                  ))}
                </ul>
              )}

              <Field data-invalid={invalido("defectos_nuevos")}>
                <FieldLabel
                  htmlFor="producto-defecto-nuevo"
                  className="sr-only"
                >
                  Otro defecto
                </FieldLabel>
                <div className="flex gap-2">
                  <Input
                    id="producto-defecto-nuevo"
                    placeholder="Otro defecto…"
                    autoComplete="off"
                    value={defectoEscrito}
                    onChange={(e) => setDefectoEscrito(e.target.value)}
                    onKeyDown={alEscribirDefecto}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={agregarDefecto}
                    disabled={!defectoEscrito.trim()}
                  >
                    <PlusIcon />
                    Agregar
                  </Button>
                </div>
                {error("defectos_nuevos")}
              </Field>
            </FieldGroup>
          </FieldSet>

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
            : producto
              ? "Guardar cambios"
              : "Cargar producto"}
        </Button>
      </SheetFooter>
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

function Monto({
  id,
  etiqueta,
  valor,
  onCambiar,
  error,
}: {
  id: string
  etiqueta: string
  valor: string
  onCambiar: (valor: string) => void
  error?: string
}) {
  return (
    <Field data-invalid={error ? true : undefined}>
      <FieldLabel htmlFor={id}>{etiqueta}</FieldLabel>
      <InputGroup>
        <InputGroupAddon>
          <InputGroupText>US$</InputGroupText>
        </InputGroupAddon>
        <InputGroupInput
          id={id}
          inputMode="decimal"
          autoComplete="off"
          placeholder="1.250"
          className="tabular-nums"
          value={valor}
          onChange={(e) => onCambiar(e.target.value)}
          aria-invalid={error ? true : undefined}
        />
      </InputGroup>
      {error && <FieldError>{error}</FieldError>}
    </Field>
  )
}
