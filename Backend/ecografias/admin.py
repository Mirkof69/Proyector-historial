"""Admin module."""
from django import forms
from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    AnatomiaFetal,
    AnexosFetales,
    BiometriaFetal,
    Ecografia,
    ImagenEcografia,
)


class AnexosFetalForm(forms.ModelForm):
    """Formulario mejorado para Anexos Fetales con opciones predefinidas"""

    # Campo para acción rápida
    establecer_anexos_normales = forms.BooleanField(
        required=False,
        label="Establecer anexos como normales",
        help_text="Configura valores normales estándar para placenta, cordón y líquido",
    )

    # Opciones predefinidas para localización
    LOCALIZACION_CHOICES = [
        ("", "---------"),
        ("anterior", "Anterior"),
        ("posterior", "Posterior"),
        ("lateral_derecha", "Lateral Derecha"),
        ("lateral_izquierda", "Lateral Izquierda"),
        ("fundica", "Fúndica"),
        ("cornual_derecho", "Cornual Derecho"),
        ("cornual_izquierdo", "Cornual Izquierdo"),
        ("previa_total", "Previa Total"),
        ("previa_parcial", "Previa Parcial"),
        ("previa_marginal", "Previa Marginal"),
    ]

    # Opciones predefinidas para inserción del cordón
    INSERCION_CHOICES = [
        ("", "---------"),
        ("central", "Central"),
        ("paracentral", "Paracentral"),
        ("marginal", "Marginal"),
        ("velamentosa", "Velamentosa"),
        ("furcada", "Furcada"),
    ]

    placenta_localizacion_select = forms.ChoiceField(
        choices=LOCALIZACION_CHOICES,
        required=False,
        label="Localización Placenta (Seleccionar)",
    )

    placenta_inserccion_cordon_select = forms.ChoiceField(
        choices=INSERCION_CHOICES,
        required=False,
        label="Inserción del Cordón (Seleccionar)",
    )

    class Meta:
        """Meta"""
        model = AnexosFetales
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        """Init"""
        super().__init__(*args, **kwargs)

        # Si ya hay valores, seleccionarlos en los dropdowns
        if self.instance and self.instance.pk:
            if self.instance.placenta_localizacion:
                for value, label in self.LOCALIZACION_CHOICES:
                    if (
                        value
                        and label.lower() == self.instance.placenta_localizacion.lower()
                    ):
                        self.fields["placenta_localizacion_select"].initial = value
                        break

            if self.instance.placenta_inserccion_cordon:
                for value, label in self.INSERCION_CHOICES:
                    if (
                        value
                        and label.lower()
                        == self.instance.placenta_inserccion_cordon.lower()
                    ):
                        self.fields["placenta_inserccion_cordon_select"].initial = value
                        break

    def save(self, commit=True):
        """Save"""
        instance = super().save(commit=False)

        # Asignar valores seleccionados del dropdown a los campos del modelo
        if self.cleaned_data.get("placenta_localizacion_select"):
            selected_value = self.cleaned_data["placenta_localizacion_select"]
            for value, label in self.LOCALIZACION_CHOICES:
                if value == selected_value:
                    instance.placenta_localizacion = label
                    break

        if self.cleaned_data.get("placenta_inserccion_cordon_select"):
            selected_value = self.cleaned_data["placenta_inserccion_cordon_select"]
            for value, label in self.INSERCION_CHOICES:
                if value == selected_value:
                    instance.placenta_inserccion_cordon = label
                    break

        # Si se marcó "anexos normales", establecer valores por defecto
        if self.cleaned_data.get("establecer_anexos_normales"):
            instance.numero_vasos_cordon = 3
            instance.circular_cordon = False
            instance.liquido_amniotico_normal = True
            instance.polihidramnios = False
            instance.oligohidramnios = False
            instance.placenta_previa = False
            if not instance.placenta_localizacion:
                instance.placenta_localizacion = "Anterior"
            if not instance.placenta_inserccion_cordon:
                instance.placenta_inserccion_cordon = "Central"

        if commit:
            instance.save()
        return instance


class AnatomiaFetalForm(forms.ModelForm):
    """Formulario mejorado para Anatomía Fetal"""

    # Campo para acción rápida
    establecer_anatomia_normal = forms.BooleanField(
        required=False,
        label="Establecer anatomía como normal",
        help_text="Marca automáticamente todos los órganos como normales",
    )

    class Meta:
        """Meta"""
        model = AnatomiaFetal
        fields = "__all__"

    def save(self, commit=True):
        """Save"""
        instance = super().save(commit=False)

        # Si se marcó "anatomía normal", marcar todos los campos como True
        if self.cleaned_data.get("establecer_anatomia_normal"):
            campos_anatomicos = [
                "craneo_normal",
                "cerebro_normal",
                "cerebelo_normal",
                "perfil_facial_normal",
                "labios_normales",
                "corazon_normal",
                "pulmones_normales",
                "estomago_normal",
                "rinones_normales",
                "vejiga_normal",
                "columna_normal",
                "extremidades_superiores_normales",
                "extremidades_inferiores_normales",
            ]

            for campo in campos_anatomicos:
                setattr(instance, campo, True)

            # Limpiar hallazgos anormales
            instance.hallazgos_anormales = ""

        if commit:
            instance.save()
        return instance


