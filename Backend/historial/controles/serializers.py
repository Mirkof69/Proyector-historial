# =============================================================================
# SERIALIZERS DE CONTROLES PRENATALES
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: controles
# Descripción: Serializers completos para controles prenatales con validaciones
#              médicas avanzadas, cálculos automáticos y generación de alertas.
# Versión: 2.0.0
# Última actualización: 2025-11-14
# =============================================================================

from rest_framework import serializers
from django.utils import timezone
from django.db.models import Q, Avg, Max, Min, Count
from datetime import datetime, timedelta
from decimal import Decimal
from .models import ControlPrenatal
from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario


# =============================================================================
# SERIALIZERS DE LECTURA (REPRESENTACIÓN)
# =============================================================================

class ControlPrenatalSerializer(serializers.ModelSerializer):
    """
    Serializer principal para controles prenatales.

    Incluye:
    - Todos los campos del modelo
    - Campos calculados (IMC, PAM, ganancia de peso)
    - Información relacionada (embarazo, paciente, médico)
    - Sistema de alertas médicas
    - Validaciones médicas completas
    """
    # Campos calculados y de lectura
    paciente_nombre = serializers.SerializerMethodField()
    paciente_id = serializers.SerializerMethodField()
    paciente_cedula = serializers.SerializerMethodField()
    edad_gestacional_formatted = serializers.SerializerMethodField()
    imc_actual = serializers.SerializerMethodField()
    clasificacion_imc = serializers.SerializerMethodField()
    ganancia_peso_ideal = serializers.SerializerMethodField()
    ganancia_peso_real = serializers.SerializerMethodField()
    diferencia_peso = serializers.SerializerMethodField()
    presion_arterial_formatted = serializers.SerializerMethodField()
    presion_arterial_media = serializers.SerializerMethodField()
    clasificacion_pa = serializers.SerializerMethodField()

    # Información de relaciones
    embarazo_info = serializers.SerializerMethodField()
    medico_info = serializers.SerializerMethodField()
    enfermero_info = serializers.SerializerMethodField()

    # Alertas y evaluaciones
    alertas = serializers.SerializerMethodField()
    tiene_alertas = serializers.SerializerMethodField()
    nivel_riesgo = serializers.SerializerMethodField()
    requiere_atencion_inmediata = serializers.SerializerMethodField()

    # Evaluación obstétrica
    concordancia_altura_eg = serializers.SerializerMethodField()
    evaluacion_fcf = serializers.SerializerMethodField()

    class Meta:
        model = ControlPrenatal
        fields = '__all__'
        read_only_fields = [
            'id',
            'fecha_creacion',
            'fecha_modificacion',
            'creado_por',
            'modificado_por',
        ]

    # =========================================================================
    # MÉTODOS DE INFORMACIÓN BÁSICA
    # =========================================================================

    def get_paciente_nombre(self, obj):
        """Obtener nombre completo del paciente"""
        try:
            if obj.embarazo and obj.embarazo.paciente:
                paciente = obj.embarazo.paciente
                return f"{paciente.nombres} {paciente.apellidos}"
            return None
        except:
            return None

    def get_paciente_id(self, obj):
        """Obtener ID del paciente"""
        try:
            if obj.embarazo and obj.embarazo.paciente:
                return obj.embarazo.paciente.id
            return None
        except:
            return None

    def get_paciente_cedula(self, obj):
        """Obtener cédula del paciente"""
        try:
            if obj.embarazo and obj.embarazo.paciente:
                return obj.embarazo.paciente.cedula_identidad
            return None
        except:
            return None

    # =========================================================================
    # CÁLCULOS DE EDAD GESTACIONAL Y PESO
    # =========================================================================

    def get_edad_gestacional_formatted(self, obj):
        """Formatear edad gestacional en formato estándar"""
        if obj.semanas_gestacion is not None:
            dias = obj.dias_gestacion or 0
            return f"{obj.semanas_gestacion}+{dias}"
        return None

    def get_imc_actual(self, obj):
        """Calcular IMC actual"""
        return obj.calcular_imc()

    def get_clasificacion_imc(self, obj):
        """Clasificar IMC según categorías OMS"""
        return obj.clasificar_imc()

    def get_ganancia_peso_real(self, obj):
        """Calcular ganancia de peso real"""
        return obj.calcular_ganancia_peso()

    def get_ganancia_peso_ideal(self, obj):
        """
        Calcula la ganancia de peso ideal según semanas de gestación e IMC pregestacional.

        Recomendaciones del Institute of Medicine (IOM):
        - Bajo peso (IMC < 18.5): 12.5-18 kg total
        - Normal (IMC 18.5-24.9): 11.5-16 kg total
        - Sobrepeso (IMC 25-29.9): 7-11.5 kg total
        - Obesidad (IMC ≥ 30): 5-9 kg total
        """
        if not obj.peso_pregestacional or not obj.talla or not obj.semanas_gestacion:
            return None

        try:
            # Calcular IMC pregestacional
            talla_m = float(obj.talla) / 100
            imc_pregestacional = float(obj.peso_pregestacional) / (talla_m ** 2)

            # Determinar categoría y ganancia total recomendada
            if imc_pregestacional < 18.5:
                ganancia_total = 15.5  # Promedio de 12.5-18 kg
            elif imc_pregestacional < 25:
                ganancia_total = 13.5  # Promedio de 11.5-16 kg
            elif imc_pregestacional < 30:
                ganancia_total = 9.5   # Promedio de 7-11.5 kg
            else:
                ganancia_total = 7.0   # Promedio de 5-9 kg

            # Calcular ganancia por semana (después de semana 13)
            if obj.semanas_gestacion <= 13:
                ganancia_ideal = ganancia_total * 0.1  # 10% en primer trimestre
            else:
                semanas_restantes = obj.semanas_gestacion - 13
                ganancia_ideal = (ganancia_total * 0.1) + (semanas_restantes * (ganancia_total * 0.9 / 27))

            return round(ganancia_ideal, 2)
        except:
            return None

    def get_diferencia_peso(self, obj):
        """Diferencia entre ganancia real e ideal"""
        ganancia_real = self.get_ganancia_peso_real(obj)
        ganancia_ideal = self.get_ganancia_peso_ideal(obj)

        if ganancia_real is not None and ganancia_ideal is not None:
            diferencia = ganancia_real - ganancia_ideal
            return {
                'valor': round(diferencia, 2),
                'porcentaje': round((diferencia / ganancia_ideal * 100), 1) if ganancia_ideal != 0 else 0,
                'estado': 'adecuada' if abs(diferencia) <= 2 else ('excesiva' if diferencia > 2 else 'insuficiente')
            }
        return None

    # =========================================================================
    # CÁLCULOS DE PRESIÓN ARTERIAL
    # =========================================================================

    def get_presion_arterial_formatted(self, obj):
        """Formatear presión arterial"""
        if obj.presion_arterial_sistolica and obj.presion_arterial_diastolica:
            return f"{obj.presion_arterial_sistolica}/{obj.presion_arterial_diastolica}"
        return None

    def get_presion_arterial_media(self, obj):
        """Calcular PAM"""
        return obj.calcular_pam()

    def get_clasificacion_pa(self, obj):
        """
        Clasificar presión arterial según guías ACOG 2019.

        Categorías:
        - Normal: < 120/80
        - Elevada: 120-129 y < 80
        - Hipertensión Estadio 1: 130-139 o 80-89
        - Hipertensión Estadio 2: ≥ 140 o ≥ 90
        - Crisis hipertensiva: ≥ 180 o ≥ 120
        """
        if not obj.presion_arterial_sistolica or not obj.presion_arterial_diastolica:
            return None

        pas = obj.presion_arterial_sistolica
        pad = obj.presion_arterial_diastolica

        if pas >= 180 or pad >= 120:
            return {
                'categoria': 'Crisis Hipertensiva',
                'severidad': 'crítica',
                'accion': 'Atención médica INMEDIATA'
            }
        elif pas >= 140 or pad >= 90:
            return {
                'categoria': 'Hipertensión Estadio 2',
                'severidad': 'alta',
                'accion': 'Evaluación urgente, considerar hospitalización'
            }
        elif pas >= 130 or pad >= 80:
            return {
                'categoria': 'Hipertensión Estadio 1',
                'severidad': 'moderada',
                'accion': 'Control estricto, considerar tratamiento'
            }
        elif pas >= 120 and pad < 80:
            return {
                'categoria': 'Presión Elevada',
                'severidad': 'leve',
                'accion': 'Monitoreo frecuente'
            }
        else:
            return {
                'categoria': 'Normal',
                'severidad': 'ninguna',
                'accion': 'Continuar controles habituales'
            }

    # =========================================================================
    # INFORMACIÓN DE RELACIONES
    # =========================================================================

    def get_embarazo_info(self, obj):
        """Información completa del embarazo"""
        if obj.embarazo:
            embarazo = obj.embarazo
            return {
                'id': embarazo.id,
                'numero_gesta': embarazo.numero_gesta if hasattr(embarazo, 'numero_gesta') else None,
                'fur': str(embarazo.fecha_ultima_menstruacion) if embarazo.fecha_ultima_menstruacion else None,
                'fpp': str(embarazo.fpp_calculada) if hasattr(embarazo, 'fpp_calculada') and embarazo.fpp_calculada else None,
                'tipo_embarazo': embarazo.tipo_embarazo if hasattr(embarazo, 'tipo_embarazo') else 'simple',
                'estado': embarazo.estado if hasattr(embarazo, 'estado') else None,
                'tiene_complicaciones': self._verificar_complicaciones(embarazo),
            }
        return None

    def _verificar_complicaciones(self, embarazo):
        """Verificar si el embarazo tiene complicaciones registradas"""
        complicaciones = []
        if hasattr(embarazo, 'diabetes_gestacional') and embarazo.diabetes_gestacional:
            complicaciones.append('diabetes_gestacional')
        if hasattr(embarazo, 'hipertension_gestacional') and embarazo.hipertension_gestacional:
            complicaciones.append('hipertension_gestacional')
        if hasattr(embarazo, 'preeclampsia') and embarazo.preeclampsia:
            complicaciones.append('preeclampsia')
        if hasattr(embarazo, 'amenaza_parto_prematuro') and embarazo.amenaza_parto_prematuro:
            complicaciones.append('amenaza_parto_prematuro')
        return complicaciones

    def get_medico_info(self, obj):
        """Información del médico que realizó el control"""
        if obj.medico:
            return {
                'id': obj.medico.id,
                'nombre': f"{obj.medico.nombres} {obj.medico.apellidos}" if hasattr(obj.medico, 'nombres') else str(obj.medico),
                'especialidad': obj.medico.especialidad if hasattr(obj.medico, 'especialidad') else None,
            }
        return None

    def get_enfermero_info(self, obj):
        """Información del enfermero que asistió"""
        if obj.enfermero:
            return {
                'id': obj.enfermero.id,
                'nombre': f"{obj.enfermero.nombres} {obj.enfermero.apellidos}" if hasattr(obj.enfermero, 'nombres') else str(obj.enfermero),
            }
        return None

    # =========================================================================
    # SISTEMA DE ALERTAS MÉDICAS
    # =========================================================================

    def get_alertas(self, obj):
        """
        Sistema completo de alertas médicas.

        Detecta:
        - Hipertensión y preeclampsia
        - FCF anormal
        - Alteraciones de peso
        - Edema y proteinuria
        - Presentación fetal anormal
        - Altura uterina discordante
        - Falta de movimientos fetales
        """
        alertas = []

        # ===== ALERTAS DE PRESIÓN ARTERIAL =====
        if obj.presion_arterial_sistolica and obj.presion_arterial_diastolica:
            pas = obj.presion_arterial_sistolica
            pad = obj.presion_arterial_diastolica

            if pas >= 160 or pad >= 110:
                alertas.append({
                    'tipo': 'hipertension_severa',
                    'severidad': 'crítica',
                    'mensaje': f'PA {pas}/{pad} mmHg - HIPERTENSIÓN SEVERA',
                    'accion': 'Evaluación INMEDIATA. Riesgo de eclampsia.'
                })
            elif pas >= 140 or pad >= 90:
                # Verificar si hay signos de preeclampsia
                if obj.proteinuria and obj.proteinuria != 'negativa':
                    alertas.append({
                        'tipo': 'preeclampsia',
                        'severidad': 'crítica',
                        'mensaje': f'PA {pas}/{pad} mmHg + Proteinuria - PREECLAMPSIA',
                        'accion': 'Evaluación urgente. Considerar hospitalización.'
                    })
                else:
                    alertas.append({
                        'tipo': 'hipertension',
                        'severidad': 'alta',
                        'mensaje': f'PA {pas}/{pad} mmHg - Hipertensión',
                        'accion': 'Control estrecho. Evaluar proteinuria.'
                    })
            elif pas >= 120 or pad >= 80:
                alertas.append({
                    'tipo': 'prehipertension',
                    'severidad': 'moderada',
                    'mensaje': f'PA {pas}/{pad} mmHg - Presión elevada',
                    'accion': 'Monitoreo frecuente.'
                })

        # ===== ALERTAS DE FRECUENCIA CARDÍACA FETAL =====
        if obj.frecuencia_cardiaca_fetal:
            fcf = obj.frecuencia_cardiaca_fetal

            if fcf < 110:
                alertas.append({
                    'tipo': 'bradicardia_fetal',
                    'severidad': 'crítica',
                    'mensaje': f'FCF {fcf} lpm - BRADICARDIA FETAL',
                    'accion': 'Evaluación URGENTE. Monitoreo fetal continuo.'
                })
            elif fcf > 160:
                alertas.append({
                    'tipo': 'taquicardia_fetal',
                    'severidad': 'alta',
                    'mensaje': f'FCF {fcf} lpm - Taquicardia fetal',
                    'accion': 'Investigar causa. Descartar infección, hipoxia.'
                })
            elif fcf < 120 or fcf > 150:
                alertas.append({
                    'tipo': 'fcf_limite',
                    'severidad': 'moderada',
                    'mensaje': f'FCF {fcf} lpm - Límite de normalidad',
                    'accion': 'Repetir medición. Monitoreo.'
                })

        # ===== ALERTAS DE PROTEINURIA Y EDEMA =====
        if obj.proteinuria and obj.proteinuria != 'negativa':
            severidad_proteinuria = {
                'trazas': 'moderada',
                'positiva_1': 'alta',
                'positiva_2': 'crítica',
                'positiva_3': 'crítica',
            }.get(obj.proteinuria, 'moderada')

            mensaje_proteinuria = {
                'trazas': 'Trazas de proteína en orina',
                'positiva_1': 'Proteinuria +',
                'positiva_2': 'Proteinuria ++ (SIGNIFICATIVA)',
                'positiva_3': 'Proteinuria +++ (SEVERA)',
            }.get(obj.proteinuria, 'Proteinuria detectada')

            alertas.append({
                'tipo': 'proteinuria',
                'severidad': severidad_proteinuria,
                'mensaje': mensaje_proteinuria,
                'accion': 'Evaluar función renal. Descartar preeclampsia.'
            })

        if obj.edema:
            if obj.edema == 'severo':
                alertas.append({
                    'tipo': 'edema_severo',
                    'severidad': 'alta',
                    'mensaje': 'Edema severo generalizado',
                    'accion': 'Descartar preeclampsia, insuficiencia cardíaca.'
                })
            elif obj.edema in ['moderado', 'leve'] and obj.proteinuria and obj.proteinuria != 'negativa':
                alertas.append({
                    'tipo': 'edema_proteinuria',
                    'severidad': 'alta',
                    'mensaje': 'Edema + Proteinuria',
                    'accion': 'Alto riesgo de preeclampsia.'
                })

        # ===== ALERTAS DE MOVIMIENTOS FETALES =====
        if obj.movimientos_fetales == 'ausentes' and obj.semanas_gestacion and obj.semanas_gestacion >= 20:
            alertas.append({
                'tipo': 'movimientos_ausentes',
                'severidad': 'crítica',
                'mensaje': 'Ausencia de movimientos fetales',
                'accion': 'Evaluación URGENTE. Monitoreo fetal inmediato.'
            })
        elif obj.movimientos_fetales == 'disminuidos' and obj.semanas_gestacion and obj.semanas_gestacion >= 28:
            alertas.append({
                'tipo': 'movimientos_disminuidos',
                'severidad': 'alta',
                'mensaje': 'Movimientos fetales disminuidos',
                'accion': 'Test no estresante. Perfil biofísico.'
            })

        # ===== ALERTAS DE PESO =====
        diferencia_peso = self.get_diferencia_peso(obj)
        if diferencia_peso:
            if diferencia_peso['estado'] == 'excesiva':
                alertas.append({
                    'tipo': 'ganancia_excesiva',
                    'severidad': 'moderada',
                    'mensaje': f"Ganancia de peso excesiva (+{diferencia_peso['porcentaje']}%)",
                    'accion': 'Asesoría nutricional. Descartar diabetes gestacional.'
                })
            elif diferencia_peso['estado'] == 'insuficiente':
                alertas.append({
                    'tipo': 'ganancia_insuficiente',
                    'severidad': 'moderada',
                    'mensaje': f"Ganancia de peso insuficiente ({diferencia_peso['porcentaje']}%)",
                    'accion': 'Asesoría nutricional. Descartar RCIU.'
                })

        # ===== ALERTAS DE IMC =====
        imc = self.get_imc_actual(obj)
        if imc:
            if imc >= 40:
                alertas.append({
                    'tipo': 'obesidad_morbida',
                    'severidad': 'alta',
                    'mensaje': f'IMC {imc} - Obesidad mórbida',
                    'accion': 'Alto riesgo obstétrico. Control multidisciplinario.'
                })
            elif imc < 16:
                alertas.append({
                    'tipo': 'bajo_peso_severo',
                    'severidad': 'alta',
                    'mensaje': f'IMC {imc} - Bajo peso severo',
                    'accion': 'Evaluación nutricional urgente.'
                })

        # ===== ALERTAS DE ALTURA UTERINA =====
        concordancia = self.get_concordancia_altura_eg(obj)
        if concordancia and concordancia['discordancia']:
            alertas.append({
                'tipo': 'altura_uterina_anormal',
                'severidad': 'moderada' if abs(concordancia['diferencia']) <= 4 else 'alta',
                'mensaje': f"Altura uterina {concordancia['interpretacion']}",
                'accion': concordancia['accion']
            })

        # ===== ALERTAS DE PRESENTACIÓN FETAL =====
        if obj.presentacion_fetal and obj.semanas_gestacion:
            if obj.presentacion_fetal in ['podalica', 'transversa'] and obj.semanas_gestacion >= 36:
                alertas.append({
                    'tipo': 'presentacion_anormal',
                    'severidad': 'alta',
                    'mensaje': f'Presentación {obj.presentacion_fetal} a las {obj.semanas_gestacion} semanas',
                    'accion': 'Considerar versión cefálica externa o cesárea.'
                })

        # Ordenar alertas por severidad
        orden_severidad = {'crítica': 0, 'alta': 1, 'moderada': 2, 'leve': 3}
        alertas.sort(key=lambda x: orden_severidad.get(x['severidad'], 999))

        return alertas

    def get_tiene_alertas(self, obj):
        """Verifica si tiene alguna alerta"""
        alertas = self.get_alertas(obj)
        return len(alertas) > 0

    def get_nivel_riesgo(self, obj):
        """
        Calcula el nivel de riesgo global del control.

        Niveles:
        - bajo: Sin alertas o solo alertas leves
        - moderado: Alertas moderadas
        - alto: Alertas altas
        - crítico: Alertas críticas
        """
        alertas = self.get_alertas(obj)

        if not alertas:
            return 'bajo'

        severidades = [a['severidad'] for a in alertas]

        if 'crítica' in severidades:
            return 'crítico'
        elif 'alta' in severidades:
            return 'alto'
        elif 'moderada' in severidades:
            return 'moderado'
        else:
            return 'bajo'

    def get_requiere_atencion_inmediata(self, obj):
        """Determina si requiere atención médica inmediata"""
        nivel_riesgo = self.get_nivel_riesgo(obj)
        return nivel_riesgo in ['crítico', 'alto']

    # =========================================================================
    # EVALUACIONES OBSTÉTRICAS
    # =========================================================================

    def get_concordancia_altura_eg(self, obj):
        """
        Evalúa la concordancia entre altura uterina y edad gestacional.

        Regla general: Altura uterina (cm) ≈ Semanas de gestación (±2-3 cm)
        Válido desde semana 20 hasta semana 36
        """
        if not obj.altura_uterina or not obj.semanas_gestacion:
            return None

        if obj.semanas_gestacion < 20 or obj.semanas_gestacion > 36:
            return {
                'aplicable': False,
                'mensaje': 'Evaluación de concordancia no aplicable fuera de 20-36 semanas'
            }

        diferencia = obj.altura_uterina - obj.semanas_gestacion

        if abs(diferencia) <= 2:
            interpretacion = 'Concordante (normal)'
            discordancia = False
            accion = 'Continuar controles habituales'
        elif abs(diferencia) <= 3:
            if diferencia > 0:
                interpretacion = 'Levemente mayor que EG'
                accion = 'Reevaluar en próximo control. Descartar polihidramnios, macrosomía.'
            else:
                interpretacion = 'Levemente menor que EG'
                accion = 'Reevaluar en próximo control. Descartar oligohidramnios, RCIU.'
            discordancia = True
        else:
            if diferencia > 0:
                interpretacion = 'Significativamente mayor que EG'
                accion = 'Ecografía urgente. Descartar polihidramnios, macrosomía, embarazo múltiple.'
            else:
                interpretacion = 'Significativamente menor que EG'
                accion = 'Ecografía urgente. Descartar RCIU, oligohidramnios.'
            discordancia = True

        return {
            'aplicable': True,
            'altura_uterina': obj.altura_uterina,
            'semanas_gestacion': obj.semanas_gestacion,
            'diferencia': round(diferencia, 1),
            'interpretacion': interpretacion,
            'discordancia': discordancia,
            'accion': accion
        }

    def get_evaluacion_fcf(self, obj):
        """Evaluación detallada de la FCF"""
        if not obj.frecuencia_cardiaca_fetal:
            return None

        fcf = obj.frecuencia_cardiaca_fetal

        if fcf < 110:
            categoria = 'Bradicardia'
            severidad = 'crítica'
            interpretacion = 'FCF anormalmente baja. Posible sufrimiento fetal.'
        elif fcf < 120:
            categoria = 'FCF baja'
            severidad = 'moderada'
            interpretacion = 'FCF en límite inferior. Requiere monitoreo.'
        elif fcf <= 160:
            categoria = 'Normal'
            severidad = 'ninguna'
            interpretacion = 'FCF dentro de rangos normales.'
        elif fcf <= 180:
            categoria = 'Taquicardia leve'
            severidad = 'moderada'
            interpretacion = 'FCF elevada. Investigar causa.'
        else:
            categoria = 'Taquicardia severa'
            severidad = 'crítica'
            interpretacion = 'FCF muy elevada. Posible infección, hipoxia fetal.'

        return {
            'valor': fcf,
            'categoria': categoria,
            'severidad': severidad,
            'interpretacion': interpretacion,
            'normal': 110 <= fcf <= 160
        }

    def to_representation(self, instance):
        """Personalizar representación de salida"""
        representation = super().to_representation(instance)

        # Formatear fechas
        if representation.get('fecha_control'):
            try:
                if isinstance(representation['fecha_control'], str):
                    fecha = datetime.strptime(representation['fecha_control'], '%Y-%m-%d')
                else:
                    fecha = representation['fecha_control']
                representation['fecha_control_formatted'] = fecha.strftime('%d/%m/%Y')
            except:
                pass

        return representation


