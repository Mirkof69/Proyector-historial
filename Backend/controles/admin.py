"""Admin module."""
from django.contrib import admin

from .models import ControlPrenatal


@admin.register(ControlPrenatal)
class ControlPrenatalAdmin(admin.ModelAdmin):
    """Controlprenataladmin"""
    list_display = [
        "id",
        "numero_control",
        "get_paciente_nombre",
        "embarazo_id",
        "fecha_control",
        "get_edad_gestacional",
        "get_presion_arterial",
        "frecuencia_cardiaca_fetal",
        "get_tiene_alertas",
        "fecha_registro",
    ]

    list_filter = [
        "fecha_control",
        "edema",
        "proteinuria",
        "movimientos_fetales",
        "presentacion_fetal",
    ]

    search_fields = [
        "numero_control",
        "paciente__nombre",
        "paciente__apellido_paterno",
        "embarazo_id",
        "observaciones",
    ]

    readonly_fields = [
        "fecha_registro",
        "get_imc",
        "get_pam",
        "get_ganancia_peso",
        "get_alertas_display",
    ]

    fieldsets = (
        (
            "Información del Control",
            {
                "fields": (
                    "embarazo_id",
                    "paciente",
                    "medico_id",
                    "numero_control",
                    "fecha_control",
                ),
            },
        ),
        (
            "Edad Gestacional",
            {
                "fields": (
                    "semanas_gestacion",
                    "dias_gestacion",
                ),
            },
        ),
        (
            "Mediciones Antropométricas",
            {
                "fields": (
                    "peso_actual",
                    "peso_pregestacional",
                    "talla",
                    "get_imc",
                    "get_ganancia_peso",
                ),
            },
        ),
        (
            "Signos Vitales Maternos",
            {
                "fields": (
                    "presion_arterial_sistolica",
                    "presion_arterial_diastolica",
                    "get_pam",
                    "frecuencia_cardiaca",
                    "temperatura",
                ),
            },
        ),
        (
            "Mediciones Obstétricas",
            {
                "fields": (
                    "altura_uterina",
                    "frecuencia_cardiaca_fetal",
                    "presentacion_fetal",
                    "movimientos_fetales",
                ),
            },
        ),
        (
            "Evaluación Clínica",
            {
                "fields": (
                    "edema",
                    "proteinuria",
                ),
            },
        ),
        ("Observaciones", {"fields": ("observaciones",)}),
        ("Alertas", {"fields": ("get_alertas_display",)}),
        ("Metadata", {"fields": ("fecha_registro",), "classes": ("collapse",)}),
    )

    @admin.display(description="Paciente")
    def get_paciente_nombre(self, obj):
        """Get paciente nombre"""
        if obj.embarazo and obj.embarazo.paciente:
            return f"{obj.embarazo.paciente.nombre} {obj.embarazo.paciente.apellido_paterno}"
        return "-"


    @admin.display(description="Edad Gestacional")
    def get_edad_gestacional(self, obj):
        """Get edad gestacional"""
        return obj.edad_gestacional_texto


    @admin.display(description="PA (mmHg)")
    def get_presion_arterial(self, obj):
        """Get presion arterial"""
        if obj.presion_arterial_sistolica and obj.presion_arterial_diastolica:
            return f"{obj.presion_arterial_sistolica}/{obj.presion_arterial_diastolica}"
        return "-"


    @admin.display(description="Alertas")
    def get_tiene_alertas(self, obj):
        """Get tiene alertas"""
        return "⚠️ Sí" if obj.tiene_alertas_criticas() else "✓ No"


    @admin.display(description="IMC")
    def get_imc(self, obj):
        """Get imc"""
        imc = obj.imc
        if imc:
            return f"{imc} - {obj.clasificacion_imc}"
        return "-"


    @admin.display(description="PAM")
    def get_pam(self, obj):
        """Get pam"""
        pam = obj.presion_arterial_media
        if pam:
            return f"{pam} mmHg"
        return "-"


    @admin.display(description="Ganancia de Peso")
    def get_ganancia_peso(self, obj):
        """Get ganancia peso"""
        ganancia = obj.ganancia_peso
        if ganancia is not None:
            signo = "+" if ganancia > 0 else ""
            return f"{signo}{ganancia} kg"
        return "-"


    @admin.display(description="Alertas Detectadas")
    def get_alertas_display(self, obj):
        """Get alertas display"""
        alertas = obj.get_alertas()
        if not alertas:
            return "✓ Sin alertas"

        from django.utils.html import format_html, format_html_join

        items = format_html_join(
            "",
            "<li><strong>{}</strong>: {}</li>",
            ((alerta["mensaje"], alerta["valor"]) for alerta in alertas),
        )
        return format_html(
            "<ul style='margin: 0; padding-left: 20px;'>{}</ul>", items,
        )

