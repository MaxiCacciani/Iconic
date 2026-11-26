export { ProductosPage } from "./pages/ProductosPage"
// Para los packs y la venta: elegir un producto disponible del stock.
export {
  BuscadorProducto,
  type ProductoElegido,
} from "./components/BuscadorProducto"
export { CONDICION, ESTADO, variante } from "./components/etiquetas"
// Para el canje de la venta: los datos del equipo que entrega el cliente.
export {
  CamposEquipo,
  datosDeEquipo,
  EQUIPO_VACIO,
  useTipoDeCategoria,
  type Equipo,
} from "./components/CamposEquipo"
export { productosKeys } from "./queries"
export { tieneCostos } from "./api"
export type { Producto, EstadoProducto } from "./api"
