from rest_framework import serializers
from .models import (
    CalculoClinico,
    EdadGestacional,
    IndiceMasaCorporal,
    GananciaPeso,
    PuntajeBishop,
    RiesgoPreeclampsia,
    DiabetesGestacional,
    IndiceLiquidoAmniotico,
    PesoFetal,
    PuntajeApgar,
    RMIOvario,
    RiesgoEndometrio,
    PresionArterialMedia,
    SuperficieCorporal,
)
from .utils import CalculadorasObstetricas, CalculadorasGinecologicas, CalculadorasGenerales
from pacientes.models import Paciente
from embarazos.models import Embarazo
from controles.models import ControlPrenatal
from datetime import date


# ============================================================================
# SERIALIZERS BASE
# ============================================================================

class CalculoClinicoSerializer(serializers.ModelSerializer):
    """Serializer base para cálculos clínicos"""
    
    tipo_calculo_display = serializers.CharField(source='get_tipo_calculo_display', read_only=True)
    paciente_nombre = serializers.CharField(source='paciente.nombre_completo', read_only=True)
    realizado_por_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = CalculoClinico
        fields = [
            'id',
            'tipo_calculo',
            'tipo_calculo_display',
            'paciente',
            'paciente_nombre',
            'embarazo',
            'control_prenatal',
            'parametros_entrada',
            'resultados',
            'interpretacion',
            'realizado_por',
            'realizado_por_nombre',
            'fecha_calculo',
            'observaciones',
        ]
        read_only_fields = ['id', 'fecha_calculo']
    
    def get_realizado_por_nombre(self, obj):
        if obj.realizado_por:
            return f"{obj.realizado_por.nombre} {obj.realizado_por.apellido_paterno}"
        return None


# ============================================================================
# SERIALIZERS OBSTÉTRICOS
# ============================================================================

class EdadGestacionalSerializer(serializers.Serializer):
    """Serializer para cálculo de edad gestacional"""
    
    # Entrada
    paciente_id = serializers.IntegerField()
    embarazo_id = serializers.IntegerField(required=False, allow_null=True)
    fum = serializers.DateField()
    fecha_calculo = serializers.DateField(required=False, allow_null=True)
    
    # Salida (read_only)
    semanas = serializers.IntegerField(read_only=True)
    dias = serializers.IntegerField(read_only=True)
    fpp = serializers.DateField(read_only=True)
    trimestre = serializers.IntegerField(read_only=True)
    edad_gestacional_texto = serializers.CharField(read_only=True)
    
    def validate_paciente_id(self, value):
        try:
            Paciente.objects.get(id=value)
        except Paciente.DoesNotExist:
            raise serializers.ValidationError("Paciente no existe")
        return value
    
    def validate_embarazo_id(self, value):
        if value:
            try:
                Embarazo.objects.get(id=value)
            except Embarazo.DoesNotExist:
                raise serializers.ValidationError("Embarazo no existe")
        return value
    
    def create(self, validated_data):
        usuario = self.context['request'].user
        fecha_calculo = validated_data.get('fecha_calculo') or date.today()
        
        # Calcular edad gestacional
        resultado = CalculadorasObstetricas.calcular_edad_gestacional(
            fum=validated_data['fum'],
            fecha_actual=fecha_calculo
        )
        
        # ✅ CONVERTIR DATES A STRINGS PARA JSON
        parametros_entrada = {
    'fum': str(validated_data['fum']),  # string
            'fecha_calculo': str(fecha_calculo)
        }
        
        # ✅ CONVERTIR FPP A STRING EN RESULTADOS
        resultados = {
            **resultado,
            'fpp': str(resultado['fpp'])  # Convertir date a string
        }
        
        # Crear registro de cálculo clínico
        calculo_clinico = CalculoClinico.objects.create(
            tipo_calculo='edad_gestacional',
            paciente_id=validated_data['paciente_id'],
            embarazo_id=validated_data.get('embarazo_id'),
            parametros_entrada=parametros_entrada,  # ✅ Ya son strings
            resultados=resultados,  # ✅ Ya son strings
            interpretacion=f"Embarazo de {resultado['edad_gestacional_texto']}, {resultado['trimestre']}° trimestre",
            realizado_por=usuario
        )
        
        # Crear registro específico
        edad_gestacional = EdadGestacional.objects.create(
            calculo=calculo_clinico,
            fum=validated_data['fum'],
            fecha_calculo=fecha_calculo,
            semanas=resultado['semanas'],
            dias=resultado['dias'],
            fpp=resultado['fpp'],  # Este es un date, está bien
            trimestre=resultado['trimestre']
        )
        
        return {
            'id': calculo_clinico.id,
            **validated_data,
            **resultado
        }

