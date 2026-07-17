# -*- coding: utf-8 -*-
"""Infraestructura COMPARTIDA para todos los PDFs clínicos del sistema.

Un solo estilo institucional (cabecera, paleta, tablas, gráficos con su
explicación y pie con paginación) para que todo PDF exportado se vea igual,
venga de embarazos, partos, controles, ecografías o consultorios.

Usa reportlab puro (ya es dependencia del proyecto: pacientes/pdf_service.py
y reportes/pdf_generator_enhanced.py). Reemplaza a pdfkit, que requería
wkhtmltopdf instalado en el sistema y en la práctica nunca funcionó: esos
endpoints devolvían JSON con "PDF no disponible".

La paleta replica los tokens por ENTIDAD del frontend (Reportes.tsx
SERIES_COLORS, validada CVD) para que PDF y pantalla cuenten la misma
historia con los mismos colores.
"""
from __future__ import annotations

from datetime import datetime
from io import BytesIO

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Paleta por entidad — misma que el frontend (validada CVD con dataviz)
COLOR_PRIMARIO = colors.HexColor("#1890ff")
COLOR_CITAS = colors.HexColor("#08979c")
COLOR_EMBARAZOS = colors.HexColor("#d48806")
COLOR_CONTROLES = colors.HexColor("#722ed1")
COLOR_PARTOS = colors.HexColor("#389e0d")
COLOR_PELIGRO = colors.HexColor("#cf1322")
COLOR_TEXTO = colors.HexColor("#1f2937")
COLOR_TEXTO_SUAVE = colors.HexColor("#6b7280")
COLOR_FONDO_SUAVE = colors.HexColor("#f5f7fa")

SERIE_COLORES = [COLOR_PRIMARIO, COLOR_EMBARAZOS, COLOR_CONTROLES, COLOR_PARTOS, COLOR_CITAS]

NOMBRE_CLINICA = "Fetal Medical Bolivia"


