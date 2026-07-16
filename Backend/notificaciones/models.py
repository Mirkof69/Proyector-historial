"""=============================================================================
MÓDULO: NOTIFICACIONES - MODELS
=============================================================================
Sistema completo de notificaciones para usuarios del sistema
Incluye notificaciones en tiempo real, alertas médicas y recordatorios
=============================================================================
"""

from datetime import timedelta

from django.db import models
from django.utils import timezone

from usuarios.models import Usuario


class TipoNotificacion(models.TextChoices):
    """Tipos de notificaciones del sistema"""

    CITA_PROXIMA = "cita_proxima", "Cita Próxima"
    CITA_CONFIRMADA = "cita_confirmada", "Cita Confirmada"
    CITA_CANCELADA = "cita_cancelada", "Cita Cancelada"
    CITA_REAGENDADA = "cita_reagendada", "Cita Reagendada"

    EXAMEN_LISTO = "examen_listo", "Resultado de Examen Listo"
    EXAMEN_CRITICO = "examen_critico", "Resultado Crítico de Examen"
    EXAMEN_SOLICITADO = "examen_solicitado", "Examen Solicitado"

    ALERTA_CRITICA = "alerta_critica", "Alerta Médica Crítica"
    ALERTA_ADVERTENCIA = "alerta_advertencia", "Advertencia Médica"
    ALERTA_INFORMACION = "alerta_informacion", "Información Médica"

    RECORDATORIO = "recordatorio", "Recordatorio General"
    RECORDATORIO_MEDICACION = "recordatorio_medicacion", "Recordatorio de Medicación"
    RECORDATORIO_CONTROL = "recordatorio_control", "Recordatorio de Control"

    DOCUMENTO_LISTO = "documento_listo", "Documento Listo"
    RECETA_NUEVA = "receta_nueva", "Nueva Receta Médica"
    CERTIFICADO_LISTO = "certificado_listo", "Certificado Médico Listo"

    MENSAJE_MEDICO = "mensaje_medico", "Mensaje del Médico"
    NOVEDAD_SISTEMA = "novedad_sistema", "Novedad del Sistema"


class PrioridadNotificacion(models.TextChoices):
    """Prioridades de las notificaciones"""

    BAJA = "baja", "Baja"
    NORMAL = "normal", "Normal"
    ALTA = "alta", "Alta"
    URGENTE = "urgente", "Urgente"
    CRITICA = "critica", "Crítica"