# =============================================================================
# SERIALIZERS DE ESCRITURA (CREACIÓN/ACTUALIZACIÓN)
# =============================================================================

class ControlPrenatalCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para creación de controles prenatales.

    Incluye validaciones médicas exhaustivas:
    - Validación de embarazo activo
    - Validación de rangos de signos vitales
    - Validación de correlación altura uterina - EG
    - Prevención de controles duplicados
    - Asignación automática de paciente
    """

    class Meta:
        model = ControlPrenatal
        fields = [
            'embarazo',
            'numero_control',
            'fecha_control',
            'semanas_gestacion',
            'dias_gestacion',
            'peso_actual',
            'peso_pregestacional',
            'talla',
            'presion_arterial_sistolica',
            'presion_arterial_diastolica',
            'frecuencia_cardiaca',
            'temperatura',
            'altura_uterina',
            'frecuencia_cardiaca_fetal',
            'presentacion_fetal',
            'movimientos_fetales',
            'edema',
            'proteinuria',
            'glucosa',
            'hemoglobina',
            'sintomas_actuales',
            'diagnostico',
            'tratamiento_indicado',
            'examenes_solicitados',
            'proxima_cita',
            'observaciones',
            'medico',
            'enfermero',
        ]

    def validate_embarazo(self, value):
        """Validar que el embarazo existe y está en curso"""
        if not value:
            raise serializers.ValidationError("Debe especificar un embarazo.")

        if hasattr(value, 'estado'):
            if value.estado not in ['en_curso', 'activo']:
                raise serializers.ValidationError(
                    f"El embarazo debe estar en curso. Estado actual: {value.estado}"
                )

        return value

    def validate_presion_arterial_sistolica(self, value):
        """Validar PA sistólica"""
        if value is not None:
            if value < 60 or value > 250:
                raise serializers.ValidationError(
                    f"PA sistólica {value} mmHg fuera de rango válido (60-250)."
                )
            if value >= 180:
                # Advertencia pero no error
                pass
        return value

    def validate_presion_arterial_diastolica(self, value):
        """Validar PA diastólica"""
        if value is not None:
            if value < 40 or value > 150:
                raise serializers.ValidationError(
                    f"PA diastólica {value} mmHg fuera de rango válido (40-150)."
                )
        return value

    def validate_frecuencia_cardiaca(self, value):
        """Validar FC materna"""
        if value is not None:
            if value < 40 or value > 200:
                raise serializers.ValidationError(
                    f"Frecuencia cardíaca {value} lpm fuera de rango válido (40-200)."
                )
        return value

    def validate_temperatura(self, value):
        """Validar temperatura"""
        if value is not None:
            if value < 35.0 or value > 42.0:
                raise serializers.ValidationError(
                    f"Temperatura {value}°C fuera de rango válido (35-42)."
                )
        return value

    def validate_frecuencia_cardiaca_fetal(self, value):
        """Validar FCF"""
        if value is not None:
            if value < 90 or value > 200:
                raise serializers.ValidationError(
                    f"FCF {value} lpm fuera de rango válido (90-200)."
                )
        return value

    def validate_semanas_gestacion(self, value):
        """Validar semanas de gestación"""
        if value is not None:
            if value < 0 or value > 44:
                raise serializers.ValidationError(
                    f"Semanas de gestación {value} fuera de rango válido (0-44)."
                )
        return value

    def validate_dias_gestacion(self, value):
        """Validar días de gestación"""
        if value is not None:
            if value < 0 or value > 6:
                raise serializers.ValidationError(
                    f"Días de gestación {value} fuera de rango válido (0-6)."
                )
        return value

    def validate(self, data):
        """Validaciones cruzadas"""
        errors = {}

        # Validar PA sistólica > diastólica
        if data.get('presion_arterial_sistolica') and data.get('presion_arterial_diastolica'):
            if data['presion_arterial_sistolica'] <= data['presion_arterial_diastolica']:
                errors['presion_arterial'] = 'PA sistólica debe ser mayor que diastólica.'

        # Validar que no exista control duplicado
        if data.get('embarazo') and data.get('numero_control'):
            existe = ControlPrenatal.objects.filter(
                embarazo=data['embarazo'],
                numero_control=data['numero_control']
            ).exists()

            if existe:
                errors['numero_control'] = f"Ya existe el control #{data['numero_control']} para este embarazo."

        # Validar fecha de control no en futuro
        if data.get('fecha_control'):
            if data['fecha_control'] > timezone.now().date():
                errors['fecha_control'] = 'La fecha del control no puede ser futura.'

        # Validar peso positivo
        if data.get('peso_actual') and data['peso_actual'] <= 0:
            errors['peso_actual'] = 'El peso debe ser mayor a 0.'

        if data.get('peso_pregestacional') and data['peso_pregestacional'] <= 0:
            errors['peso_pregestacional'] = 'El peso pregestacional debe ser mayor a 0.'

        # Validar talla positiva
        if data.get('talla') and (data['talla'] <= 0 or data['talla'] > 250):
            errors['talla'] = 'La talla debe estar entre 0 y 250 cm.'

        if errors:
            raise serializers.ValidationError(errors)

        return data


class ControlPrenatalUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualización de controles prenatales.
    No permite cambiar el embarazo asociado.
    """

    class Meta:
        model = ControlPrenatal
        fields = [
            'numero_control',
            'fecha_control',
            'semanas_gestacion',
            'dias_gestacion',
            'peso_actual',
            'peso_pregestacional',
            'talla',
            'presion_arterial_sistolica',
            'presion_arterial_diastolica',
            'frecuencia_cardiaca',
            'temperatura',
            'altura_uterina',
            'frecuencia_cardiaca_fetal',
            'presentacion_fetal',
            'movimientos_fetales',
            'edema',
            'proteinuria',
            'glucosa',
            'hemoglobina',
            'sintomas_actuales',
            'diagnostico',
            'tratamiento_indicado',
            'examenes_solicitados',
            'proxima_cita',
            'observaciones',
            'medico',
            'enfermero',
        ]
        read_only_fields = ['embarazo']