class IMCSerializer(serializers.Serializer):
    """Serializer para cálculo de IMC"""
    
    # Entrada
    paciente_id = serializers.IntegerField()
    embarazo_id = serializers.IntegerField(required=False, allow_null=True)
    peso = serializers.DecimalField(max_digits=5, decimal_places=2)
    altura = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    # Salida
    imc = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    clasificacion = serializers.CharField(read_only=True)
    clasificacion_texto = serializers.CharField(read_only=True)
    ganancia_peso_recomendada_min = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    ganancia_peso_recomendada_max = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    
    def create(self, validated_data):
        usuario = self.context['request'].user
        
        # Calcular IMC
        resultado = CalculadorasObstetricas.calcular_imc(
            peso=validated_data['peso'],
            altura=validated_data['altura']
        )
        
        # Crear registro de cálculo clínico
        calculo_clinico = CalculoClinico.objects.create(
            tipo_calculo='imc',
            paciente_id=validated_data['paciente_id'],
            embarazo_id=validated_data.get('embarazo_id'),
            parametros_entrada={
                'peso': str(validated_data['peso']),
                'altura': str(validated_data['altura'])
            },
            resultados=resultado,
            interpretacion=f"IMC: {resultado['imc']} - {resultado['clasificacion_texto']}",
            realizado_por=usuario
        )
        
        # Crear registro específico
        imc = IndiceMasaCorporal.objects.create(
            calculo=calculo_clinico,
            peso=validated_data['peso'],
            altura=validated_data['altura'],
            imc=resultado['imc'],
            clasificacion=resultado['clasificacion'],
            ganancia_peso_recomendada_min=resultado['ganancia_peso_recomendada_min'],
            ganancia_peso_recomendada_max=resultado['ganancia_peso_recomendada_max']
        )
        
        return {
            'id': calculo_clinico.id,
            **validated_data,
            **resultado
        }


class GananciaPesoSerializer(serializers.Serializer):
    """Serializer para cálculo de ganancia de peso gestacional"""
    
    # Entrada
    paciente_id = serializers.IntegerField()
    embarazo_id = serializers.IntegerField()
    peso_pregestacional = serializers.DecimalField(max_digits=5, decimal_places=2)
    peso_actual = serializers.DecimalField(max_digits=5, decimal_places=2)
    semanas_gestacion = serializers.IntegerField()
    imc_pregestacional = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    # Salida
    ganancia_peso_actual = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    ganancia_peso_esperada_min = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    ganancia_peso_esperada_max = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    adecuada = serializers.BooleanField(read_only=True)
    interpretacion = serializers.CharField(read_only=True)
    
    def create(self, validated_data):
        usuario = self.context['request'].user
        
        # Calcular ganancia de peso
        resultado = CalculadorasObstetricas.calcular_ganancia_peso(
            peso_pregestacional=validated_data['peso_pregestacional'],
            peso_actual=validated_data['peso_actual'],
            semanas_gestacion=validated_data['semanas_gestacion'],
            imc_pregestacional=validated_data['imc_pregestacional']
        )
        
        # Crear registro de cálculo clínico
        calculo_clinico = CalculoClinico.objects.create(
            tipo_calculo='ganancia_peso',
            paciente_id=validated_data['paciente_id'],
            embarazo_id=validated_data['embarazo_id'],
            parametros_entrada={
                'peso_pregestacional': str(validated_data['peso_pregestacional']),
                'peso_actual': str(validated_data['peso_actual']),
                'semanas_gestacion': validated_data['semanas_gestacion'],
                'imc_pregestacional': str(validated_data['imc_pregestacional'])
            },
            resultados=resultado,
            interpretacion=resultado['interpretacion'],
            realizado_por=usuario
        )
        
        # Crear registro específico
        ganancia = GananciaPeso.objects.create(
            calculo=calculo_clinico,
            peso_pregestacional=validated_data['peso_pregestacional'],
            peso_actual=validated_data['peso_actual'],
            semanas_gestacion=validated_data['semanas_gestacion'],
            imc_pregestacional=validated_data['imc_pregestacional'],
            ganancia_peso_actual=resultado['ganancia_peso_actual'],
            ganancia_peso_esperada_min=resultado['ganancia_peso_esperada_min'],
            ganancia_peso_esperada_max=resultado['ganancia_peso_esperada_max'],
            adecuada=resultado['adecuada'],
            interpretacion=resultado['interpretacion']
        )
        
        return {
            'id': calculo_clinico.id,
            **validated_data,
            **resultado
        }


