"""==========================================================================================
MODELOS DE CONFIGURACIÓN DEL SISTEMA
==========================================================================================
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

# ✅ CIRCULAR IMPORT FIX: Usar get_user_model() en ForeignKeys


class SistemaConfiguracion(models.Model):
    """Configuración global del sistema clínico
    """

    # IDENTIDAD DE LA CLÍNICA
    nombre_clinica = models.CharField(
        max_length=200,
        default="Centro Médico",
        verbose_name="Nombre de la Clínica/Consultorio",
    )

    direccion = models.TextField(blank=True, verbose_name="Dirección Física")

    telefono_contacto = models.CharField(
        max_length=50, blank=True, verbose_name="Teléfono Principal",
    )

    email_contacto = models.EmailField(blank=True, verbose_name="Email de Contacto")

    logo = models.ImageField(
        upload_to="logos/",
        blank=True,
        null=True,
        verbose_name="Logo Institucional",
        help_text="Logo que aparecerá en reportes y documentos oficiales",
    )

    # CONFIGURACIÓN TÉCNICA
    modo_mantenimiento = models.BooleanField(
        default=False,
        verbose_name="Modo Mantenimiento",
        help_text="Solo administradores podrán acceder al sistema",
    )

    permitir_registro_publico = models.BooleanField(
        default=False, verbose_name="Permitir Registro Público",
    )

    dias_retencion_logs = models.IntegerField(
        default=90,
        validators=[MinValueValidator(1), MaxValueValidator(730)],
        verbose_name="Días de Retención de Logs",
    )

    # CONFIGURACIÓN SMTP (CORREO)
    smtp_host = models.CharField(
        max_length=100, default="smtp.gmail.com", verbose_name="Servidor SMTP",
    )

    smtp_port = models.IntegerField(default=587, verbose_name="Puerto SMTP")

    smtp_user = models.EmailField(blank=True, verbose_name="Usuario SMTP")

    smtp_password = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Contraseña SMTP",
        help_text="Se almacena encriptada",
    )

    smtp_secure = models.BooleanField(default=True, verbose_name="Usar TLS/SSL")

    # METADATOS
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    actualizado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Última Actualización Por",
    )

    class Meta:
        """Meta"""
        db_table = "sistema_configuracion"
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuración del Sistema"

    def __str__(self):
        """Str"""
        return f"Configuración: {self.nombre_clinica}"

    @classmethod
    def get_configuracion(cls):
        """Obtener o crear la configuración única del sistema"""
        config, _created = cls.objects.get_or_create(pk=1)
        return config


class ConfiguracionAlertas(models.Model):
    """Configuración global de umbrales y canales de notificación
    para el sistema de alertas médicas.
    """

    # SIGNOS VITALES
    alertar_presion_alta = models.BooleanField(
        default=True, verbose_name="Alertar sobre presión arterial alta",
    )
    limite_presion_sistolica = models.IntegerField(
        default=140,
        validators=[MinValueValidator(100), MaxValueValidator(250)],
        verbose_name="Límite superior presión sistólica (mmHg)",
    )
    alertar_glucosa_alta = models.BooleanField(
        default=True, verbose_name="Alertar sobre glucosa elevada",
    )
    limite_glucosa_ayunas = models.IntegerField(
        default=105,
        validators=[MinValueValidator(70), MaxValueValidator(300)],
        verbose_name="Límite glucosa en ayunas (mg/dL)",
    )

    # LABORATORIO
    alertar_resultados_criticos = models.BooleanField(
        default=True, verbose_name="Alertar sobre resultados críticos",
    )
    alertar_resultados_anormales = models.BooleanField(
        default=True, verbose_name="Alertar sobre resultados anormales",
    )

    # NOTIFICACIONES
    notificar_por_email = models.BooleanField(
        default=False, verbose_name="Enviar notificaciones por email",
    )
    notificar_por_sistema = models.BooleanField(
        default=True, verbose_name="Mostrar notificaciones en el sistema",
    )

    # METADATOS
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    actualizado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Última Actualización Por",
    )

    class Meta:
        """Meta"""
        db_table = "configuracion_alertas"
        verbose_name = "Configuración de Alertas"
        verbose_name_plural = "Configuración de Alertas"

    def __str__(self):
        """Str"""
        return "Configuración de Alertas Médicas"

    @classmethod
    def get_configuracion(cls):
        """Obtener o crear la configuración única de alertas"""
        config, _created = cls.objects.get_or_create(pk=1)
        return config


class HorarioAtencion(models.Model):
    """Horarios de atención por día de la semana
    """

    DIAS_SEMANA = [
        ("lunes", "Lunes"),
        ("martes", "Martes"),
        ("miercoles", "Miércoles"),
        ("jueves", "Jueves"),
        ("viernes", "Viernes"),
        ("sabado", "Sábado"),
        ("domingo", "Domingo"),
    ]

    dia = models.CharField(
        max_length=10, choices=DIAS_SEMANA, unique=True, verbose_name="Día de la Semana",
    )

    activo = models.BooleanField(
        default=True,
        verbose_name="Día Activo",
        help_text="Si está desactivado, no se podrán agendar citas en este día",
    )

    hora_inicio = models.TimeField(
        verbose_name="Hora de Inicio", help_text="Formato 24 horas (ej: 08:00)",
    )

    hora_fin = models.TimeField(
        verbose_name="Hora de Cierre", help_text="Formato 24 horas (ej: 18:00)",
    )

    # METADATOS
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta"""
        db_table = "horarios_atencion"
        ordering = ["id"]
        verbose_name = "Horario de Atención"
        verbose_name_plural = "Horarios de Atención"

    def __str__(self):
        """Str"""
        estado = "Abierto" if self.activo else "Cerrado"
        if self.activo:
            return f"{getattr(self, 'get_dia_display')()}: {self.hora_inicio.strftime('%H:%M')} - {self.hora_fin.strftime('%H:%M')}"
        return f"{getattr(self, 'get_dia_display')()}: {estado}"

    def clean(self):
        """Validar que hora_fin sea después de hora_inicio"""
        from django.core.exceptions import ValidationError

        if self.hora_inicio and self.hora_fin:
            if self.hora_fin <= self.hora_inicio:
                raise ValidationError(
                    {
                        "hora_fin": "La hora de cierre debe ser posterior a la hora de inicio",
                    },
                )
