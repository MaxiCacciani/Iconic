export { CatalogosPage } from "./pages/CatalogosPage"
// Para las fases que eligen de un catálogo (productos, clientes, ventas, reclamos).
export {
  catalogosKeys,
  useCatalogoQuery,
  useOpcionesDeModeloQuery,
} from "./queries"
export type { ItemPorCatalogo, Slug as SlugCatalogo } from "./api"
