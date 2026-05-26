"""=============================================================================
PDF SERVICE - GENERACIÓN DE DOCUMENTOS MÉDICOS PROFESIONALES
=============================================================================
Servicio centralizado para generar PDFs de:
    pass
- Historia Clínica Completa
- Reportes de Controles Prenatales
- Certificados Médicos
- Resúmenes de Laboratorio
- Informes de Ecografías
=============================================================================
"""

from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
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


class PDFService:
    """Servicio para generación de PDFs médicos profesionales"""

    def __init__(self):
        """Init"""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Configurar estilos personalizados"""
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
                name="CustomHeading",
                parent=self.styles["Heading2"],
                fontSize=14,
                textColor=colors.HexColor("#262626"),
                spaceAfter=10,
                spaceBefore=10,
                fontName="Helvetica-Bold",
            ),
        )

        # Texto normal justificado
        self.styles.add(
            ParagraphStyle(
                name="CustomBody",
                parent=self.styles["BodyText"],
                fontSize=10,
                alignment=TA_JUSTIFY,
                spaceAfter=6,
            ),
        )

        # Etiqueta (label)
        self.styles.add(
            ParagraphStyle(
                name="Label",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#8c8c8c"),
                fontName="Helvetica-Bold",
            ),
        )

    def _add_header(self, canvas, _doc):
        """Agregar encabezado a cada página"""
        canvas.saveState()

        # Logo (si existe)
        # logo_path = os.path.join(settings.STATIC_ROOT, 'images', 'logo.png')
        # if os.path.exists(logo_path):
        #     canvas.drawImage(logo_path, 50, 750, width=100, height=50, preserveAspectRatio=True)

        # Nombre del centro médico
        canvas.setFont("Helvetica-Bold", 14)
        canvas.setFillColor(colors.HexColor("#1890f"))
        canvas.drawString(50, 780, "CENTRO MÉDICO DE ATENCIÓN PRENATAL")

        # Información del centro
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.black)
        canvas.drawString(
            50, 765, "Dirección: Av. Principal #123 | Tel: (123) 456-7890",
        )
        canvas.drawString(50, 755, "Email: contacto@centromedico.com")

        # Línea separadora
        canvas.setStrokeColor(colors.HexColor("#d9d9d9"))
        canvas.setLineWidth(0.5)
        canvas.line(50, 745, 560, 745)

        canvas.restoreState()

    def _add_footer(self, canvas, doc):
        """Agregar pie de página"""
        canvas.saveState()

        # Línea separadora
        canvas.setStrokeColor(colors.HexColor("#d9d9d9"))
        canvas.setLineWidth(0.5)
        canvas.line(50, 50, 560, 50)

        # Información del pie
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#8c8c8c"))

        # Fecha de generación
        fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M")
        canvas.drawString(50, 35, f"Generado: {fecha_generacion}")

        # Número de página
        canvas.drawRightString(560, 35, f"Página {doc.page}")

        # Texto de confidencialidad
        canvas.drawCentredString(
            305,
            20,
            "DOCUMENTO MÉDICO CONFIDENCIAL - Uso exclusivo del personal autorizado",
        )

        canvas.restoreState()

    def generar_historia_clinica(
        self, paciente_data, timeline_data, _embarazos_data, estadisticas,
    ):
        """Generar PDF de Historia Clínica Integrada

        Args:
            paciente_data: Datos del paciente
            timeline_data: Timeline de eventos
            embarazos_data: Lista de embarazos
            estadisticas: Estadísticas resumidas

        Returns:
            BytesIO: Buffer con el PDF generado

        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=100,
            bottomMargin=80,
        )

        # Contenedor de elementos
        story = []

        # TÍTULO
        story.append(
            Paragraph("HISTORIA CLÍNICA INTEGRADA", self.styles["CustomTitle"]),
        )
        story.append(Spacer(1, 0.2 * inch))

        # INFORMACIÓN DEL PACIENTE
        story.append(Paragraph("DATOS DEL PACIENTE", self.styles["CustomHeading"]))

        paciente_table_data = [
            [
                "Nombre Completo:",
                f"{paciente_data.get('nombre', '')} {paciente_data.get('apellido_paterno', '')} {paciente_data.get('apellido_materno', '')}",
            ],
            ["ID Clínico:", paciente_data.get("id_clinico", "")],
            ["CI:", paciente_data.get("ci", "")],
            ["Fecha de Nacimiento:", paciente_data.get("fecha_nacimiento", "")],
            ["Edad:", f"{paciente_data.get('edad', '')} años"],
            ["Teléfono:", paciente_data.get("telefono", "No especificado")],
            ["Email:", paciente_data.get("email", "No especificado")],
        ]

        paciente_table = Table(paciente_table_data, colWidths=[2 * inch, 4 * inch])
        paciente_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                    ("ALIGN", (1, 0), (1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ],
            ),
        )

        story.append(paciente_table)
        story.append(Spacer(1, 0.3 * inch))

        # ESTADÍSTICAS RESUMIDAS
        story.append(Paragraph("RESUMEN ESTADÍSTICO", self.styles["CustomHeading"]))

        stats_table_data = [
            ["Total Embarazos", estadisticas.get("total_embarazos", 0)],
            ["Controles Prenatales", estadisticas.get("total_controles", 0)],
            ["Ecografías", estadisticas.get("total_ecografias", 0)],
            ["Estudios de Laboratorio", estadisticas.get("total_laboratorios", 0)],
            ["Partos", estadisticas.get("total_partos", 0)],
            ["TOTAL EVENTOS", estadisticas.get("total_eventos", 0)],
        ]

        stats_table = Table(stats_table_data, colWidths=[4 * inch, 2 * inch])
        stats_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#1890f")),
                    ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("BACKGROUND", (0, 0), (-1, -2), colors.HexColor("#f5f5f5")),
                    ("ALIGN", (1, 0), (1, -1), "CENTER"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ],
            ),
        )

        story.append(stats_table)
        story.append(Spacer(1, 0.3 * inch))

        # TIMELINE DE EVENTOS
        story.append(PageBreak())
        story.append(
            Paragraph("TIMELINE DE EVENTOS MÉDICOS", self.styles["CustomTitle"]),
        )
        story.append(Spacer(1, 0.2 * inch))

        # Agrupar por tipo de evento
        tipos_evento = {
            "embarazo": " EMBARAZO",
            "control_prenatal": " CONTROL PRENATAL",
            "ecografia": "️ ECOGRAFÍA",
            "laboratorio": " LABORATORIO",
            "parto": "✅ PARTO",
        }

        for evento in timeline_data:
            tipo = evento.get("tipo_evento", "")
            titulo_tipo = tipos_evento.get(tipo, tipo.upper())

            story.append(
                Paragraph(f"<b>{titulo_tipo}</b>", self.styles["CustomHeading"]),
            )
            story.append(
                Paragraph(
                    f"Fecha: {evento.get('fecha_evento', 'No especificada')}",
                    self.styles["Label"],
                ),
            )

            # Detalles según tipo
            if tipo == "control_prenatal":
                detalles = [
                    f"Control #{evento.get('numero_control', 'N/A')}",
                    f"Semanas gestación: {evento.get('semanas_gestacion', '')}s {evento.get('dias_gestacion', '')}d",
                    f"Peso: {evento.get('peso_actual', '')} kg",
                    f"Presión Arterial: {evento.get('presion_arterial', '')}",
                ]
            elif tipo == "ecografia":
                detalles = [
                    f"Tipo: {evento.get('tipo_ecografia', '')}",
                    f"Peso fetal estimado: {evento.get('peso_fetal_estimado', '')}g",
                    f"Líquido amniótico: {evento.get('liquido_amniotico', '')}",
                ]
            elif tipo == "parto":
                detalles = [
                    f"Vía: {evento.get('via_parto', '')}",
                    f"Sexo bebé: {evento.get('sexo_bebe', '')}",
                    f"Peso: {evento.get('peso_bebe', '')}g",
                    f"Apgar: {evento.get('apgar_1min', '')}/{evento.get('apgar_5min', '')}",
                ]
            else:
                detalles = []

            for detalle in detalles:
                story.append(Paragraph(f"• {detalle}", self.styles["CustomBody"]))

            if evento.get("observaciones"):
                story.append(
                    Paragraph(
                        f"<i>Observaciones: {evento.get('observaciones', '')}</i>",
                        self.styles["CustomBody"],
                    ),
                )

            story.append(Spacer(1, 0.15 * inch))

        # Generar PDF
        doc.build(story, onFirstPage=self._add_header, onLaterPages=self._add_header)

        buffer.seek(0)
        return buffer

    def generar_certificado_medico(
        self, paciente_data, _embarazo_data, texto_certificado,
    ):
        """Generar certificado médico simple"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=100,
            bottomMargin=80,
        )

        story = []

        story.append(Paragraph("CERTIFICADO MÉDICO", self.styles["CustomTitle"]))
        story.append(Spacer(1, 0.4 * inch))

        # Cuerpo del certificado
        story.append(
            Paragraph(
                "El que suscribe, médico especialista en Obstetricia, certifica que:",
                self.styles["CustomBody"],
            ),
        )
        story.append(Spacer(1, 0.2 * inch))

        story.append(
            Paragraph(
                f"<b>Paciente:</b> {paciente_data.get('nombre', '')} {paciente_data.get('apellido_paterno', '')} {paciente_data.get('apellido_materno', '')}",
                self.styles["CustomBody"],
            ),
        )
        story.append(
            Paragraph(
                f"<b>CI:</b> {paciente_data.get('ci', '')}", self.styles["CustomBody"],
            ),
        )
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph(texto_certificado, self.styles["CustomBody"]))
        story.append(Spacer(1, 0.4 * inch))

        # Firma
        story.append(
            Paragraph("_____________________________", self.styles["CustomBody"]),
        )
        story.append(Paragraph("Firma y Sello del Médico", self.styles["CustomBody"]))
        story.append(
            Paragraph(
                f"Fecha: {datetime.now().strftime('%d/%m/%Y')}",
                self.styles["CustomBody"],
            ),
        )

        doc.build(story, onFirstPage=self._add_header, onLaterPages=self._add_header)

        buffer.seek(0)
        return buffer


# Instancia global del servicio
pdf_service = PDFService()
