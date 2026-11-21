// Solo formateo para mostrar. Los montos y fechas ya vienen calculados del backend.

const numero = new Intl.NumberFormat("es-AR", { maximumFractionDigits: 2 })

/** `1250` o `"1250.00"` → `US$ 1.250` */
export function formatearUSD(monto: number | string): string {
  return `US$ ${numero.format(Number(monto))}`
}

/** `1250000` → `$ 1.250.000` */
export function formatearARS(monto: number | string): string {
  return `$ ${numero.format(Number(monto))}`
}

/** `"2026-11-21"` o un ISO con hora → `21/11/2026` (sin corrimientos de zona horaria). */
export function formatearFecha(fecha: string): string {
  const [anio, mes, dia] = fecha.slice(0, 10).split("-")
  return `${dia}/${mes}/${anio}`
}