class BishopSerializer(serializers.Serializer):
    """Serializer para puntaje de Bishop"""
    
    # Entrada
    paciente_id = serializers.IntegerField()
    embarazo_id = serializers.IntegerField()
    dilatacion = serializers.IntegerField(min_value=0, max_value=10)
    borramiento = serializers.IntegerField(min_value=0, max_value=100)
    estacion = serializers.IntegerField()
    consistencia = serializers.IntegerField(min_value=0, max_value=2)
    posicion = serializers.IntegerField(min_value=0, max_value=2)
    
    # Salida
    puntaje_total = serializers.IntegerField(read_only=True)
    interpretacion = serializers.CharField(read_only=True)
    detalle = serializers.DictField(read_only=True)
    
    def create(self, validated_data):
        usuario = self.context['request'].user
        
        # Calcular Bishop
        resultado = CalculadorasObstetricas.calcular_bishop(
            dilatacion=validated_data['dilatacion'],
            borramiento=validated_data['borramiento'],
            estacion=validated_data['estacion'],
            consistencia=validated_data['consistencia'],
            posicion=validated_data['posicion']
        )
        
        # Crear registro de cálculo clínico
        calculo_clinico = CalculoClinico.objects.create(
            tipo_calculo='bishop',
            paciente_id=validated_data['paciente_id'],
            embarazo_id=validated_data['embarazo_id'],
            parametros_entrada={
                'dilatacion': validated_data['dilatacion'],
                'borramiento': validated_data['borramiento'],
                'estacion': validated_data['estacion'],
                'consistencia': validated_data['consistencia'],
                'posicion': validated_data['posicion']
            },
            resultados=resultado,
            interpretacion=resultado['interpretacion'],
            realizado_por=usuario
        )
        
        # Crear registro específico
        bishop = PuntajeBishop.objects.create(
            calculo=calculo_clinico,
            dilatacion=validated_data['dilatacion'],
            borramiento=validated_data['borramiento'],
            estacion=validated_data['estacion'],
            consistencia=validated_data['consistencia'],
            posicion=validated_data['posicion'],
            puntaje_total=resultado['puntaje_total'],
            interpretacion=resultado['interpretacion']
        )
        
        return {
            'id': calculo_clinico.id,
            **validated_data,
            **resultado
        }


