import { FloppyDiskIcon, PlusIcon, TrashIcon } from "@phosphor-icons/react"
import { useEffect, useState, type FormEvent } from "react"
import { toast } from "sonner"

import { useCatalogoQuery } from "@/features/catalogos"
import { BuscadorProducto, type ProductoElegido } from "@/features/productos"
import { ApiError, mensajeDeError } from "@/shared/api"
import { Alert, AlertDescription } from "@/shared/ui/alert"
import { Button } from "@/shared/ui/button"
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
import { RadioGroup, RadioGroupItem } from "@/shared/ui/radio-group"
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
import { Switch } from "@/shared/ui/switch"
import { Textarea } from "@/shared/ui/textarea"

import type { DatosPack, Pack } from "../api"
import { useActualizarPack, useCrearPack } from "../queries"

type Props = {
  abierto: boolean
  onAbiertoChange: (abierto: boolean) => void
  /** Sin pack es un alta; con pack, una edición. */
  pack: Pack | null
  /** Cambia en cada apertura, así el formulario arranca de cero. */
  apertura: number
}

type Tipo = "categoria" | "producto"

/** Lo que el usuario va cargando en cada ítem, tal cual. Lo valida la API al guardar. */
type ItemForm = {
  clave: number
  tipo: Tipo
  categoriaId: string
  producto: ProductoElegido | null
  cantidad: string
  esRegalo: boolean
}

const FORM_ID = "form-pack"

let siguienteClave = 0
function itemVacio(): ItemForm {
  return {
    clave: siguienteClave++,
    tipo: "categoria",
    categoriaId: "",
    producto: null,
    cantidad: "1",
    esRegalo: false,
  }
}

function itemsDe(pack: Pack | null): ItemForm[] {
  if (!pack || pack.items.length === 0) return [itemVacio()]
  return pack.items.map((i) => ({
    clave: siguienteClave++,
    tipo: i.producto ? "producto" : "categoria",
    categoriaId: i.categoria ? String(i.categoria.id) : "",
    producto: i.producto,
    cantidad: String(i.cantidad),
    esRegalo: i.es_regalo,
  }))
}

export function PackSheet({ abierto, onAbiertoChange, pack, apertura }: Props) {
  return (
    <Sheet open={abierto} onOpenChange={onAbiertoChange}>
      <SheetContent className="flex flex-col sm:max-w-xl">
        <SheetHeader>
          <SheetTitle className="font-heading text-2xl">
            {pack ? "Editar pack" : "Nuevo pack"}
          </SheetTitle>
          <SheetDescription>
            Cada ítem es un producto puntual del stock o una categoría. Con una
            categoría, al armar la venta se toma el primer producto disponible,
            sin repetir equipos.
          </SheetDescription>
        </SheetHeader>
        <Formulario
          key={`${pack?.id ?? "nuevo"}-${apertura}`}
          pack={pack}
          abierto={abierto}
          onGuardado={() => onAbiertoChange(false)}
        />
      </SheetContent>
    </Sheet>
  )
}

