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

/** Las listas que se mandan a la vez: la que no va, queda como estaba. */
export type Asignaciones = Schemas["AsignacionesUpdate"]

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
  /** Devuelve los avisos del borrado (un modelo que se quedó sin colores marcados). */
  eliminar: (slug: Slug, id: number) =>
    pedir<Schemas["BorradoRead"]>(`/catalogos/${slug}/${id}`, {
      method: "DELETE",
    }),
  /** Guarda los colores y las capacidades del modelo juntos: se graban los dos o ninguno. */
  asignar: (modeloId: number, cambios: Asignaciones) =>
    pedir<Modelo>(`/catalogos/modelos/${modeloId}/asignaciones`, {
      method: "PUT",
      body: cambios,
    }),
}
