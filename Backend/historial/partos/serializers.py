# =============================================================================
# SERIALIZERS DE PARTOS
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: partos
# Descripción: Serializers para gestión de registros de partos
# Versión: 1.0.0
# =============================================================================

from rest_framework import serializers
from decimal import Decimal
from datetime import datetime, timedelta

from .models import Parto
from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario


# =============================================================================
# SERIALIZER PRINCIPAL DE PARTO
# =============================================================================

class PartoSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el modelo Parto.

    Incluye:
    - Validaciones extensas de todos los campos
    - Clasificaciones automáticas (peso RN, APGAR, edad gestacional)
    - Validación cruzada entre campos
    - Formateo de respuestas
    - Campos calculados
    - Evaluación de riesgos

    Campos calculados:
    - paciente_nombre: Nombre completo de la paciente
    - clasificacion_peso_rn: Clasificación del peso del RN
    - evaluacion_apgar: Interpretación de scores APGAR
    - clasificacion_edad_gestacional: Clasificación según semanas
    - riesgo_rn: Evaluación de riesgo neonatal
    - duracion_parto_texto: Duración formateada
    """

    # Campos calculados de solo lectura
    paciente_nombre = serializers.SerializerMethodField()
    clasificacion_peso_rn = serializers.SerializerMethodField()
    evaluacion_apgar = serializers.SerializerMethodField()
    clasificacion_edad_gestacional = serializers.SerializerMethodField()
    riesgo_rn = serializers.SerializerMethodField()
    duracion_parto_texto = serializers.SerializerMethodField()
    tiene_complicaciones = serializers.SerializerMethodField()

    class Meta:
        model = Parto
        fields = '__all__'
        read_only_fields = [
            'fecha_registro',
            'fecha_modificacion',
            'fecha_eliminacion',
            'creado_por',
            'modificado_por',
        ]

    # =========================================================================
    # MÉTODOS DE OBTENCIÓN DE CAMPOS CALCULADOS
    # =========================================================================

    def get_paciente_nombre(self, obj):
        """
        Retorna el nombre completo de la paciente.

        Args:
            obj: Instancia de Parto

        Returns:
            str: Nombre completo o None
        """
        if obj.paciente:
            return obj.paciente.get_nombre_completo()
        return None

    def get_clasificacion_peso_rn(self, obj):
        """
        Clasifica el peso del recién nacido.

        Clasificación:
        - <2500g: Bajo peso al nacer
        - 2500-4000g: Peso normal
        - >4000g: Macrosomía

        Args:
            obj: Instancia de Parto

        Returns:
            dict: Diccionario con clasificación del peso
        """
        if not obj.peso_rn_gramos:
            return None

        peso = obj.peso_rn_gramos
        clasificacion = {
            'peso': peso,
            'categoria': None,
            'recomendacion': None
        }

        if peso < 2500:
            clasificacion['categoria'] = 'Bajo peso al nacer'
            clasificacion['recomendacion'] = 'Evaluar causas y seguimiento estrecho'
        elif peso > 4000:
            clasificacion['categoria'] = 'Macrosomía'
            clasificacion['recomendacion'] = 'Descartar diabetes gestacional, seguimiento'
        else:
            clasificacion['categoria'] = 'Peso normal'
            clasificacion['recomendacion'] = 'Peso adecuado para recién nacido'

        # Clasificaciones adicionales
        if peso < 1500:
            clasificacion['severidad'] = 'Muy bajo peso al nacer'
        elif peso < 1000:
            clasificacion['severidad'] = 'Extremadamente bajo peso'

        return clasificacion

    def get_evaluacion_apgar(self, obj):
        """
        Evalúa e interpreta los scores APGAR.

        APGAR:
        - 7-10: Normal
        - 4-6: Depresión moderada
        - 0-3: Depresión severa

        Args:
            obj: Instancia de Parto

        Returns:
            dict: Diccionario con evaluación de APGAR
        """
        evaluacion = {
            'apgar_1_min': None,
            'apgar_5_min': None,
            'interpretacion': None,
            'requiere_atencion': False
        }

        # Evaluar APGAR 1 minuto
        if obj.apgar_1_min is not None:
            apgar1 = obj.apgar_1_min
            evaluacion['apgar_1_min'] = {
                'valor': apgar1,
                'estado': None
            }

            if apgar1 >= 7:
                evaluacion['apgar_1_min']['estado'] = 'Normal'
            elif apgar1 >= 4:
                evaluacion['apgar_1_min']['estado'] = 'Depresión moderada'
                evaluacion['requiere_atencion'] = True
            else:
                evaluacion['apgar_1_min']['estado'] = 'Depresión severa'
                evaluacion['requiere_atencion'] = True

        # Evaluar APGAR 5 minutos
        if obj.apgar_5_min is not None:
            apgar5 = obj.apgar_5_min
            evaluacion['apgar_5_min'] = {
                'valor': apgar5,
                'estado': None
            }

            if apgar5 >= 7:
                evaluacion['apgar_5_min']['estado'] = 'Normal'
            elif apgar5 >= 4:
                evaluacion['apgar_5_min']['estado'] = 'Depresión moderada'
                evaluacion['requiere_atencion'] = True
            else:
                evaluacion['apgar_5_min']['estado'] = 'Depresión severa'
                evaluacion['requiere_atencion'] = True

        # Interpretación general
        if obj.apgar_5_min is not None:
            if obj.apgar_5_min >= 7:
                evaluacion['interpretacion'] = 'RN en buenas condiciones'
            elif obj.apgar_5_min >= 4:
                evaluacion['interpretacion'] = 'RN requiere monitoreo'
            else:
                evaluacion['interpretacion'] = 'RN requiere atención inmediata'

        return evaluacion

    def get_clasificacion_edad_gestacional(self, obj):
        """
        Clasifica la edad gestacional al momento del parto.

        Clasificación:
        - <37 semanas: Prematuro
        - 37-42 semanas: A término
        - >42 semanas: Postérmino

        Args:
            obj: Instancia de Parto

        Returns:
            dict: Diccionario con clasificación
        """
        if not obj.edad_gestacional_parto_semanas:
            return None

        semanas = obj.edad_gestacional_parto_semanas
        clasificacion = {
            'semanas': semanas,
            'categoria': None,
            'recomendacion': None
        }

        if semanas < 37:
            clasificacion['categoria'] = 'Prematuro'
            if semanas < 28:
                clasificacion['severidad'] = 'Extremadamente prematuro'
                clasificacion['recomendacion'] = 'Cuidados intensivos neonatales'
            elif semanas < 32:
                clasificacion['severidad'] = 'Muy prematuro'
                clasificacion['recomendacion'] = 'UCI neonatal'
            elif semanas < 34:
                clasificacion['severidad'] = 'Prematuro moderado'
                clasificacion['recomendacion'] = 'Cuidados especiales'
            else:
                clasificacion['severidad'] = 'Prematuro tardío'
                clasificacion['recomendacion'] = 'Monitoreo cercano'
        elif semanas <= 42:
            clasificacion['categoria'] = 'A término'
            clasificacion['recomendacion'] = 'Edad gestacional adecuada'
        else:
            clasificacion['categoria'] = 'Postérmino'
            clasificacion['recomendacion'] = 'Vigilar signos de insuficiencia placentaria'

        return clasificacion

    def get_riesgo_rn(self, obj):
        """
        Evalúa el riesgo neonatal basado en múltiples factores.

        Factores de riesgo:
        - APGAR bajo (<7 a los 5 min)
        - Peso bajo (<2500g)
        - Prematuridad (<37 sem)
        - Reanimación neonatal
        - Complicaciones neonatales

        Args:
            obj: Instancia de Parto

        Returns:
            dict: Diccionario con evaluación de riesgo
        """
        riesgo = {
            'nivel': 'bajo',
            'factores': [],
            'puntaje': 0
        }

        # APGAR bajo
        if obj.apgar_5_min is not None and obj.apgar_5_min < 7:
            riesgo['factores'].append('APGAR bajo a los 5 minutos')
            riesgo['puntaje'] += 2

        # Bajo peso
        if obj.peso_rn_gramos and obj.peso_rn_gramos < 2500:
            riesgo['factores'].append('Bajo peso al nacer')
            riesgo['puntaje'] += 1
            if obj.peso_rn_gramos < 1500:
                riesgo['puntaje'] += 1

        # Prematuridad
        if obj.edad_gestacional_parto_semanas and obj.edad_gestacional_parto_semanas < 37:
            riesgo['factores'].append('Prematuridad')
            riesgo['puntaje'] += 1
            if obj.edad_gestacional_parto_semanas < 32:
                riesgo['puntaje'] += 2

        # Reanimación
        if obj.reanimacion_neonatal:
            riesgo['factores'].append('Requirió reanimación neonatal')
            riesgo['puntaje'] += 2

        # Complicaciones
        if obj.complicaciones_neonatales:
            riesgo['factores'].append('Complicaciones neonatales presentes')
            riesgo['puntaje'] += 2

        # Determinar nivel de riesgo
        if riesgo['puntaje'] >= 5:
            riesgo['nivel'] = 'alto'
            riesgo['recomendacion'] = 'UCI neonatal y seguimiento intensivo'
        elif riesgo['puntaje'] >= 3:
            riesgo['nivel'] = 'moderado'
            riesgo['recomendacion'] = 'Monitoreo estrecho'
        else:
            riesgo['nivel'] = 'bajo'
            riesgo['recomendacion'] = 'Cuidados neonatales de rutina'

        return riesgo

    def get_duracion_parto_texto(self, obj):
        """
        Formatea la duración del trabajo de parto.

        Args:
            obj: Instancia de Parto

        Returns:
            str: Duración formateada o None
        """
        if not obj.duracion_trabajo_parto_horas:
            return None

        horas = float(obj.duracion_trabajo_parto_horas)
        horas_int = int(horas)
        minutos = int((horas - horas_int) * 60)

        return f"{horas_int}h {minutos}min"

    def get_tiene_complicaciones(self, obj):
        """
        Indica si hubo complicaciones en el parto.

        Args:
            obj: Instancia de Parto

        Returns:
            bool: True si hay complicaciones
        """
        return bool(
            obj.complicaciones_maternas or
            obj.complicaciones_neonatales or
            obj.hemorragia_postparto or
            (obj.desgarros and obj.grado_desgarro in ['III', 'IV'])
        )

    # =========================================================================
    # MÉTODOS DE VALIDACIÓN
    # =========================================================================

    def validate_fecha_hora_parto(self, value):
        """
        Valida que la fecha del parto sea razonable.

        Args:
            value: Fecha y hora del parto

        Returns:
            datetime: Fecha validada

        Raises:
            ValidationError: Si la fecha no es válida
        """
        ahora = datetime.now()

        if value > ahora:
            raise serializers.ValidationError(
                "La fecha del parto no puede ser futura"
            )

        # No más de 10 años atrás
        limite_antiguo = ahora - timedelta(days=365*10)
        if value < limite_antiguo:
            raise serializers.ValidationError(
                "La fecha del parto es muy antigua. Verificar."
            )

        return value

    def validate_apgar_1_min(self, value):
        """Valida APGAR 1 minuto."""
        if value is not None and (value < 0 or value > 10):
            raise serializers.ValidationError(
                "APGAR debe estar entre 0 y 10"
            )
        return value

    def validate_apgar_5_min(self, value):
        """Valida APGAR 5 minutos."""
        if value is not None and (value < 0 or value > 10):
            raise serializers.ValidationError(
                "APGAR debe estar entre 0 y 10"
            )
        return value

    def validate_peso_rn_gramos(self, value):
        """Valida peso del RN."""
        if value and (value < 500 or value > 6000):
            raise serializers.ValidationError(
                f"Peso del RN ({value}g) fuera de rango razonable (500-6000g)"
            )
        return value

    def validate_talla_rn_cm(self, value):
        """Valida talla del RN."""
        if value and (value < 30.0 or value > 70.0):
            raise serializers.ValidationError(
                f"Talla del RN ({value}cm) fuera de rango razonable (30-70cm)"
            )
        return value

    def validate_sangrado_ml(self, value):
        """Valida sangrado."""
        if value and value > 2000:
            # Solo advertencia, no error
            pass  # Podría agregarse a warnings
        return value

    def validate(self, data):
        """
        Validación cruzada de campos.

        Verifica:
        - Coherencia entre tipo de parto y campos específicos
        - APGAR 5min >= APGAR 1min (generalmente)
        - Campos obligatorios según tipo de parto
        - Coherencia entre complicaciones y valores

        Args:
            data: Datos del parto

        Returns:
            dict: Datos validados

        Raises:
            ValidationError: Si hay inconsistencias
        """
        # Validar embarazo y paciente activos
        embarazo = data.get('embarazo')
        if embarazo and not embarazo.activo:
            raise serializers.ValidationError({
                'embarazo': 'El embarazo especificado no está activo'
            })

        paciente = data.get('paciente')
        if paciente and not paciente.activo:
            raise serializers.ValidationError({
                'paciente': 'La paciente especificada no está activa'
            })

        # Validar coherencia de APGAR
        apgar1 = data.get('apgar_1_min')
        apgar5 = data.get('apgar_5_min')

        if apgar1 is not None and apgar5 is not None:
            # Normalmente APGAR mejora, pero puede no mejorar
            if apgar5 < apgar1 - 3:
                # Advertencia: APGAR empeoró significativamente
                pass  # En producción, podría generar una alerta

        # Validar cesárea
        tipo_parto = data.get('tipo_parto')
        if tipo_parto == 'cesarea':
            if not data.get('indicacion_cesarea'):
                raise serializers.ValidationError({
                    'indicacion_cesarea': 'Debe especificar la indicación de la cesárea'
                })

        # Validar desgarros
        if data.get('desgarros') and not data.get('grado_desgarro'):
            raise serializers.ValidationError({
                'grado_desgarro': 'Debe especificar el grado del desgarro'
            })

        # Validar hemorragia
        if data.get('hemorragia_postparto') and not data.get('sangrado_ml'):
            raise serializers.ValidationError({
                'sangrado_ml': 'Debe especificar la cantidad de sangrado'
            })

        return data


# =============================================================================
# SERIALIZER PARA LISTADOS
# =============================================================================

class PartoListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listados de partos."""

    paciente_nombre = serializers.SerializerMethodField()
    tipo_parto_display = serializers.CharField(source='get_tipo_parto_display', read_only=True)
    tiene_complicaciones = serializers.SerializerMethodField()

    class Meta:
        model = Parto
        fields = [
            'id',
            'uuid',
            'paciente',
            'paciente_nombre',
            'embarazo',
            'fecha_hora_parto',
            'tipo_parto',
            'tipo_parto_display',
            'peso_rn_gramos',
            'apgar_5_min',
            'edad_gestacional_parto_semanas',
            'tiene_complicaciones',
            'fecha_registro',
        ]

    def get_paciente_nombre(self, obj):
        if obj.paciente:
            return obj.paciente.get_nombre_completo()
        return None

    def get_tiene_complicaciones(self, obj):
        return bool(
            obj.complicaciones_maternas or
            obj.complicaciones_neonatales or
            obj.hemorragia_postparto
        )


# =============================================================================
# SERIALIZER PARA CREACIÓN
# =============================================================================

class PartoCreateSerializer(serializers.ModelSerializer):
    """Serializer para creación de partos."""

    class Meta:
        model = Parto
        fields = '__all__'
        read_only_fields = [
            'fecha_registro',
            'fecha_modificacion',
            'fecha_eliminacion',
            'creado_por',
            'modificado_por',
        ]

    def validate_embarazo(self, value):
        """Valida que el embarazo existe y está activo."""
        try:
            embarazo = Embarazo.objects.get(id=value.id, activo=True)
            return embarazo
        except Embarazo.DoesNotExist:
            raise serializers.ValidationError(
                "El embarazo especificado no existe o no está activo"
            )

    def validate_paciente(self, value):
        """Valida que la paciente existe y está activa."""
        try:
            paciente = Paciente.objects.get(id=value.id, activo=True)
            return paciente
        except Paciente.DoesNotExist:
            raise serializers.ValidationError(
                "La paciente especificada no existe o no está activa"
            )

    def create(self, validated_data):
        """Crea un nuevo registro de parto."""
        # Asignar usuario que crea
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['creado_por'] = request.user

        parto = Parto.objects.create(**validated_data)
        return parto
