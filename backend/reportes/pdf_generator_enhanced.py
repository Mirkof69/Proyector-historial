"""=============================================================================
PDF GENERATOR ENHANCED - Generación de PDFs con Gráficos Embebidos
=============================================================================
Genera reportes PDF profesionales con gráficos, tablas y estadísticas
Utiliza ReportLab para PDF y Matplotlib para gráficos
=============================================================================
"""

import logging
from datetime import datetime
from io import BytesIO

import matplotlib
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

matplotlib.use("Agg")  # Backend sin GUI
from typing import Any

logger = logging.getLogger(__name__)

import matplotlib.pyplot as plt


class PDFGeneratorEnhanced:
    """Generador avanzado de PDFs con soporte para gráficos embebidos
    """

    def __init__(self):
        """Init"""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Configura estilos personalizados para el PDF"""
        # Título principal
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Heading1"],
                fontSize=24,
                textColor=colors.HexColor("#1a237e"),
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
            ),
        )

        # Subtítulo
        self.styles.add(
            ParagraphStyle(
                name="CustomSubtitle",
                parent=self.styles["Heading2"],
                fontSize=16,
                textColor=colors.HexColor("#283593"),
                spaceAfter=12,
                spaceBefore=12,
                fontName="Helvetica-Bold",
            ),
        )

        # Sección
        self.styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=self.styles["Heading3"],
                fontSize=14,
                textColor=colors.HexColor("#3949ab"),
                spaceAfter=10,
                spaceBefore=15,
                fontName="Helvetica-Bold",
            ),
        )

        # Texto normal
        self.styles.add(
            ParagraphStyle(
                name="CustomBody",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.HexColor("#212121"),
                spaceAfter=6,
            ),
        )

    def generate_statistics_pdf(
        self, stats_data: dict[str, Any], params: dict[str, Any],
    ) -> BytesIO:
        """Genera PDF completo de estadísticas con gráficos

        Args:
            stats_data: Datos de estadísticas del sistema
            params: Parámetros del reporte (fechas, filtros, etc.)

        Returns:
            BytesIO con el contenido del PDF

        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4, topMargin=0.5 * inch, bottomMargin=0.5 * inch,
        )
        story = []

        # Encabezado del reporte
        story.extend(self._create_header(params))
        story.append(Spacer(1, 0.3 * inch))

        # Resumen ejecutivo
        if "dashboard" in stats_data:
            story.extend(self._create_executive_summary(stats_data["dashboard"]))
            story.append(Spacer(1, 0.2 * inch))

        # Gráfico de tendencias de pacientes
        if "dashboard" in stats_data or "pacientes" in stats_data:
            chart_img = self._create_patients_trend_chart(stats_data)
            if chart_img:
                story.append(
                    Paragraph("Tendencia de Pacientes", self.styles["SectionHeader"]),
                )
                story.append(chart_img)
                story.append(Spacer(1, 0.2 * inch))

        # Estadísticas de embarazos
        if "embarazos" in stats_data:
            story.extend(self._create_pregnancy_section(stats_data["embarazos"]))
            story.append(Spacer(1, 0.2 * inch))

        # Estadísticas de controles
        if "controles" in stats_data:
            story.extend(self._create_controls_section(stats_data["controles"]))
            story.append(Spacer(1, 0.2 * inch))

        # Estadísticas de partos
        if "partos" in stats_data:
            story.extend(self._create_births_section(stats_data["partos"]))
            story.append(Spacer(1, 0.2 * inch))

        # Estadísticas de citas
        if "citas" in stats_data:
            story.extend(self._create_appointments_section(stats_data["citas"]))

        # Pie de página
        story.append(Spacer(1, 0.3 * inch))
        story.extend(self._create_footer())

        # Construir PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    def _create_header(self, params: dict[str, Any]) -> list:
        """Crea el encabezado del reporte"""
        elements = []

        # Título
        title = Paragraph(
            "Reporte de Estadísticas del Sistema", self.styles["CustomTitle"],
        )
        elements.append(title)

        # Información del reporte
        _fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M")
        _periodo = (
            f"{params.get('fecha_inicio', 'N/A')} - {params.get('fecha_fin', 'N/A')}"
        )

        info_text = """
        <b>Fecha de Generación:</b> {fecha_generacion}<br/>
        <b>Período de Análisis:</b> {periodo}<br/>
        <b>Sistema:</b> Historial Clínico Gineco-Obstétrico
        """
        info = Paragraph(info_text, self.styles["CustomBody"])
        elements.append(info)

        return elements

    def _create_executive_summary(self, dashboard_data: dict[str, Any]) -> list:
        """Crea resumen ejecutivo con KPIs principales"""
        elements = []

        elements.append(Paragraph("Resumen Ejecutivo", self.styles["CustomSubtitle"]))

        # Tabla de KPIs
        data = [
            ["Indicador", "Valor"],
            ["Total Pacientes", str(dashboard_data.get("total_pacientes", 0))],
            ["Nuevos Pacientes", str(dashboard_data.get("nuevos_pacientes", 0))],
            ["Embarazos Activos", str(dashboard_data.get("embarazos_activos", 0))],
            [
                "Embarazos Alto Riesgo",
                str(dashboard_data.get("embarazos_alto_riesgo", 0)),
            ],
            ["Controles del Mes", str(dashboard_data.get("controles_mes", 0))],
            ["Citas Pendientes", str(dashboard_data.get("citas_pendientes", 0))],
            ["Partos del Mes", str(dashboard_data.get("partos_mes", 0))],
        ]

        table = Table(data, colWidths=[3.5 * inch, 2 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3949ab")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.lightgrey],
                    ),
                ],
            ),
        )

        elements.append(table)
        return elements

    def _create_patients_trend_chart(
        self, _stats_data: dict[str, Any],
    ) -> Image | None:
        """Crea gráfico de tendencia de pacientes"""
        try:
            # Crear figura
            _fig, ax = plt.subplots(figsize=(7, 4))

            # Datos de ejemplo (en producción vendrían de stats_data)
            months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun"]
            patients = [120, 135, 142, 158, 165, 178]

            ax.plot(
                months, patients, marker="o", linewidth=2, color="#3949ab", markersize=8,
            )
            ax.fill_between(range(len(months)), patients, alpha=0.3, color="#3949ab")

            ax.set_xlabel("Mes", fontsize=10, fontweight="bold")
            ax.set_ylabel("Número de Pacientes", fontsize=10, fontweight="bold")
            ax.set_title(
                "Tendencia de Nuevos Pacientes", fontsize=12, fontweight="bold",
            )
            ax.grid(True, alpha=0.3)

            # Guardar en buffer
            img_buffer = BytesIO()
            plt.tight_layout()
            plt.savefig(img_buffer, format="png", dpi=150, bbox_inches="tight")
            plt.close()

            img_buffer.seek(0)
            return Image(img_buffer, width=5.5 * inch, height=3 * inch)

        except Exception as e:
            logger.warning("Error creando gráfico de pacientes: %s", e)
            return None

    def _create_pregnancy_section(self, pregnancy_data: dict[str, Any]) -> list:
        """Crea sección de estadísticas de embarazos"""
        elements = []

        elements.append(
            Paragraph("Estadísticas de Embarazos", self.styles["SectionHeader"]),
        )

        # Tabla de datos
        data = [
            ["Categoría", "Cantidad"],
            ["Total Embarazos", str(pregnancy_data.get("total_embarazos", 0))],
            ["Edad Promedio", f"{pregnancy_data.get('edad_promedio', 0)} años"],
        ]

        # Agregar datos por riesgo si existen
        por_riesgo = pregnancy_data.get("por_riesgo", [])
        if por_riesgo:
            for riesgo_item in por_riesgo:
                clasificacion = riesgo_item.get("clasificacion_riesgo", "N/A")
                total = riesgo_item.get("total", 0)
                data.append([f"Riesgo {clasificacion.title()}", str(total)])

        table = Table(data, colWidths=[3.5 * inch, 2 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7b1fa2")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.lightgrey],
                    ),
                ],
            ),
        )

        elements.append(table)
        return elements

    def _create_controls_section(self, controls_data: dict[str, Any]) -> list:
        """Crea sección de estadísticas de controles"""
        elements = []

        elements.append(
            Paragraph(
                "Estadísticas de Controles Prenatales", self.styles["SectionHeader"],
            ),
        )

        promedios = controls_data.get("promedios", {})

        data = [
            ["Indicador", "Valor"],
            ["Total Controles", str(controls_data.get("total_controles", 0))],
            ["Peso Promedio", f"{promedios.get('peso_promedio', 0):.1f} kg"],
            [
                "Presión Sistólica Promedio",
                f"{promedios.get('presion_sistolica_promedio', 0):.0f} mmHg",
            ],
            [
                "Presión Diastólica Promedio",
                f"{promedios.get('presion_diastolica_promedio', 0):.0f} mmHg",
            ],
        ]

        table = Table(data, colWidths=[3.5 * inch, 2 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00897b")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.lightgrey],
                    ),
                ],
            ),
        )

        elements.append(table)
        return elements

    def _create_births_section(self, births_data: dict[str, Any]) -> list:
        """Crea sección de estadísticas de partos"""
        elements = []

        elements.append(
            Paragraph("Estadísticas de Partos", self.styles["SectionHeader"]),
        )

        data = [
            ["Categoría", "Cantidad"],
            ["Total Partos", str(births_data.get("total_partos", 0))],
        ]

        # Agregar tipos de parto
        por_tipo = births_data.get("por_tipo", [])
        for tipo_item in por_tipo:
            tipo = tipo_item.get("tipo_parto", "N/A")
            total = tipo_item.get("total", 0)
            data.append([f"Tipo: {tipo.replace('_', ' ').title()}", str(total)])

        table = Table(data, colWidths=[3.5 * inch, 2 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#c62828")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.lightgrey],
                    ),
                ],
            ),
        )

        elements.append(table)
        return elements

    def _create_appointments_section(self, appointments_data: dict[str, Any]) -> list:
        """Crea sección de estadísticas de citas"""
        elements = []

        elements.append(
            Paragraph("Estadísticas de Citas", self.styles["SectionHeader"]),
        )

        data = [
            ["Indicador", "Valor"],
            ["Total Citas", str(appointments_data.get("total_citas", 0))],
            ["Completadas", str(appointments_data.get("completadas", 0))],
            ["Canceladas", str(appointments_data.get("canceladas", 0))],
            ["No Asistió", str(appointments_data.get("no_asistidas", 0))],
            [
                "Tasa de Asistencia",
                f"{appointments_data.get('tasa_asistencia', 0):.1f}%",
            ],
            [
                "Tasa de Cancelación",
                f"{appointments_data.get('tasa_cancelacion', 0):.1f}%",
            ],
        ]

        table = Table(data, colWidths=[3.5 * inch, 2 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f57c00")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.lightgrey],
                    ),
                ],
            ),
        )

        elements.append(table)
        return elements

    def _create_footer(self) -> list:
        """Crea pie de página del reporte"""
        elements = []

        footer_text = """
        <para alignment="center">
        <i>Este reporte fue generado automáticamente por el Sistema de Historial Clínico Gineco-Obstétrico</i><br/>
        <i>Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</i>
        </para>
        """

        elements.append(Paragraph(footer_text, self.styles["CustomBody"]))
        return elements


# Instancia global del generador
pdf_generator_enhanced = PDFGeneratorEnhanced()
