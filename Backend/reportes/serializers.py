"""Serializers module."""
from rest_framework import serializers

from .models import (
    AlertaMedica,
    AuditoriaReporte,
    DashboardKPI,
    ReporteGenerado,
    TipoReporte,
)

# ============================================================================
# SERIALIZERS PARA TIPO DE REPORTE
# ============================================================================


class TipoReporteSerializer(serializers.ModelSerializer):
    """Serializer detallado para la configuración de tipos de reporte.
    Incluye campos calculados para mostrar roles y formatos de manera amigable.
    """

    roles_autorizados_display = serializers.SerializerMethodField()
    formatos_disponibles_display = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = TipoReporte
        fields = [
            "id",
            "nombre",
            "codigo",
            "descripcion",
            "categoria",
            "frecuencia",
            "automatico",
            "requiere_parametros",
            "confidencial",
            "activo",
            # Filtros disponibles
            "incluir_fecha_inicio",
            "incluir_fecha_fin",
            "incluir_paciente",
            "incluir_medico",
            "incluir_servicio",
            # Permisos
            "permitir_medico",
            "permitir_enfermero",
            "permitir_administrador",
            "permitir_director",
            # Formatos
            "formato_pdf",
            "formato_excel",
            "formato_csv",
            "formato_json",
            # Internos / compatibles
            "parametros_esquema",
            "roles_autorizados",
            "campos_requeridos",
            "formato_salida",
            # Metadatos
            "fecha_creacion",
            "fecha_modificacion",
            # Campos calculados
            "roles_autorizados_display",
            "formatos_disponibles_display",
        ]
        read_only_fields = [
            "codigo",
            "roles_autorizados",
            "campos_requeridos",
            "formato_salida",
            "fecha_creacion",
            "fecha_modificacion",
        ]

    def get_roles_autorizados_display(self, obj):
        """Get roles autorizados display"""
        return obj.get_roles_autorizados_display()

    def get_formatos_disponibles_display(self, obj):
        """Get formatos disponibles display"""
        return obj.get_formatos_disponibles_display()

    def validate(self, attrs):
        """Validaciones de coherencia básica:
            pass
        - Si es automático, debe tener una frecuencia distinta de 'bajo_demanda'.
        - Debe tener al menos un formato disponible.
        - Debe haber al menos un rol con permiso.
        """
        automatico = attrs.get("automatico", getattr(self.instance, "automatico", False))
        frecuencia = attrs.get(
            "frecuencia", getattr(self.instance, "frecuencia", "bajo_demanda"),
        )

        if automatico and frecuencia == "bajo_demanda":
            raise serializers.ValidationError(
                {
                    "frecuencia": 'Si el reporte es automático, debe tener una frecuencia distinta de "bajo_demanda".',
                },
            )

        # Formatos
        formato_pdf = attrs.get(
            "formato_pdf", getattr(self.instance, "formato_pdf", False),
        )
        formato_excel = attrs.get(
            "formato_excel", getattr(self.instance, "formato_excel", False),
        )
        formato_csv = attrs.get(
            "formato_csv", getattr(self.instance, "formato_csv", False),
        )
        formato_json = attrs.get(
            "formato_json", getattr(self.instance, "formato_json", False),
        )

        if not any([formato_pdf, formato_excel, formato_csv, formato_json]):
            raise serializers.ValidationError(
                {
                    "formato_pdf": "Debe habilitar al menos un formato de salida para el reporte.",
                },
            )

        # Roles
        permitir_medico = attrs.get(
            "permitir_medico", getattr(self.instance, "permitir_medico", False),
        )
        permitir_enfermero = attrs.get(
            "permitir_enfermero", getattr(self.instance, "permitir_enfermero", False),
        )
        permitir_administrador = attrs.get(
            "permitir_administrador",
            getattr(self.instance, "permitir_administrador", False),
        )
        permitir_director = attrs.get(
            "permitir_director", getattr(self.instance, "permitir_director", False),
        )

        if not any(
            [
                permitir_medico,
                permitir_enfermero,
                permitir_administrador,
                permitir_director,
            ],
        ):
            raise serializers.ValidationError(
                {
                    "permitir_medico": "Debe haber al menos un rol autorizado para generar este reporte.",
                },
            )

        return attrs


class TipoReporteResumenSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados de tipos de reporte.
    """

    categoria_display = serializers.CharField(
        source="get_categoria_display", read_only=True,
    )
    frecuencia_display = serializers.CharField(
        source="get_frecuencia_display", read_only=True,
    )

    class Meta:
        """Meta"""
        model = TipoReporte
        fields = [
            "id",
            "nombre",
            "codigo",
            "categoria",
            "categoria_display",
            "frecuencia",
            "frecuencia_display",
            "automatico",
            "confidencial",
            "activo",
        ]


# ============================================================================
# SERIALIZERS PARA REPORTES GENERADOS
# ============================================================================


class ReporteGeneradoSerializer(serializers.ModelSerializer):
    """Serializer detallado para instancias de reportes generados.
    Incluye información básica del tipo de reporte.
    """

    tipo_reporte_nombre = serializers.CharField(
        source="tipo_reporte.nombre", read_only=True,
    )
    tipo_reporte_categoria = serializers.CharField(
        source="tipo_reporte.categoria", read_only=True,
    )
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    formato_display = serializers.CharField(
        source="get_formato_display", read_only=True,
    )
    tamano_archivo_display = serializers.SerializerMethodField()
    tiempo_procesamiento_display = serializers.SerializerMethodField()
    esta_expirado = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = ReporteGenerado
        fields = [
            "id",
            "tipo_reporte",
            "tipo_reporte_nombre",
            "tipo_reporte_categoria",
            "usuario_solicitante",
            "estado",
            "estado_display",
            "formato",
            "formato_display",
            "parametros",
            "fecha_inicio",
            "fecha_fin",
            "filtro_paciente",
            "filtro_medico",
            "filtro_servicio",
            "fecha_solicitud",
            "fecha_procesamiento",
            "fecha_completado",
            "fecha_expiracion",
            "ruta_archivo",
            "tamano_archivo",
            "tamano_archivo_display",
            "hash_archivo",
            "accesos_descarga",
            "total_registros",
            "datos_resumen",
            "observaciones",
            "mensaje_error",
            "tiempo_procesamiento",
            "tiempo_procesamiento_display",
            "esta_expirado",
        ]
        read_only_fields = [
            "fecha_solicitud",
            "fecha_procesamiento",
            "fecha_completado",
            "fecha_expiracion",
            "tamano_archivo",
            "hash_archivo",
            "accesos_descarga",
            "total_registros",
            "datos_resumen",
            "mensaje_error",
            "tiempo_procesamiento",
        ]

    def get_tamano_archivo_display(self, obj):
        """Get tamano archivo display"""
        return obj.get_tamano_archivo_display()

    def get_tiempo_procesamiento_display(self, obj):
        """Get tiempo procesamiento display"""
        return obj.get_tiempo_procesamiento_display()

    def get_esta_expirado(self, obj):
        """Get esta expirado"""
        return obj.esta_expirado()

    def validate(self, attrs):
        """Valida coherencia entre fechas.
        """
        fecha_inicio = attrs.get(
            "fecha_inicio", getattr(self.instance, "fecha_inicio", None),
        )
        fecha_fin = attrs.get("fecha_fin", getattr(self.instance, "fecha_fin", None))

        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            raise serializers.ValidationError(
                {
                    "fecha_fin": "La fecha de fin debe ser mayor o igual que la fecha de inicio.",
                },
            )
        return attrs


class ReporteGeneradoResumenSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar reportes generados en tablas.
    """

    tipo_reporte_nombre = serializers.CharField(
        source="tipo_reporte.nombre", read_only=True,
    )
    categoria = serializers.CharField(source="tipo_reporte.categoria", read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    formato_display = serializers.CharField(
        source="get_formato_display", read_only=True,
    )
    tamano_archivo_display = serializers.SerializerMethodField()
    esta_expirado = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = ReporteGenerado
        fields = [
            "id",
            "tipo_reporte",
            "tipo_reporte_nombre",
            "categoria",
            "usuario_solicitante",
            "estado",
            "estado_display",
            "formato",
            "formato_display",
            "fecha_solicitud",
            "fecha_completado",
            "tamano_archivo_display",
            "esta_expirado",
        ]

    def get_tamano_archivo_display(self, obj):
        """Get tamano archivo display"""
        return obj.get_tamano_archivo_display()

    def get_esta_expirado(self, obj):
        """Get esta expirado"""
        return obj.esta_expirado()


class ReporteGeneradoCreateSerializer(serializers.ModelSerializer):
    """Serializer específico para crear solicitudes de reporte.
    El usuario_solicitante se toma del request en la vista.
    """

    class Meta:
        """Meta"""
        model = ReporteGenerado
        fields = [
            "id",
            "tipo_reporte",
            "formato",
            "fecha_inicio",
            "fecha_fin",
            "filtro_paciente",
            "filtro_medico",
            "filtro_servicio",
            "parametros",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        """Valida parámetros según el TipoReporte asociado.
        """
        tipo_reporte = attrs.get("tipo_reporte")
        if not tipo_reporte:
            raise serializers.ValidationError(
                {"tipo_reporte": "Debe indicar el tipo de reporte."},
            )

        # Validar que el formato esté permitido por el tipo de reporte
        formatos_disponibles = tipo_reporte.get_formatos_disponibles()
        formato = attrs.get("formato", "pdf")
        if formato not in formatos_disponibles:
            raise serializers.ValidationError(
                {
                    "formato": f'El formato "{formato}" no está habilitado para este reporte.',
                },
            )

        # Validar fechas si el tipo de reporte lo requiere
        campos_requeridos = tipo_reporte.get_campos_requeridos()
        fecha_inicio = attrs.get("fecha_inicio")
        fecha_fin = attrs.get("fecha_fin")

        if "fecha_inicio" in campos_requeridos and not fecha_inicio:
            raise serializers.ValidationError(
                {"fecha_inicio": "Este reporte requiere una fecha de inicio."},
            )
        if "fecha_fin" in campos_requeridos and not fecha_fin:
            raise serializers.ValidationError(
                {"fecha_fin": "Este reporte requiere una fecha de fin."},
            )
        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            raise serializers.ValidationError(
                {
                    "fecha_fin": "La fecha de fin debe ser mayor o igual que la fecha de inicio.",
                },
            )

        # Validar filtros específicos
        if "filtro_paciente" in campos_requeridos and not attrs.get("filtro_paciente"):
            raise serializers.ValidationError(
                {"filtro_paciente": "Este reporte requiere un paciente específico."},
            )
        if "filtro_medico" in campos_requeridos and not attrs.get("filtro_medico"):
            raise serializers.ValidationError(
                {"filtro_medico": "Este reporte requiere un médico específico."},
            )

        return attrs


# ============================================================================
# SERIALIZERS PARA DASHBOARD KPI
# ============================================================================


class DashboardKPISerializer(serializers.ModelSerializer):
    """Serializer detallado para KPIs del dashboard.
    Incluye estado vs meta, tendencia y color.
    """

    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    categoria_display = serializers.CharField(
        source="get_categoria_display", read_only=True,
    )
    frecuencia_display = serializers.CharField(
        source="get_frecuencia_actualizacion_display", read_only=True,
    )
    tendencia = serializers.SerializerMethodField()
    estado_vs_meta = serializers.SerializerMethodField()
    color_estado = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = DashboardKPI
        fields = [
            "id",
            "nombre",
            "codigo",
            "descripcion",
            "categoria",
            "categoria_display",
            "tipo",
            "tipo_display",
            "consulta_sql",
            "parametros_calculo",
            "frecuencia_actualizacion",
            "frecuencia_display",
            # Valores
            "valor_actual",
            "valor_anterior",
            # Metas
            "meta_minima",
            "meta_optima",
            "unidad_medida",
            # Visual
            "color_normal",
            "color_advertencia",
            "color_critico",
            "icono",
            "orden_dashboard",
            # Acceso
            "activo",
            "visible_medico",
            "visible_administrador",
            "visible_director",
            "roles_autorizados",
            # Metadatos
            "ultima_actualizacion",
            "fecha_creacion",
            "fecha_modificacion",
            # Calculados
            "tendencia",
            "estado_vs_meta",
            "color_estado",
        ]
        read_only_fields = [
            "roles_autorizados",
            "ultima_actualizacion",
            "fecha_creacion",
            "fecha_modificacion",
        ]

    def get_tendencia(self, obj):
        """Get tendencia"""
        return obj.calcular_tendencia()

    def get_estado_vs_meta(self, obj):
        """Get estado vs meta"""
        return obj.get_estado_vs_meta()

    def get_color_estado(self, obj):
        """Get color estado"""
        return obj.get_estado_color()


class DashboardKPIResumenSerializer(serializers.ModelSerializer):
    """Serializer ligero para mostrar KPIs en tarjetas del dashboard.
    """

    categoria_display = serializers.CharField(
        source="get_categoria_display", read_only=True,
    )
    tendencia = serializers.SerializerMethodField()
    estado_vs_meta = serializers.SerializerMethodField()
    color_estado = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = DashboardKPI
        fields = [
            "id",
            "nombre",
            "codigo",
            "categoria",
            "categoria_display",
            "valor_actual",
            "unidad_medida",
            "tendencia",
            "estado_vs_meta",
            "color_estado",
            "icono",
            "orden_dashboard",
        ]

    def get_tendencia(self, obj):
        """Get tendencia"""
        return obj.calcular_tendencia()

    def get_estado_vs_meta(self, obj):
        """Get estado vs meta"""
        return obj.get_estado_vs_meta()

    def get_color_estado(self, obj):
        """Get color estado"""
        return obj.get_estado_color()


# ============================================================================
# SERIALIZERS PARA ALERTAS MÉDICAS
# ============================================================================


class AlertaMedicaSerializer(serializers.ModelSerializer):
    """Serializer detallado para alertas médicas.
    """

    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    prioridad_display = serializers.CharField(
        source="get_prioridad_display", read_only=True,
    )
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    modulo_origen_display = serializers.CharField(
        source="get_modulo_origen_display", read_only=True,
    )
    color_prioridad = serializers.SerializerMethodField()
    es_vencida = serializers.SerializerMethodField()
    tiempo_transcurrido = serializers.SerializerMethodField()
    paciente_nombre = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = AlertaMedica
        fields = [
            "id",
            "titulo",
            "descripcion",
            "tipo",
            "tipo_display",
            "prioridad",
            "prioridad_display",
            "estado",
            "estado_display",
            "paciente_id",
            "paciente_nombre",
            "embarazo_id",
            "medico_responsable_id",
            "modulo_origen",
            "modulo_origen_display",
            "registro_origen_id",
            "datos_contexto",
            "valor_actual",
            "valor_umbral",
            "accion_recomendada",
            "protocolo_seguimiento",
            "fecha_creacion",
            "fecha_vencimiento",
            "fecha_revision",
            "fecha_resolucion",
            "usuario_revision_id",
            "usuario_resolucion_id",
            "comentario_revision",
            "comentario_resolucion",
            "notificacion_enviada",
            "recordatorio_enviado",
            "escalamiento_automatico",
            "tiempo_escalamiento_horas",
            # Calculados
            "color_prioridad",
            "es_vencida",
            "tiempo_transcurrido",
        ]
        read_only_fields = [
            "fecha_creacion",
        ]

    def get_color_prioridad(self, obj):
        """Get color prioridad"""
        return obj.get_color_prioridad()

    def get_es_vencida(self, obj):
        """Get es vencida"""
        return obj.is_vencida()

    def get_tiempo_transcurrido(self, obj):
        """Get tiempo transcurrido"""
        delta = obj.tiempo_transcurrido()
        # Representación simple en horas
        return int(delta.total_seconds() // 3600)

    def get_paciente_nombre(self, obj):
        """Get paciente nombre"""
        if obj.paciente_id and obj.paciente:
            return obj.paciente.nombre_completo
        return None


class AlertaMedicaResumenSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados/tabla de alertas.
    """

    prioridad_display = serializers.CharField(
        source="get_prioridad_display", read_only=True,
    )
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    modulo_origen_display = serializers.CharField(
        source="get_modulo_origen_display", read_only=True,
    )
    color_prioridad = serializers.SerializerMethodField()
    es_vencida = serializers.SerializerMethodField()
    paciente_nombre = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = AlertaMedica
        fields = [
            "id",
            "titulo",
            "tipo",
            "prioridad",
            "prioridad_display",
            "estado",
            "estado_display",
            "paciente_id",
            "paciente_nombre",
            "modulo_origen",
            "modulo_origen_display",
            "fecha_creacion",
            "fecha_vencimiento",
            "color_prioridad",
            "es_vencida",
        ]

    def get_color_prioridad(self, obj):
        """Get color prioridad"""
        return obj.get_color_prioridad()

    def get_es_vencida(self, obj):
        """Get es vencida"""
        return obj.is_vencida()

    def get_paciente_nombre(self, obj):
        """Get paciente nombre"""
        if obj.paciente_id and obj.paciente:
            return obj.paciente.nombre_completo
        return None


# ============================================================================
# SERIALIZER PARA AUDITORÍA DE REPORTES
# ============================================================================


class AuditoriaReporteSerializer(serializers.ModelSerializer):
    """Serializer para registros de auditoría de reportes.
    """

    accion_display = serializers.CharField(source="get_accion_display", read_only=True)
    tipo_reporte_nombre = serializers.CharField(
        source="reporte_generado.tipo_reporte.nombre", read_only=True,
    )
    fecha_solicitud_reporte = serializers.DateTimeField(
        source="reporte_generado.fecha_solicitud", read_only=True,
    )

    class Meta:
        """Meta"""
        model = AuditoriaReporte
        fields = [
            "id",
            "reporte_generado",
            "tipo_reporte_nombre",
            "usuario_id",
            "accion",
            "accion_display",
            "fecha_accion",
            "direccion_ip",
            "user_agent",
            "detalles",
            "cumple_ley_3871",
            "justificacion_acceso",
            "observaciones",
            "fecha_solicitud_reporte",
        ]
        read_only_fields = [
            "fecha_accion",
        ]