class RiesgoPreeclampsiaSerializer(serializers.Serializer):
    """Serializer para cálculo de riesgo de preeclampsia"""
    
    # Entrada
    paciente_id = serializers.IntegerField()
    embarazo_id = serializers.IntegerField()
    edad = serializers.IntegerField()
    primiparidad = serializers.BooleanField(default=False)
    antecedente_preeclampsia = serializers.BooleanField(default=False)
    diabetes = serializers.BooleanField(default=False)
    hipertension_cronica = serializers.BooleanField(default=False)
    obesidad = serializers.BooleanField(default=False)
    embarazo_multiple = serializers.BooleanField(default=False)
    enfermedad_renal = serializers.BooleanField(default=False)
    enfermedad_autoinmune = serializers.BooleanField(default=False)
    
    # Salida
    nivel_riesgo = serializers.CharField(read_only=True)
    recomienda_aspirina = serializers.BooleanField(read_only=True)
    factores_riesgo_count = serializers.IntegerField(read_only=True)
    factores_alto_riesgo = serializers.IntegerField(read_only=True)
    factores_moderado_riesgo = serializers.IntegerField(read_only=True)
    interpretacion = serializers.CharField(read_only=True)
    
    def create(self, validated_data):
        usuario = self.context['request'].user
        
        # Calcular riesgo
        resultado = CalculadorasObstetricas.calcular_riesgo_preeclampsia(
            edad=validated_data['edad'],
            primiparidad=validated_data['primiparidad'],
            antecedente_preeclampsia=validated_data['antecedente_preeclampsia'],
            diabetes=validated_data['diabetes'],
            hipertension_cronica=validated_data['hipertension_cronica'],
            obesidad=validated_data['obesidad'],
            embarazo_multiple=validated_data['embarazo_multiple'],
            enfermedad_renal=validated_data['enfermedad_renal'],
            enfermedad_autoinmune=validated_data['enfermedad_autoinmune']
        )
        
        # Crear registro de cálculo clínico
        calculo_clinico = CalculoClinico.objects.create(
            tipo_calculo='preeclampsia',
            paciente_id=validated_data['paciente_id'],
            embarazo_id=validated_data['embarazo_id'],
            parametros_entrada=validated_data,
            resultados=resultado,
            interpretacion=resultado['interpretacion'],
            realizado_por=usuario
        )
        
        # Crear registro específico
        riesgo = RiesgoPreeclampsia.objects.create(
            calculo=calculo_clinico,
            edad=validated_data['edad'],
            primiparidad=validated_data['primiparidad'],
            antecedente_preeclampsia=validated_data['antecedente_preeclampsia'],
            diabetes=validated_data['diabetes'],
            hipertension_cronica=validated_data['hipertension_cronica'],
            obesidad=validated_data['obesidad'],
            embarazo_multiple=validated_data['embarazo_multiple'],
            enfermedad_renal=validated_data['enfermedad_renal'],
            enfermedad_autoinmune=validated_data['enfermedad_autoinmune'],
            nivel_riesgo=resultado['nivel_riesgo'],
            recomienda_aspirina=resultado['recomienda_aspirina'],
            factores_riesgo_count=resultado['factores_riesgo_count']
        )
        
        return {
            'id': calculo_clinico.id,
            **validated_data,
            **resultado
        }


class DiabetesGestacionalSerializer(serializers.Serializer):
    """Serializer para tamizaje de diabetes gestacional"""
    
    # Entrada
    paciente_id = serializers.IntegerField()
    embarazo_id = serializers.IntegerField()
    tipo_test = serializers.ChoiceField(choices=['ogtt_75g', 'ogtt_100g', 'glucosa_ayunas'])
    semanas_gestacion = serializers.IntegerField()
    glucosa_ayunas = serializers.DecimalField(max_digits=5, decimal_places=2)
    glucosa_1h = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    glucosa_2h = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    glucosa_3h = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    
    # Salida
    diagnostico = serializers.CharField(read_only=True)
    valores_alterados = serializers.IntegerField(read_only=True)
    valores_alterados_lista = serializers.ListField(read_only=True)
    requiere_seguimiento = serializers.BooleanField(read_only=True)
    
    def create(self, validated_data):
        usuario = self.context['request'].user
        
        # Calcular tamizaje
        resultado = CalculadorasObstetricas.calcular_diabetes_gestacional(
            tipo_test=validated_data['tipo_test'],
            glucosa_ayunas=validated_data['glucosa_ayunas'],
            glucosa_1h=validated_data.get('glucosa_1h'),
            glucosa_2h=validated_data.get('glucosa_2h'),
            glucosa_3h=validated_data.get('glucosa_3h')
        )
        
        # Crear registro de cálculo clínico
        calculo_clinico = CalculoClinico.objects.create(
            tipo_calculo='diabetes_gestacional',
            paciente_id=validated_data['paciente_id'],
            embarazo_id=validated_data['embarazo_id'],
            parametros_entrada={k: str(v) if v is not None else None for k, v in validated_data.items()},
            resultados=resultado,
            interpretacion=resultado['diagnostico'],
            realizado_por=usuario
        )
        
        # Crear registro específico
        diabetes = DiabetesGestacional.objects.create(
            calculo=calculo_clinico,
            tipo_test=validated_data['tipo_test'],
            semanas_gestacion=validated_data['semanas_gestacion'],
            glucosa_ayunas=validated_data['glucosa_ayunas'],
            glucosa_1h=validated_data.get('glucosa_1h'),
            glucosa_2h=validated_data.get('glucosa_2h'),
            glucosa_3h=validated_data.get('glucosa_3h'),
            diagnostico=resultado['diagnostico'],
            valores_alterados=resultado['valores_alterados'],
            requiere_seguimiento=resultado['requiere_seguimiento']
        )
        
        return {
            'id': calculo_clinico.id,
            **validated_data,
            **resultado
        }