class PdfClinico:
    """Constructor de PDFs clínicos con formato institucional consistente."""

    def __init__(self, titulo: str, subtitulo: str = ""):
        self.titulo = titulo
        self.subtitulo = subtitulo
        self.buffer = BytesIO()
        self.story: list = []
        base = getSampleStyleSheet()
        self.st_titulo = ParagraphStyle(
            "TituloClinico", parent=base["Title"], fontSize=17,
            textColor=COLOR_PRIMARIO, spaceAfter=2,
        )
        self.st_subtitulo = ParagraphStyle(
            "SubtituloClinico", parent=base["Normal"], fontSize=10,
            textColor=COLOR_TEXTO_SUAVE, alignment=TA_CENTER, spaceAfter=8,
        )
        self.st_seccion = ParagraphStyle(
            "SeccionClinica", parent=base["Heading2"], fontSize=12,
            textColor=colors.white, backColor=COLOR_PRIMARIO,
            borderPadding=(4, 6, 4, 6), spaceBefore=12, spaceAfter=6,
        )
        self.st_normal = ParagraphStyle(
            "NormalClinico", parent=base["Normal"], fontSize=9.5,
            textColor=COLOR_TEXTO, leading=13,
        )
        # La explicación bajo cada gráfico: interpretación en lenguaje clínico
        self.st_explicacion = ParagraphStyle(
            "ExplicacionClinica", parent=base["Normal"], fontSize=8.5,
            textColor=COLOR_TEXTO_SUAVE, leading=12, alignment=TA_JUSTIFY,
            leftIndent=8, borderPadding=4, backColor=COLOR_FONDO_SUAVE,
        )
        self._encabezar()

    # ── Bloques ──────────────────────────────────────────────────────────────

    def _encabezar(self) -> None:
        self.story.append(Paragraph(NOMBRE_CLINICA, self.st_titulo))
        self.story.append(Paragraph(
            "Sistema de Historia Clínica Gineco-Obstétrica", self.st_subtitulo,
        ))
        self.story.append(HRFlowable(width="100%", thickness=1.4, color=COLOR_PRIMARIO))
        self.story.append(Spacer(1, 8))
        st_doc = ParagraphStyle(
            "TituloDoc", parent=self.st_titulo, fontSize=13.5,
            textColor=COLOR_TEXTO, alignment=TA_CENTER,
        )
        self.story.append(Paragraph(self.titulo, st_doc))
        if self.subtitulo:
            self.story.append(Paragraph(self.subtitulo, self.st_subtitulo))
        self.story.append(Spacer(1, 6))

    def seccion(self, texto: str) -> None:
        self.story.append(Paragraph(texto, self.st_seccion))

    def parrafo(self, texto: str) -> None:
        self.story.append(Paragraph(texto, self.st_normal))
        self.story.append(Spacer(1, 4))

    def explicacion(self, texto: str) -> None:
        """Interpretación clínica del gráfico/tabla anterior."""
        self.story.append(Paragraph(f"<b>Interpretación:</b> {texto}", self.st_explicacion))
        self.story.append(Spacer(1, 8))

    def tabla(self, encabezados: list[str], filas: list[list], anchos: list[float] | None = None) -> None:
        data = [encabezados] + [[self._celda(v) for v in fila] for fila in filas]
        t = Table(data, colWidths=anchos, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARIO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d9d9d9")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_FONDO_SUAVE]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        self.story.append(t)
        self.story.append(Spacer(1, 6))

    def ficha(self, pares: list[tuple[str, object]], columnas: int = 2) -> None:
        """Tabla campo→valor (tipo Descriptions) en N columnas."""
        celdas: list[list] = []
        fila: list = []
        for etiqueta, valor in pares:
            fila.extend([
                Paragraph(f"<b>{etiqueta}</b>", self.st_normal),
                Paragraph(self._celda(valor), self.st_normal),
            ])
            if len(fila) >= columnas * 2:
                celdas.append(fila)
                fila = []
        if fila:
            while len(fila) < columnas * 2:
                fila.append("")
            celdas.append(fila)
        t = Table(celdas, colWidths=None)
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
            ("BACKGROUND", (0, 0), (0, -1), COLOR_FONDO_SUAVE),
            ("BACKGROUND", (2, 0), (2, -1), COLOR_FONDO_SUAVE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        self.story.append(t)
        self.story.append(Spacer(1, 6))

    # ── Gráficos (reportlab.graphics: sin dependencias externas) ─────────────

    def grafico_lineas(self, titulo: str, etiquetas: list[str], series: dict[str, list[float]]) -> None:
        d = Drawing(440, 190)
        d.add(String(220, 178, titulo, fontSize=10, fillColor=COLOR_TEXTO, textAnchor="middle"))
        chart = HorizontalLineChart()
        chart.x, chart.y, chart.width, chart.height = 40, 30, 380, 130
        chart.data = list(series.values())
        chart.categoryAxis.categoryNames = etiquetas
        chart.categoryAxis.labels.fontSize = 7
        chart.categoryAxis.labels.angle = 30
        chart.categoryAxis.labels.dy = -6
        chart.valueAxis.labels.fontSize = 7
        for idx in range(len(series)):
            chart.lines[idx].strokeColor = SERIE_COLORES[idx % len(SERIE_COLORES)]
            chart.lines[idx].strokeWidth = 1.8
        d.add(chart)
        # Leyenda simple bajo el título
        x = 60
        for idx, nombre in enumerate(series):
            d.add(String(x, 12, f"— {nombre}", fontSize=8,
                         fillColor=SERIE_COLORES[idx % len(SERIE_COLORES)]))
            x += 120
        self.story.append(d)

    def grafico_barras(self, titulo: str, etiquetas: list[str], valores: list[float],
                       color=COLOR_PRIMARIO) -> None:
        d = Drawing(440, 190)
        d.add(String(220, 178, titulo, fontSize=10, fillColor=COLOR_TEXTO, textAnchor="middle"))
        chart = VerticalBarChart()
        chart.x, chart.y, chart.width, chart.height = 40, 30, 380, 130
        chart.data = [valores]
        chart.categoryAxis.categoryNames = etiquetas
        chart.categoryAxis.labels.fontSize = 7
        chart.categoryAxis.labels.angle = 20
        chart.categoryAxis.labels.dy = -4
        chart.valueAxis.labels.fontSize = 7
        chart.valueAxis.valueMin = 0
        chart.bars[0].fillColor = color
        chart.bars[0].strokeColor = colors.white
        d.add(chart)
        self.story.append(d)

    def grafico_torta(self, titulo: str, etiquetas: list[str], valores: list[float]) -> None:
        d = Drawing(440, 190)
        d.add(String(220, 178, titulo, fontSize=10, fillColor=COLOR_TEXTO, textAnchor="middle"))
        pie = Pie()
        pie.x, pie.y = 160, 25
        pie.width = pie.height = 120
        pie.data = valores
        pie.labels = [f"{e} ({v})" for e, v in zip(etiquetas, valores)]
        pie.slices.fontSize = 7
        for idx in range(len(valores)):
            pie.slices[idx].fillColor = SERIE_COLORES[idx % len(SERIE_COLORES)]
            pie.slices[idx].strokeColor = colors.white
            pie.slices[idx].strokeWidth = 1
        d.add(pie)
        self.story.append(d)

    # ── Salida ───────────────────────────────────────────────────────────────

    @staticmethod
    def _celda(valor: object) -> str:
        if valor is None or valor == "":
            return "—"
        return str(valor)

    def _pie_pagina(self, canvas, doc) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(COLOR_TEXTO_SUAVE)
        canvas.drawString(
            2 * cm, 1.2 * cm,
            f"{NOMBRE_CLINICA} — generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        )
        canvas.drawRightString(letter[0] - 2 * cm, 1.2 * cm, f"Página {doc.page}")
        canvas.setStrokeColor(colors.HexColor("#e5e7eb"))
        canvas.line(2 * cm, 1.5 * cm, letter[0] - 2 * cm, 1.5 * cm)
        canvas.restoreState()

    def generar(self) -> BytesIO:
        doc = SimpleDocTemplate(
            self.buffer, pagesize=letter,
            topMargin=1.6 * cm, bottomMargin=2 * cm,
            leftMargin=2 * cm, rightMargin=2 * cm,
            title=self.titulo, author=NOMBRE_CLINICA,
        )
        doc.build(self.story, onFirstPage=self._pie_pagina, onLaterPages=self._pie_pagina)
        self.buffer.seek(0)
        return self.buffer
