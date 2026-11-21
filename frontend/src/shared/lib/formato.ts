// Solo formateo para mostrar. Los montos y fechas ya vienen calculados del backend.

const entero = new Intl.NumberFormat("es-AR", { maximumFractionDigits: 0 })
const conCentavos = new Intl.NumberFormat("es-AR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

/** Sin centavos no muestra decimales; con centavos, siempre dos (`1.180,50`, no `1.180,5`). */
function numero(monto: number | string): string {
  const valor = Number(monto)
  return (Number.isInteger(valor) ? entero : conCentavos).format(valor)
}

/** `1250` o `"1250.00"` → `US$ 1.250` */
export function formatearUSD(monto: number | string): string {
  return `US$ ${numero(monto)}`
}

/** `1250000` → `$ 1.250.000`; `"1180.5"` → `$ 1.180,50` */
export function formatearARS(monto: number | string): string {
  return `$ ${numero(monto)}`
}

/** `"2026-11-21"` o un ISO con hora → `21/11/2026` (sin corrimientos de zona horaria). */
export function formatearFecha(fecha: string): string {
  const [anio, mes, dia] = fecha.slice(0, 10).split("-")
  return `${dia}/${mes}/${anio}`
}
