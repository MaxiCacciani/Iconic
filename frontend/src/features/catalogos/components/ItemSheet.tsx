import { FloppyDiskIcon } from "@phosphor-icons/react"
import { useEffect, type FormEvent } from "react"
import { toast } from "sonner"

import { ApiError, mensajeDeError } from "@/shared/api"
import { Alert, AlertDescription } from "@/shared/ui/alert"
import { Button } from "@/shared/ui/button"
import {
  Field,
  FieldContent,
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
import { Switch } from "@/shared/ui/switch"

import type { Categoria, DatosItem, ItemCatalogo, TipoCategoria } from "../api"
import { valorDe, type DefinicionCatalogo } from "../catalogos"
import { useActualizarItem, useCrearItem } from "../queries"

type Props = {
  abierto: boolean
  onAbiertoChange: (abierto: boolean) => void
  definicion: DefinicionCatalogo
  /** Sin ítem es un alta; con ítem, una edición. */
  item: ItemCatalogo | null
  categorias: Categoria[]
  /** La categoría que se está mirando: viene elegida en el alta. */
  categoriaInicial?: number
  tipos: TipoCategoria[]
}

const FORM_ID = "form-catalogo"

export function ItemSheet({
  abierto,
  onAbiertoChange,
  definicion: d,
  item,
  categorias,
  categoriaInicial,
  tipos,
}: Props) {
  const crear = useCrearItem(d.slug)
  const actualizar = useActualizarItem(d.slug)
  const mutacion = item ? actualizar : crear
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
  const invalido = (campo: string) => (campos[campo] ? true : undefined)

  const categoriaDelItem = item
    ? categorias.find((c) => c.id === valorDe(item, "categoria_id"))?.nombre
    : undefined

  const alTerminar = (mensaje: string) => () => {
    toast.success(mensaje)
    onAbiertoChange(false)
  }

  function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const form = new FormData(evento.currentTarget)
    const texto = String(form.get(d.campoTexto) ?? "")
    const datos: DatosItem = { [d.campoTexto]: texto }

    const elegido = (campo: string) => {
      const valor = String(form.get(campo) ?? "")
      if (valor) datos[campo] = Number(valor)
    }
    if (d.porCategoria && !item) elegido("categoria_id")
    if (d.conTipo) elegido("tipo_categoria_id")
    for (const i of d.interruptores ?? []) datos[i.campo] = form.has(i.campo)

    if (item) {
      actualizar.mutate(
        { id: item.id, cambios: datos },
        { onSuccess: alTerminar(`Se guardó «${texto.trim()}».`) }
      )
    } else {
      crear.mutate(datos, {
        onSuccess: alTerminar(`Se agregó «${texto.trim()}».`),
      })
    }
  }

  return (
    <Sheet open={abierto} onOpenChange={onAbiertoChange}>
      <SheetContent className="flex flex-col sm:max-w-md">
        <SheetHeader>
          <SheetTitle className="font-heading text-2xl">
            {item ? `Editar ${d.singular}` : d.nuevo}
          </SheetTitle>
          <SheetDescription>
            {item
              ? d.porCategoria
                ? `Categoría: ${categoriaDelItem ?? "—"}. No se puede cambiar.`
                : "El cambio se ve en todas las pantallas que usan esta lista."
              : d.descripcion}
          </SheetDescription>
        </SheetHeader>

        <form
          id={FORM_ID}
          key={`${d.slug}-${item?.id ?? "nuevo"}`}
          onSubmit={enviar}
          noValidate
          className="flex-1 overflow-y-auto px-4"
        >
          <FieldGroup>
            {d.porCategoria && !item && (
              <Field data-invalid={invalido("categoria_id")}>
                <FieldLabel htmlFor="catalogo-categoria">Categoría</FieldLabel>
                <Select
                  name="categoria_id"
                  defaultValue={
                    categoriaInicial ? String(categoriaInicial) : undefined
                  }
                >
                  <SelectTrigger
                    id="catalogo-categoria"
                    className="w-full"
                    aria-invalid={invalido("categoria_id")}
                  >
                    <SelectValue placeholder="Elegí una categoría" />
                  </SelectTrigger>
                  <SelectContent>
                    {categorias.map((c) => (
                      <SelectItem key={c.id} value={String(c.id)}>
                        {c.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {campos.categoria_id && (
                  <FieldError>{campos.categoria_id}</FieldError>
                )}
              </Field>
            )}

            <Field data-invalid={invalido(d.campoTexto)}>
              <FieldLabel htmlFor="catalogo-texto">
                {d.etiquetaTexto}
              </FieldLabel>
              <Input
                id="catalogo-texto"
                name={d.campoTexto}
                autoComplete="off"
                defaultValue={
                  item ? String(valorDe(item, d.campoTexto)) : undefined
                }
                aria-invalid={invalido(d.campoTexto)}
              />
              {campos[d.campoTexto] && (
                <FieldError>{campos[d.campoTexto]}</FieldError>
              )}
            </Field>

            {d.conTipo && (
              <Field data-invalid={invalido("tipo_categoria_id")}>
                <FieldLabel htmlFor="catalogo-tipo">Tipo</FieldLabel>
                <Select
                  name="tipo_categoria_id"
                  defaultValue={
                    item
                      ? String(valorDe(item, "tipo_categoria_id"))
                      : undefined
                  }
                >
                  <SelectTrigger
                    id="catalogo-tipo"
                    className="w-full"
                    aria-invalid={invalido("tipo_categoria_id")}
                  >
                    <SelectValue placeholder="Elegí un tipo" />
                  </SelectTrigger>
                  <SelectContent>
                    {tipos.map((t) => (
                      <SelectItem key={t.id} value={String(t.id)}>
                        {t.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FieldDescription>
                  Define qué datos se cargan en sus productos: IMEI, batería,
                  controles o cantidad.
                </FieldDescription>
                {campos.tipo_categoria_id && (
                  <FieldError>{campos.tipo_categoria_id}</FieldError>
                )}
              </Field>
            )}

            {d.interruptores?.map((i) => (
              <Field
                key={i.campo}
                orientation="horizontal"
                data-invalid={invalido(i.campo)}
              >
                <FieldContent>
                  <FieldLabel htmlFor={`catalogo-${i.campo}`}>
                    {i.etiqueta}
                  </FieldLabel>
                  <FieldDescription>{i.descripcion}</FieldDescription>
                  {campos[i.campo] && (
                    <FieldError>{campos[i.campo]}</FieldError>
                  )}
                </FieldContent>
                <Switch
                  id={`catalogo-${i.campo}`}
                  name={i.campo}
                  defaultChecked={
                    item
                      ? valorDe(item, i.campo) === true
                      : // Lo que se agrega a mano en defectos es para elegirlo después.
                        i.campo === "es_comun"
                  }
                  aria-invalid={invalido(i.campo)}
                />
              </Field>
            ))}

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
              : item
                ? "Guardar cambios"
                : "Agregar"}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}
