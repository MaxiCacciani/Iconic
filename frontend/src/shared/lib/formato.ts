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

/** `"30123456"` → `30.123.456`. El DNI llega solo con dígitos. */
export function formatearDNI(dni: string): string {
  return dni.replace(/\B(?=(\d{3})+(?!\d))/g, ".")
}

const diaEnArgentina = new Intl.DateTimeFormat("es-AR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  timeZone: "America/Argentina/Buenos_Aires",
})

/** Un instante (`"2026-11-25T02:30:00Z"`) → el día en Argentina: `24/11/2026`. Para las
 * fechas sin hora, `formatearFecha`. */
export function formatearDiaDe(instante: string): string {
  // Sin zona (SQLite la pierde), el instante está en UTC, como lo guarda la API.
  const conZona = /(Z|[+-]\d{2}:?\d{2})$/.test(instante)
    ? instante
    : `${instante}Z`
  return diaEnArgentina.format(new Date(conZona))
}

const mesYAnio = new Intl.DateTimeFormat("es-AR", {
  month: "long",
  year: "numeric",
})

/** `(2026, 11)` → `noviembre de 2026` */
export function formatearMes(anio: number, mes: number): string {
  return mesYAnio.format(new Date(anio, mes - 1, 1))
}
