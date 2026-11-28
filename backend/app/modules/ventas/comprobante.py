"""Comprobante de la venta en PDF (ReportLab). Se arma desde el DTO del Vendedor, así
nunca lleva costos, ganancia ni comisión."""

from datetime import date
from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core import reloj
from app.modules.ventas.schemas import ProductoVendido, VentaReadVendedor

_ESTADOS = {"pendiente": "Pendiente", "vencida": "Vencida", "cobrada": "Cobrada"}


def _numero(monto: Decimal) -> str:
    """Como en pantalla: `1.250` o `1.180,50`."""
    texto = f"{monto:,.0f}" if monto == monto.to_integral() else f"{monto:,.2f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def _usd(monto: Decimal) -> str:
    return f"US$ {_numero(monto)}"


def _fecha(dia: date) -> str:
    return dia.strftime("%d/%m/%Y")


def _producto(p: ProductoVendido) -> str:
    partes = [p.modelo.nombre, p.capacidad.nombre if p.capacidad else None]
    partes.append(p.color.nombre if p.color else None)
    nombre = " · ".join(x for x in partes if x)
    return f"{nombre} (IMEI {p.imei})" if p.imei else nombre


def _tabla(filas: list[list], anchos: list[float], encabezado: bool = True) -> Table:
    estilo = [
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if encabezado:
        estilo += [
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.grey),
        ]
    tabla = Table(filas, colWidths=anchos, hAlign="LEFT")
    tabla.setStyle(TableStyle(estilo))
    return tabla


def comprobante_pdf(v: VentaReadVendedor) -> bytes:
    estilos = getSampleStyleSheet()
    texto = estilos["Normal"]
    cuerpo: list = [
        Paragraph("Iconic", estilos["Title"]),
        Paragraph(f"Comprobante de la venta #{v.id}", estilos["Heading2"]),
        Paragraph(f"Fecha: {_fecha(reloj.dia_de(v.fecha))}", texto),
        Paragraph(f"Cliente: {v.cliente.nombre}", texto),
        Paragraph(f"Pago: {v.metodo_pago.nombre}", texto),
        Paragraph(
            f"Garantía: {v.garantia_meses} {'mes' if v.garantia_meses == 1 else 'meses'}", texto
        ),
        Spacer(1, 6 * mm),
    ]

    items = [["Producto", "Cant.", "Precio"]] + [
        [
            Paragraph(_producto(i.producto), texto),
            str(i.cantidad),
            "Regalo" if i.es_regalo else _usd(i.precio_usd),
        ]
        for i in v.items
    ]
    cuerpo += [_tabla(items, [120 * mm, 15 * mm, 35 * mm]), Spacer(1, 4 * mm)]

    totales = [["Total", _usd(v.total_usd)]]
    if v.canje:
        totales.append(["Canje", f"− {_usd(v.canje.valor_usd)}"])
    if v.anticipo_usd:
        totales.append(["Anticipo", f"− {_usd(v.anticipo_usd)}"])
    saldo = "A financiar" if v.cuotas else "Saldo"
    totales.append([saldo, _usd(v.saldo_usd)])
    totales.append([f"{saldo} en pesos (TC $ {_numero(v.tc_ars)})", f"$ {_numero(v.saldo_ars)}"])
    cuerpo += [_tabla(totales, [135 * mm, 35 * mm], encabezado=False)]

    if v.cuotas:
        cuerpo += [
            Spacer(1, 6 * mm),
            Paragraph(f"Plan de {len(v.cuotas)} cuotas", estilos["Heading3"]),
            _tabla(
                [["Cuota", "Vencimiento", "Estado", "Monto"]]
                + [
                    [
                        f"{c.numero} de {len(v.cuotas)}",
                        _fecha(c.vencimiento),
                        _ESTADOS[c.estado],
                        _usd(c.monto_usd),
                    ]
                    for c in v.cuotas
                ],
                [30 * mm, 40 * mm, 65 * mm, 35 * mm],
            ),
        ]
        if v.cuotas[-1].monto_usd != v.cuotas[0].monto_usd:
            cuerpo.append(
                Paragraph("La última cuota ajusta el redondeo para que la suma dé exacta.", texto)
            )

    salida = BytesIO()
    SimpleDocTemplate(salida, pagesize=A4, title=f"Venta #{v.id}").build(cuerpo)
    return salida.getvalue()
