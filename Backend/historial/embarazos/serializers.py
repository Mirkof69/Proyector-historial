# =============================================================================
# SERIALIZERS DE EMBARAZOS
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: embarazos
# Descripción: Serializers completos para el módulo de embarazos y complicaciones.
#              Incluye validaciones médicas, cálculos automáticos y transformación
#              de datos para API REST.
# Autor: Sistema de Gestión Médica
# Versión: 3.0.0 COMPLETO
# Última actualización: 2025-11-14
# =============================================================================

from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from datetime import date, timedelta
import re

from .models import Embarazo, ComplicacionEmbarazo
from pacientes.models import Paciente
from usuarios.models import Usuario


# =============================================================================
# SERIALIZER BASE DE EMBARAZO (LECTURA COMPLETA)
# =============================================================================

class EmbarazoSerializer(serializers.ModelSerializer):
    """
    Serializer completo para lectura de embarazos.

    Incluye:
    - Todos los campos del modelo
    - Campos calculados (edad gestacional, trimestre, riesgo)
    - Información relacionada de paciente
    - Lista de complicaciones
    - Información de médico responsable
    """

    # Campos relacionados de solo lectura
    paciente_nombre = serializers.CharField(source='paciente.nombres', read_only=True)
    paciente_apellidos = serializers.CharField(source='paciente.apellidos', read_only=True)
    paciente_nombre_completo = serializers.SerializerMethodField()
    paciente_cedula = serializers.CharField(source='paciente.cedula_identidad', read_only=True)
    paciente_edad = serializers.SerializerMethodField()

    # Campos calculados del embarazo
    edad_gestacional_actual = serializers.SerializerMethodField()
    edad_gestacional_texto = serializers.SerializerMethodField()
    trimestre = serializers.SerializerMethodField()
    semanas_restantes = serializers.SerializerMethodField()
    dias_gestacionales = serializers.SerializerMethodField()

    # Información de riesgo
    nivel_riesgo_calculado = serializers.SerializerMethodField()
    complicaciones_lista = serializers.SerializerMethodField()
    numero_complicaciones = serializers.SerializerMethodField()

    # IMC
    imc_calculado = serializers.SerializerMethodField()
    clasificacion_imc_display = serializers.SerializerMethodField()

    # Médico responsable
    medico_nombre = serializers.CharField(source='medico_responsable', read_only=True)
    medico_especialidad = serializers.SerializerMethodField()

    # Formateo de fechas
    fecha_ultima_menstruacion_formatted = serializers.SerializerMethodField()
    fecha_probable_parto_formatted = serializers.SerializerMethodField()
    fecha_finalizacion_formatted = serializers.SerializerMethodField()

    # Estado legible
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tipo_embarazo_display = serializers.CharField(source='get_tipo_embarazo_display', read_only=True)

    class Meta:
        model = Embarazo
        fields = '__all__'
        read_only_fields = [
            'id', 'uuid', 'fecha_registro', 'fecha_modificacion',
            'fecha_eliminacion', 'imc_pregestacional', 'clasificacion_imc',
            'fecha_probable_parto'
        ]

    # -------------------------------------------------------------------------
    # MÉTODOS SERIALIZADORES
    # -------------------------------------------------------------------------

    def get_paciente_nombre_completo(self, obj):
        """Nombre completo de la paciente."""
        if obj.paciente:
            return f"{obj.paciente.nombres} {obj.paciente.apellidos}"
        return None

    def get_paciente_edad(self, obj):
        """Edad de la paciente."""
        if obj.paciente:
            return obj.paciente.calcular_edad()
        return None

    def get_edad_gestacional_actual(self, obj):
        """Edad gestacional actual en semanas decimales."""
        return obj.get_edad_gestacional_actual()

    def get_edad_gestacional_texto(self, obj):
        """Edad gestacional en formato texto legible."""
        eg = obj.get_edad_gestacional_actual()
        if eg:
            semanas = int(eg)
            dias = int((eg - semanas) * 7)
            return f"{semanas} semanas + {dias} días"
        return None

    def get_trimestre(self, obj):
        """Trimestre actual del embarazo."""
        return obj.get_trimestre_actual()

    def get_semanas_restantes(self, obj):
        """Semanas restantes hasta FPP."""
        return obj.get_semanas_restantes()

    def get_dias_gestacionales(self, obj):
        """Días totales de gestación."""
        return obj.get_dias_gestacionales()

    def get_nivel_riesgo_calculado(self, obj):
        """Nivel de riesgo evaluado automáticamente."""
        return obj.evaluar_nivel_riesgo()

    def get_complicaciones_lista(self, obj):
        """Lista de complicaciones del embarazo."""
        return obj.get_complicaciones_listado()

    def get_numero_complicaciones(self, obj):
        """Número total de complicaciones."""
        return len(obj.get_complicaciones_listado())

    def get_imc_calculado(self, obj):
        """IMC pre-gestacional calculado."""
        return obj.calcular_imc_pregestacional()

    def get_clasificacion_imc_display(self, obj):
        """Clasificación del IMC."""
        return obj.clasificar_imc()

    def get_medico_especialidad(self, obj):
        """Especialidad del médico responsable."""
        if obj.medico_responsable_fk:
            return obj.medico_responsable_fk.especialidad
        return None

    def get_fecha_ultima_menstruacion_formatted(self, obj):
        """FUR formateada."""
        if obj.fecha_ultima_menstruacion:
            return obj.fecha_ultima_menstruacion.strftime('%d/%m/%Y')
        return None

    def get_fecha_probable_parto_formatted(self, obj):
        """FPP formateada."""
        fpp = obj.get_fecha_parto_estimada()
        if fpp:
            return fpp.strftime('%d/%m/%Y')
        return None

    def get_fecha_finalizacion_formatted(self, obj):
        """Fecha de finalización formateada."""
        if obj.fecha_finalizacion:
            return obj.fecha_finalizacion.strftime('%d/%m/%Y')
        return None


