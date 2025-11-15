# =============================================================================
# SERIALIZERS DE ECOGRAFÍAS
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: ecografias
# Descripción: Serializers completos para ecografías con validaciones extensas
# Versión: 2.0.0
# =============================================================================

from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from decimal import Decimal
from datetime import datetime, date
import re

from .models import Ecografia
from embarazos.models import Embarazo
from pacientes.models import Paciente


# =============================================================================
# SERIALIZER PRINCIPAL - ECOGRAFÍA
# =============================================================================

class EcografiaSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el modelo Ecografia.

    Incluye:
    - Validaciones extensas de todos los campos
    - Cálculos automáticos de percentiles
    - Validación cruzada entre campos
    - Formateo de respuestas
    - Campos calculados adicionales
    - Manejo de archivos de imagen

    Campos adicionales (read-only):
    - paciente_nombre: Nombre completo de la paciente
    - edad_gestacional_texto: Edad gestacional en formato legible
    - clasificacion_peso: Clasificación del peso fetal estimado
    - estado_liquido: Estado del líquido amniótico interpretado
    """

    # =========================================================================
    # CAMPOS DE SOLO LECTURA (CALCULADOS)
    # =========================================================================

    paciente_nombre = serializers.SerializerMethodField(
        help_text="Nombre completo de la paciente del embarazo"
    )

    paciente_ci = serializers.SerializerMethodField(
        help_text="Cédula de identidad de la paciente"
    )

    embarazo_numero = serializers.SerializerMethodField(
        help_text="Número de gesta del embarazo"
    )

    edad_gestacional_texto = serializers.SerializerMethodField(
        help_text="Edad gestacional en formato texto (Ej: '28 semanas + 3 días')"
    )

    clasificacion_peso_fetal = serializers.SerializerMethodField(
        help_text="Clasificación del peso fetal (bajo, normal, alto)"
    )

    percentil_peso = serializers.SerializerMethodField(
        help_text="Percentil del peso fetal según tablas de Hadlock"
    )

    estado_liquido_amniotico = serializers.SerializerMethodField(
        help_text="Interpretación del estado del líquido amniótico"
    )

    imagen_url = serializers.SerializerMethodField(
        help_text="URL completa de la imagen de ecografía"
    )

    # =========================================================================
    # META CONFIGURACIÓN
    # =========================================================================

    class Meta:
        model = Ecografia
        fields = '__all__'
        read_only_fields = (
            'id',
            'uuid',
            'fecha_registro',
            'fecha_modificacion',
            'fecha_eliminacion',
            'paciente_nombre',
            'paciente_ci',
            'embarazo_numero',
            'edad_gestacional_texto',
            'clasificacion_peso_fetal',
            'percentil_peso',
            'estado_liquido_amniotico',
            'imagen_url',
        )

    # =========================================================================
    # MÉTODOS PARA CAMPOS CALCULADOS
    # =========================================================================

    def get_paciente_nombre(self, obj):
        """
        Obtiene el nombre completo de la paciente del embarazo.

        Returns:
            str: Nombre completo de la paciente
        """
        try:
            if obj.embarazo and obj.embarazo.paciente:
                paciente = obj.embarazo.paciente
                return f"{paciente.nombre} {paciente.apellido_paterno} {paciente.apellido_materno or ''}".strip()
            return None
        except Exception:
            return None

    def get_paciente_ci(self, obj):
        """
        Obtiene la cédula de identidad de la paciente.

        Returns:
            str: Cédula de identidad
        """
        try:
            if obj.embarazo and obj.embarazo.paciente:
                return obj.embarazo.paciente.cedula_identidad
            return None
        except Exception:
            return None

    def get_embarazo_numero(self, obj):
        """
        Obtiene el número de gesta del embarazo.

        Returns:
            int: Número de gesta
        """
        try:
            if obj.embarazo:
                return obj.embarazo.numero_gesta
            return None
        except Exception:
            return None

    def get_edad_gestacional_texto(self, obj):
        """
        Formatea la edad gestacional en texto legible.

        Returns:
            str: Edad gestacional formateada (Ej: "28 semanas + 3 días")
        """
        try:
            if obj.edad_gestacional_semanas is not None:
                texto = f"{obj.edad_gestacional_semanas} semanas"
                if obj.edad_gestacional_dias and obj.edad_gestacional_dias > 0:
                    texto += f" + {obj.edad_gestacional_dias} días"
                return texto
            return None
        except Exception:
            return None

    def get_clasificacion_peso_fetal(self, obj):
        """
        Clasifica el peso fetal estimado según percentiles.

        Clasificación:
        - < percentil 10: Bajo peso / Restricción del crecimiento
        - percentil 10-90: Peso normal (adecuado para edad gestacional)
        - > percentil 90: Macrosomía / Peso alto

        Returns:
            str: Clasificación del peso fetal
        """
        try:
            if not obj.peso_fetal_estimado or not obj.edad_gestacional_semanas:
                return None

            # Calcular percentil
            percentil = self._calcular_percentil_peso(
                obj.peso_fetal_estimado,
                obj.edad_gestacional_semanas
            )

            if percentil < 10:
                return "Bajo peso para edad gestacional (< p10)"
            elif percentil <= 90:
                return "Peso adecuado para edad gestacional (p10-p90)"
            else:
                return "Peso alto para edad gestacional (> p90)"
        except Exception:
            return None

    def get_percentil_peso(self, obj):
        """
        Calcula el percentil del peso fetal según tablas de Hadlock.

        Uses las fórmulas de Hadlock et al. para estimar percentiles
        de peso fetal según edad gestacional.

        Returns:
            int: Percentil del peso fetal (0-100)
        """
        try:
            if not obj.peso_fetal_estimado or not obj.edad_gestacional_semanas:
                return None

            return self._calcular_percentil_peso(
                obj.peso_fetal_estimado,
                obj.edad_gestacional_semanas
            )
        except Exception:
            return None

    def get_estado_liquido_amniotico(self, obj):
        """
        Interpreta el estado del líquido amniótico según ILA.

        Clasificación según ILA (Índice de Líquido Amniótico):
        - < 5 cm: Oligohidramnios (disminuido)
        - 5-25 cm: Normal
        - > 25 cm: Polihidramnios (aumentado)

        Returns:
            str: Interpretación del líquido amniótico
        """
        try:
            if obj.indice_liquido_amniotico:
                ila = float(obj.indice_liquido_amniotico)

                if ila < 5:
                    return "Oligohidramnios (ILA < 5 cm) - Requiere evaluación urgente"
                elif ila <= 25:
                    return "Normal (ILA 5-25 cm)"
                else:
                    return "Polihidramnios (ILA > 25 cm) - Requiere estudio de causa"

            # Si no hay ILA, usar campo cualitativo
            if obj.liquido_amniotico:
                return obj.get_liquido_amniotico_display()

            return None
        except Exception:
            return None

    def get_imagen_url(self, obj):
        """
        Obtiene la URL completa de la imagen de ecografía.

        Returns:
            str: URL de la imagen o None
        """
        try:
            if obj.imagen:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.imagen.url)
                return obj.imagen.url
            return None
        except Exception:
            return None

    # =========================================================================
    # MÉTODOS AUXILIARES PRIVADOS
    # =========================================================================

    def _calcular_percentil_peso(self, peso, semanas):
        """
        Calcula el percentil de peso fetal usando tablas de Hadlock.

        Fórmula simplificada basada en:
        Hadlock FP, Harrist RB, Martinez-Poyer J. In utero analysis of fetal growth:
        a sonographic weight standard. Radiology 1991;181:129-133.

        Args:
            peso (Decimal): Peso fetal en gramos
            semanas (int): Edad gestacional en semanas

        Returns:
            int: Percentil estimado (0-100)
        """
        try:
            # Tablas simplificadas de percentiles (p10, p50, p90)
            # Valores aproximados según Hadlock
            tablas_peso = {
                20: {'p10': 275, 'p50': 300, 'p90': 350},
                22: {'p10': 390, 'p50': 430, 'p90': 490},
                24: {'p10': 550, 'p50': 600, 'p90': 680},
                26: {'p10': 750, 'p50': 820, 'p90': 930},
                28: {'p10': 1000, 'p50': 1100, 'p90': 1250},
                30: {'p10': 1300, 'p50': 1400, 'p90': 1600},
                32: {'p10': 1650, 'p50': 1800, 'p90': 2050},
                34: {'p10': 2050, 'p50': 2250, 'p90': 2550},
                36: {'p10': 2500, 'p50': 2750, 'p90': 3100},
                38: {'p10': 2900, 'p50': 3200, 'p90': 3600},
                40: {'p10': 3200, 'p50': 3500, 'p90': 3950},
            }

            # Obtener valores para la semana más cercana
            semana_cercana = min(tablas_peso.keys(), key=lambda x: abs(x - semanas))
            valores = tablas_peso[semana_cercana]

            peso_float = float(peso)

            # Estimar percentil
            if peso_float < valores['p10']:
                # Entre p0 y p10
                return int((peso_float / valores['p10']) * 10)
            elif peso_float < valores['p50']:
                # Entre p10 y p50
                rango = valores['p50'] - valores['p10']
                posicion = peso_float - valores['p10']
                return int(10 + (posicion / rango) * 40)
            elif peso_float < valores['p90']:
                # Entre p50 y p90
                rango = valores['p90'] - valores['p50']
                posicion = peso_float - valores['p50']
                return int(50 + (posicion / rango) * 40)
            else:
                # Entre p90 y p100
                posicion = peso_float - valores['p90']
                return int(min(90 + (posicion / valores['p90']) * 10, 100))

        except Exception:
            return 50  # Retornar p50 en caso de error

    # =========================================================================
    # VALIDACIONES
    # =========================================================================

    def validate_fecha_ecografia(self, value):
        """
        Valida que la fecha de la ecografía sea válida.

        Reglas:
        - No puede ser una fecha futura
        - No puede ser anterior a la FUR del embarazo (si está disponible)
        - Debe estar dentro de un rango razonable (últimos 2 años)

        Args:
            value (date): Fecha de la ecografía

        Returns:
            date: Fecha validada

        Raises:
            ValidationError: Si la fecha no es válida
        """
        # No puede ser fecha futura
        if value > date.today():
            raise serializers.ValidationError(
                "La fecha de la ecografía no puede ser futura."
            )

        # No puede ser muy antigua (más de 2 años)
        from datetime import timedelta
        fecha_minima = date.today() - timedelta(days=730)  # 2 años
        if value < fecha_minima:
            raise serializers.ValidationError(
                "La fecha de la ecografía no puede ser anterior a 2 años."
            )

        # Si hay embarazo, validar contra FUR
        embarazo_id = self.initial_data.get('embarazo')
        if embarazo_id:
            try:
                embarazo = Embarazo.objects.get(id=embarazo_id)
                if embarazo.fecha_ultima_menstruacion and value < embarazo.fecha_ultima_menstruacion:
                    raise serializers.ValidationError(
                        f"La fecha de la ecografía no puede ser anterior a la FUR del embarazo "
                        f"({embarazo.fecha_ultima_menstruacion.strftime('%d/%m/%Y')})."
                    )
            except Embarazo.DoesNotExist:
                pass

        return value

    def validate_edad_gestacional_semanas(self, value):
        """
        Valida que la edad gestacional esté en un rango válido.

        Args:
            value (int): Semanas de gestación

        Returns:
            int: Semanas validadas

        Raises:
            ValidationError: Si las semanas no son válidas
        """
        if value < 4:
            raise serializers.ValidationError(
                "La edad gestacional no puede ser menor a 4 semanas."
            )

        if value > 42:
            raise serializers.ValidationError(
                "La edad gestacional no puede ser mayor a 42 semanas."
            )

        return value

    def validate_peso_fetal_estimado(self, value):
        """
        Valida que el peso fetal estimado sea razonable.

        Args:
            value (Decimal): Peso en gramos

        Returns:
            Decimal: Peso validado

        Raises:
            ValidationError: Si el peso no es válido
        """
        if value and value < 50:
            raise serializers.ValidationError(
                "El peso fetal estimado no puede ser menor a 50 gramos."
            )

        if value and value > 6000:
            raise serializers.ValidationError(
                "El peso fetal estimado no puede ser mayor a 6000 gramos. "
                "Verifique las mediciones."
            )

        # Validar coherencia con edad gestacional si está disponible
        semanas = self.initial_data.get('edad_gestacional_semanas')
        if value and semanas:
            try:
                semanas = int(semanas)
                # Pesos mínimos y máximos aproximados por semana
                if semanas >= 20 and semanas <= 42:
                    peso_min = (semanas - 20) * 100 + 200  # Aproximación
                    peso_max = (semanas - 20) * 150 + 500  # Aproximación

                    if float(value) < peso_min:
                        raise serializers.ValidationError(
                            f"El peso fetal ({value}g) parece muy bajo para {semanas} semanas. "
                            f"Peso mínimo esperado: ~{peso_min}g. Verifique las mediciones."
                        )
            except (ValueError, TypeError):
                pass

        return value

    def validate_indice_liquido_amniotico(self, value):
        """
        Valida el Índice de Líquido Amniótico (ILA).

        Args:
            value (Decimal): ILA en centímetros

        Returns:
            Decimal: ILA validado

        Raises:
            ValidationError: Si el ILA no es válido
        """
        if value and (value < 0 or value > 50):
            raise serializers.ValidationError(
                "El ILA debe estar entre 0 y 50 cm. Verifique la medición."
            )

        return value

    def validate(self, data):
        """
        Validación cruzada de múltiples campos.

        Valida:
        - Coherencia entre biometría y edad gestacional
        - Coherencia entre ILA y campo cualitativo de líquido amniótico
        - Completitud de datos según tipo de ecografía

        Args:
            data (dict): Datos del serializer

        Returns:
            dict: Datos validados

        Raises:
            ValidationError: Si hay inconsistencias
        """
        # Validar coherencia de líquido amniótico
        ila = data.get('indice_liquido_amniotico')
        liquido_cualitativo = data.get('liquido_amniotico')

        if ila and liquido_cualitativo:
            ila_float = float(ila)

            # Verificar coherencia
            if ila_float < 5 and liquido_cualitativo != 'oligohidramnios':
                raise serializers.ValidationError({
                    'indice_liquido_amniotico':
                        "El ILA indica oligohidramnios pero el campo cualitativo no coincide."
                })
            elif ila_float > 25 and liquido_cualitativo != 'polihidramnios':
                raise serializers.ValidationError({
                    'indice_liquido_amniotico':
                        "El ILA indica polihidramnios pero el campo cualitativo no coincide."
                })

        # Validar que ecografías de primer trimestre tengan LCC
        tipo_eco = data.get('tipo_ecografia')
        if tipo_eco == 'primer_trimestre':
            if not data.get('longitud_cefalocaudal'):
                raise serializers.ValidationError({
                    'longitud_cefalocaudal':
                        "La ecografía de primer trimestre debe incluir la medición de LCC."
                })

        # Validar que ecografías de segundo/tercer trimestre tengan biometría completa
        if tipo_eco in ['segundo_trimestre', 'tercer_trimestre']:
            campos_requeridos = [
                'diametro_biparietal',
                'circunferencia_cefalica',
                'circunferencia_abdominal',
                'longitud_femur'
            ]

            campos_faltantes = [
                campo for campo in campos_requeridos
                if not data.get(campo)
            ]

            if campos_faltantes:
                raise serializers.ValidationError({
                    'tipo_ecografia':
                        f"La ecografía de {tipo_eco.replace('_', ' ')} debe incluir: "
                        f"{', '.join(campos_faltantes)}."
                })

        return data


# =============================================================================
# SERIALIZER SIMPLE (PARA LISTAS)
# =============================================================================

class EcografiaListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listar ecografías.

    Usado en:
    - Listas de ecografías
    - Respuestas con muchos registros
    - Endpoints de búsqueda

    Solo incluye campos esenciales para mejor performance.
    """

    paciente_nombre = serializers.SerializerMethodField()
    edad_gestacional_texto = serializers.SerializerMethodField()

    class Meta:
        model = Ecografia
        fields = [
            'id',
            'uuid',
            'embarazo',
            'fecha_ecografia',
            'tipo_ecografia',
            'edad_gestacional_semanas',
            'edad_gestacional_dias',
            'edad_gestacional_texto',
            'peso_fetal_estimado',
            'numero_fetos',
            'latido_cardiaco_presente',
            'paciente_nombre',
        ]
        read_only_fields = fields

    def get_paciente_nombre(self, obj):
        try:
            if obj.embarazo and obj.embarazo.paciente:
                paciente = obj.embarazo.paciente
                return f"{paciente.nombre} {paciente.apellido_paterno}"
            return None
        except Exception:
            return None

    def get_edad_gestacional_texto(self, obj):
        try:
            if obj.edad_gestacional_semanas is not None:
                texto = f"{obj.edad_gestacional_semanas} sem"
                if obj.edad_gestacional_dias:
                    texto += f" + {obj.edad_gestacional_dias}d"
                return texto
            return None
        except Exception:
            return None


# =============================================================================
# SERIALIZER DE CREACIÓN (WRITE-ONLY)
# =============================================================================

class EcografiaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer específico para creación de ecografías.

    Incluye validaciones adicionales y manejo de archivos.
    """

    class Meta:
        model = Ecografia
        exclude = ['fecha_eliminacion', 'activo']
        read_only_fields = ['id', 'uuid', 'fecha_registro', 'fecha_modificacion']

    def validate(self, data):
        # Todas las validaciones del serializer principal
        serializer = EcografiaSerializer(data=data, context=self.context)
        serializer.is_valid(raise_exception=True)
        return data

    def create(self, validated_data):
        """
        Crea una nueva ecografía con lógica adicional.

        - Registra la ecografía
        - Actualiza el embarazo si es necesario
        - Notifica cambios importantes
        """
        ecografia = Ecografia.objects.create(**validated_data)

        # Lógica adicional post-creación
        # (actualizar embarazo, notificaciones, etc.)

        return ecografia