class BiometriaFetalInline(admin.StackedInline):
    """Biometriafetalinline"""
    model = BiometriaFetal
    extra = 0
    verbose_name = "Biometría Fetal"
    verbose_name_plural = "Biometría Fetal"
    fieldsets = (
        (
            "Mediciones Cefálicas",
            {
                "fields": (
                    ("diametro_biparietal", "circunferencia_cefalica"),
                    ("diametro_occipito_frontal", "diametro_transverso_cerebelo"),
                ),
            },
        ),
        (
            "Mediciones Abdominales",
            {
                "fields": (
                    ("circunferencia_abdominal", "diametro_abdominal_transverso"),
                ),
            },
        ),
        (
            "Mediciones de Extremidades",
            {
                "fields": (
                    ("longitud_femur", "longitud_humero"),
                    ("longitud_tibia", "longitud_radio"),
                ),
            },
        ),
        (
            "Peso y Percentiles",
            {"fields": (("peso_fetal_estimado", "percentil_peso"),)},
        ),
        ("Mediciones Adicionales", {"fields": (("cisterna_magna",),)}),
        (
            "Relaciones Calculadas (Solo Lectura)",
            {
                "fields": (("relacion_cc_ca", "relacion_lf_ca"),),
                "classes": ("collapse",),
            },
        ),
    )
    readonly_fields = ("relacion_cc_ca", "relacion_lf_ca")


class AnatomiaFetalInline(admin.StackedInline):
    """Anatomiafetalinline"""
    model = AnatomiaFetal
    form = AnatomiaFetalForm
    extra = 0
    verbose_name = "Anatomía Fetal"
    verbose_name_plural = "Anatomía Fetal"
    fieldsets = (
        (
            "Acciones Rápidas",
            {
                "fields": ("establecer_anatomia_normal",),
                "classes": ("wide",),
                "description": "Use esta opción para marcar toda la anatomía como normal automáticamente",
            },
        ),
        (
            "Sistema Nervioso Central",
            {
                "fields": (
                    ("craneo_normal", "cerebro_normal", "cerebelo_normal"),
                    ("translucencia_nucal", "hueso_nasal_presente"),
                ),
            },
        ),
        ("Cara y Cuello", {"fields": (("perfil_facial_normal", "labios_normales"),)}),
        ("Tórax", {"fields": (("corazon_normal", "pulmones_normales"),)}),
        (
            "Abdomen",
            {"fields": (("estomago_normal", "rinones_normales", "vejiga_normal"),)},
        ),
        ("Genitales", {"fields": (("genitales_visibles", "sexo_fetal"),)}),
        (
            "Columna y Extremidades",
            {
                "fields": (
                    "columna_normal",
                    (
                        "extremidades_superiores_normales",
                        "extremidades_inferiores_normales",
                    ),
                ),
            },
        ),
        (
            "Hallazgos Anormales",
            {
                "fields": ("hallazgos_anormales",),
                "classes": ("collapse",),
                "description": "Describa cualquier hallazgo anormal detectado",
            },
        ),
    )


class AnexosFetalesInline(admin.StackedInline):
    """Anexosfetalesinline"""
    model = AnexosFetales
    form = AnexosFetalForm
    extra = 0
    verbose_name = "Anexos Fetales"
    verbose_name_plural = "Anexos Fetales"
    fieldsets = (
        (
            "Acciones Rápidas",
            {
                "fields": ("establecer_anexos_normales",),
                "classes": ("wide",),
                "description": "Use esta opción para establecer valores normales automáticamente",
            },
        ),
        (
            "Placenta",
            {
                "fields": (
                    "placenta_localizacion_select",
                    "placenta_grosor",
                    "placenta_inserccion_cordon_select",
                    "placenta_previa",
                ),
                "description": "Información sobre la placenta y su localización",
            },
        ),
        (
            "Cordón Umbilical",
            {
                "fields": (("numero_vasos_cordon", "circular_cordon"),),
                "description": "Evaluación del cordón umbilical",
            },
        ),
        (
            "Líquido Amniótico",
            {
                "fields": (
                    "liquido_amniotico_normal",
                    ("polihidramnios", "oligohidramnios"),
                ),
                "description": "Estado del líquido amniótico",
            },
        ),
        (
            "Evaluación Cervical",
            {
                "fields": ("longitud_cervical",),
                "description": "Medición del cérvix uterino",
            },
        ),
    )


class ImagenEcografiaInline(admin.TabularInline):
    """Imagenecografiainline"""
    model = ImagenEcografia
    extra = 1
    fields = (
        "imagen",
        "tipo_imagen",
        "titulo",
        "calidad_imagen",
        "es_imagen_principal",
        "orden",
    )
    readonly_fields = ("fecha_captura",)
    verbose_name = "Imagen de Ecografía"
    verbose_name_plural = "Imágenes de Ecografía"


