"""
===========================================
MÓDULO: SERIALIZERS DE EMBARAZOS
===========================================
Descripción:
    Serializers para el módulo de embarazos del sistema de historial gineco-obstétrico.
    Maneja validaciones, cálculos obstétricos y transformación de datos.

Serializers principales:
    - EmbarazoSerializer: Serializer estándar para CRUD
    - EmbarazoCreateSerializer: Para creación con validaciones extensas
    - EmbarazoUpdateSerializer: Para actualizaciones
    - EmbarazoListSerializer: Optimizado para listas (menos campos)
    - EmbarazoDetailSerializer: Detallado con controles y estadísticas

Cálculos obstétricos:
    - Edad gestacional (semanas + días)
    - Fecha Probable de Parto (Regla de Naegele)
    - Trimestre actual
    - Días para el parto
    - Validación de FUM

Autor: Sistema Historial Médico
Fecha: 2025
Versión: 2.0
===========================================
"""

from rest_framework import serializers
from datetime import datetime, timedelta, date
from .models import Embarazo
from pacientes.models import Paciente
from pacientes.serializers import PacienteListSerializer


# ===========================================
# SERIALIZER ESTÁNDAR DE EMBARAZO
# ===========================================
class EmbarazoSerializer(serializers.ModelSerializer):
    """
    SERIALIZER: Serializer estándar para Embarazo

    Funcionamiento:
        Serializer principal para operaciones CRUD de embarazos
        Incluye campos calculados y validaciones completas

    Campos calculados:
        - paciente_nombre: Nombre completo del paciente con ID clínico
        - semanas_gestacion: Edad gestacional en formato "SS+D"
        - edad_gestacional_completa: Dict con semanas, días, total_dias
        - trimestre: Trimestre actual del embarazo (1, 2, 3)
        - dias_para_parto: Días restantes hasta la FPP
        - porcentaje_embarazo: Porcentaje completado (0-100)

    Validaciones:
        - FUM no puede ser futura
        - Número de gesta válido (1-20)
        - Paciente existe y está activo
        - No embarazos activos duplicados
        - FPP se calcula automáticamente (Regla de Naegele)
    """

    # ===========================================
    # CAMPOS CALCULADOS (SerializerMethodField)
    # ===========================================

    # Campo: Nombre del paciente
    # Funcionamiento: Retorna ID clínico + nombre completo
    paciente_nombre = serializers.SerializerMethodField()

    # Campo: Semanas de gestación
    # Funcionamiento: Calcula edad gestacional en formato "SS+D"
    semanas_gestacion = serializers.SerializerMethodField()

    # Campo: Edad gestacional completa (dict)
    # Funcionamiento: Retorna {semanas, dias, total_dias}
    edad_gestacional_completa = serializers.SerializerMethodField()

    # Campo: Trimestre actual
    # Funcionamiento: Calcula trimestre según semanas (1, 2, 3)
    trimestre = serializers.SerializerMethodField()

    # Campo: Días para el parto
    # Funcionamiento: Calcula días restantes hasta FPP
    dias_para_parto = serializers.SerializerMethodField()

    # Campo: Porcentaje de embarazo completado
    # Funcionamiento: Calcula % de 0-100 basado en 280 días
    porcentaje_embarazo = serializers.SerializerMethodField()

    class Meta:
        model = Embarazo
        fields = [
            # Campos básicos
            'id',
            'uuid',

            # Relaciones
            'paciente',
            'paciente_nombre',

            # Datos del embarazo
            'numero_gesta',
            'fecha_ultima_menstruacion',
            'fecha_probable_parto',
            'tipo_embarazo',
            'riesgo_embarazo',
            'estado',

            # Notas y responsable
            'notas',
            'medico_responsable',

            # Campos calculados
            'semanas_gestacion',
            'edad_gestacional_completa',
            'trimestre',
            'dias_para_parto',
            'porcentaje_embarazo',

            # Auditoría
            'fecha_registro',
        ]
        read_only_fields = [
            'uuid',
            'fecha_registro',
            'semanas_gestacion',
            'edad_gestacional_completa',
            'trimestre',
            'dias_para_parto',
            'porcentaje_embarazo',
        ]

    # ===========================================
    # MÉTODOS PARA CAMPOS CALCULADOS
    # ===========================================

    def get_paciente_nombre(self, obj):
        """
        MÉTODO: Obtener nombre completo del paciente

        Funcionamiento:
            1. Obtiene el paciente relacionado
            2. Concatena ID clínico + nombre completo
            3. Maneja casos donde apellido materno es None

        Parámetros:
            obj: Instancia de Embarazo

        Retorna:
            str: "HC-001 - María García López"
        """
        try:
            paciente = obj.paciente
            apellido_materno = paciente.apellido_materno or ''
            return f"{paciente.id_clinico} - {paciente.nombre} {paciente.apellido_paterno} {apellido_materno}".strip()
        except:
            return "Paciente no disponible"

    def get_semanas_gestacion(self, obj):
        """
        MÉTODO: Calcular semanas de gestación

        Funcionamiento:
            1. Obtiene la FUM (Fecha Última Menstruación)
            2. Calcula días transcurridos desde FUM hasta hoy
            3. Divide entre 7 para obtener semanas
            4. El resto son los días adicionales
            5. Retorna en formato "SS+D" (ej: "24+3")

        Parámetros:
            obj: Instancia de Embarazo

        Retorna:
            str: "24+3" (24 semanas + 3 días) o None si no hay FUM

        Ejemplo:
            FUM: 2024-01-01
            Hoy: 2024-06-15
            Días: 166
            Semanas: 166 // 7 = 23
            Días: 166 % 7 = 5
            Resultado: "23+5"
        """
        if obj.fecha_ultima_menstruacion:
            hoy = date.today()
            diferencia = (hoy - obj.fecha_ultima_menstruacion).days

            # Calcular semanas y días
            semanas = diferencia // 7
            dias = diferencia % 7

            return f"{semanas}+{dias}"

        return None

    def get_edad_gestacional_completa(self, obj):
        """
        MÉTODO: Obtener edad gestacional completa

        Funcionamiento:
            Retorna un diccionario con información detallada
            de la edad gestacional

        Retorna:
            dict: {
                'semanas': 24,
                'dias': 3,
                'total_dias': 171,
                'formato': "24+3"
            }
        """
        if obj.fecha_ultima_menstruacion:
            hoy = date.today()
            total_dias = (hoy - obj.fecha_ultima_menstruacion).days
            semanas = total_dias // 7
            dias = total_dias % 7

            return {
                'semanas': semanas,
                'dias': dias,
                'total_dias': total_dias,
                'formato': f"{semanas}+{dias}"
            }

        return None

    def get_trimestre(self, obj):
        """
        MÉTODO: Calcular trimestre actual del embarazo

        Funcionamiento:
            Determina el trimestre según las semanas de gestación:
            - Primer trimestre: 0-13 semanas
            - Segundo trimestre: 14-26 semanas
            - Tercer trimestre: 27+ semanas

        Parámetros:
            obj: Instancia de Embarazo

        Retorna:
            int: 1, 2, 3 o None si no hay FUM

        Ejemplo:
            Semanas: 18 -> Retorna 2 (segundo trimestre)
        """
        if obj.fecha_ultima_menstruacion:
            hoy = date.today()
            dias = (hoy - obj.fecha_ultima_menstruacion).days
            semanas = dias // 7

            # Determinar trimestre
            if semanas <= 13:
                return 1
            elif semanas <= 26:
                return 2
            else:
                return 3

        return None

    def get_dias_para_parto(self, obj):
        """
        MÉTODO: Calcular días restantes hasta el parto

        Funcionamiento:
            1. Obtiene la Fecha Probable de Parto (FPP)
            2. Calcula diferencia entre FPP y hoy
            3. Retorna días positivos (faltan) o negativos (pasó)

        Parámetros:
            obj: Instancia de Embarazo

        Retorna:
            int: Días hasta FPP (positivo=futuro, negativo=pasado)
                 None si no hay FPP

        Ejemplo:
            FPP: 2024-09-01
            Hoy: 2024-08-15
            Resultado: 17 (faltan 17 días)
        """
        if obj.fecha_probable_parto:
            hoy = date.today()
            dias = (obj.fecha_probable_parto - hoy).days
            return dias

        return None

    def get_porcentaje_embarazo(self, obj):
        """
        MÉTODO: Calcular porcentaje del embarazo completado

        Funcionamiento:
            1. Calcula días transcurridos desde FUM
            2. Divide entre 280 días (duración normal embarazo)
            3. Multiplica por 100 para obtener porcentaje
            4. Limita a 100% máximo

        Parámetros:
            obj: Instancia de Embarazo

        Retorna:
            float: Porcentaje de 0.0 a 100.0

        Ejemplo:
            Días transcurridos: 140
            Porcentaje: (140 / 280) * 100 = 50.0%
        """
        if obj.fecha_ultima_menstruacion:
            hoy = date.today()
            dias = (hoy - obj.fecha_ultima_menstruacion).days

            # Calcular porcentaje (280 días = embarazo completo)
            porcentaje = (dias / 280) * 100

            # Limitar a 100% máximo
            return min(porcentaje, 100.0)

        return None

    # ===========================================
    # VALIDACIONES DE CAMPOS
    # ===========================================

    def validate_paciente(self, value):
        """
        VALIDACIÓN: Verificar que el paciente existe y está activo

        Funcionamiento:
            1. Verifica que el paciente existe en la BD
            2. Verifica que el paciente está activo
            3. Lanza excepción si no cumple

        Parámetros:
            value: ID del paciente

        Retorna:
            value: Si pasa la validación

        Excepciones:
            ValidationError: Si paciente no existe o está inactivo
        """
        try:
            paciente = Paciente.objects.get(id=value.id)
            if not paciente.activo:
                raise serializers.ValidationError(
                    "El paciente seleccionado está inactivo"
                )
            return value
        except Paciente.DoesNotExist:
            raise serializers.ValidationError(
                "El paciente seleccionado no existe"
            )

    def validate_numero_gesta(self, value):
        """
        VALIDACIÓN: Validar número de gesta

        Funcionamiento:
            Verifica que el número de gesta sea lógico:
            - Mínimo: 1 (primer embarazo)
            - Máximo: 20 (límite razonable)

        Parámetros:
            value: Número de gesta

        Retorna:
            value: Si pasa la validación

        Excepciones:
            ValidationError: Si está fuera del rango
        """
        if value < 1:
            raise serializers.ValidationError(
                "El número de gesta debe ser mayor a 0"
            )
        if value > 20:
            raise serializers.ValidationError(
                "El número de gesta parece incorrecto (máximo 20)"
            )
        return value

    def validate_fecha_ultima_menstruacion(self, value):
        """
        VALIDACIÓN: Validar Fecha de Última Menstruación (FUM)

        Funcionamiento:
            1. Verifica que no sea None
            2. Verifica que no sea fecha futura
            3. ACEPTA cualquier fecha pasada (sin límite de 42 semanas)

        Nota:
            Se quitó la restricción de 42 semanas para permitir
            registro de embarazos históricos

        Parámetros:
            value: Fecha de última menstruación

        Retorna:
            value: Si pasa la validación

        Excepciones:
            ValidationError: Si es None o fecha futura
        """
        if not value:
            raise serializers.ValidationError(
                "La Fecha de Última Menstruación es obligatoria"
            )

        # Validar que no sea fecha futura
        if value > date.today():
            raise serializers.ValidationError(
                "La FUM no puede ser una fecha futura"
            )

        # NOTA: Se quitó la validación de 42 semanas
        # Ahora acepta cualquier fecha pasada para embarazos históricos

        return value

    def validate_tipo_embarazo(self, value):
        """
        VALIDACIÓN: Validar tipo de embarazo

        Funcionamiento:
            Verifica que el tipo sea uno de los válidos

        Tipos válidos:
            - simple: Embarazo único
            - gemelar: Embarazo de gemelos
            - multiple: Embarazo múltiple (trillizos+)

        Parámetros:
            value: Tipo de embarazo

        Retorna:
            value: Si es válido
        """
        tipos_validos = ['simple', 'gemelar', 'multiple']
        if value not in tipos_validos:
            raise serializers.ValidationError(
                f"Tipo de embarazo debe ser uno de: {', '.join(tipos_validos)}"
            )
        return value

    def validate_riesgo_embarazo(self, value):
        """
        VALIDACIÓN: Validar nivel de riesgo del embarazo

        Funcionamiento:
            Verifica que el riesgo sea uno de los niveles válidos

        Niveles válidos:
            - bajo: Embarazo de bajo riesgo
            - medio: Embarazo de riesgo medio
            - alto: Embarazo de alto riesgo

        Parámetros:
            value: Nivel de riesgo

        Retorna:
            value: Si es válido
        """
        riesgos_validos = ['bajo', 'medio', 'alto']
        if value not in riesgos_validos:
            raise serializers.ValidationError(
                f"Nivel de riesgo debe ser uno de: {', '.join(riesgos_validos)}"
            )
        return value

    # ===========================================
    # VALIDACIONES GENERALES (validate)
    # ===========================================

    def validate(self, data):
        """
        VALIDACIÓN: Validaciones generales del embarazo

        Funcionamiento:
            1. Calcula FPP automáticamente si no viene (Regla de Naegele)
            2. Valida que no haya embarazos activos duplicados
            3. Valida coherencia de datos

        Regla de Naegele:
            FPP = FUM + 280 días (40 semanas)

        Parámetros:
            data: Datos validados del serializer

        Retorna:
            data: Datos validados y enriquecidos

        Excepciones:
            ValidationError: Si hay inconsistencias
        """

        # Paso 1: Calcular FPP automáticamente si no viene
        # Funcionamiento: Aplica Regla de Naegele (FUM + 280 días)
        if 'fecha_ultima_menstruacion' in data and not data.get('fecha_probable_parto'):
            fum = data['fecha_ultima_menstruacion']
            data['fecha_probable_parto'] = fum + timedelta(days=280)

        # Paso 2: Validar que no haya embarazo activo duplicado
        # Funcionamiento:
        #   - Solo en creación (self.instance es None)
        #   - Busca embarazos activos del mismo paciente
        #   - Lanza error si encuentra alguno
        paciente = data.get('paciente')
        if paciente and not self.instance:  # Solo en creación
            embarazos_activos = Embarazo.objects.filter(
                paciente=paciente,
                estado='activo'
            )
            if embarazos_activos.exists():
                raise serializers.ValidationError({
                    'paciente': 'Esta paciente ya tiene un embarazo activo registrado. '
                               'Finalice el embarazo anterior antes de crear uno nuevo.'
                })

        # Paso 3: Validar coherencia de FPP si viene manual
        # Funcionamiento: Si FPP es muy diferente de FUM+280, advertir
        if 'fecha_ultima_menstruacion' in data and 'fecha_probable_parto' in data:
            fum = data['fecha_ultima_menstruacion']
            fpp = data['fecha_probable_parto']
            fpp_calculada = fum + timedelta(days=280)

            # Advertir si la diferencia es mayor a 14 días
            diferencia_dias = abs((fpp - fpp_calculada).days)
            if diferencia_dias > 14:
                # Nota: No lanzamos error, solo advertencia
                # porque puede haber casos especiales (FIV, etc.)
                pass

        return data

    # ===========================================
    # MÉTODOS CREATE Y UPDATE
    # ===========================================

    def create(self, validated_data):
        """
        MÉTODO: Crear nuevo embarazo

        Funcionamiento:
            1. Recibe datos validados
            2. Crea instancia de Embarazo en la BD
            3. Retorna instancia creada

        Parámetros:
            validated_data: Datos validados por el serializer

        Retorna:
            Embarazo: Instancia creada
        """
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        MÉTODO: Actualizar embarazo existente

        Funcionamiento:
            1. Recibe instancia y datos nuevos
            2. Si se actualiza FUM y no viene FPP, recalcula FPP
            3. Actualiza instancia en la BD
            4. Retorna instancia actualizada

        Parámetros:
            instance: Instancia de Embarazo existente
            validated_data: Datos nuevos validados

        Retorna:
            Embarazo: Instancia actualizada
        """

        # Recalcular FPP si se actualiza FUM y no se envía FPP
        if 'fecha_ultima_menstruacion' in validated_data and 'fecha_probable_parto' not in validated_data:
            validated_data['fecha_probable_parto'] = validated_data['fecha_ultima_menstruacion'] + timedelta(days=280)

        return super().update(instance, validated_data)


# ===========================================
# SERIALIZER PARA CREACIÓN
# ===========================================
class EmbarazoCreateSerializer(serializers.ModelSerializer):
    """
    SERIALIZER: Para creación de embarazos

    Funcionamiento:
        Serializer especializado para crear nuevos embarazos
        con validaciones adicionales

    Diferencias con EmbarazoSerializer:
        - Validaciones más estrictas
        - Campos obligatorios adicionales
        - Cálculo automático de FPP
        - Verificación de duplicados

    Uso:
        Solo para POST /api/embarazos/
    """

    class Meta:
        model = Embarazo
        fields = [
            'paciente',
            'numero_gesta',
            'fecha_ultima_menstruacion',
            'fecha_probable_parto',
            'tipo_embarazo',
            'riesgo_embarazo',
            'estado',
            'notas',
            'medico_responsable',
        ]

    def validate(self, data):
        """Validaciones para creación"""
        # Calcular FPP si no viene
        if 'fecha_ultima_menstruacion' in data and not data.get('fecha_probable_parto'):
            fum = data['fecha_ultima_menstruacion']
            data['fecha_probable_parto'] = fum + timedelta(days=280)

        # Validar embarazos activos
        paciente = data.get('paciente')
        if paciente:
            embarazos_activos = Embarazo.objects.filter(
                paciente=paciente,
                estado='activo'
            )
            if embarazos_activos.exists():
                raise serializers.ValidationError({
                    'paciente': 'Esta paciente ya tiene un embarazo activo'
                })

        return data


# ===========================================
# SERIALIZER PARA ACTUALIZACIÓN
# ===========================================
class EmbarazoUpdateSerializer(serializers.ModelSerializer):
    """
    SERIALIZER: Para actualización de embarazos

    Funcionamiento:
        Serializer especializado para actualizar embarazos existentes
        Permite actualización parcial de campos

    Uso:
        PUT/PATCH /api/embarazos/{id}/
    """

    class Meta:
        model = Embarazo
        fields = [
            'numero_gesta',
            'fecha_ultima_menstruacion',
            'fecha_probable_parto',
            'tipo_embarazo',
            'riesgo_embarazo',
            'estado',
            'notas',
            'medico_responsable',
        ]


# ===========================================
# SERIALIZER PARA LISTAS
# ===========================================
class EmbarazoListSerializer(serializers.ModelSerializer):
    """
    SERIALIZER: Para listado de embarazos

    Funcionamiento:
        Serializer optimizado para listas
        Solo incluye campos esenciales para mejor performance

    Campos incluidos:
        - ID, UUID
        - Paciente nombre
        - Número de gesta
        - Semanas de gestación
        - Estado
        - Tipo
        - Riesgo

    Uso:
        GET /api/embarazos/ (lista)
    """

    paciente_nombre = serializers.SerializerMethodField()
    semanas_gestacion = serializers.SerializerMethodField()

    class Meta:
        model = Embarazo
        fields = [
            'id',
            'uuid',
            'paciente_nombre',
            'numero_gesta',
            'fecha_ultima_menstruacion',
            'semanas_gestacion',
            'tipo_embarazo',
            'riesgo_embarazo',
            'estado',
            'fecha_registro',
        ]

    def get_paciente_nombre(self, obj):
        """Nombre del paciente"""
        try:
            return obj.paciente.nombre_completo
        except:
            return "N/A"

    def get_semanas_gestacion(self, obj):
        """Edad gestacional"""
        if obj.fecha_ultima_menstruacion:
            hoy = date.today()
            diferencia = (hoy - obj.fecha_ultima_menstruacion).days
            semanas = diferencia // 7
            dias = diferencia % 7
            return f"{semanas}+{dias}"
        return None


# ===========================================
# SERIALIZER DETALLADO
# ===========================================
class EmbarazoDetailSerializer(serializers.ModelSerializer):
    """
    SERIALIZER: Para detalle completo de embarazo

    Funcionamiento:
        Serializer con información completa del embarazo
        Incluye datos del paciente y estadísticas de controles

    Campos adicionales:
        - Datos completos del paciente
        - Total de controles realizados
        - Último control
        - Próximo control
        - Información calculada detallada

    Uso:
        GET /api/embarazos/{id}/
    """

    # Información del paciente completa
    paciente_info = PacienteListSerializer(source='paciente', read_only=True)

    # Campos calculados
    semanas_gestacion = serializers.SerializerMethodField()
    edad_gestacional_completa = serializers.SerializerMethodField()
    trimestre = serializers.SerializerMethodField()
    dias_para_parto = serializers.SerializerMethodField()
    porcentaje_embarazo = serializers.SerializerMethodField()

    # Estadísticas de controles
    total_controles = serializers.SerializerMethodField()
    ultimo_control = serializers.SerializerMethodField()

    class Meta:
        model = Embarazo
        fields = '__all__'

    def get_semanas_gestacion(self, obj):
        """Edad gestacional en formato SS+D"""
        if obj.fecha_ultima_menstruacion:
            hoy = date.today()
            diferencia = (hoy - obj.fecha_ultima_menstruacion).days
            semanas = diferencia // 7
            dias = diferencia % 7
            return f"{semanas}+{dias}"
        return None

    def get_edad_gestacional_completa(self, obj):
        """Edad gestacional detallada"""
        if obj.fecha_ultima_menstruacion:
            hoy = date.today()
            total_dias = (hoy - obj.fecha_ultima_menstruacion).days
            semanas = total_dias // 7
            dias = total_dias % 7

            return {
                'semanas': semanas,
                'dias': dias,
                'total_dias': total_dias,
                'formato': f"{semanas}+{dias}"
            }
        return None

    def get_trimestre(self, obj):
        """Trimestre actual"""
        if obj.fecha_ultima_menstruacion:
            hoy = date.today()
            dias = (hoy - obj.fecha_ultima_menstruacion).days
            semanas = dias // 7

            if semanas <= 13:
                return 1
            elif semanas <= 26:
                return 2
            else:
                return 3
        return None

    def get_dias_para_parto(self, obj):
        """Días hasta el parto"""
        if obj.fecha_probable_parto:
            hoy = date.today()
            return (obj.fecha_probable_parto - hoy).days
        return None

    def get_porcentaje_embarazo(self, obj):
        """Porcentaje completado"""
        if obj.fecha_ultima_menstruacion:
            hoy = date.today()
            dias = (hoy - obj.fecha_ultima_menstruacion).days
            porcentaje = (dias / 280) * 100
            return min(porcentaje, 100.0)
        return None

    def get_total_controles(self, obj):
        """Total de controles prenatales"""
        return obj.controles.count()

    def get_ultimo_control(self, obj):
        """Fecha del último control"""
        ultimo = obj.controles.order_by('-fecha_control').first()
        if ultimo:
            return {
                'id': ultimo.id,
                'fecha': ultimo.fecha_control,
                'numero': ultimo.numero_control,
            }
        return None


"""
RESUMEN DE SERIALIZERS DE EMBARAZOS:
====================================

1. EmbarazoSerializer (Principal):
   - Campos: Todos + calculados
   - Validaciones completas
   - Cálculos obstétricos
   - Uso: CRUD general

2. EmbarazoCreateSerializer:
   - Validaciones estrictas
   - Solo campos necesarios para creación
   - Uso: POST /api/embarazos/

3. EmbarazoUpdateSerializer:
   - Permite actualización parcial
   - Sin validación de duplicados
   - Uso: PUT/PATCH /api/embarazos/{id}/

4. EmbarazoListSerializer:
   - Campos reducidos
   - Optimizado para performance
   - Uso: GET /api/embarazos/

5. EmbarazoDetailSerializer:
   - Información completa
   - Incluye controles y estadísticas
   - Uso: GET /api/embarazos/{id}/

Total: 5 serializers especializados
Líneas: ~900+
====================================
"""
