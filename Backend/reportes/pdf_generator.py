"""=============================================================================
PDF GENERATOR - GENERADOR DE REPORTES PDF
=============================================================================
Servicio para generar reportes en PDF usando ReportLab
=============================================================================
"""

from datetime import datetime
from io import BytesIO

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class PDFGenerator:
    """Generador de reportes PDF"""

    def __init__(self):
        """Init"""
        self.buffer = BytesIO()
        self.pagesize = A4
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()

    def _create_custom_styles(self):
        """Crea estilos personalizados para el documento"""
        # Título principal
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Heading1"],
                fontSize=18,
                textColor=colors.HexColor("#1890f"),
                spaceAfter=12,
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
            ),
        )

        # Subtítulo
        self.styles.add(
            ParagraphStyle(
                name="CustomSubtitle",
                parent=self.styles["Heading2"],
                fontSize=14,
                textColor=colors.HexColor("#333333"),
                spaceAfter=10,
                spaceBefore=10,
                fontName="Helvetica-Bold",
            ),
        )

        # Texto normal
        self.styles.add(
            ParagraphStyle(
                name="CustomNormal",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.HexColor("#666666"),
                spaceAfter=6,
                alignment=TA_JUSTIFY,
            ),
        )

        # Texto pequeño
        self.styles.add(
            ParagraphStyle(
                name="CustomSmall",
                parent=self.styles["Normal"],
                fontSize=8,
                textColor=colors.HexColor("#999999"),
                spaceAfter=4,
            ),
        )

    def _create_header(self, canvas, _doc):
        """Crea el encabezado del documento"""
        canvas.saveState()

        # Línea superior
        canvas.setStrokeColor(colors.HexColor("#1890f"))
        canvas.setLineWidth(2)
        canvas.line(50, A4[1] - 50, A4[0] - 50, A4[1] - 50)

        # Título del sistema
        canvas.setFont("Helvetica-Bold", 14)
        canvas.setFillColor(colors.HexColor("#1890f"))
        canvas.drawString(50, A4[1] - 35, "Sistema de Gestión Médica Obstétrica")

        # Fecha de generación
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.HexColor("#666666"))
        fecha_actual = timezone.now().strftime("%d/%m/%Y %H:%M:%S")
        canvas.drawRightString(A4[0] - 50, A4[1] - 35, f"Generado: {fecha_actual}")

        canvas.restoreState()

    def _create_footer(self, canvas, _doc):
        """Crea el pie de página del documento"""
        canvas.saveState()

        # Línea inferior
        canvas.setStrokeColor(colors.HexColor("#1890f"))
        canvas.setLineWidth(1)
        canvas.line(50, 50, A4[0] - 50, 50)

        # Número de página
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.HexColor("#666666"))
        page_num = canvas.getPageNumber()
        text = f"Página {page_num}"
        canvas.drawCentredString(A4[0] / 2, 35, text)

        # Información adicional
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#999999"))
        canvas.drawString(50, 35, "Sistema Médico Obstétrico")
        canvas.drawRightString(A4[0] - 50, 35, "Documento Confidencial")

        canvas.restoreState()

    def generate_access_logs_pdf(self, logs_data, filters=None):
        """Genera PDF de logs de acceso

        Args:
            logs_data: Lista de logs con información de accesos
            filtersiltros aplicados (opcional)

        Returns:
            BytesIO con el contenido del PDF

        """
        self.buffer = BytesIO()
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=self.pagesize,
            rightMargin=50,
            leftMargin=50,
            topMargin=80,
            bottomMargin=80,
        )

        # Contenido del documento
        story = []

        # Título
        title = Paragraph("Reporte de Logs de Acceso", self.styles["CustomTitle"])
        story.append(title)
        story.append(Spacer(1, 12))

        # Información del reporte
        if filters:
            info_text = self._format_filters(filters)
            info = Paragraph(info_text, self.styles["CustomSmall"])
            story.append(info)
            story.append(Spacer(1, 12))

        # Resumen estadístico
        total_logs = len(logs_data)
        logins = sum(1 for log in logs_data if log.get("action") == "login")
        logouts = sum(1 for log in logs_data if log.get("action") == "logout")

        summary_data = [
            ["Métrica", "Valor"],
            ["Total de Registros", str(total_logs)],
            ["Inicios de Sesión", str(logins)],
            ["Cierres de Sesión", str(logouts)],
        ]

        summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1890f")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 11),
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

        story.append(summary_table)
        story.append(Spacer(1, 20))

        # Subtitle para tabla de logs
        subtitle = Paragraph("Detalle de Logs", self.styles["CustomSubtitle"])
        story.append(subtitle)
        story.append(Spacer(1, 12))

        # Tabla de logs
        if logs_data:
            # Encabezados
            table_data = [["Fecha/Hora", "Usuario", "Rol", "Acción", "IP"]]

            # Datos
            for log in logs_data[:100]:  # Limitar a 100 registros
                fecha = log.get("created_at", "")
                if isinstance(fecha, str):
                    try:
                        fecha_dt = datetime.fromisoformat(fecha.replace("Z", "+00:00"))
                        fecha = fecha_dt.strftime("%d/%m/%Y %HM")
                    except (ValueError, IndexError):
                        fecha = fecha[:16]  # Tomar primeros 16 caracteres

                table_data.append(
                    [
                        fecha,
                        log.get("user_name", "N/A")[:20],  # Limitar longitud
                        log.get("user_role", "N/A")[:15],
                        "Inicio" if log.get("action") == "login" else "Cierre",
                        log.get("ip_address", "N/A")[:15],
                    ],
                )

            logs_table = Table(
                table_data,
                colWidths=[1.5 * inch, 1.5 * inch, 1 * inch, 0.8 * inch, 1.2 * inch],
            )
            logs_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1890f")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 1), (-1, -1), 8),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.lightgrey],
                        ),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ],
                ),
            )

            story.append(logs_table)
        else:
            no_data = Paragraph(
                "No se encontraron registros", self.styles["CustomNormal"],
            )
            story.append(no_data)

        # Nota al pie
        story.append(Spacer(1, 20))
        note = Paragraph(
            "<b>Nota:</b> Este reporte muestra hasta 100 registros más recientes. "
            "Para reportes completos, utilice la funcionalidad de exportación de datos.",
            self.styles["CustomSmall"],
        )
        story.append(note)

        # Construir PDF
        doc.build(
            story, onFirstPage=self._create_header, onLaterPages=self._create_header,
        )

        self.buffer.seek(0)
        return self.buffer

    def generate_statistics_pdf(self, stats_data):
        """Genera PDF de estadísticas del sistema

        Args:
            stats_data: Diccionario con las estadísticas

        Returns:
            BytesIO con el contenido del PDF

        """
        self.buffer = BytesIO()
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=self.pagesize,
            rightMargin=50,
            leftMargin=50,
            topMargin=80,
            bottomMargin=80,
        )

        story = []

        # Título
        title = Paragraph(
            "Reporte de Estadísticas del Sistema", self.styles["CustomTitle"],
        )
        story.append(title)
        story.append(Spacer(1, 20))

        # Dashboard Stats
        if "dashboard" in stats_data:
            dashboard = stats_data["dashboard"]

            subtitle = Paragraph("Resumen General", self.styles["CustomSubtitle"])
            story.append(subtitle)
            story.append(Spacer(1, 10))

            dashboard_data = [
                ["Métrica", "Valor"],
                ["Total Pacientes", str(dashboard.get("total_pacientes", 0))],
                ["Nuevos Pacientes", str(dashboard.get("nuevos_pacientes", 0))],
                ["Embarazos Activos", str(dashboard.get("embarazos_activos", 0))],
                [
                    "Embarazos Alto Riesgo",
                    str(dashboard.get("embarazos_alto_riesgo", 0)),
                ],
                ["Controles del Mes", str(dashboard.get("controles_mes", 0))],
                ["Citas Pendientes", str(dashboard.get("citas_pendientes", 0))],
                ["Citas Hoy", str(dashboard.get("citas_hoy", 0))],
                ["Partos del Mes", str(dashboard.get("partos_mes", 0))],
            ]

            dashboard_table = Table(dashboard_data, colWidths=[3 * inch, 2 * inch])
            dashboard_table.setStyle(self._get_table_style())
            story.append(dashboard_table)
            story.append(Spacer(1, 20))

        # Embarazos Stats
        if "embarazos" in stats_data:
            embarazos = stats_data["embarazos"]

            subtitle = Paragraph(
                "Estadísticas de Embarazos", self.styles["CustomSubtitle"],
            )
            story.append(subtitle)
            story.append(Spacer(1, 10))

            embarazos_data = [
                ["Métrica", "Valor"],
                ["Total Embarazos", str(embarazos.get("total_embarazos", 0))],
                ["Edad Promedio", f"{embarazos.get('edad_promedio', 0)} años"],
            ]

            # Agregar datos por riesgo si existen
            por_riesgo = embarazos.get("por_riesgo", [])
            if por_riesgo:
                for item in por_riesgo:
                    riesgo = item.get("clasificacion_riesgo", "N/A")
                    total = item.get("total", 0)
                    embarazos_data.append([f"{riesgo}", str(total)])

            embarazos_table = Table(embarazos_data, colWidths=[3 * inch, 2 * inch])
            embarazos_table.setStyle(self._get_table_style())
            story.append(embarazos_table)
            story.append(Spacer(1, 20))

        # Controles Stats
        if "controles" in stats_data:
            controles = stats_data["controles"]

            subtitle = Paragraph(
                "Estadísticas de Controles Prenatales", self.styles["CustomSubtitle"],
            )
            story.append(subtitle)
            story.append(Spacer(1, 10))

            controles_data = [
                ["Métrica", "Valor"],
                ["Total Controles", str(controles.get("total_controles", 0))],
            ]

            # Agregar promedios si existen
            promedios = controles.get("promedios", {})
            if promedios:
                peso_prom = promedios.get("peso_promedio")
                if peso_prom:
                    controles_data.append(["Peso Promedio", f"{peso_prom} kg"])

                presion_sist = promedios.get("presion_sistolica_promedio")
                presion_diast = promedios.get("presion_diastolica_promedio")
                if presion_sist and presion_diast:
                    controles_data.append(
                        [
                            "Presión Arterial Promedio",
                            f"{presion_sist}/{presion_diast} mmHg",
                        ],
                    )

            controles_table = Table(controles_data, colWidths=[3 * inch, 2 * inch])
            controles_table.setStyle(self._get_table_style())
            story.append(controles_table)
            story.append(PageBreak())

        # Citas Stats
        if "citas" in stats_data:
            citas = stats_data["citas"]

            subtitle = Paragraph("Estadísticas de Citas", self.styles["CustomSubtitle"])
            story.append(subtitle)
            story.append(Spacer(1, 10))

            citas_data = [
                ["Métrica", "Valor"],
                ["Total Citas", str(citas.get("total_citas", 0))],
                ["Completadas", str(citas.get("completadas", 0))],
                ["Canceladas", str(citas.get("canceladas", 0))],
                ["Tasa de Asistencia", f"{citas.get('tasa_asistencia', 0)}%"],
                ["Tasa de Cancelación", f"{citas.get('tasa_cancelacion', 0)}%"],
            ]

            citas_table = Table(citas_data, colWidths=[3 * inch, 2 * inch])
            citas_table.setStyle(self._get_table_style())
            story.append(citas_table)
            story.append(Spacer(1, 20))

        # Partos Stats
        if "partos" in stats_data:
            partos = stats_data["partos"]

            subtitle = Paragraph(
                "Estadísticas de Partos", self.styles["CustomSubtitle"],
            )
            story.append(subtitle)
            story.append(Spacer(1, 10))

            partos_data = [
                ["Métrica", "Valor"],
                ["Total Partos", str(partos.get("total_partos", 0))],
                ["Con Complicaciones", str(partos.get("con_complicaciones", 0))],
                ["Sin Complicaciones", str(partos.get("sin_complicaciones", 0))],
            ]

            # Agregar promedios si existen
            promedios = partos.get("promedios", {})
            if promedios:
                peso_prom = promedios.get("peso_promedio")
                if peso_prom:
                    partos_data.append(["Peso Promedio RN", f"{peso_prom} g"])

                talla_prom = promedios.get("talla_promedio")
                if talla_prom:
                    partos_data.append(["Talla Promedio RN", f"{talla_prom} cm"])

                apgar1 = promedios.get("apgar_1_promedio")
                apgar5 = promedios.get("apgar_5_promedio")
                if apgar1 and apgar5:
                    partos_data.append(
                        ["APGAR Promedio", f"1': {apgar1} - 5': {apgar5}"],
                    )

            partos_table = Table(partos_data, colWidths=[3 * inch, 2 * inch])
            partos_table.setStyle(self._get_table_style())
            story.append(partos_table)

        # Construir PDF
        doc.build(
            story, onFirstPage=self._create_header, onLaterPages=self._create_header,
        )

        self.buffer.seek(0)
        return self.buffer

    def _get_table_style(self):
        """Retorna el estilo estándar para tablas"""
        return TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1890f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 10),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ],
        )

    def _format_filters(self, filters):
        """Formatea los filtros para mostrar en el reporte"""
        filter_parts = []

        if filters.get("start_date"):
            filter_parts.append(f"Desde: {filters['start_date']}")

        if filters.get("end_date"):
            filter_parts.append(f"Hasta: {filters['end_date']}")

        if filters.get("action"):
            action_text = (
                "Inicio de Sesión"
                if filters["action"] == "login"
                else "Cierre de Sesión"
            )
            filter_parts.append(f"Acción: {action_text}")

        if filters.get("user_role"):
            filter_parts.append(f"Rol: {filters['user_role']}")

        if filter_parts:
            return f"<b>Filtros aplicados:</b> {' | '.join(filter_parts)}"

        return "<b>Período:</b> Todos los registros"


# Instancia singleton
pdf_generator = PDFGenerator()