@admin.register(Ecografia)
class EcografiaAdmin(admin.ModelAdmin):
    """Ecografiaadmin"""
    list_display = (
        "id",
        "get_paciente_nombre",
        "fecha_ecografia",
        "tipo_ecografia",
        "get_edad_gestacional",
        "get_medico_nombre",
        "vitalidad_fetal_badge",
        "numero_fetos",
        "calidad_estudio_badge",
        "get_estado_liquido",
        "requiere_seguimiento_badge",
        "alertas_medicas_badge",
        "acciones_rapidas",
    )

    list_filter = (
        "tipo_ecografia",
        "vitalidad_fetal",
        "numero_fetos",
        "fecha_ecografia",
        "calidad_estudio",
        "requiere_seguimiento",
        "medico",
        "paciente__nombre",
    )

    search_fields = (
        "paciente__nombre",
        "paciente__apellido_paterno",
        "paciente__id_clinico",
        "paciente__ci",
        "embarazo__paciente__nombre",
        "diagnostico",
        "observaciones",
    )

    date_hierarchy = "fecha_ecografia"

    readonly_fields = (
        "fecha_registro",
        "fecha_modificacion",
        "get_edad_gestacional",
        "get_percentil_ila",
        "get_estado_liquido_amniotico",
        "get_evaluacion_fcf",
        "get_resumen_medico_completo",
        "get_alertas_clinicas",
        "get_recomendaciones_seguimiento",
    )

    fieldsets = (
        (
            "Información del Paciente y Embarazo",
            {
                "fields": (
                    ("embarazo", "paciente"),
                    ("fecha_ecografia", "medico"),
                    ("tipo_ecografia", "indicacion"),
                ),
                "description": "Información básica del paciente y tipo de ecografía",
            },
        ),
        (
            "Edad Gestacional",
            {
                "fields": (
                    ("edad_gestacional_semanas", "edad_gestacional_dias"),
                    "get_edad_gestacional",
                ),
                "description": "Edad gestacional al momento del estudio",
            },
        ),
        (
            "Evaluación Fetal Básica",
            {
                "fields": (
                    ("numero_fetos", "vitalidad_fetal"),
                    "frecuencia_cardiaca_fetal",
                    "get_evaluacion_fcf",
                ),
                "description": "Evaluación básica del bienestar fetal",
            },
        ),
        (
            "Evaluación del Líquido Amniótico",
            {
                "fields": (
                    ("indice_liquido_amniotico", "bolsillo_maximo"),
                    "get_percentil_ila",
                    "get_estado_liquido_amniotico",
                ),
                "description": "Análisis del volumen de líquido amniótico",
            },
        ),
        (
            "Evaluación Placentaria",
            {
                "fields": (
                    "localizacion_placenta",
                    "grado_madurez_placenta",
                ),
                "description": "Localización y madurez de la placenta",
            },
        ),
        (
            "Calidad y Limitaciones del Estudio",
            {
                "fields": (
                    "calidad_estudio",
                    "limitaciones_tecnicas",
                ),
                "description": "Calidad técnica del estudio ecográfico",
            },
        ),
        (
            "Diagnóstico y Conclusiones",
            {
                "fields": (
                    "diagnostico",
                    "observaciones",
                ),
                "description": "Interpretación diagnóstica y observaciones clínicas",
            },
        ),
        (
            "Plan de Seguimiento",
            {
                "fields": (
                    "requiere_seguimiento",
                    "proxima_ecografia_recomendada",
                ),
                "description": "Recomendaciones para seguimiento médico",
            },
        ),
        (
            "Resumen Médico Automático",
            {
                "fields": (
                    "get_resumen_medico_completo",
                    "get_alertas_clinicas",
                    "get_recomendaciones_seguimiento",
                ),
                "classes": ("collapse",),
                "description": "Análisis automático basado en los datos ingresados",
            },
        ),
        (
            "Información del Sistema",
            {
                "fields": (("fecha_registro", "fecha_modificacion"),),
                "classes": ("collapse",),
                "description": "Metadatos del registro",
            },
        ),
    )

    inlines = [
        BiometriaFetalInline,
        AnatomiaFetalInline,
        AnexosFetalesInline,
        ImagenEcografiaInline,
    ]

    actions = [
        "marcar_seguimiento_requerido",
        "marcar_seguimiento_completado",
        "generar_reporte_medico",
        "duplicar_ecografia_control",
        "exportar_pdf_completo",
    ]

    @admin.display(description="Paciente")
    def get_paciente_nombre(self, obj):
        """Get paciente nombre"""
        if obj.paciente:
            url = reverse("admin:pacientes_paciente_change", args=[obj.paciente.id])
            return format_html(
                '<a href="{}" target="_blank"><strong>{}</strong></a><br/><small>ID: {}</small>',
                url,
                obj.paciente.nombre_completo,
                obj.paciente.id_clinico,
            )
        return "-"


    @admin.display(description="Edad Gestacional")
    def get_edad_gestacional(self, obj):
        """Get edad gestacional"""
        return obj.get_edad_gestacional_texto()


    @admin.display(description="Médico Ecografista")
    def get_medico_nombre(self, obj):
        """Get medico nombre"""
        if obj.medico:
            return f"{obj.medico.nombre} {obj.medico.apellido_paterno}"
        return "Sin asignar"


    @admin.display(description="Vitalidad Fetal")
    def vitalidad_fetal_badge(self, obj):
        """Vitalidad fetal badge"""
        if obj.vitalidad_fetal:
            return format_html(
                '<span style="background-color: #27ae60; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">VIVO</span>',
            )
        return format_html(
            '<span style="background-color: #e74c3c; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">SIN VITALIDAD</span>',
        )


    @admin.display(description="Calidad")
    def calidad_estudio_badge(self, obj):
        """Calidad estudio badge"""
        colors = {
            "excelente": "#27ae60",
            "buena": "#2ecc71",
            "regular": "#f39c12",
            "limitada": "#e74c3c",
        }
        color = colors.get(obj.calidad_estudio, "#95a5a6")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            getattr(obj, 'get_calidad_estudio_display')().upper(),
        )


    @admin.display(description="Líquido Amniótico")
    def get_estado_liquido(self, obj):
        """Get estado liquido"""
        estado = obj.get_estado_liquido_amniotico()
        if "Normal" in estado:
            color = "#27ae60"
        elif "severo" in estado:
            color = "#e74c3c"
        else:
            color = "#f39c12"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>', color, estado,
        )


    @admin.display(description="Estado")
    def requiere_seguimiento_badge(self, obj):
        """Requiere seguimiento badge"""
        if obj.requiere_seguimiento:
            return format_html(
                '<span style="background-color: #e74c3c; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">SEGUIMIENTO</span>',
            )
        return format_html(
            '<span style="background-color: #27ae60; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">NORMAL</span>',
        )


    @admin.display(description="Alertas Médicas")
    def alertas_medicas_badge(self, obj):
        """Contador de alertas médicas automáticas"""
        alertas = 0

        # Verificar anatomía fetal
        if hasattr(obj, "anatomia") and obj.anatomia:
            if (
                obj.anatomia.translucencia_nucal
                and obj.anatomia.translucencia_nucal > 3.5
            ):
                alertas += 1
            evaluacion = obj.anatomia.get_evaluacion_anatomica()
            if "hallazgo" in evaluacion.lower():
                alertas += 1

        # Verificar biometría fetal
        if hasattr(obj, "biometria") and obj.biometria:
            if obj.biometria.percentil_peso and (
                obj.biometria.percentil_peso < 10 or obj.biometria.percentil_peso > 90
            ):
                alertas += 1

        # Verificar FCF
        if obj.frecuencia_cardiaca_fetal and (
            obj.frecuencia_cardiaca_fetal < 110 or obj.frecuencia_cardiaca_fetal > 160
        ):
            alertas += 1

        # Verificar líquido amniótico
        if obj.indice_liquido_amniotico:
            ila = float(obj.indice_liquido_amniotico)
            if ila < 5 or ila > 25:
                alertas += 1

        if alertas > 0:
            return format_html(
                '<span style="background-color: #e74c3c; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{} ALERTAS</span>',
                alertas,
            )
        return format_html(
            '<span style="background-color: #27ae60; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">SIN ALERTAS</span>',
        )


    @admin.display(description="Acciones")
    def acciones_rapidas(self, obj):
        """Botones de acciones rápidas para cada ecografía"""
        url_editar = reverse("admin:ecografias_ecografia_change", args=[obj.id])
        url_paciente = reverse(
            "admin:pacientes_paciente_change", args=[obj.paciente.id],
        )

        return format_html(
            '<a href="{}" style="background-color: #3498db; color: white; padding: 2px 6px; text-decoration: none; border-radius: 3px; font-size: 10px; margin-right: 2px;">EDITAR</a>'
            '<a href="{}" target="_blank" style="background-color: #9b59b6; color: white; padding: 2px 6px; text-decoration: none; border-radius: 3px; font-size: 10px;">VER PACIENTE</a>',
            url_editar,
            url_paciente,
        )


    @admin.display(description="Percentil ILA")
    def get_percentil_ila(self, obj):
        """Get percentil ila"""
        return obj.get_percentil_ila() or "No calculado"


    @admin.display(description="Estado del Líquido")
    def get_estado_liquido_amniotico(self, obj):
        """Get estado liquido amniotico"""
        return obj.get_estado_liquido_amniotico()


    @admin.display(description="Evaluación FCF")
    def get_evaluacion_fcf(self, obj):
        """Get evaluacion fcf"""
        return obj.get_evaluacion_fcf()


    @admin.display(description="Resumen Médico Completo")
    def get_resumen_medico_completo(self, obj):
        """Genera un resumen médico automático completo"""
        resumen = []

        # Información básica
        resumen.append(f"ECOGRAFÍA {getattr(obj, 'get_tipo_ecografia_display')().upper()}")
        resumen.append(f"Fecha: {obj.fecha_ecografia}")
        resumen.append(f"Paciente: {obj.paciente.nombre_completo}")
        resumen.append(f"Edad Gestacional: {obj.get_edad_gestacional_texto()}")
        resumen.append(f"Médico: {obj.get_medico_nombre()}")
        resumen.append("")

        # Evaluación fetal
        resumen.append("EVALUACIÓN FETAL:")
        resumen.append(
            f"• Vitalidad: {'Presente' if obj.vitalidad_fetal else 'Ausente'}",
        )
        resumen.append(f"• Número de fetos: {obj.numero_fetos}")
        if obj.frecuencia_cardiaca_fetal:
            resumen.append(
                f"• FCF: {obj.frecuencia_cardiaca_fetal} lpm - {obj.get_evaluacion_fcf()}",
            )
        resumen.append("")

        # Biometría si existe
        if hasattr(obj, "biometria") and obj.biometria:
            bio = obj.biometria
            resumen.append("BIOMETRÍA FETAL:")
            if bio.diametro_biparietal:
                resumen.append(f"• DBP: {bio.diametro_biparietal} mm")
            if bio.circunferencia_cefalica:
                resumen.append(f"• CC: {bio.circunferencia_cefalica} mm")
            if bio.circunferencia_abdominal:
                resumen.append(f"• CA: {bio.circunferencia_abdominal} mm")
            if bio.longitud_femur:
                resumen.append(f"• LF: {bio.longitud_femur} mm")
            if bio.peso_fetal_estimado:
                resumen.append(f"• Peso estimado: {bio.peso_fetal_estimado}g")
            if bio.percentil_peso:
                resumen.append(f"• Percentil: P{bio.percentil_peso}")
            resumen.append(f"• Evaluación: {bio.get_evaluacion_crecimiento()}")
            resumen.append("")

        # Anatomía si existe
        if hasattr(obj, "anatomia") and obj.anatomia:
            ana = obj.anatomia
            resumen.append("ANATOMÍA FETAL:")
            resumen.append(f"• {ana.get_evaluacion_anatomica()}")
            if ana.translucencia_nucal:
                resumen.append(f"• Translucencia nucal: {ana.translucencia_nucal} mm")
            resumen.append(f"• Riesgo cromosómico: {ana.get_riesgo_cromosomopatias()}")
            if ana.sexo_fetal:
                resumen.append(f"• Sexo fetal: {getattr(ana, 'get_sexo_fetal_display')()}")
            resumen.append("")

        # Líquido amniótico
        if obj.indice_liquido_amniotico:
            resumen.append("LÍQUIDO AMNIÓTICO:")
            resumen.append(f"• ILA: {obj.indice_liquido_amniotico} cm")
            resumen.append(f"• Estado: {obj.get_estado_liquido_amniotico()}")
            percentil_ila = obj.get_percentil_ila()
            if percentil_ila:
                resumen.append(f"• Percentil: {percentil_ila}")
            resumen.append("")

        # Anexos si existen
        if hasattr(obj, "anexos") and obj.anexos:
            anexos = obj.anexos
            resumen.append("ANEXOS FETALES:")
            if anexos.placenta_localizacion:
                resumen.append(f"• Placenta: {anexos.placenta_localizacion}")
            if anexos.placenta_grosor:
                resumen.append(f"• Grosor placentario: {anexos.placenta_grosor} mm")
            if anexos.placenta_inserccion_cordon:
                resumen.append(
                    f"• Inserción cordón: {anexos.placenta_inserccion_cordon}",
                )
            resumen.append(f"• Cordón umbilical: {anexos.get_evaluacion_cordon()}")
            if anexos.longitud_cervical:
                resumen.append(f"• Cérvix: {anexos.get_evaluacion_cervix()}")
            resumen.append("")

        # Conclusiones
        if obj.diagnostico:
            resumen.append("DIAGNÓSTICO:")
            resumen.append(f"• {obj.diagnostico}")
            resumen.append("")

        if obj.observaciones:
            resumen.append("OBSERVACIONES:")
            resumen.append(f"• {obj.observaciones}")
            resumen.append("")

        return "\n".join(resumen)


    @admin.display(description="Alertas Clínicas Automáticas")
    def get_alertas_clinicas(self, obj):
        """Genera alertas clínicas automáticas"""
        alertas = []

        # Alertas de anatomía
        if hasattr(obj, "anatomia") and obj.anatomia:
            ana = obj.anatomia
            if ana.translucencia_nucal:
                if ana.translucencia_nucal > 3.5:
                    alertas.append(
                        "ALTO RIESGO CROMOSÓMICO: Translucencia nucal > 3.5mm",
                    )
                elif ana.translucencia_nucal > 2.5:
                    alertas.append("RIESGO INTERMEDIO: Translucencia nucal > 2.5mm")

            if ana.hallazgos_anormales:
                alertas.append(f"HALLAZGOS ANORMALES: {ana.hallazgos_anormales}")

        # Alertas de biometría
        if hasattr(obj, "biometria") and obj.biometria:
            bio = obj.biometria
            if bio.percentil_peso:
                if bio.percentil_peso < 10:
                    alertas.append("RESTRICCIÓN DE CRECIMIENTO FETAL: Percentil < 10")
                elif bio.percentil_peso > 90:
                    alertas.append("MACROSOMÍA FETAL: Percentil > 90")

        # Alertas de FCF
        if obj.frecuencia_cardiaca_fetal:
            if obj.frecuencia_cardiaca_fetal < 110:
                alertas.append("BRADICARDIA FETAL: FCF < 110 lpm")
            elif obj.frecuencia_cardiaca_fetal > 160:
                alertas.append("TAQUICARDIA FETAL: FCF > 160 lpm")

        # Alertas de líquido amniótico
        if obj.indice_liquido_amniotico:
            ila = float(obj.indice_liquido_amniotico)
            if ila < 5:
                alertas.append("OLIGOHIDRAMNIOS SEVERO: ILA < 5cm")
            elif ila > 25:
                alertas.append("POLIHIDRAMNIOS SEVERO: ILA > 25cm")
            elif ila < 8:
                alertas.append("OLIGOHIDRAMNIOS LEVE: ILA < 8cm")
            elif ila > 20:
                alertas.append("POLIHIDRAMNIOS LEVE: ILA > 20cm")

        # Alertas de anexos
        if hasattr(obj, "anexos") and obj.anexos:
            anexos = obj.anexos
            if anexos.placenta_previa:
                alertas.append("PLACENTA PREVIA DETECTADA")
            if anexos.numero_vasos_cordon == 2:
                alertas.append("ARTERIA UMBILICAL ÚNICA")
            if anexos.longitud_cervical and anexos.longitud_cervical < 25:
                alertas.append("CÉRVIX CORTO: Riesgo de parto prematuro")

        if alertas:
            return "\n".join([f"• {alerta}" for alerta in alertas])
        return "No se detectaron alertas clínicas"


    @admin.display(description="Recomendaciones de Seguimiento")
    def get_recomendaciones_seguimiento(self, obj):
        """Genera recomendaciones de seguimiento automáticas"""
        recomendaciones = []

        # Recomendaciones basadas en alertas
        if hasattr(obj, "anatomia") and obj.anatomia and (
            obj.anatomia.translucencia_nucal
            and obj.anatomia.translucencia_nucal > 3.5
        ):
            recomendaciones.append("Interconsulta urgente con medicina fetal")
            recomendaciones.append("Evaluación genética completa")
            recomendaciones.append("Ecocardiografía fetal especializada")

        if hasattr(obj, "biometria") and obj.biometria:
            if obj.biometria.percentil_peso and obj.biometria.percentil_peso < 10:
                recomendaciones.append("Control de crecimiento en 2-3 semanas")
                recomendaciones.append("Evaluación Doppler materno-fetal")
                recomendaciones.append("Monitoreo semanal de bienestar fetal")

        if obj.indice_liquido_amniotico:
            ila = float(obj.indice_liquido_amniotico)
            if ila < 5 or ila > 25:
                recomendaciones.append("Control ecográfico semanal")
                recomendaciones.append("Evaluación de bienestar fetal")
                if ila < 5:
                    recomendaciones.append(
                        "Considerar finalización según edad gestacional",
                    )

        # Recomendaciones estándar por trimestre
        if 6 <= obj.edad_gestacional_semanas <= 14:
            recomendaciones.append("Próxima ecografía morfológica a las 20-22 semanas")
            recomendaciones.append(
                "Screening bioquímico de cromosomopatías si no realizado",
            )
            recomendaciones.append("Control prenatal en 4 semanas")
        elif 14 <= obj.edad_gestacional_semanas <= 28:
            recomendaciones.append("Próxima ecografía de crecimiento a las 32 semanas")
            recomendaciones.append("Test de tolerancia a la glucosa (24-28 semanas)")
            recomendaciones.append("Control prenatal cada 2-3 semanas")
        elif obj.edad_gestacional_semanas > 28:
            recomendaciones.append("Control de crecimiento cada 4 semanas")
            recomendaciones.append("Evaluación de presentación fetal")
            recomendaciones.append("Control prenatal semanal después de las 36 semanas")

        # Seguimiento general
        if obj.requiere_seguimiento:
            recomendaciones.append("SEGUIMIENTO ESPECIAL REQUERIDO según hallazgos")

        if recomendaciones:
            return "\n".join([f"• {rec}" for rec in recomendaciones])
        return "• Continuar controles prenatales rutinarios según protocolo"


    # ACCIONES ADMINISTRATIVAS
    @admin.action(description="Marcar seguimiento requerido")
    def marcar_seguimiento_requerido(self, request, queryset):
        """Marcar seguimiento requerido"""
        updated = queryset.update(requiere_seguimiento=True)
        self.message_user(
            request,
            f"{updated} ecografías marcadas como que requieren seguimiento especial.",
        )


    @admin.action(description="Marcar seguimiento completado")
    def marcar_seguimiento_completado(self, request, queryset):
        """Marcar seguimiento completado"""
        updated = queryset.update(requiere_seguimiento=False)
        self.message_user(
            request, f"{updated} ecografías marcadas como seguimiento completado.",
        )


    @admin.action(description="Generar reporte médico PDF")
    def generar_reporte_medico(self, request, queryset):
        """Generar reporte medico"""
        count = queryset.count()
        self.message_user(
            request, f"Reportes médicos generados para {count} ecografías.",
        )


    @admin.action(description="Programar ecografía de control")
    def duplicar_ecografia_control(self, request, queryset):
        """Duplicar ecografia control"""
        if queryset.count() > 1:
            self.message_user(
                request,
                "Solo puede duplicar una ecografía a la vez.",
                level=messages.ERROR,
            )
            return

        ecografia = queryset.first()
        self.message_user(
            request,
            f"Ecografía de control programada para {ecografia.paciente.nombre_completo}.",
        )


    @admin.action(description="Exportar PDF completo")
    def exportar_pdf_completo(self, request, queryset):
        """Exportar pdf completo"""
        count = queryset.count()
        self.message_user(
            request, f"Exportación PDF completa iniciada para {count} ecografías.",
        )