class ILASerializer(serializers.Serializer):
    """Serializer para índice de líquido amniótico"""
    
    # Entrada
    paciente_id = serializers.IntegerField()
    embarazo_id = serializers.IntegerField()
    semanas_gestacion = serializers.IntegerField()
    cuadrante_1 = serializers.DecimalField(max_digits=5, decimal_places=2)
    cuadrante_2 = serializers.DecimalField(max_digits=5, decimal_places=2)
    cuadrante_3 = serializers.DecimalField(max_digits=5, decimal_places=2)
    cuadrante_4 = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    # Salida
    ila = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    ila_cm = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    interpretacion = serializers.CharField(read_only=True)
    interpretacion_texto = serializers.CharField(read_only=True)
    recomendacion = serializers.CharField(read_only=True)
    
    def create(self, validated_data):
        usuario = self.context['request'].user
        
        # Calcular ILA
        resultado = CalculadorasObstetricas.calcular_ila(
            cuadrante_1=validated_data['cuadrante_1'],
            cuadrante_2=validated_data['cuadrante_2'],
            cuadrante_3=validated_data['cuadrante_3'],
            cuadrante_4=validated_data['cuadrante_4']
        )
        
        # Crear registro de cálculo clínico
        calculo_clinico = CalculoClinico.objects.create(
            tipo_calculo='ila',
            paciente_id=validated_data['paciente_id'],
            embarazo_id=validated_data['embarazo_id'],
            parametros_entrada={k: str(v) for k, v in validated_data.items() if k not in ['paciente_id', 'embarazo_id']},
            resultados=resultado,
            interpretacion=resultado['interpretacion_texto'],
            realizado_por=usuario
        )
        
        # Crear registro específico
        ila = IndiceLiquidoAmniotico.objects.create(
            calculo=calculo_clinico,
            semanas_gestacion=validated_data['semanas_gestacion'],
            cuadrante_1=validated_data['cuadrante_1'],
            cuadrante_2=validated_data['cuadrante_2'],
            cuadrante_3=validated_data['cuadrante_3'],
            cuadrante_4=validated_data['cuadrante_4'],
            ila=resultado['ila'],
            interpretacion=resultado['interpretacion']
        )
        
        return {
            'id': calculo_clinico.id,
            **validated_data,
            **resultado
        }


class PesoFetalSerializer(serializers.Serializer):
    """Serializer para estimación de peso fetal"""
    
    # Entrada
    paciente_id = serializers.IntegerField()
    embarazo_id = serializers.IntegerField()
    semanas_gestacion = serializers.IntegerField()
    dbp = serializers.DecimalField(max_digits=5, decimal_places=2, help_text="Diámetro Biparietal (mm)")
    cc = serializers.DecimalField(max_digits=5, decimal_places=2, help_text="Circunferencia Cefálica (mm)")
    ca = serializers.DecimalField(max_digits=5, decimal_places=2, help_text="Circunferencia Abdominal (mm)")
    lf = serializers.DecimalField(max_digits=5, decimal_places=2, help_text="Longitud del Fémur (mm)")
    
    # Salida
    peso_estimado = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    percentil = serializers.IntegerField(read_only=True)
    clasificacion = serializers.CharField(read_only=True)
    clasificacion_texto = serializers.CharField(read_only=True)
    
    def create(self, validated_data):
        usuario = self.context['request'].user
        
        # Calcular peso fetal
        resultado = CalculadorasObstetricas.calcular_peso_fetal(
            dbp=validated_data['dbp'],
            cc=validated_data['cc'],
            ca=validated_data['ca'],
            lf=validated_data['lf'],
            semanas_gestacion=validated_data['semanas_gestacion']
        )
        
        # Crear registro de cálculo clínico
        calculo_clinico = CalculoClinico.objects.create(
            tipo_calculo='peso_fetal',
            paciente_id=validated_data['paciente_id'],
            embarazo_id=validated_data['embarazo_id'],
            parametros_entrada={k: str(v) for k, v in validated_data.items() if k not in ['paciente_id', 'embarazo_id']},
            resultados=resultado,
            interpretacion=f"Peso fetal estimado: {resultado['peso_estimado']}g - {resultado['clasificacion_texto']}",
            realizado_por=usuario
        )
        
        # Crear registro específico
        peso_fetal = PesoFetal.objects.create(
            calculo=calculo_clinico,
            semanas_gestacion=validated_data['semanas_gestacion'],
            dbp=validated_data['dbp'],
            cc=validated_data['cc'],
            ca=validated_data['ca'],
            lf=validated_data['lf'],
            peso_estimado=resultado['peso_estimado'],
            percentil=resultado['percentil'],
            clasificacion=resultado['clasificacion']
        )
        
        return {
            'id': calculo_clinico.id,
            **validated_data,
            **resultado
        }


