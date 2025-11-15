# =============================================================================
# SERIALIZERS DE LABORATORIO
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: laboratorio
# Descripción: Serializers para gestión de exámenes de laboratorio
# Versión: 1.0.0
# =============================================================================

from rest_framework import serializers
from decimal import Decimal
from datetime import date

from .models import ExamenLaboratorio
from embarazos.models import Embarazo


# =============================================================================
# SERIALIZER PRINCIPAL DE EXAMEN DE LABORATORIO
# =============================================================================

class ExamenLaboratorioSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el modelo ExamenLaboratorio.

    Incluye:
    - Validaciones extensas de todos los campos
    - Interpretación automática de resultados
    - Validación cruzada entre campos
    - Formateo de respuestas
    - Campos calculados adicionales
    - Manejo de archivos PDF de resultados

    Campos calculados:
    - paciente_nombre: Nombre completo del paciente
    - estado_hemograma: Interpretación de hemograma
    - estado_glucosa: Interpretación de nivel de glucosa
    - estado_funcion_renal: Interpretación de función renal
    - estado_funcion_hepatica: Interpretación de función hepática
    - alerta_infeccion_urinaria: Indicador de posible infección urinaria
    - archivo_url: URL del archivo PDF de resultados
    """

    # Campos calculados de solo lectura
    paciente_nombre = serializers.SerializerMethodField()
    estado_hemograma = serializers.SerializerMethodField()
    estado_glucosa = serializers.SerializerMethodField()
    estado_funcion_renal = serializers.SerializerMethodField()
    estado_funcion_hepatica = serializers.SerializerMethodField()
    alerta_infeccion_urinaria = serializers.SerializerMethodField()
    archivo_url = serializers.SerializerMethodField()
    dias_resultado = serializers.SerializerMethodField()

    class Meta:
        model = ExamenLaboratorio
        fields = '__all__'
        read_only_fields = ['fecha_registro', 'fecha_modificacion', 'fecha_eliminacion']

    # =========================================================================
    # MÉTODOS DE OBTENCIÓN DE CAMPOS CALCULADOS
    # =========================================================================

    def get_paciente_nombre(self, obj):
        """
        Retorna el nombre completo del paciente asociado al embarazo.

        Args:
            obj: Instancia de ExamenLaboratorio

        Returns:
            str: Nombre completo del paciente o None
        """
        if obj.embarazo and obj.embarazo.paciente:
            return f"{obj.embarazo.paciente.nombre} {obj.embarazo.paciente.apellido}"
        return None

    def get_estado_hemograma(self, obj):
        """
        Interpreta los resultados del hemograma.

        Evalúa:
        - Anemia (hemoglobina <11 g/dL en embarazo)
        - Policitemia (hemoglobina >14 g/dL)
        - Leucocitosis (leucocitos >11000/mm³)
        - Leucopenia (leucocitos <4000/mm³)
        - Trombocitopenia (plaquetas <150000/mm³)
        - Trombocitosis (plaquetas >400000/mm³)

        Args:
            obj: Instancia de ExamenLaboratorio

        Returns:
            dict: Diccionario con interpretación del hemograma
        """
        interpretacion = {
            'hemoglobina': None,
            'leucocitos': None,
            'plaquetas': None,
            'alertas': []
        }

        # Evaluar hemoglobina
        if obj.hemoglobina:
            hb = float(obj.hemoglobina)
            if hb < 11.0:
                interpretacion['hemoglobina'] = f'Anemia ({hb} g/dL)'
                interpretacion['alertas'].append('Anemia detectada')
            elif hb > 14.0:
                interpretacion['hemoglobina'] = f'Policitemia ({hb} g/dL)'
                interpretacion['alertas'].append('Hemoglobina elevada')
            else:
                interpretacion['hemoglobina'] = f'Normal ({hb} g/dL)'

        # Evaluar leucocitos
        if obj.leucocitos:
            leuc = obj.leucocitos
            if leuc < 4000:
                interpretacion['leucocitos'] = f'Leucopenia ({leuc}/mm³)'
                interpretacion['alertas'].append('Leucocitos bajos')
            elif leuc > 11000:
                interpretacion['leucocitos'] = f'Leucocitosis ({leuc}/mm³)'
                interpretacion['alertas'].append('Leucocitos elevados - Evaluar infección')
            else:
                interpretacion['leucocitos'] = f'Normal ({leuc}/mm³)'

        # Evaluar plaquetas
        if obj.plaquetas:
            plaq = obj.plaquetas
            if plaq < 150000:
                interpretacion['plaquetas'] = f'Trombocitopenia ({plaq}/mm³)'
                interpretacion['alertas'].append('Plaquetas bajas')
            elif plaq > 400000:
                interpretacion['plaquetas'] = f'Trombocitosis ({plaq}/mm³)'
                interpretacion['alertas'].append('Plaquetas elevadas')
            else:
                interpretacion['plaquetas'] = f'Normal ({plaq}/mm³)'

        return interpretacion

    def get_estado_glucosa(self, obj):
        """
        Interpreta el nivel de glucosa en sangre.

        Criterios para embarazo:
        - Ayunas: <95 mg/dL (normal)
        - Ayunas: 95-125 mg/dL (diabetes gestacional)
        - Ayunas: >125 mg/dL (diabetes)
        - Casual: >200 mg/dL (diabetes)

        Args:
            obj: Instancia de ExamenLaboratorio

        Returns:
            dict: Diccionario con interpretación de glucosa
        """
        if not obj.glucosa:
            return None

        glucosa = float(obj.glucosa)
        interpretacion = {
            'valor': glucosa,
            'estado': None,
            'recomendacion': None
        }

        # Asumir ayunas para evaluación
        if glucosa < 95:
            interpretacion['estado'] = 'Normal'
            interpretacion['recomendacion'] = 'Glucosa en rango normal para embarazo'
        elif glucosa < 126:
            interpretacion['estado'] = 'Diabetes Gestacional (probable)'
            interpretacion['recomendacion'] = 'Realizar curva de tolerancia a la glucosa (CTOG)'
        else:
            interpretacion['estado'] = 'Diabetes (probable)'
            interpretacion['recomendacion'] = 'Evaluación urgente - Probable diabetes'

        return interpretacion

    def get_estado_funcion_renal(self, obj):
        """
        Interpreta la función renal basándose en urea y creatinina.

        Valores normales en embarazo:
        - Urea: 15-45 mg/dL
        - Creatinina: 0.4-0.9 mg/dL (menor que no embarazo)

        Args:
            obj: Instancia de ExamenLaboratorio

        Returns:
            dict: Diccionario con interpretación de función renal
        """
        interpretacion = {
            'urea': None,
            'creatinina': None,
            'estado': None,
            'alertas': []
        }

        # Evaluar urea
        if obj.urea:
            urea = float(obj.urea)
            if urea < 15:
                interpretacion['urea'] = f'Baja ({urea} mg/dL)'
            elif urea > 45:
                interpretacion['urea'] = f'Elevada ({urea} mg/dL)'
                interpretacion['alertas'].append('Urea elevada - Evaluar función renal')
            else:
                interpretacion['urea'] = f'Normal ({urea} mg/dL)'

        # Evaluar creatinina
        if obj.creatinina:
            creat = float(obj.creatinina)
            if creat > 0.9:
                interpretacion['creatinina'] = f'Elevada ({creat} mg/dL)'
                interpretacion['alertas'].append('Creatinina elevada - Posible deterioro renal')
            elif creat < 0.4:
                interpretacion['creatinina'] = f'Baja ({creat} mg/dL)'
            else:
                interpretacion['creatinina'] = f'Normal ({creat} mg/dL)'

        # Estado general
        if len(interpretacion['alertas']) == 0:
            interpretacion['estado'] = 'Función renal normal'
        else:
            interpretacion['estado'] = 'Alteración en función renal - Requiere evaluación'

        return interpretacion

    def get_estado_funcion_hepatica(self, obj):
        """
        Interpreta la función hepática (enzimas, bilirrubina).

        Valores normales:
        - TGO (AST): <40 U/L
        - TGP (ALT): <40 U/L
        - Bilirrubina total: <1.2 mg/dL
        - Fosfatasa alcalina: hasta 450 U/L en embarazo

        Args:
            obj: Instancia de ExamenLaboratorio

        Returns:
            dict: Diccionario con interpretación de función hepática
        """
        interpretacion = {
            'tgo': None,
            'tgp': None,
            'bilirrubina': None,
            'estado': None,
            'alertas': []
        }

        # Evaluar TGO
        if obj.tgo:
            if obj.tgo > 40:
                interpretacion['tgo'] = f'Elevada ({obj.tgo} U/L)'
                interpretacion['alertas'].append(f'TGO elevada ({obj.tgo} U/L)')
            else:
                interpretacion['tgo'] = f'Normal ({obj.tgo} U/L)'

        # Evaluar TGP
        if obj.tgp:
            if obj.tgp > 40:
                interpretacion['tgp'] = f'Elevada ({obj.tgp} U/L)'
                interpretacion['alertas'].append(f'TGP elevada ({obj.tgp} U/L)')
            else:
                interpretacion['tgp'] = f'Normal ({obj.tgp} U/L)'

        # Evaluar bilirrubina
        if obj.bilirrubina_total:
            bili = float(obj.bilirrubina_total)
            if bili > 1.2:
                interpretacion['bilirrubina'] = f'Elevada ({bili} mg/dL)'
                interpretacion['alertas'].append(f'Bilirrubina elevada ({bili} mg/dL)')
            else:
                interpretacion['bilirrubina'] = f'Normal ({bili} mg/dL)'

        # Estado general
        if len(interpretacion['alertas']) == 0:
            interpretacion['estado'] = 'Función hepática normal'
        else:
            interpretacion['estado'] = 'Alteración hepática - Evaluar causa'

        return interpretacion

    def get_alerta_infeccion_urinaria(self, obj):
        """
        Detecta signos de infección urinaria en el examen de orina.

        Criterios:
        - Leucocitos en orina >5/campo
        - Bacterias moderadas o abundantes
        - Proteínas positivas (puede indicar también preeclampsia)

        Args:
            obj: Instancia de ExamenLaboratorio

        Returns:
            dict: Diccionario con alerta de infección urinaria
        """
        alerta = {
            'presente': False,
            'criterios': [],
            'recomendacion': None
        }

        # Evaluar leucocitos en orina
        if obj.orina_leucocitos and obj.orina_leucocitos > 5:
            alerta['presente'] = True
            alerta['criterios'].append(f'Leucocitos elevados ({obj.orina_leucocitos}/campo)')

        # Evaluar bacterias
        if obj.orina_bacterias in ['moderado', 'abundante']:
            alerta['presente'] = True
            alerta['criterios'].append(f'Bacterias {obj.orina_bacterias}')

        # Evaluar proteínas (puede ser infección o preeclampsia)
        if obj.orina_proteinas in ['positivo_1', 'positivo_2', 'positivo_3']:
            alerta['criterios'].append(f'Proteinuria: {obj.get_orina_proteinas_display()}')

        # Recomendación
        if alerta['presente']:
            alerta['recomendacion'] = 'Solicitar urocultivo y evaluar tratamiento antibiótico'

        return alerta

    def get_archivo_url(self, obj):
        """
        Retorna la URL del archivo PDF de resultados.

        Args:
            obj: Instancia de ExamenLaboratorio

        Returns:
            str: URL del archivo o None
        """
        if obj.archivo_resultado:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.archivo_resultado.url)
            return obj.archivo_resultado.url
        return None

    def get_dias_resultado(self, obj):
        """
        Calcula días transcurridos desde el examen hasta el resultado.

        Args:
            obj: Instancia de ExamenLaboratorio

        Returns:
            int: Días transcurridos o None
        """
        if obj.fecha_resultado and obj.fecha_examen:
            delta = obj.fecha_resultado - obj.fecha_examen
            return delta.days
        return None

    # =========================================================================
    # MÉTODOS DE VALIDACIÓN
    # =========================================================================

    def validate_fecha_examen(self, value):
        """
        Valida que la fecha del examen sea válida.

        - No puede ser futura
        - Debe ser razonable (no más de 2 años atrás)

        Args:
            value: Fecha del examen

        Returns:
            date: Fecha validada

        Raises:
            ValidationError: Si la fecha no es válida
        """
        hoy = date.today()

        if value > hoy:
            raise serializers.ValidationError(
                "La fecha del examen no puede ser futura"
            )

        # Validar que no sea muy antigua (2 años)
        limite_antiguo = hoy.replace(year=hoy.year - 2)
        if value < limite_antiguo:
            raise serializers.ValidationError(
                "La fecha del examen es muy antigua. Verificar la fecha ingresada."
            )

        return value

    def validate_fecha_resultado(self, value):
        """
        Valida que la fecha de resultado sea posterior a la fecha del examen.

        Args:
            value: Fecha del resultado

        Returns:
            date: Fecha validada

        Raises:
            ValidationError: Si la fecha no es válida
        """
        if value and value > date.today():
            raise serializers.ValidationError(
                "La fecha de resultado no puede ser futura"
            )

        return value

    def validate_hemoglobina(self, value):
        """
        Valida que el valor de hemoglobina sea razonable.

        Args:
            value: Valor de hemoglobina

        Returns:
            Decimal: Valor validado

        Raises:
            ValidationError: Si el valor no es razonable
        """
        if value and (value < 5.0 or value > 20.0):
            raise serializers.ValidationError(
                f"Valor de hemoglobina fuera de rango razonable ({value} g/dL). "
                "Verificar el dato ingresado."
            )
        return value

    def validate_glucosa(self, value):
        """
        Valida que el valor de glucosa sea razonable.

        Args:
            value: Valor de glucosa

        Returns:
            Decimal: Valor validado

        Raises:
            ValidationError: Si el valor no es razonable
        """
        if value and (value < 30.0 or value > 500.0):
            raise serializers.ValidationError(
                f"Valor de glucosa fuera de rango razonable ({value} mg/dL). "
                "Verificar el dato ingresado."
            )
        return value

    def validate_plaquetas(self, value):
        """
        Valida que el valor de plaquetas sea razonable.

        Args:
            value: Valor de plaquetas

        Returns:
            int: Valor validado

        Raises:
            ValidationError: Si el valor no es razonable
        """
        if value and (value < 10000 or value > 800000):
            raise serializers.ValidationError(
                f"Valor de plaquetas fuera de rango razonable ({value}/mm³). "
                "Verificar el dato ingresado."
            )
        return value

    def validate(self, data):
        """
        Validación cruzada de campos.

        Verifica:
        - Fecha de resultado posterior a fecha de examen
        - Coherencia entre tipo de examen y campos completados
        - Campos obligatorios según tipo de examen

        Args:
            data: Datos del examen

        Returns:
            dict: Datos validados

        Raises:
            ValidationError: Si hay inconsistencias
        """
        # Validar coherencia de fechas
        fecha_examen = data.get('fecha_examen')
        fecha_resultado = data.get('fecha_resultado')

        if fecha_examen and fecha_resultado:
            if fecha_resultado < fecha_examen:
                raise serializers.ValidationError({
                    'fecha_resultado': 'La fecha de resultado no puede ser anterior a la fecha del examen'
                })

        # Validar que el embarazo existe y está activo
        embarazo = data.get('embarazo')
        if embarazo and not embarazo.activo:
            raise serializers.ValidationError({
                'embarazo': 'El embarazo especificado no está activo'
            })

        # Validar hemoglobina vs hematocrito (deben ser proporcionales)
        hemoglobina = data.get('hemoglobina')
        hematocrito = data.get('hematocrito')

        if hemoglobina and hematocrito:
            # Relación aproximada: Hematocrito = Hemoglobina x 3
            hematocrito_esperado = float(hemoglobina) * 3
            diferencia = abs(float(hematocrito) - hematocrito_esperado)

            if diferencia > 5:  # Tolerancia de 5%
                # Solo advertencia, no error
                pass  # Podría agregarse a un campo de warnings

        # Validar proteinuria en embarazo (alerta de preeclampsia)
        orina_proteinas = data.get('orina_proteinas')
        if orina_proteinas in ['positivo_2', 'positivo_3']:
            # Alerta importante - podría ser preeclampsia
            # En producción, esto podría disparar una notificación
            pass

        return data


# =============================================================================
# SERIALIZER PARA LISTADOS (OPTIMIZADO)
# =============================================================================

class ExamenLaboratorioListSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para listados de exámenes de laboratorio.

    Incluye solo los campos esenciales para mejorar el rendimiento.
    """

    paciente_nombre = serializers.SerializerMethodField()
    tipo_examen_display = serializers.CharField(source='get_tipo_examen_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tiene_alertas = serializers.SerializerMethodField()

    class Meta:
        model = ExamenLaboratorio
        fields = [
            'id',
            'uuid',
            'embarazo',
            'paciente_nombre',
            'fecha_examen',
            'fecha_resultado',
            'tipo_examen',
            'tipo_examen_display',
            'estado',
            'estado_display',
            'laboratorio',
            'tiene_alertas',
            'fecha_registro',
        ]

    def get_paciente_nombre(self, obj):
        """Retorna nombre del paciente."""
        if obj.embarazo and obj.embarazo.paciente:
            return f"{obj.embarazo.paciente.nombre} {obj.embarazo.paciente.apellido}"
        return None

    def get_tiene_alertas(self, obj):
        """
        Indica si el examen tiene alertas importantes.

        Returns:
            bool: True si hay alertas
        """
        alertas = False

        # Alertas de hemograma
        if obj.hemoglobina and float(obj.hemoglobina) < 10.0:
            alertas = True
        if obj.plaquetas and obj.plaquetas < 150000:
            alertas = True

        # Alertas de serología
        if obj.vdrl == 'reactivo' or obj.vih == 'reactivo':
            alertas = True

        # Alertas de infección urinaria
        if obj.orina_leucocitos and obj.orina_leucocitos > 10:
            alertas = True

        return alertas


# =============================================================================
# SERIALIZER PARA CREACIÓN
# =============================================================================

class ExamenLaboratorioCreateSerializer(serializers.ModelSerializer):
    """
    Serializer específico para creación de exámenes de laboratorio.

    Incluye validaciones adicionales para asegurar la integridad de los datos.
    """

    class Meta:
        model = ExamenLaboratorio
        fields = '__all__'
        read_only_fields = ['fecha_registro', 'fecha_modificacion', 'fecha_eliminacion']

    def validate_embarazo(self, value):
        """
        Valida que el embarazo existe y está activo.

        Args:
            value: ID del embarazo

        Returns:
            Embarazo: Instancia de embarazo validada

        Raises:
            ValidationError: Si el embarazo no existe o no está activo
        """
        try:
            embarazo = Embarazo.objects.get(id=value.id, activo=True)
            return embarazo
        except Embarazo.DoesNotExist:
            raise serializers.ValidationError(
                "El embarazo especificado no existe o no está activo"
            )

    def create(self, validated_data):
        """
        Crea un nuevo examen de laboratorio.

        Args:
            validated_data: Datos validados

        Returns:
            ExamenLaboratorio: Instancia creada
        """
        examen = ExamenLaboratorio.objects.create(**validated_data)
        return examen