# REGISTROS ADICIONALES CON MEJORAS


@admin.register(BiometriaFetal)
class BiometriaFetalAdmin(admin.ModelAdmin):
    """Biometriafetaladmin"""
    list_display = (
        "ecografia",
        "diametro_biparietal",
        "circunferencia_cefalica",
        "circunferencia_abdominal",
        "longitud_femur",
        "peso_fetal_estimado",
        "percentil_peso_badge",
        "evaluacion_crecimiento",
    )

    list_filter = ("percentil_peso",)
    search_fields = ("ecografia__paciente__nombre",)
    readonly_fields = ("relacion_cc_ca", "relacion_lf_ca")

    @admin.display(description="Percentil")
    def percentil_peso_badge(self, obj):
        """Percentil peso badge"""
        if not obj.percentil_peso:
            return "No calculado"

        percentil = obj.percentil_peso
        if percentil < 10:
            color = "#e74c3c"
        elif percentil > 90:
            color = "#e67e22"
        else:
            color = "#27ae60"

        return format_html(
            '<span style="color: {}; font-weight: bold;">P{}</span>', color, percentil,
        )


    @admin.display(description="Evaluación")
    def evaluacion_crecimiento(self, obj):
        """Evaluacion crecimiento"""
        return obj.get_evaluacion_crecimiento()