class ApgarSerializer(serializers.Serializer):
    """Serializer para puntaje Apgar"""
    
    # Entrada
    paciente_id = serializers.IntegerField()
    minuto = serializers.ChoiceField(choices=[1, 5, 10])
    frecuencia_cardiaca = serializers.IntegerField(min_value=0, max_value=2)
    esfuerzo_respiratorio = serializers.IntegerField(min_value=0, max_value=2)
    tono_muscular = serializers.IntegerField(min_value=0, max_value=2)
    irritabilidad_refleja = serializers.IntegerField(min_value=0, max_value=2)
    coloracion = serializers.IntegerField(min_value=0, max_value=2)
    
    # Salida
    puntaje_total = serializers.IntegerField(read_only=True)
    interpretacion = serializers.CharField(read_only=True)
    interpretacion_texto = serializers.CharField(read_only=True)
    
    def create(self, validated_data):
        usuario = self.context['request'].user
        
        # Calcular Apgar
        resultado = CalculadorasObstetricas.calcular_apgar(
            frecuencia_cardiaca=validated_data['frecuencia_cardiaca'],
            esfuerzo_respiratorio=validated_data['esfuerzo_respiratorio'],
            tono_muscular=validated_data['tono_muscular'],
            irritabilidad_refleja=validated_data['irritabilidad_refleja'],
            coloracion=validated_data['coloracion']
        )
        
        # Crear registro de cálculo clínico
        calculo_clinico = CalculoClinico.objects.create(
            tipo_calculo='apgar',
            paciente_id=validated_data['paciente_id'],
            parametros_entrada={k: v for k, v in validated_data.items() if k != 'paciente_id'},
            resultados=resultado,
            interpretacion=resultado['interpretacion_texto'],
            realizado_por=usuario
        )
        
        # Crear registro específico
        apgar = PuntajeApgar.objects.create(
            calculo=calculo_clinico,
            minuto=validated_data['minuto'],
            frecuencia_cardiaca=validated_data['frecuencia_cardiaca'],
            esfuerzo_respiratorio=validated_data['esfuerzo_respiratorio'],
            tono_muscular=validated_data['tono_muscular'],
            irritabilidad_refleja=validated_data['irritabilidad_refleja'],
            coloracion=validated_data['coloracion'],
            puntaje_total=resultado['puntaje_total'],
            interpretacion=resultado['interpretacion']
        )
        
        return {
            'id': calculo_clinico.id,
            **validated_data,
            **resultado
        }


# ============================================================================
# SERIALIZERS GINECOLÓGICOS
# ============================================================================