function Formulario({
  pack,
  abierto,
  onGuardado,
}: {
  pack: Pack | null
  abierto: boolean
  onGuardado: () => void
}) {
  const crear = useCrearPack()
  const actualizar = useActualizarPack()
  const mutacion = pack ? actualizar : crear
  const { reset } = mutacion
  const categorias = useCatalogoQuery("categorias", undefined, {
    habilitado: abierto,
  })
  const [items, setItems] = useState(() => itemsDe(pack))

  useEffect(() => {
    if (abierto) reset()
  }, [abierto, reset])

  const campos = mutacion.error instanceof ApiError ? mutacion.error.campos : {}
  const errorGeneral =
    mutacion.error && Object.keys(campos).length === 0
      ? mensajeDeError(mutacion.error)
      : null
  const invalido = (campo: string) => (campos[campo] ? true : undefined)

  function cambiar(clave: number, cambios: Partial<ItemForm>) {
    setItems((actuales) =>
      actuales.map((i) => (i.clave === clave ? { ...i, ...cambios } : i))
    )
  }

  // Los errores vienen por posición (`items.2.cantidad`): al sumar o sacar un ítem ya
  // no corresponden, así que se limpian.
  function agregar() {
    reset()
    setItems((actuales) => [...actuales, itemVacio()])
  }
  function quitar(clave: number) {
    reset()
    setItems((actuales) => actuales.filter((i) => i.clave !== clave))
  }

  function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const form = new FormData(evento.currentTarget)
    const descripcion = String(form.get("descripcion") ?? "").trim()
    const datos: DatosPack = {
      nombre: String(form.get("nombre") ?? ""),
      descripcion: descripcion || null,
      items: items.map((i) => ({
        producto_id: i.tipo === "producto" ? (i.producto?.id ?? null) : null,
        categoria_id:
          i.tipo === "categoria" && i.categoriaId
            ? Number(i.categoriaId)
            : null,
        cantidad: i.cantidad.trim(),
        es_regalo: i.esRegalo,
      })),
    }
    const alTerminar = (guardado: Pack) => {
      toast.success(
        pack
          ? `Se guardaron los cambios de «${guardado.nombre}».`
          : `Se creó el pack «${guardado.nombre}».`
      )
      onGuardado()
    }
    if (pack)
      actualizar.mutate({ id: pack.id, datos }, { onSuccess: alTerminar })
    else crear.mutate(datos, { onSuccess: alTerminar })
  }

  return (
    <>
      <form
        id={FORM_ID}
        onSubmit={enviar}
        noValidate
        className="flex-1 overflow-y-auto px-4"
      >
        <FieldGroup>
          <Field data-invalid={invalido("nombre")}>
            <FieldLabel htmlFor="pack-nombre">Nombre</FieldLabel>
            <Input
              id="pack-nombre"
              name="nombre"
              autoComplete="off"
              placeholder="iPhone + accesorios de regalo"
              defaultValue={pack?.nombre ?? ""}
              aria-invalid={invalido("nombre")}
            />
            {campos.nombre && <FieldError>{campos.nombre}</FieldError>}
          </Field>

          <Field data-invalid={invalido("descripcion")}>
            <FieldLabel htmlFor="pack-descripcion">Descripción</FieldLabel>
            <Textarea
              id="pack-descripcion"
              name="descripcion"
              rows={2}
              defaultValue={pack?.descripcion ?? ""}
              aria-invalid={invalido("descripcion")}
            />
            <FieldDescription>Opcional.</FieldDescription>
            {campos.descripcion && (
              <FieldError>{campos.descripcion}</FieldError>
            )}
          </Field>

          <FieldSet>
            <FieldLegend>Qué lleva</FieldLegend>
            <ol className="flex flex-col gap-3">
              {items.map((item, n) => (
                <FilaItem
                  key={item.clave}
                  item={item}
                  posicion={n}
                  categorias={categorias.data ?? []}
                  cargandoCategorias={categorias.isPending}
                  campos={campos}
                  puedeQuitar={items.length > 1}
                  onCambiar={(cambios) => cambiar(item.clave, cambios)}
                  onQuitar={() => quitar(item.clave)}
                />
              ))}
            </ol>
            {campos.items && <FieldError>{campos.items}</FieldError>}
            <Button
              type="button"
              variant="outline"
              className="self-start"
              onClick={agregar}
            >
              <PlusIcon />
              Agregar ítem
            </Button>
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
            : pack
              ? "Guardar cambios"
              : "Crear pack"}
        </Button>
      </SheetFooter>
    </>
  )
}

type PropsFila = {
  item: ItemForm
  posicion: number
  categorias: { id: number; nombre: string }[]
  cargandoCategorias: boolean
  campos: Record<string, string>
  puedeQuitar: boolean
  onCambiar: (cambios: Partial<ItemForm>) => void
  onQuitar: () => void
}