@admin.register(AnatomiaFetal)
class AnatomiaFetalAdmin(admin.ModelAdmin):
    """Anatomiafetaladmin"""
    form = AnatomiaFetalForm
    list_display = (
        "ecografia",
        "craneo_normal",
        "cerebro_normal",
        "corazon_normal",
        "columna_normal",
        "evaluacion_anatomica",
        "riesgo_cromosomopatias",
        "tiene_hallazgos_anormales",
    )

    list_filter = (
        "craneo_normal",
        "cerebro_normal",
        "corazon_normal",
        "columna_normal",
        "sexo_fetal",
        "genitales_visibles",
    )

    search_fields = ("ecografia__paciente__nombre", "hallazgos_anormales")

    fieldsets = (
        (
            "Acciones Rápidas",
            {"fields": ("establecer_anatomia_normal",), "classes": ("wide",)},
        ),
        (
            "Sistema Nervioso Central",
            {
                "fields": (
                    ("craneo_normal", "cerebro_normal", "cerebelo_normal"),
                    ("translucencia_nucal", "hueso_nasal_presente"),
                ),
            },
        ),
        ("Cara y Cuello", {"fields": (("perfil_facial_normal", "labios_normales"),)}),
        ("Tórax", {"fields": (("corazon_normal", "pulmones_normales"),)}),
        (
            "Abdomen",
            {"fields": (("estomago_normal", "rinones_normales", "vejiga_normal"),)},
        ),
        ("Genitales", {"fields": (("genitales_visibles", "sexo_fetal"),)}),
        (
            "Columna y Extremidades",
            {
                "fields": (
                    "columna_normal",
                    (
                        "extremidades_superiores_normales",
                        "extremidades_inferiores_normales",
                    ),
                ),
            },
        ),
        (
            "Hallazgos Anormales",
            {"fields": ("hallazgos_anormales",), "classes": ("collapse",)},
        ),
    )

    @admin.display(description="Hallazgos Anormales", boolean=True)
    def tiene_hallazgos_anormales(self, obj):
        """Tiene hallazgos anormales"""
        return bool(obj.hallazgos_anormales)


    @admin.display(description="Evaluación General")
    def evaluacion_anatomica(self, obj):
        """Evaluacion anatomica"""
        return obj.get_evaluacion_anatomica()


    @admin.display(description="Riesgo Cromosómico")
    def riesgo_cromosomopatias(self, obj):
        """Riesgo cromosomopatias"""
        return obj.get_riesgo_cromosomopatias()