class RMIOvarioSerializer(serializers.Serializer):
    """Serializer para RMI de ovario"""
    
    # Entrada
    paciente_id = serializers.IntegerField()
    estado_menopausia = serializers.ChoiceField(choices=['premenopausia', 'postmenopausia'])
    masa_multilocular = serializers.BooleanField(default=False)
    masa_solida = serializers.BooleanField(default=False)
    masa_bilateral = serializers.BooleanField(default=False)
    ascitis = serializers.BooleanField(default=False)
    metastasis = serializers.BooleanField(default=False)
    ca125 = serializers.DecimalField(max_digits=7, decimal_places=2)
    
    # Salida
    puntuacion_u = serializers.IntegerField(read_only=True)
    factor_m = serializers.IntegerField(read_only=True)
    rmi = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    nivel_riesgo = serializers.CharField(read_only=True)
    nivel_riesgo_texto = serializers.CharField(read_only=True)
    recomendacion = serializers.CharField(read_only=True)
    
    def create(self, validated_data):
        usuario = self.context['request'].user
        
        # Calcular RMI
        resultado = CalculadorasGinecologicas.calcular_rmi_ovario(
            estado_menopausia=validated_data['estado_menopausia'],
            masa_multilocular=validated_data['masa_multilocular'],
            masa_solida=validated_data['masa_solida'],
            masa_bilateral=validated_data['masa_bilateral'],
            ascitis=validated_data['ascitis'],
            metastasis=validated_data['metastasis'],
            ca125=validated_data['ca125']
        )
        
        # Crear registro de cálculo clínico
        calculo_clinico = CalculoClinico.objects.create(
            tipo_calculo='rmi_ovario',
            paciente_id=validated_data['paciente_id'],
            parametros_entrada={k: v if not isinstance(v, bool) else str(v) for k, v in validated_data.items() if k != 'paciente_id'},
            resultados=resultado,
            interpretacion=resultado['recomendacion'],
            realizado_por=usuario
        )
        
        # Crear registro específico
        rmi = RMIOvario.objects.create(
            calculo=calculo_clinico,
            estado_menopausia=validated_data['estado_menopausia'],
            masa_multilocular=validated_data['masa_multilocular'],
            masa_solida=validated_data['masa_solida'],
            masa_bilateral=validated_data['masa_bilateral'],
            ascitis=validated_data['ascitis'],
            metastasis=validated_data['metastasis'],
            ca125=validated_data['ca125'],
            puntuacion_u=resultado['puntuacion_u'],
            factor_m=resultado['factor_m'],
            rmi=resultado['rmi'],
            nivel_riesgo=resultado['nivel_riesgo']
        )
        
        return {
            'id': calculo_clinico.id,
            **validated_data,
            **resultado
        }


class RiesgoEndometrioSerializer(serializers.Serializer):
    """Serializer para riesgo de cáncer de endometrio"""
    
    # Entrada
    paciente_id = serializers.IntegerField()
    edad = serializers.IntegerField()
    obesidad = serializers.BooleanField(default=False)
    diabetes = serializers.BooleanField(default=False)
    hipertension = serializers.BooleanField(default=False)
    nuliparidad = serializers.BooleanField(default=False)
    menarquia_temprana = serializers.BooleanField(default=False)
    menopausia_tardia = serializers.BooleanField(default=False)
    terapia_hormonal = serializers.BooleanField(default=False)
    tamoxifeno = serializers.BooleanField(default=False)
    sindrome_ovario_poliquistico = serializers.BooleanField(default=False)
    antecedente_familiar = serializers.BooleanField(default=False)
    grosor_endometrial = serializers.DecimalField(max_digits=4, decimal_places=1, required=False, allow_null=True)
    
    # Salida
    factores_riesgo_count = serializers.IntegerField(read_only=True)
    factores_lista = serializers.ListField(read_only=True)
    nivel_riesgo = serializers.CharField(read_only=True)
    nivel_riesgo_texto = serializers.CharField(read_only=True)
    requiere_biopsia = serializers.BooleanField(read_only=True)
    recomendacion = serializers.CharField(read_only=True)
    
    def create(self, validated_data):
        usuario = self.context['request'].user
        
        # Calcular riesgo
        resultado = CalculadorasGinecologicas.calcular_riesgo_endometrio(
            edad=validated_data['edad'],
            obesidad=validated_data['obesidad'],
            diabetes=validated_data['diabetes'],
            hipertension=validated_data['hipertension'],
            nuliparidad=validated_data['nuliparidad'],
            menarquia_temprana=validated_data['menarquia_temprana'],
            menopausia_tardia=validated_data['menopausia_tardia'],
            terapia_hormonal=validated_data['terapia_hormonal'],
            tamoxifeno=validated_data['tamoxifeno'],
            sindrome_ovario_poliquistico=validated_data['sindrome_ovario_poliquistico'],
            antecedente_familiar=validated_data['antecedente_familiar'],
            grosor_endometrial=validated_data.get('grosor_endometrial')
        )
        
        # Crear registro de cálculo clínico
        calculo_clinico = CalculoClinico.objects.create(
            tipo_calculo='riesgo_endometrio',
            paciente_id=validated_data['paciente_id'],
            parametros_entrada={k: v if not isinstance(v, bool) else str(v) for k, v in validated_data.items() if k != 'paciente_id'},
            resultados=resultado,
            interpretacion=resultado['recomendacion'],
            realizado_por=usuario
        )
        
        # Crear registro específico
        riesgo = RiesgoEndometrio.objects.create(
            calculo=calculo_clinico,
            edad=validated_data['edad'],
            obesidad=validated_data['obesidad'],
            diabetes=validated_data['diabetes'],
            hipertension=validated_data['hipertension'],
            nuliparidad=validated_data['nuliparidad'],
            menarquia_temprana=validated_data['menarquia_temprana'],
            menopausia_tardia=validated_data['menopausia_tardia'],
            terapia_hormonal=validated_data['terapia_hormonal'],
            tamoxifeno=validated_data['tamoxifeno'],
            sindrome_ovario_poliquistico=validated_data['sindrome_ovario_poliquistico'],
            antecedente_familiar=validated_data['antecedente_familiar'],
            grosor_endometrial=validated_data.get('grosor_endometrial'),
            factores_riesgo_count=resultado['factores_riesgo_count'],
            nivel_riesgo=resultado['nivel_riesgo'],
            requiere_biopsia=resultado['requiere_biopsia']
        )
        
        return {
            'id': calculo_clinico.id,
            **validated_data,
            **resultado
        }


