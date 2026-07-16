"""TRIAJE - ADMIN"""

from django.contrib import admin
from django.utils.html import format_html

from .models import TriajeEnfermeria


@admin.register(TriajeEnfermeria)
class TriajeEnfermeriaAdmin(admin.ModelAdmin):
    """Triajeenfermeriaadmin"""
    list_display = (
        "paciente",
        "fecha_registro",
        "get_presion",
        "get_imc_badge",
        "get_alertas",
        "enfermera",
    )
    list_filter = (
        "alerta_presion_alta",
        "alerta_fiebre",
        "alerta_taquicardia",
        "nivel_conciencia",
        "fecha_registro",
    )
    search_fields = ("paciente__nombre", "paciente__ci", "motivo_visita")
    readonly_fields = (
        "fecha_registro",
        "imc",
        "alerta_presion_alta",
        "alerta_fiebre",
        "alerta_taquicardia",
    )

    fieldsets = (
        ("Relaciones", {"fields": ("paciente", "cita", "enfermera")}),
        (
            "Antropometría",
            {"fields": (("peso_kg", "talla_cm", "imc"), "perimetro_abdominal_cm")},
        ),
        (
            "Signos Vitales",
            {
                "fields": (
                    ("presion_sistolica", "presion_diastolica"),
                    "temperatura",
                    ("frecuencia_cardiaca", "frecuencia_respiratoria"),
                    "saturacion_oxigeno",
                ),
            },
        ),
        (
            "Evaluación",
            {
                "fields": (
                    "motivo_visita",
                    "dolor_escala",
                    "nivel_conciencia",
                    "observaciones",
                ),
            },
        ),
        (
            "Alertas Automáticas",
            {
                "fields": (
                    "alerta_presion_alta",
                    "alerta_fiebre",
                    "alerta_taquicardia",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Metadatos", {"fields": ("fecha_registro",), "classes": ("collapse",)}),
    )

    @admin.display(description="PA")
    def get_presion(self, obj):
        """Get presion"""
        return obj.get_presion_arterial()


    @admin.display(description="IMC")
    def get_imc_badge(self, obj):
        """Get imc badge"""
        if obj.imc:
            color = "#27ae60" if 18.5 <= float(obj.imc) < 25 else "#f39c12"
            return format_html(
                '<span style="color:{};font-weight:bold;">{} ({})</span>',
                color,
                obj.imc,
                obj.get_clasificacion_imc(),
            )
        return "-"


    @admin.display(description="Alertas")
    def get_alertas(self, obj):
        """Get alertas"""
        alertas = []
        if obj.alerta_presion_alta:
            alertas.append("⚠️ PA")
        if obj.alerta_fiebre:
            alertas.append("⚠️ Fiebre")
        if obj.alerta_taquicardia:
            alertas.append("⚠️ Taqui")
        return " ".join(alertas) if alertas else "✅"