# =============================================================================
# SERIALIZER PARA CREACIÓN DE EMBARAZOS
# =============================================================================

class EmbarazoCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para creación de nuevos embarazos.

    Validaciones:
    - FUR no puede ser futura
    - Paciente debe existir y estar activa
    - Edad gestacional coherente
    - Validaciones antropométricas
    """

    class Meta:
        model = Embarazo
        exclude = ['fecha_registro', 'fecha_modificacion', 'creado_por', 'modificado_por',
                   'fecha_eliminacion', 'eliminado_por', 'imc_pregestacional',
                   'clasificacion_imc', 'fecha_probable_parto', 'eliminado']

    def validate_paciente(self, value):
        """Valida que la paciente exista y esté activa."""
        if not value.activo:
            raise serializers.ValidationError(
                "La paciente está inactiva. No se puede crear un embarazo."
            )
        return value

    def validate_fecha_ultima_menstruacion(self, value):
        """Valida que la FUR no sea futura."""
        if value > timezone.now().date():
            raise serializers.ValidationError(
                "La Fecha de Última Regla (FUR) no puede ser futura."
            )

        # Validar que no sea muy antigua (>1 año)
        hace_un_anio = timezone.now().date() - timedelta(days=365)
        if value < hace_un_anio:
            raise serializers.ValidationError(
                "La FUR no puede ser mayor a 1 año. Verifique la fecha."
            )

        return value

    def validate_numero_gesta(self, value):
        """Valida número de gesta."""
        if value < 1:
            raise serializers.ValidationError(
                "El número de gesta debe ser al menos 1 (embarazo actual)."
            )
        if value > 20:
            raise serializers.ValidationError(
                "Número de gesta inusualmente alto. Verifique el dato."
            )
        return value

    def validate_peso_pregestacional(self, value):
        """Valida peso pre-gestacional."""
        if value:
            if value < 30 or value > 200:
                raise serializers.ValidationError(
                    "Peso pre-gestacional fuera de rango válido (30-200 kg)."
                )
        return value

    def validate_talla_madre(self, value):
        """Valida talla materna."""
        if value:
            if value < 120 or value > 220:
                raise serializers.ValidationError(
                    "Talla fuera de rango válido (120-220 cm)."
                )
        return value

    def validate(self, data):
        """Validaciones cruzadas."""
        errors = {}

        # Validar tipo de embarazo vs número de fetos
        tipo_embarazo = data.get('tipo_embarazo')
        numero_fetos = data.get('numero_fetos', 1)

        if tipo_embarazo == 'unico' and numero_fetos != 1:
            errors['numero_fetos'] = "Embarazo único debe tener 1 feto."

        if tipo_embarazo == 'gemelar' and numero_fetos != 2:
            errors['numero_fetos'] = "Embarazo gemelar debe tener 2 fetos."

        # Validar corionicidad solo para embarazos múltiples
        if tipo_embarazo == 'unico' and data.get('corionicidad'):
            errors['corionicidad'] = "Corionicidad solo aplica para embarazos múltiples."

        # Validar fechas de complicaciones
        fur = data.get('fecha_ultima_menstruacion')
        if fur:
            # Diabetes gestacional
            if data.get('diabetes_gestacional_fecha'):
                if data['diabetes_gestacional_fecha'] < fur:
                    errors['diabetes_gestacional_fecha'] = "Fecha no puede ser anterior a FUR."

            # Preeclampsia
            if data.get('preeclampsia_fecha'):
                if data['preeclampsia_fecha'] < fur:
                    errors['preeclampsia_fecha'] = "Fecha no puede ser anterior a FUR."

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        """Crea un nuevo embarazo con cálculos automáticos."""
        # El método save() del modelo ya calcula FPP, IMC, etc.
        embarazo = Embarazo.objects.create(**validated_data)
        return embarazo


# =============================================================================
# SERIALIZER PARA ACTUALIZACIÓN DE EMBARAZOS
# =============================================================================

class EmbarazoUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualización de embarazos existentes.
    Permite actualizar complicaciones, datos antropométricos, etc.
    """

    class Meta:
        model = Embarazo
        exclude = ['id', 'uuid', 'paciente', 'fecha_registro', 'creado_por',
                   'fecha_eliminacion', 'eliminado_por', 'eliminado']
        read_only_fields = ['fecha_modificacion']

    def validate(self, data):
        """Validaciones para actualización."""
        # No permitir cambiar paciente
        if 'paciente' in data:
            raise serializers.ValidationError({
                'paciente': "No se puede cambiar la paciente de un embarazo existente."
            })

        # Si se finaliza el embarazo, validar datos
        if data.get('estado') and data['estado'] != 'en_curso':
            if not data.get('fecha_finalizacion'):
                raise serializers.ValidationError({
                    'fecha_finalizacion': "Debe especificar fecha de finalización."
                })

            if not data.get('edad_gestacional_finalizacion'):
                raise serializers.ValidationError({
                    'edad_gestacional_finalizacion': "Debe especificar edad gestacional de finalización."
                })

        return data