class Notificacion(models.Model):
    """Modelo principal de Notificaciones

    Gestiona todas las notificaciones del sistema, incluyendo:
        pass
    - Recordatorios de citas
    - Resultados de exámenes
    - Alertas médicas
    - Mensajes del sistema
    """

    # ============== DESTINATARIO ==============
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="notificaciones",
        verbose_name="Usuario Destinatario",
        help_text="Usuario que recibirá la notificación",
    )

    # ============== TIPO Y PRIORIDAD ==============
    tipo = models.CharField(
        max_length=30,
        choices=TipoNotificacion.choices,
        verbose_name="Tipo de Notificación",
    )

    prioridad = models.CharField(
        max_length=10,
        choices=PrioridadNotificacion.choices,
        default=PrioridadNotificacion.NORMAL,
        verbose_name="Prioridad",
    )

    # ============== CONTENIDO ==============
    titulo = models.CharField(
        max_length=200,
        verbose_name="Título",
        help_text="Título breve de la notificación",
    )

    mensaje = models.TextField(
        verbose_name="Mensaje", help_text="Contenido detallado de la notificación",
    )

    icono = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Icono",
        help_text="Nombre del icono para UI (ej: bell, alert-circle, check-circle)",
    )

    color = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Color",
        help_text="Color para UI (ej: blue, red, green, yellow)",
    )

    # ============== ENLACES ==============
    url = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="URL de Acción",
        help_text="URL para redireccionar al hacer clic (ruta del frontend)",
    )

    url_texto = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Texto del Botón",
        help_text="Texto del botón de acción (ej: Ver Detalle, Ir a Cita)",
    )

    # ============== ESTADO ==============
    leida = models.BooleanField(
        default=False,
        verbose_name="Leída",
        help_text="Indica si el usuario ya leyó la notificación",
    )

    fecha_leida = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de Lectura",
    )

    archivada = models.BooleanField(
        default=False,
        verbose_name="Archivada",
        help_text="Indica si el usuario archivó la notificación",
    )

    # ============== METADATOS ==============
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Metadatos",
        help_text="Datos adicionales en formato JSON (IDs relacionados, etc.)",
    )

    # Relaciones opcionales (para trazabilidad)
    entidad_tipo = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Tipo de Entidad Relacionada",
        help_text="Ej: cita, examen, control, parto",
    )

    entidad_id = models.IntegerField(
        null=True, blank=True, verbose_name="ID de Entidad Relacionada",
    )

    # ============== FECHAS ==============
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Creación",
    )

    fecha_expiracion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de Expiración",
        help_text="Fecha en que la notificación deja de ser relevante",
    )

    # ============== ENVÍO ==============
    enviada_push = models.BooleanField(
        default=False,
        verbose_name="Enviada por Push",
        help_text="Indica si se envió notificación push",
    )

    enviada_email = models.BooleanField(
        default=False,
        verbose_name="Enviada por Email",
        help_text="Indica si se envió por correo electrónico",
    )

    enviada_sms = models.BooleanField(
        default=False,
        verbose_name="Enviada por SMS",
        help_text="Indica si se envió por SMS",
    )

    class Meta:
        db_table = "notificaciones"
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ["-fecha_creacion"]
        indexes = [
            models.Index(fields=["usuario", "-fecha_creacion"]),
            models.Index(fields=["usuario", "leida"]),
            models.Index(fields=["tipo"]),
            models.Index(fields=["prioridad"]),
            models.Index(fields=["fecha_creacion"]),
            models.Index(fields=["entidad_tipo", "entidad_id"]),
        ]

    def __str__(self):
        return f"{getattr(self, 'get_tipo_display')()} - {self.usuario.nombre_completo} - {self.titulo}"

    def marcar_como_leida(self):
        """Marca la notificación como leída"""
        if not self.leida:
            self.leida = True
            self.fecha_leida = timezone.now()
            self.save(update_fields=["leida", "fecha_leida"])

    def archivar(self):
        """Archiva la notificación"""
        self.archivada = True
        if not self.leida:
            self.marcar_como_leida()
        self.save(update_fields=["archivada"])

    def esta_vigente(self):
        """Verifica si la notificación aún está vigente"""
        if self.fecha_expiracion:
            return timezone.now() < self.fecha_expiracion
        return True

    def get_tiempo_transcurrido(self):
        """Obtiene el tiempo transcurrido desde la creación"""
        delta = timezone.now() - self.fecha_creacion

        if delta < timedelta(minutes=1):
            return "Hace menos de 1 minuto"
        if delta < timedelta(hours=1):
            minutos = int(delta.total_seconds() / 60)
            return f"Hace {minutos} minuto{'s' if minutos > 1 else ''}"
        if delta < timedelta(days=1):
            horas = int(delta.total_seconds() / 3600)
            return f"Hace {horas} hora{'s' if horas > 1 else ''}"
        if delta < timedelta(days=7):
            dias = delta.days
            return f"Hace {dias} día{'s' if dias > 1 else ''}"
        if delta < timedelta(days=30):
            semanas = delta.days // 7
            return f"Hace {semanas} semana{'s' if semanas > 1 else ''}"
        return self.fecha_creacion.strftime("%d/%m/%Y")

    def get_icono_automatico(self):
        """Obtiene icono sugerido según el tipo"""
        iconos = {
            "cita_proxima": "calendar",
            "cita_confirmada": "check-circle",
            "cita_cancelada": "x-circle",
            "cita_reagendada": "refresh-cw",
            "examen_listo": "file-text",
            "examen_critico": "alert-triangle",
            "examen_solicitado": "clipboard",
            "alerta_critica": "alert-octagon",
            "alerta_advertencia": "alert-triangle",
            "alerta_informacion": "info",
            "recordatorio": "bell",
            "recordatorio_medicacion": "pill",
            "recordatorio_control": "heart",
            "documento_listo": "file",
            "receta_nueva": "file-plus",
            "certificado_listo": "award",
            "mensaje_medico": "message-circle",
            "novedad_sistema": "star",
        }
        return iconos.get(self.tipo, "bell")

    def get_color_automatico(self):
        """Obtiene color sugerido según prioridad y tipo"""
        if self.prioridad == PrioridadNotificacion.CRITICA:
            return "red"
        if self.prioridad == PrioridadNotificacion.URGENTE:
            return "orange"
        if self.prioridad == PrioridadNotificacion.ALTA:
            return "yellow"
        tipo_str = self.tipo if self.tipo else ""
        if "critico" in tipo_str or "alerta_critica" in tipo_str:
            return "red"
        if "examen_listo" in tipo_str or "documento_listo" in tipo_str:
            return "green"
        if "cita" in tipo_str:
            return "blue"
        return "gray"

    def save(self, *args, **kwargs):
        """Guardar con valores automáticos"""
        # Asignar icono y color si no están establecidos
        if not self.icono:
            self.icono = self.get_icono_automatico()
        if not self.color:
            self.color = self.get_color_automatico()

        super().save(*args, **kwargs)

    @classmethod
    def crear_notificacion_cita_proxima(cls, cita):
        """Crea una notificación para recordar una cita próxima

        Args:
            cita: Instancia del modelo Cita

        """
        # Calcular tiempo hasta la cita
        ahora = timezone.now()
        tiempo_hasta_cita = cita.fecha_hora_cita - ahora
        horas_hasta = int(tiempo_hasta_cita.total_seconds() / 3600)

        # Determinar prioridad según cercanía
        if horas_hasta <= 2:
            prioridad = PrioridadNotificacion.URGENTE
        elif horas_hasta <= 24:
            prioridad = PrioridadNotificacion.ALTA
        else:
            prioridad = PrioridadNotificacion.NORMAL

        return cls.objects.create(
            usuario=cita.paciente.usuario
            if hasattr(cita.paciente, "usuario")
            else None,
            tipo=TipoNotificacion.CITA_PROXIMA,
            prioridad=prioridad,
            titulo=f"Recordatorio: Cita {getattr(cita, 'get_tipo_cita_display')()}",
            mensaje=f"Tiene una cita agendada el {cita.fecha_hora_cita.strftime('%d/%m/%Y a las %H:%M')} con el Dr./Dra. {cita.medico.nombre_completo if cita.medico else 'pendiente'}",
            url=f"/citas/{cita.id}",
            url_texto="Ver Detalle de Cita",
            entidad_tipo="cita",
            entidad_id=cita.id,
            metadata={
                "cita_id": cita.id,
                "fecha_cita": cita.fecha_hora_cita.isoformat(),
                "medico": cita.medico.nombre_completo if cita.medico else None,
            },
        )

    @classmethod
    def crear_notificacion_examen_listo(cls, examen):
        """Crea una notificación cuando un examen de laboratorio está listo

        Args:
            examen: Instancia del modelo ExamenLaboratorio

        """
        # Verificar si hay resultados críticos
        tiene_criticos = examen.resultados.filter(es_critico=True).exists()

        return cls.objects.create(
            usuario=examen.paciente.usuario
            if hasattr(examen.paciente, "usuario")
            else None,
            tipo=TipoNotificacion.EXAMEN_CRITICO
            if tiene_criticos
            else TipoNotificacion.EXAMEN_LISTO,
            prioridad=PrioridadNotificacion.CRITICA
            if tiene_criticos
            else PrioridadNotificacion.ALTA,
            titulo="⚠️ RESULTADOS CRÍTICOS"
            if tiene_criticos
            else "Resultados de Examen Listos",
            mensaje=f"Los resultados de {examen.tipo_examen.nombre} ya están disponibles."
            + (
                " ATENCIÓN: Se encontraron valores críticos que requieren atención médica inmediata."
                if tiene_criticos
                else ""
            ),
            url=f"/laboratorio/{examen.id}",
            url_texto="Ver Resultados",
            entidad_tipo="examen",
            entidad_id=examen.id,
            metadata={
                "examen_id": examen.id,
                "tipo_examen": examen.tipo_examen.nombre,
                "tiene_criticos": tiene_criticos,
                "fecha_resultado": examen.fecha_resultado.isoformat()
                if examen.fecha_resultado
                else None,
            },
        )

    @classmethod
    def crear_alerta_medica(
        cls,
        paciente,
        titulo,
        mensaje,
        prioridad=PrioridadNotificacion.ALTA,
        metadata=None,
    ):
        """Crea una alerta médica genérica

        Args:
            paciente: Instancia del modelo Paciente
            titulo: Título de la alerta
            mensaje: Mensaje detallado
            prioridad: Prioridad de la alerta
            metadata: Datos adicionales (dict)

        """
        return cls.objects.create(
            usuario=paciente.usuario if hasattr(paciente, "usuario") else None,
            tipo=TipoNotificacion.ALERTA_CRITICA
            if prioridad == PrioridadNotificacion.CRITICA
            else TipoNotificacion.ALERTA_ADVERTENCIA,
            prioridad=prioridad,
            titulo=titulo,
            mensaje=mensaje,
            url=f"/pacientes/{paciente.id}",
            url_texto="Ver Historia Clínica",
            entidad_tipo="paciente",
            entidad_id=paciente.id,
            metadata=metadata or {},
        )

    @classmethod
    def agrupar_por_tipo(cls, usuario, solo_no_leidas=False):
        """Agrupar notificaciones por tipo para un usuario

        Args:
            usuario: Usuario para filtrar
            solo_no_leidas: Si True, solo incluye no leídas

        Returns:
            dict: Diccionario con tipos como claves y listas de notificaciones

        """
        queryset = cls.objects.filter(usuario=usuario, archivada=False)

        if solo_no_leidas:
            queryset = queryset.filter(leida=False)

        agrupadas = {}
        for notif in queryset:
            tipo = notif.tipo
            if tipo not in agrupadas:
                agrupadas[tipo] = []
            agrupadas[tipo].append(notif)

        return agrupadas

    @classmethod
    def marcar_todas_leidas(cls, usuario):
        """Marcar todas las notificaciones de un usuario como leídas

        Args:
            usuario: Usuario cuyas notificaciones marcar

        Returns:
            int: Número de notificaciones marcadas

        """
        ahora = timezone.now()
        return cls.objects.filter(usuario=usuario, leida=False).update(
            leida=True, fecha_leida=ahora,
        )

    @classmethod
    def obtener_recientes(cls, usuario, limite=10, solo_no_leidas=False):
        """Obtener notificaciones recientes de un usuario

        Args:
            usuario: Usuario para filtrar
            limite: Número máximo de notificaciones
            solo_no_leidas: Si True, solo incluye no leídas

        Returns:
            QuerySet: Notificaciones ordenadas por fecha

        """
        queryset = cls.objects.filter(usuario=usuario, archivada=False)

        if solo_no_leidas:
            queryset = queryset.filter(leida=False)

        return queryset.order_by("-fecha_creacion")[:limite]

    @classmethod
    def contar_por_prioridad(cls, usuario, solo_no_leidas=True):
        """Contar notificaciones por prioridad

        Args:
            usuario: Usuario para filtrar
            solo_no_leidas: Si True, solo cuenta no leídas

        Returns:
            dict: Diccionario con prioridades y conteos

        """
        queryset = cls.objects.filter(usuario=usuario, archivada=False)

        if solo_no_leidas:
            queryset = queryset.filter(leida=False)

        conteos = {}
        for prioridad, _ in PrioridadNotificacion.choices:
            conteos[prioridad] = queryset.filter(prioridad=prioridad).count()

        return conteos