# ============================================================================
# SERIALIZERS GENERALES
# ============================================================================

class PAMSerializer(serializers.Serializer):
    """Serializer para presión arterial media"""
    
    # Entrada
    paciente_id = serializers.IntegerField()
    control_prenatal_id = serializers.IntegerField(required=False, allow_null=True)
    presion_sistolica = serializers.IntegerField()
    presion_diastolica = serializers.IntegerField()
    
    # Salida
    pam = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    interpretacion = serializers.CharField(read_only=True)
    interpretacion_texto = serializers.CharField(read_only=True)
    recomendacion = serializers.CharField(read_only=True)
    
    def create(self, validated_data):
        usuario = self.context['request'].user
        
        # Calcular PAM
        resultado = CalculadorasGenerales.calcular_pam(
            presion_sistolica=validated_data['presion_sistolica'],
            presion_diastolica=validated_data['presion_diastolica']
        )
        
        # Crear registro de cálculo clínico
        calculo_clinico = CalculoClinico.objects.create(
            tipo_calculo='pam',
            paciente_id=validated_data['paciente_id'],
            control_prenatal_id=validated_data.get('control_prenatal_id'),
            parametros_entrada={
                'presion_sistolica': validated_data['presion_sistolica'],
                'presion_diastolica': validated_data['presion_diastolica']
            },
            resultados=resultado,
            interpretacion=resultado['interpretacion_texto'],
            realizado_por=usuario
        )
        
        # Crear registro específico
        pam = PresionArterialMedia.objects.create(
            calculo=calculo_clinico,
            presion_sistolica=validated_data['presion_sistolica'],
            presion_diastolica=validated_data['presion_diastolica'],
            pam=resultado['pam'],
            interpretacion=resultado['interpretacion']
        )
        
        return {
            'id': calculo_clinico.id,
            **validated_data,
            **resultado
        }


class SuperficieCorporalSerializer(serializers.Serializer):
    """Serializer para superficie corporal"""
    
    # Entrada
    paciente_id = serializers.IntegerField()
    peso = serializers.DecimalField(max_digits=5, decimal_places=2)
    altura = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    # Salida
    superficie_corporal = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    
    def create(self, validated_data):
        usuario = self.context['request'].user
        
        # Calcular superficie corporal
        resultado = CalculadorasGenerales.calcular_superficie_corporal(
            peso=validated_data['peso'],
            altura=validated_data['altura']
        )
        
        # Crear registro de cálculo clínico
        calculo_clinico = CalculoClinico.objects.create(
            tipo_calculo='superficie_corporal',
            paciente_id=validated_data['paciente_id'],
            parametros_entrada={
                'peso': str(validated_data['peso']),
                'altura': str(validated_data['altura'])
            },
            resultados=resultado,
            interpretacion=f"Superficie Corporal: {resultado['superficie_corporal']} m²",
            realizado_por=usuario
        )
        
        # Crear registro específico
        sc = SuperficieCorporal.objects.create(
            calculo=calculo_clinico,
            peso=validated_data['peso'],
            altura=validated_data['altura'],
            superficie_corporal=resultado['superficie_corporal']
        )
        
        return {
            'id': calculo_clinico.id,
            **validated_data,
            **resultado
        }