# =============================================================================
# SERIALIZERS ESPECIALIZADOS
# =============================================================================

class ControlPrenatalListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    paciente_nombre = serializers.SerializerMethodField()
    edad_gestacional = serializers.SerializerMethodField()
    presion_arterial = serializers.SerializerMethodField()
    tiene_alertas = serializers.SerializerMethodField()
    nivel_riesgo = serializers.SerializerMethodField()

    class Meta:
        model = ControlPrenatal
        fields = [
            'id',
            'embarazo',
            'paciente_nombre',
            'numero_control',
            'fecha_control',
            'edad_gestacional',
            'presion_arterial',
            'frecuencia_cardiaca_fetal',
            'tiene_alertas',
            'nivel_riesgo',
        ]

    def get_paciente_nombre(self, obj):
        try:
            if obj.embarazo and obj.embarazo.paciente:
                paciente = obj.embarazo.paciente
                return f"{paciente.nombres} {paciente.apellidos}"
            return None
        except:
            return None

    def get_edad_gestacional(self, obj):
        if obj.semanas_gestacion is not None:
            dias = obj.dias_gestacion or 0
            return f"{obj.semanas_gestacion}+{dias}"
        return None

    def get_presion_arterial(self, obj):
        if obj.presion_arterial_sistolica and obj.presion_arterial_diastolica:
            return f"{obj.presion_arterial_sistolica}/{obj.presion_arterial_diastolica}"
        return None

    def get_tiene_alertas(self, obj):
        """Verifica alertas críticas rápidamente"""
        # Verificación rápida sin crear todo el serializer completo
        if obj.presion_arterial_sistolica and obj.presion_arterial_sistolica >= 140:
            return True
        if obj.presion_arterial_diastolica and obj.presion_arterial_diastolica >= 90:
            return True
        if obj.frecuencia_cardiaca_fetal and (obj.frecuencia_cardiaca_fetal < 110 or obj.frecuencia_cardiaca_fetal > 160):
            return True
        if obj.proteinuria and obj.proteinuria not in ['negativa', 'trazas']:
            return True
        if obj.movimientos_fetales == 'ausentes':
            return True
        return False

    def get_nivel_riesgo(self, obj):
        """Evaluación rápida de riesgo"""
        if obj.presion_arterial_sistolica and obj.presion_arterial_sistolica >= 160:
            return 'crítico'
        if obj.frecuencia_cardiaca_fetal and obj.frecuencia_cardiaca_fetal < 110:
            return 'crítico'
        if obj.movimientos_fetales == 'ausentes':
            return 'crítico'
        if self.get_tiene_alertas(obj):
            return 'alto'
        return 'bajo'