# =============================================================================
# SERIALIZER DETALLADO DE EMBARAZO (CON RELACIONES)
# =============================================================================

class EmbarazoDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para visualización completa de embarazo.

    Incluye:
    - Todos los datos del embarazo
    - Información completa de la paciente
    - Complicaciones detalladas
    - Controles prenatales (opcional)
    - Estadísticas del embarazo
    """

    # Paciente completa
    paciente_detalle = serializers.SerializerMethodField()

    # Complicaciones detalladas
    complicaciones_detalladas = serializers.SerializerMethodField()

    # Controles prenatales
    numero_controles = serializers.SerializerMethodField()
    ultimo_control = serializers.SerializerMethodField()

    # Métricas del embarazo
    edad_gestacional_actual = serializers.SerializerMethodField()
    trimestre_actual = serializers.SerializerMethodField()
    nivel_riesgo_evaluado = serializers.SerializerMethodField()
    dias_hasta_parto = serializers.SerializerMethodField()

    # Información adicional
    complicaciones_lista = serializers.SerializerMethodField()
    requiere_atencion_urgente = serializers.SerializerMethodField()

    class Meta:
        model = Embarazo
        fields = '__all__'

    def get_paciente_detalle(self, obj):
        """Información completa de la paciente."""
        if obj.paciente:
            return {
                'id': obj.paciente.id,
                'nombre_completo': f"{obj.paciente.nombres} {obj.paciente.apellidos}",
                'cedula': obj.paciente.cedula_identidad,
                'edad': obj.paciente.calcular_edad(),
                'telefono': obj.paciente.telefono_principal,
                'email': obj.paciente.email,
                'direccion': obj.paciente.direccion,
                'grupo_sanguineo': obj.paciente.grupo_sanguineo,
                'factor_rh': obj.paciente.factor_rh
            }
        return None

    def get_complicaciones_detalladas(self, obj):
        """Complicaciones detalladas del embarazo."""
        complicaciones = ComplicacionEmbarazo.objects.filter(embarazo=obj).order_by('-fecha_diagnostico')
        return ComplicacionEmbarazoSerializer(complicaciones, many=True).data

    def get_numero_controles(self, obj):
        """Número total de controles prenatales."""
        return obj.controles.filter(activo=True).count()

    def get_ultimo_control(self, obj):
        """Información del último control prenatal."""
        ultimo = obj.controles.filter(activo=True).order_by('-fecha_control').first()
        if ultimo:
            return {
                'fecha': ultimo.fecha_control,
                'semanas_gestacion': ultimo.semanas_gestacion,
                'peso': float(ultimo.peso_actual) if ultimo.peso_actual else None,
                'presion_sistolica': ultimo.presion_arterial_sistolica,
                'presion_diastolica': ultimo.presion_arterial_diastolica
            }
        return None

    def get_edad_gestacional_actual(self, obj):
        """Edad gestacional actual."""
        return obj.get_edad_gestacional_actual()

    def get_trimestre_actual(self, obj):
        """Trimestre actual."""
        return obj.get_trimestre_actual()

    def get_nivel_riesgo_evaluado(self, obj):
        """Nivel de riesgo evaluado."""
        return obj.evaluar_nivel_riesgo()

    def get_dias_hasta_parto(self, obj):
        """Días hasta la fecha probable de parto."""
        if obj.estado == 'en_curso':
            fpp = obj.get_fecha_parto_estimada()
            if fpp:
                dias = (fpp - timezone.now().date()).days
                return dias
        return None

    def get_complicaciones_lista(self, obj):
        """Lista de complicaciones."""
        return obj.get_complicaciones_listado()

    def get_requiere_atencion_urgente(self, obj):
        """Indica si requiere atención urgente."""
        # Criterios de urgencia
        if obj.estado != 'en_curso':
            return False

        urgente = False

        # Complicaciones graves
        if obj.eclampsia or obj.sindrome_hellp:
            urgente = True

        # Preeclampsia grave
        if obj.preeclampsia and obj.preeclampsia_severidad == 'grave':
            urgente = True

        # Desprendimiento de placenta
        if obj.desprendimiento_placenta:
            urgente = True

        # Riesgo muy alto
        if obj.evaluar_nivel_riesgo() == 'muy_alto':
            urgente = True

        return urgente


# =============================================================================
# SERIALIZER PARA LISTADO SIMPLE DE EMBARAZOS
# =============================================================================

class EmbarazoListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listados de embarazos.
    Optimizado para rendimiento en listas largas.
    """

    paciente_nombre = serializers.CharField(source='paciente.nombres', read_only=True)
    paciente_apellidos = serializers.CharField(source='paciente.apellidos', read_only=True)
    paciente_cedula = serializers.CharField(source='paciente.cedula_identidad', read_only=True)

    edad_gestacional = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    nivel_riesgo_display = serializers.CharField(source='get_nivel_riesgo_display', read_only=True)

    class Meta:
        model = Embarazo
        fields = [
            'id', 'uuid', 'paciente', 'paciente_nombre', 'paciente_apellidos',
            'paciente_cedula', 'numero_gesta', 'fecha_ultima_menstruacion',
            'fecha_probable_parto', 'tipo_embarazo', 'estado', 'estado_display',
            'nivel_riesgo', 'nivel_riesgo_display', 'edad_gestacional',
            'embarazo_alto_riesgo', 'tiene_complicaciones'
        ]

    def get_edad_gestacional(self, obj):
        """Edad gestacional simplificada."""
        eg = obj.get_edad_gestacional_actual()
        if eg:
            return f"{int(eg)} sem"
        return None


