// Cómo se muestra cada catálogo. Solo textos y qué campos tiene el formulario:
// las reglas (repetidos, el predeterminado único, qué se puede borrar) las decide la API.
import type { ItemCatalogo, Slug } from "./api"

export type Interruptor = {
  campo: string
  etiqueta: string
  descripcion: string
  /** Lo que se muestra en la tabla cuando está activado. */
  insignia: string
}

export type DefinicionCatalogo = {
  slug: Slug
  titulo: string
  /** Para los textos: "modelo", "localidad". */
  singular: string
  /** "Nuevo modelo", "Nueva localidad". */
  nuevo: string
  grupo: "Productos" | "Clientes y reclamos" | "Ventas"
  descripcion: string
  campoTexto: "nombre" | "descripcion"
  etiquetaTexto: string
  /** Modelos, capacidades y colores: cada ítem es de una categoría. */
  porCategoria?: boolean
  /** Categorías: cada una es de un tipo. */
  conTipo?: boolean
  interruptores?: Interruptor[]
}

export const CATALOGOS: DefinicionCatalogo[] = [
  {
    slug: "categorias",
    titulo: "Categorías",
    singular: "categoría",
    nuevo: "Nueva categoría",
    grupo: "Productos",
    descripcion:
      "Cada producto del stock es de una categoría. El tipo define qué datos se le cargan.",
    campoTexto: "nombre",
    etiquetaTexto: "Nombre",
    conTipo: true,
  },
  {
    slug: "modelos",
    titulo: "Modelos",
    singular: "modelo",
    nuevo: "Nuevo modelo",
    grupo: "Productos",
    descripcion:
      "Los modelos que se eligen al cargar un producto de cada categoría.",
    campoTexto: "nombre",
    etiquetaTexto: "Nombre",
    porCategoria: true,
  },
  {
    slug: "capacidades",
    titulo: "Capacidades",
    singular: "capacidad",
    nuevo: "Nueva capacidad",
    grupo: "Productos",
    descripcion: "El almacenamiento de cada categoría: 128 GB, 256 GB, 1 TB.",
    campoTexto: "nombre",
    etiquetaTexto: "Nombre",
    porCategoria: true,
  },
  {
    slug: "colores",
    titulo: "Colores",
    singular: "color",
    nuevo: "Nuevo color",
    grupo: "Productos",
    descripcion:
      "Los colores de cada categoría, con el nombre que les da la marca.",
    campoTexto: "nombre",
    etiquetaTexto: "Nombre",
    porCategoria: true,
  },
  {
    slug: "proveedores",
    titulo: "Proveedores",
    singular: "proveedor",
    nuevo: "Nuevo proveedor",
    grupo: "Productos",
    descripcion:
      "De dónde viene cada producto. Los que entran por canje quedan con «Plan canje».",
    campoTexto: "nombre",
    etiquetaTexto: "Nombre",
  },
  {
    slug: "defectos",
    titulo: "Defectos",
    singular: "defecto",
    nuevo: "Nuevo defecto",
    grupo: "Productos",
    descripcion:
      "Los defectos comunes se ofrecen para elegir al cargar un producto usado.",
    campoTexto: "descripcion",
    etiquetaTexto: "Descripción",
    interruptores: [
      {
        campo: "es_comun",
        etiqueta: "Aparece en la lista",
        descripcion:
          "Se ofrece para elegir al cargar un producto. Si no, solo queda en los productos que ya lo tienen.",
        insignia: "En la lista",
      },
    ],
  },
  {
    slug: "tipos-categoria",
    titulo: "Tipos de categoría",
    singular: "tipo de categoría",
    nuevo: "Nuevo tipo",
    grupo: "Productos",
    descripcion:
      "Qué datos lleva cada producto según su categoría: IMEI, batería, controles o cantidad.",
    campoTexto: "nombre",
    etiquetaTexto: "Nombre",
    interruptores: [
      {
        campo: "usa_imei",
        etiqueta: "Lleva IMEI",
        descripcion: "Cada unidad se identifica con su IMEI de 15 dígitos.",
        insignia: "IMEI",
      },
      {
        campo: "usa_bateria",
        etiqueta: "Lleva batería",
        descripcion: "Se carga el porcentaje de batería de cada unidad.",
        insignia: "Batería",
      },
      {
        campo: "usa_controles",
        etiqueta: "Lleva controles",
        descripcion: "Se cargan la cantidad de controles (0 a 4) y los extras.",
        insignia: "Controles",
      },
      {
        campo: "por_cantidad",
        etiqueta: "Por cantidad",
        descripcion: "Varias unidades en una sola fila, como los accesorios.",
        insignia: "Por cantidad",
      },
    ],
  },
  {
    slug: "localidades",
    titulo: "Localidades",
    singular: "localidad",
    nuevo: "Nueva localidad",
    grupo: "Clientes y reclamos",
    descripcion: "Dónde vive cada cliente. Se elige en su ficha.",
    campoTexto: "nombre",
    etiquetaTexto: "Nombre",
  },
  {
    slug: "diagnosticos",
    titulo: "Diagnósticos",
    singular: "diagnóstico",
    nuevo: "Nuevo diagnóstico",
    grupo: "Clientes y reclamos",
    descripcion: "Qué falla tiene el equipo de un reclamo.",
    campoTexto: "nombre",
    etiquetaTexto: "Nombre",
  },
  {
    slug: "estados-reclamo",
    titulo: "Estados de reclamo",
    singular: "estado",
    nuevo: "Nuevo estado",
    grupo: "Clientes y reclamos",
    descripcion:
      "Cómo va cada reclamo, desde que se carga hasta que se resuelve.",
    campoTexto: "nombre",
    etiquetaTexto: "Nombre",
    interruptores: [
      {
        campo: "es_inicial",
        etiqueta: "Estado inicial",
        descripcion:
          "Cada reclamo nuevo arranca con este estado. Hay uno solo: si marcás este, se le saca al anterior.",
        insignia: "Inicial",
      },
    ],
  },
  {
    slug: "metodos-pago",
    titulo: "Métodos de pago",
    singular: "método de pago",
    nuevo: "Nuevo método",
    grupo: "Ventas",
    descripcion:
      "Cómo paga el cliente. El predeterminado viene elegido en cada venta.",
    campoTexto: "nombre",
    etiquetaTexto: "Nombre",
    interruptores: [
      {
        campo: "predeterminado",
        etiqueta: "Predeterminado",
        descripcion:
          "Viene elegido al registrar una venta. Hay uno solo: si marcás este, se le saca al anterior.",
        insignia: "Predeterminado",
      },
    ],
  },
]

export const CATALOGO_INICIAL: Slug = "categorias"

export function definicionDe(slug: string | null): DefinicionCatalogo {
  return (
    CATALOGOS.find((c) => c.slug === slug) ??
    CATALOGOS.find((c) => c.slug === CATALOGO_INICIAL)!
  )
}

/** Lee un campo de un ítem de cualquier catálogo. */
export function valorDe(item: ItemCatalogo, campo: string): unknown {
  return (item as Record<string, unknown>)[campo]
}