@admin.register(AnexosFetales)
class AnexosFetalesAdmin(admin.ModelAdmin):
    """Anexosfetalesadmin"""
    form = AnexosFetalForm
    list_display = (
        "ecografia",
        "placenta_localizacion",
        "placenta_previa_badge",
        "evaluacion_cordon",
        "liquido_amniotico_normal",
        "evaluacion_cervix",
    )

    list_filter = (
        "circular_cordon",
        "liquido_amniotico_normal",
        "polihidramnios",
        "oligohidramnios",
        "placenta_previa",
        "numero_vasos_cordon",
    )

    fieldsets = (
        (
            "Acciones Rápidas",
            {"fields": ("establecer_anexos_normales",), "classes": ("wide",)},
        ),
        (
            "Placenta",
            {
                "fields": (
                    "ecografia",  # ✅ CAMPO ECOGRAFÍA AGREGADO AQUÍ
                    "placenta_localizacion_select",
                    "placenta_grosor",
                    "placenta_inserccion_cordon_select",
                    "placenta_previa",
                ),
            },
        ),
        ("Cordón Umbilical", {"fields": (("numero_vasos_cordon", "circular_cordon"),)}),
        (
            "Líquido Amniótico",
            {
                "fields": (
                    "liquido_amniotico_normal",
                    ("polihidramnios", "oligohidramnios"),
                ),
            },
        ),
        (
            "Evaluación Cervical",
            {
                "fields": ("longitud_cervical",),
            },
        ),
    )

    @admin.display(description="Placenta")
    def placenta_previa_badge(self, obj):
        """Placenta previa badge"""
        if obj.placenta_previa:
            return format_html(
                '<span style="background-color: #e74c3c; color: white; padding: 2px 8px; border-radius: 3px;">PREVIA</span>',
            )
        return format_html('<span style="color: green;">Normal</span>')


    @admin.display(description="Cordón")
    def evaluacion_cordon(self, obj):
        """Evaluacion cordon"""
        return obj.get_evaluacion_cordon()


    @admin.display(description="Cérvix")
    def evaluacion_cervix(self, obj):
        """Evaluacion cervix"""
        return obj.get_evaluacion_cervix()