class ControlPrenatalEstadisticasSerializer(serializers.Serializer):
    """Serializer para estadísticas de controles de un embarazo"""
    total_controles = serializers.IntegerField()
    promedio_pa_sistolica = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    promedio_pa_diastolica = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    promedio_fcf = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    ganancia_peso_total = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    controles_con_alertas = serializers.IntegerField()
    ultimo_control_fecha = serializers.DateField(allow_null=True)
    proxima_cita = serializers.DateField(allow_null=True)


class ControlPrenatalExportSerializer(serializers.ModelSerializer):
    """Serializer para exportación de datos (CSV, Excel)"""
    paciente_nombre = serializers.SerializerMethodField()
    paciente_cedula = serializers.SerializerMethodField()
    edad_gestacional = serializers.SerializerMethodField()
    presion_arterial = serializers.SerializerMethodField()
    imc = serializers.SerializerMethodField()

    class Meta:
        model = ControlPrenatal
        fields = [
            'id',
            'numero_control',
            'fecha_control',
            'paciente_nombre',
            'paciente_cedula',
            'edad_gestacional',
            'peso_actual',
            'imc',
            'presion_arterial',
            'frecuencia_cardiaca',
            'temperatura',
            'altura_uterina',
            'frecuencia_cardiaca_fetal',
            'presentacion_fetal',
            'movimientos_fetales',
            'edema',
            'proteinuria',
        ]

    def get_paciente_nombre(self, obj):
        if obj.embarazo and obj.embarazo.paciente:
            p = obj.embarazo.paciente
            return f"{p.nombres} {p.apellidos}"
        return ""

    def get_paciente_cedula(self, obj):
        if obj.embarazo and obj.embarazo.paciente:
            return obj.embarazo.paciente.cedula_identidad or ""
        return ""

    def get_edad_gestacional(self, obj):
        if obj.semanas_gestacion:
            return f"{obj.semanas_gestacion}+{obj.dias_gestacion or 0}"
        return ""

    def get_presion_arterial(self, obj):
        if obj.presion_arterial_sistolica and obj.presion_arterial_diastolica:
            return f"{obj.presion_arterial_sistolica}/{obj.presion_arterial_diastolica}"
        return ""

    def get_imc(self, obj):
        imc = obj.calcular_imc()
        return imc if imc else ""
