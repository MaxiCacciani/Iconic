import { pedir, type Schemas } from "@/shared/api"

/** Lo que devuelve `GET /catalogos/{slug}` para cada catálogo. */
export type ItemPorCatalogo = {
  "tipos-categoria": Schemas["TipoCategoriaRead"]
  categorias: Schemas["CategoriaRead"]
  modelos: Schemas["ModeloRead"]
  capacidades: Schemas["ItemDeCategoriaRead"]
  colores: Schemas["ItemDeCategoriaRead"]
  proveedores: Schemas["ItemCatalogoRead"]
  defectos: Schemas["DefectoRead"]
  localidades: Schemas["ItemCatalogoRead"]
  diagnosticos: Schemas["ItemCatalogoRead"]
  "estados-reclamo": Schemas["EstadoReclamoRead"]
  "metodos-pago": Schemas["MetodoPagoRead"]
}

export type Slug = keyof ItemPorCatalogo
export type ItemCatalogo = ItemPorCatalogo[Slug]
export type TipoCategoria = ItemPorCatalogo["tipos-categoria"]
export type Categoria = ItemPorCatalogo["categorias"]
export type Modelo = ItemPorCatalogo["modelos"]

/** Lo que un modelo elige de su categoría. */
export type Asignable = "colores" | "capacidades"

/** Lo que se manda al crear o editar. Cada catálogo valida su forma en la API. */
export type DatosItem = Record<string, string | number | boolean>

export const catalogosApi = {
  listar: <S extends Slug>(
    slug: S,
    categoriaId?: number,
    signal?: AbortSignal
  ) =>
    pedir<ItemPorCatalogo[S][]>(
      `/catalogos/${slug}${categoriaId ? `?categoria_id=${categoriaId}` : ""}`,
      { signal }
    ),
  crear: (slug: Slug, datos: DatosItem) =>
    pedir<ItemCatalogo>(`/catalogos/${slug}`, { method: "POST", body: datos }),
  actualizar: (slug: Slug, id: number, cambios: DatosItem) =>
    pedir<ItemCatalogo>(`/catalogos/${slug}/${id}`, {
      method: "PATCH",
      body: cambios,
    }),
  eliminar: (slug: Slug, id: number) =>
    pedir<null>(`/catalogos/${slug}/${id}`, { method: "DELETE" }),
  /** Reemplaza los colores o capacidades del modelo. Vacío: ofrece todos los de su categoría. */
  asignar: (modeloId: number, que: Asignable, ids: number[]) =>
    pedir<Modelo>(`/catalogos/modelos/${modeloId}/${que}`, {
      method: "PUT",
      body: { ids },
    }),
}