# =============================================================================
# SERIALIZER DE COMPLICACIÓN DE EMBARAZO
# =============================================================================

class ComplicacionEmbarazoSerializer(serializers.ModelSerializer):
    """
    Serializer completo para complicaciones de embarazo.
    """

    tipo_complicacion_display = serializers.CharField(
        source='get_tipo_complicacion_display',
        read_only=True
    )
    severidad_display = serializers.CharField(
        source='get_severidad_display',
        read_only=True
    )

    embarazo_info = serializers.SerializerMethodField()
    creado_por_nombre = serializers.CharField(source='creado_por.get_nombre_completo', read_only=True)

    class Meta:
        model = ComplicacionEmbarazo
        fields = '__all__'
        read_only_fields = ['id', 'fecha_creacion', 'fecha_modificacion']

    def get_embarazo_info(self, obj):
        """Información básica del embarazo."""
        if obj.embarazo:
            return {
                'id': obj.embarazo.id,
                'paciente': f"{obj.embarazo.paciente.nombres} {obj.embarazo.paciente.apellidos}",
                'numero_gesta': obj.embarazo.numero_gesta,
                'edad_gestacional': obj.embarazo.get_edad_gestacional_actual()
            }
        return None

    def validate_fecha_diagnostico(self, value):
        """Valida fecha de diagnóstico."""
        if value > timezone.now().date():
            raise serializers.ValidationError("La fecha de diagnóstico no puede ser futura.")
        return value

    def validate(self, data):
        """Validaciones cruzadas."""
        # Validar que fecha de diagnóstico no sea anterior a FUR
        embarazo = data.get('embarazo')
        fecha_diag = data.get('fecha_diagnostico')

        if embarazo and fecha_diag:
            if fecha_diag < embarazo.fecha_ultima_menstruacion:
                raise serializers.ValidationError({
                    'fecha_diagnostico': "La fecha no puede ser anterior a la FUR del embarazo."
                })

        # Si está resuelto, debe tener fecha de resolución
        if data.get('resuelto') and not data.get('fecha_resolucion'):
            raise serializers.ValidationError({
                'fecha_resolucion': "Debe especificar fecha de resolución si la complicación está resuelta."
            })

        return data