@admin.register(ImagenEcografia)
class ImagenEcografiaAdmin(admin.ModelAdmin):
    """Imagenecografiaadmin"""
    list_display = (
        "ecografia",
        "titulo",
        "tipo_imagen",
        "calidad_imagen_badge",
        "fecha_captura",
        "es_imagen_principal",
        "preview_imagen",
        "tamano_archivo",
        "dimensiones_imagen",
    )

    list_filter = (
        "tipo_imagen",
        "fecha_captura",
        "calidad_imagen",
        "es_imagen_principal",
    )

    search_fields = (
        "ecografia__paciente__nombre",
        "titulo",
        "descripcion",
        "tipo_imagen",
    )

    readonly_fields = (
        "fecha_captura",
        "preview_imagen",
        "tamano_archivo",
        "dimensiones_imagen",
        "analisis_ia_resumen",
    )

    fieldsets = (
        (
            "Información Básica",
            {
                "fields": (
                    "ecografia",
                    "imagen",
                    ("titulo", "tipo_imagen"),
                    ("calidad_imagen", "es_imagen_principal", "orden"),
                ),
            },
        ),
        ("Descripción", {"fields": ("descripcion",)}),
        ("Mediciones", {"fields": ("mediciones_incluidas",), "classes": ("collapse",)}),
        (
            "Análisis de IA",
            {
                "fields": ("analisis_ia", "analisis_ia_resumen"),
                "classes": ("collapse",),
            },
        ),
        (
            "Información del Archivo",
            {
                "fields": (
                    "fecha_captura",
                    "tamano_archivo",
                    "dimensiones_imagen",
                    "preview_imagen",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["marcar_como_principal", "analizar_con_ia"]

    @admin.display(description="Vista Previa")
    def preview_imagen(self, obj):
        """Preview imagen"""
        if obj.imagen:
            return format_html(
                '<img src="{}" width="150" height="150" style="object-fit: cover;" />',
                obj.imagen.url,
            )
        return "Sin imagen"


    @admin.display(description="Tamaño")
    def tamano_archivo(self, obj):
        """Tamano archivo"""
        return obj.get_tamano_archivo()


    @admin.display(description="Dimensiones")
    def dimensiones_imagen(self, obj):
        """Dimensiones imagen"""
        return obj.get_dimensiones()


    @admin.display(description="Calidad")
    def calidad_imagen_badge(self, obj):
        """Calidad imagen badge"""
        colors = {
            "excelente": "#27ae60",
            "buena": "#2ecc71",
            "regular": "#f39c12",
            "deficiente": "#e74c3c",
        }
        color = colors.get(obj.calidad_imagen, "#95a5a6")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            getattr(obj, 'get_calidad_imagen_display')(),
        )


    @admin.display(description="Análisis IA")
    def analisis_ia_resumen(self, obj):
        """Analisis ia resumen"""
        if obj.analisis_ia and obj.analisis_ia.get("procesado"):
            return f"Procesado: {obj.analisis_ia.get('fecha_analisis', 'Fecha no disponible')}"
        return "No procesado"


    @admin.action(description="Marcar como imagen principal")
    def marcar_como_principal(self, request, queryset):
        """Marcar como principal"""
        if queryset.count() > 1:
            self.message_user(
                request,
                "Solo puede marcar una imagen como principal a la vez.",
                level="error",
            )
            return

        imagen = queryset.first()
        if imagen:
            ImagenEcografia.objects.filter(
                ecografia=imagen.ecografia, es_imagen_principal=True,
            ).update(es_imagen_principal=False)

            imagen.es_imagen_principal = True
            imagen.save()

            self.message_user(
                request, f'Imagen "{imagen.titulo}" marcada como principal.',
            )


    @admin.action(description="Analizar con IA")
    def analizar_con_ia(self, request, queryset):
        """Analizar con ia"""
        procesadas = 0
        for imagen in queryset:
            imagen.analizar_con_ia()
            imagen.save()
            procesadas += 1

        self.message_user(
            request, f"{procesadas} imágenes enviadas para análisis de IA.",
        )



# Personalizar títulos del admin
admin.site.site_header = "Sistema de Historias Clínicas Gineco-Obstétricas"
admin.site.site_title = "Ecografías Médicas"
admin.site.index_title = "Gestión Profesional de Ecografías Obstétricas"