class ConfiguracionNotificaciones(models.Model):
    """Configuración de preferencias de notificaciones por usuario

    Permite a cada usuario personalizar qué notificaciones recibe y por qué canales
    """

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name="config_notificaciones",
        verbose_name="Usuario",
    )

    # ============== CANALES ACTIVOS ==============
    recibir_push = models.BooleanField(
        default=True,
        verbose_name="Recibir Notificaciones Push",
        help_text="Notificaciones en la aplicación web/móvil",
    )

    recibir_email = models.BooleanField(
        default=True, verbose_name="Recibir Notificaciones por Email",
    )

    recibir_sms = models.BooleanField(
        default=False, verbose_name="Recibir Notificaciones por SMS",
    )

    # ============== TIPOS DE NOTIFICACIONES ==============
    notificar_citas = models.BooleanField(default=True, verbose_name="Notificar Citas")

    notificar_examenes = models.BooleanField(
        default=True, verbose_name="Notificar Exámenes",
    )

    notificar_alertas = models.BooleanField(
        default=True, verbose_name="Notificar Alertas Médicas",
    )

    notificar_mensajes = models.BooleanField(
        default=True, verbose_name="Notificar Mensajes",
    )

    notificar_documentos = models.BooleanField(
        default=True, verbose_name="Notificar Documentos",
    )

    # ============== RECORDATORIOS ==============
    recordatorio_citas_horas = models.IntegerField(
        default=24,
        verbose_name="Recordar Citas (horas antes)",
        help_text="Cuántas horas antes de la cita enviar recordatorio",
    )

    recordatorio_controles = models.BooleanField(
        default=True, verbose_name="Recordar Controles Prenatales",
    )

    # ============== HORARIO ==============
    no_molestar_inicio = models.TimeField(
        null=True,
        blank=True,
        verbose_name="No Molestar - Inicio",
        help_text="Hora de inicio del modo no molestar (ej: 22:00)",
    )

    no_molestar_fin = models.TimeField(
        null=True,
        blank=True,
        verbose_name="No Molestar - Fin",
        help_text="Hora de fin del modo no molestar (ej: 08:00)",
    )

    # ============== METADATOS ==============
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "configuracion_notificaciones"
        verbose_name = "Configuración de Notificaciones"
        verbose_name_plural = "Configuraciones de Notificaciones"

    def __str__(self):
        return f"Configuración de {self.usuario.nombre_completo}"

    def puede_recibir_ahora(self):
        """Verifica si el usuario puede recibir notificaciones en este momento"""
        if not self.no_molestar_inicio or not self.no_molestar_fin:
            return True

        ahora = timezone.now().time()

        # Si el horario cruza medianoche
        if self.no_molestar_inicio > self.no_molestar_fin:
            return not (
                ahora >= self.no_molestar_inicio or ahora <= self.no_molestar_fin
            )
        return not self.no_molestar_inicio <= ahora <= self.no_molestar_fin


class HistorialNotificaciones(models.Model):
    """Registro histórico de notificaciones enviadas

    Útil para auditoría y estadísticas
    """

    notificacion = models.ForeignKey(
        Notificacion,
        on_delete=models.CASCADE,
        related_name="historial",
        verbose_name="Notificación",
    )

    accion = models.CharField(
        max_length=50,
        choices=[
            ("creada", "Creada"),
            ("enviada_push", "Enviada por Push"),
            ("enviada_email", "Enviada por Email"),
            ("enviada_sms", "Enviada por SMS"),
            ("leida", "Leída"),
            ("archivada", "Archivada"),
            ("expirada", "Expirada"),
        ],
        verbose_name="Acción",
    )

    fecha = models.DateTimeField(auto_now_add=True)

    detalles = models.JSONField(
        default=dict, blank=True, verbose_name="Detalles Adicionales",
    )

    class Meta:
        db_table = "historial_notificaciones"
        verbose_name = "Historial de Notificación"
        verbose_name_plural = "Historial de Notificaciones"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["notificacion", "-fecha"]),
        ]

    def __str__(self):
        return f"{getattr(self, 'get_accion_display')()} - {self.notificacion.titulo} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"