# =============================================================================
# SERIALIZER PARA CREACIÓN DE COMPLICACIONES
# =============================================================================

class ComplicacionEmbarazoCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear nuevas complicaciones.
    """

    class Meta:
        model = ComplicacionEmbarazo
        exclude = ['fecha_creacion', 'creado_por', 'fecha_modificacion', 'modificado_por']

    def validate(self, data):
        """Validaciones."""
        embarazo = data.get('embarazo')

        # Validar que el embarazo esté activo
        if not embarazo.activo:
            raise serializers.ValidationError({
                'embarazo': "No se pueden registrar complicaciones en embarazos eliminados."
            })

        # Validar fecha de diagnóstico
        if data.get('fecha_diagnostico'):
            if data['fecha_diagnostico'] < embarazo.fecha_ultima_menstruacion:
                raise serializers.ValidationError({
                    'fecha_diagnostico': "Fecha no puede ser anterior a FUR del embarazo."
                })

        return data


# =============================================================================
# SERIALIZER PARA ESTADÍSTICAS DE EMBARAZOS
# =============================================================================

class EmbarazoEstadisticasSerializer(serializers.Serializer):
    """
    Serializer para estadísticas agregadas de embarazos.
    """

    total_embarazos = serializers.IntegerField()
    embarazos_en_curso = serializers.IntegerField()
    embarazos_finalizados = serializers.IntegerField()
    embarazos_alto_riesgo = serializers.IntegerField()
    embarazos_con_complicaciones = serializers.IntegerField()

    promedio_edad_gestacional = serializers.FloatField()
    embarazos_primer_trimestre = serializers.IntegerField()
    embarazos_segundo_trimestre = serializers.IntegerField()
    embarazos_tercer_trimestre = serializers.IntegerField()

    embarazos_unicos = serializers.IntegerField()
    embarazos_multiples = serializers.IntegerField()

    total_complicaciones = serializers.IntegerField()
    complicacion_mas_frecuente = serializers.CharField()


# =============================================================================
# FIN DEL ARCHIVO - embarazos/serializers.py
# =============================================================================