function FilaItem({
  item,
  posicion,
  categorias,
  cargandoCategorias,
  campos,
  puedeQuitar,
  onCambiar,
  onQuitar,
}: PropsFila) {
  const base = `pack-item-${item.clave}`
  const ruta = `items.${posicion}`
  // "Producto o categoría" viene en el ítem; el resto, en su campo.
  const errorEleccion =
    campos[ruta] ??
    campos[
      `${ruta}.${item.tipo === "producto" ? "producto_id" : "categoria_id"}`
    ]
  const errorCantidad = campos[`${ruta}.cantidad`]
  const numero = posicion + 1

  return (
    <li className="flex flex-col gap-3 rounded-lg border p-3">
      <div className="flex items-center justify-between gap-3">
        <RadioGroup
          aria-label={`Tipo del ítem ${numero}`}
          value={item.tipo}
          onValueChange={(v) => onCambiar({ tipo: v as Tipo })}
          className="flex gap-5"
        >
          <Field orientation="horizontal" className="w-auto">
            <RadioGroupItem value="categoria" id={`${base}-categoria`} />
            <FieldLabel htmlFor={`${base}-categoria`} className="font-normal">
              Categoría
            </FieldLabel>
          </Field>
          <Field orientation="horizontal" className="w-auto">
            <RadioGroupItem value="producto" id={`${base}-producto`} />
            <FieldLabel htmlFor={`${base}-producto`} className="font-normal">
              Producto puntual
            </FieldLabel>
          </Field>
        </RadioGroup>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={onQuitar}
          disabled={!puedeQuitar}
          aria-label={`Quitar el ítem ${numero}`}
        >
          <TrashIcon />
        </Button>
      </div>

      <Field data-invalid={errorEleccion ? true : undefined}>
        <FieldLabel htmlFor={`${base}-eleccion`} className="sr-only">
          {item.tipo === "producto"
            ? `Producto del ítem ${numero}`
            : `Categoría del ítem ${numero}`}
        </FieldLabel>
        {item.tipo === "producto" ? (
          <BuscadorProducto
            id={`${base}-eleccion`}
            producto={item.producto}
            onElegir={(producto) => onCambiar({ producto })}
            invalido={errorEleccion ? true : undefined}
          />
        ) : (
          <Select
            value={item.categoriaId}
            onValueChange={(categoriaId) => onCambiar({ categoriaId })}
            disabled={cargandoCategorias}
          >
            <SelectTrigger
              id={`${base}-eleccion`}
              className="w-full"
              aria-invalid={errorEleccion ? true : undefined}
            >
              <SelectValue
                placeholder={
                  cargandoCategorias ? "Cargando…" : "Elegí una categoría"
                }
              />
            </SelectTrigger>
            <SelectContent>
              {categorias.map((c) => (
                <SelectItem key={c.id} value={String(c.id)}>
                  {c.nombre}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
        {errorEleccion && <FieldError>{errorEleccion}</FieldError>}
      </Field>

      <div className="flex flex-wrap items-start gap-x-6 gap-y-3">
        <Field
          orientation="horizontal"
          className="w-auto"
          data-invalid={errorCantidad ? true : undefined}
        >
          <FieldLabel htmlFor={`${base}-cantidad`} className="font-normal">
            Cantidad
          </FieldLabel>
          <Input
            id={`${base}-cantidad`}
            inputMode="numeric"
            autoComplete="off"
            className="w-20 tabular-nums"
            value={item.cantidad}
            onChange={(e) => onCambiar({ cantidad: e.target.value })}
            aria-invalid={errorCantidad ? true : undefined}
          />
        </Field>
        <Field orientation="horizontal" className="w-auto">
          <Switch
            id={`${base}-regalo`}
            checked={item.esRegalo}
            onCheckedChange={(esRegalo) => onCambiar({ esRegalo })}
          />
          <FieldLabel htmlFor={`${base}-regalo`} className="font-normal">
            Regalo (US$ 0)
          </FieldLabel>
        </Field>
      </div>
      {errorCantidad && <FieldError>{errorCantidad}</FieldError>}
    </li>
  )
}
