from rest_framework import serializers
from .models import ControlPrenatal
from embarazos.models import Embarazo
from pacientes.models import Paciente


class ControlPrenatalListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados rápidos"""
    
    paciente_nombre = serializers.SerializerMethodField()
    embarazo_info = serializers.SerializerMethodField()
    edad_gestacional = serializers.SerializerMethodField()
    presion_arterial = serializers.SerializerMethodField()
    tiene_alertas = serializers.SerializerMethodField()
    num_alertas = serializers.SerializerMethodField()
    
    class Meta:
        model = ControlPrenatal
        fields = [
            'id',  # ✅ CORRECCIÓN: Usar 'id' en lugar de 'uuid'
            'embarazo_id',
            'embarazo_info',
            'paciente_nombre',
            'numero_control',
            'fecha_control',
            'edad_gestacional',
            'presion_arterial',
            'frecuencia_cardiaca_fetal',
            'tiene_alertas',
            'num_alertas',
        ]
    
    def get_paciente_nombre(self, obj):
        try:
            if hasattr(obj, 'embarazo_id') and obj.embarazo_id and obj.embarazo_id.paciente:
                paciente = obj.embarazo_id.paciente
                return f"{paciente.nombre} {paciente.apellido_paterno}"
            return "Sin nombre"
        except:
            return None
    
    def get_embarazo_info(self, obj):
        try:
            if hasattr(obj, 'embarazo_id') and obj.embarazo_id:
                return {
                    'id': obj.embarazo_id.id,
                    'numero_gesta': getattr(obj.embarazo_id, 'numero_gesta', None),
                    'riesgo': getattr(obj.embarazo_id, 'riesgo_embarazo', None),
                    'estado': obj.embarazo_id.estado,
                }
        except:
            return None
    
    def get_edad_gestacional(self, obj):
        return f"{obj.semanas_gestacion}+{obj.dias_gestacion or 0}"
    
    def get_presion_arterial(self, obj):
        if obj.presion_arterial_sistolica and obj.presion_arterial_diastolica:
            return f"{obj.presion_arterial_sistolica}/{obj.presion_arterial_diastolica}"
        return None
    
    def get_tiene_alertas(self, obj):
        """Verificar si tiene alertas críticas usando métodos del modelo"""
        return obj.tiene_alertas_criticas()
    
    def get_num_alertas(self, obj):
        """Contar número de alertas"""
        count = 0
        if obj.tiene_hipertension() or obj.tiene_prehipertension():
            count += 1
        if obj.fcf_es_anormal():
            count += 1
        if obj.edema in ['severo', 'generalizado']:
            count += 1
        if obj.proteinuria in ['positiva_1', 'positiva_2', 'positiva_3', 'positiva_4']:
            count += 1
        if obj.movimientos_fetales == 'ausentes':
            count += 1
        return count


class ControlPrenatalSerializer(serializers.ModelSerializer):
    """Serializer COMPLETO para visualización detallada de controles prenatales"""
    
    # Campos calculados y de lectura
    paciente_nombre = serializers.SerializerMethodField()
    embarazo_info = serializers.SerializerMethodField()
    edad_gestacional = serializers.SerializerMethodField()
    imc_actual = serializers.SerializerMethodField()
    clasificacion_imc = serializers.SerializerMethodField()
    presion_arterial = serializers.SerializerMethodField()
    presion_arterial_media = serializers.SerializerMethodField()
    ganancia_peso = serializers.SerializerMethodField()
    alertas = serializers.SerializerMethodField()
    tiene_alertas = serializers.SerializerMethodField()
    
    class Meta:
        model = ControlPrenatal
        fields = [
            'id',  # ✅ CORRECCIÓN: Usar 'id' en lugar de 'uuid'
            'embarazo_id',
            'embarazo_info',
            'paciente',
            'paciente_nombre',
            'numero_control',
            'fecha_control',
            'semanas_gestacion',
            'dias_gestacion',
            'edad_gestacional',
            'peso_actual',
            'peso_pregestacional',
            'ganancia_peso',
            'talla',
            'imc_actual',
            'clasificacion_imc',
            'presion_arterial_sistolica',
            'presion_arterial_diastolica',
            'presion_arterial',
            'presion_arterial_media',
            'frecuencia_cardiaca',
            'temperatura',
            'altura_uterina',
            'frecuencia_cardiaca_fetal',
            'presentacion_fetal',
            'movimientos_fetales',
            'edema',
            'proteinuria',
            'observaciones',
            'medico_id',
            'fecha_registro',
            'alertas',
            'tiene_alertas',
        ]
        read_only_fields = ['id', 'fecha_registro']  # ✅ CORRECCIÓN: Quitar 'uuid'
    
    def get_paciente_nombre(self, obj):
        """Obtener nombre completo del paciente"""
        try:
            if hasattr(obj, 'embarazo_id') and obj.embarazo_id:
                paciente = obj.embarazo_id.paciente
                apellido_materno = paciente.apellido_materno if hasattr(paciente, 'apellido_materno') else ''
                return f"{paciente.nombre} {paciente.apellido_paterno} {apellido_materno or ''}".strip()
            elif obj.paciente:
                apellido_materno = obj.paciente.apellido_materno if hasattr(obj.paciente, 'apellido_materno') else ''
                return f"{obj.paciente.nombre} {obj.paciente.apellido_paterno} {apellido_materno or ''}".strip()
            return "Paciente no especificado"
        except Exception:
            return None
    
    def get_embarazo_info(self, obj):
        """Información adicional del embarazo"""
        try:
            if hasattr(obj, 'embarazo_id') and obj.embarazo_id:
                embarazo = obj.embarazo_id
                return {
                    'id': embarazo.id,
                    'paciente_id': embarazo.paciente.id,
                    'paciente_nombre': f"{embarazo.paciente.nombre} {embarazo.paciente.apellido_paterno}",
                    'numero_gesta': getattr(embarazo, 'numero_gesta', None),
                    'fecha_ultima_menstruacion': str(embarazo.fecha_ultima_menstruacion),
                    'fecha_probable_parto': str(embarazo.fecha_probable_parto),
                    'estado': embarazo.estado,
                }
        except Exception:
            pass
        return None
    
    def get_edad_gestacional(self, obj):
        """Formatear edad gestacional"""
        dias = obj.dias_gestacion if obj.dias_gestacion else 0
        return f"{obj.semanas_gestacion}+{dias}"
    
    def get_imc_actual(self, obj):
        """Calcular IMC actual usando el property del modelo"""
        return obj.imc
    
    def get_clasificacion_imc(self, obj):
        """Obtener clasificación IMC usando el property del modelo"""
        return obj.clasificacion_imc
    
    def get_presion_arterial(self, obj):
        """Formatear presión arterial"""
        if obj.presion_arterial_sistolica and obj.presion_arterial_diastolica:
            return f"{obj.presion_arterial_sistolica}/{obj.presion_arterial_diastolica}"
        return None
    
    def get_presion_arterial_media(self, obj):
        """Calcular PAM usando el property del modelo"""
        return obj.presion_arterial_media
    
    def get_ganancia_peso(self, obj):
        """Calcular ganancia de peso usando el property del modelo"""
        return obj.ganancia_peso
    
    def get_alertas(self, obj):
        """Obtener lista detallada de alertas"""
        alertas = []
        
        # Hipertensión
        if obj.tiene_hipertension():
            alertas.append({
                'tipo': 'hipertension',
                'nivel': 'alto',
                'mensaje': 'Hipertensión detectada',
                'valor': f"{obj.presion_arterial_sistolica}/{obj.presion_arterial_diastolica}"
            })
        elif obj.tiene_prehipertension():
            alertas.append({
                'tipo': 'prehipertension',
                'nivel': 'medio',
                'mensaje': 'Prehipertensión detectada',
                'valor': f"{obj.presion_arterial_sistolica}/{obj.presion_arterial_diastolica}"
            })
        
        # FCF anormal
        if obj.fcf_es_anormal():
            alertas.append({
                'tipo': 'fcf_anormal',
                'nivel': 'alto',
                'mensaje': 'Frecuencia cardíaca fetal anormal',
                'valor': obj.frecuencia_cardiaca_fetal
            })
        
        # Edema severo
        if obj.edema in ['severo', 'generalizado']:
            alertas.append({
                'tipo': 'edema_severo',
                'nivel': 'medio',
                'mensaje': f'Edema {obj.edema}',
                'valor': obj.edema
            })
        
        # Proteinuria
        if obj.proteinuria in ['positiva_1', 'positiva_2', 'positiva_3', 'positiva_4']:
            alertas.append({
                'tipo': 'proteinuria',
                'nivel': 'alto',
                'mensaje': 'Proteinuria positiva',
                'valor': obj.proteinuria
            })
        
        # Movimientos fetales ausentes
        if obj.movimientos_fetales == 'ausentes':
            alertas.append({
                'tipo': 'movimientos_ausentes',
                'nivel': 'alto',
                'mensaje': 'Movimientos fetales ausentes'
            })
        
        # IMC
        imc = obj.imc
        if imc:
            if imc < 18.5:
                alertas.append({
                    'tipo': 'bajo_peso',
                    'nivel': 'medio',
                    'mensaje': 'Bajo peso materno',
                    'valor': round(imc, 2)
                })
            elif imc >= 30:
                alertas.append({
                    'tipo': 'obesidad',
                    'nivel': 'medio',
                    'mensaje': 'Obesidad materna',
                    'valor': round(imc, 2)
                })
        
        # Fiebre
        if obj.temperatura and float(obj.temperatura) >= 38:
            alertas.append({
                'tipo': 'fiebre',
                'nivel': 'alto',
                'mensaje': f'Fiebre: {obj.temperatura}°C',
                'valor': float(obj.temperatura)
            })
        
        return alertas
    
    def get_tiene_alertas(self, obj):
        """Verificar si tiene alertas críticas"""
        return obj.tiene_alertas_criticas()


class ControlPrenatalCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar controles prenatales"""
    
    # Campos calculados y de lectura
    paciente_nombre = serializers.SerializerMethodField()
    edad_gestacional = serializers.SerializerMethodField()
    imc_actual = serializers.SerializerMethodField()
    clasificacion_imc = serializers.SerializerMethodField()
    presion_arterial = serializers.SerializerMethodField()
    presion_arterial_media = serializers.SerializerMethodField()
    ganancia_peso = serializers.SerializerMethodField()
    embarazo_info = serializers.SerializerMethodField()
    
    class Meta:
        model = ControlPrenatal
        fields = [
            'id',  # ✅ CORRECCIÓN
            'embarazo_id',
            'embarazo_info',
            'paciente',
            'paciente_nombre',
            'numero_control',
            'fecha_control',
            'semanas_gestacion',
            'dias_gestacion',
            'edad_gestacional',
            'peso_actual',
            'peso_pregestacional',
            'ganancia_peso',
            'talla',
            'imc_actual',
            'clasificacion_imc',
            'presion_arterial_sistolica',
            'presion_arterial_diastolica',
            'presion_arterial',
            'presion_arterial_media',
            'frecuencia_cardiaca',
            'temperatura',
            'altura_uterina',
            'frecuencia_cardiaca_fetal',
            'presentacion_fetal',
            'movimientos_fetales',
            'edema',
            'proteinuria',
            'observaciones',
            'medico_id',
            'fecha_registro',
        ]
        read_only_fields = ['id', 'fecha_registro']  # ✅ CORRECCIÓN
    
    def get_paciente_nombre(self, obj):
        """Obtener nombre completo del paciente"""
        try:
            if hasattr(obj, 'embarazo_id') and obj.embarazo_id:
                paciente = obj.embarazo_id.paciente
                apellido_materno = paciente.apellido_materno if hasattr(paciente, 'apellido_materno') else ''
                return f"{paciente.nombre} {paciente.apellido_paterno} {apellido_materno or ''}".strip()
            elif obj.paciente:
                apellido_materno = obj.paciente.apellido_materno if hasattr(obj.paciente, 'apellido_materno') else ''
                return f"{obj.paciente.nombre} {obj.paciente.apellido_paterno} {apellido_materno or ''}".strip()
            return "Paciente no especificado"
        except Exception:
            return None
    
    def get_edad_gestacional(self, obj):
        """Formatear edad gestacional"""
        dias = obj.dias_gestacion if obj.dias_gestacion else 0
        return f"{obj.semanas_gestacion}+{dias}"
    
    def get_imc_actual(self, obj):
        """Calcular IMC actual usando el property del modelo"""
        return obj.imc
    
    def get_clasificacion_imc(self, obj):
        """Obtener clasificación IMC usando el property del modelo"""
        return obj.clasificacion_imc
    
    def get_presion_arterial(self, obj):
        """Formatear presión arterial"""
        if obj.presion_arterial_sistolica and obj.presion_arterial_diastolica:
            return f"{obj.presion_arterial_sistolica}/{obj.presion_arterial_diastolica}"
        return None
    
    def get_presion_arterial_media(self, obj):
        """Calcular PAM usando el property del modelo"""
        return obj.presion_arterial_media
    
    def get_ganancia_peso(self, obj):
        """Calcular ganancia de peso usando el property del modelo"""
        return obj.ganancia_peso
    
    def get_embarazo_info(self, obj):
        """Información adicional del embarazo"""
        try:
            if hasattr(obj, 'embarazo_id') and obj.embarazo_id:
                embarazo = obj.embarazo_id
                return {
                    'id': embarazo.id,
                    'paciente_id': embarazo.paciente.id,
                    'paciente_nombre': f"{embarazo.paciente.nombre} {embarazo.paciente.apellido_paterno}",
                    'numero_gesta': getattr(embarazo, 'numero_gesta', None),
                    'fecha_ultima_menstruacion': str(embarazo.fecha_ultima_menstruacion),
                    'fecha_probable_parto': str(embarazo.fecha_probable_parto),
                    'estado': embarazo.estado,
                }
        except Exception:
            pass
        return None
    
    def validate(self, data):
        """Validaciones adicionales y completas"""
        
        # Validar que la PA sistólica sea mayor que la diastólica
        sistolica = data.get('presion_arterial_sistolica')
        diastolica = data.get('presion_arterial_diastolica')
        
        if sistolica and diastolica:
            if sistolica <= diastolica:
                raise serializers.ValidationError({
                    'presion_arterial_sistolica': 'La presión sistólica debe ser mayor que la diastólica'
                })
        
        # Validar FCF
        if 'frecuencia_cardiaca_fetal' in data:
            fcf = data['frecuencia_cardiaca_fetal']
            if fcf and (fcf < 90 or fcf > 180):
                raise serializers.ValidationError({
                    'frecuencia_cardiaca_fetal': 'FCF debe estar entre 90 y 180 lpm'
                })
        
        # Validar semanas de gestación
        if 'semanas_gestacion' in data:
            semanas = data['semanas_gestacion']
            if semanas < 0 or semanas > 42:
                raise serializers.ValidationError({
                    'semanas_gestacion': 'Las semanas deben estar entre 0 y 42'
                })
        
        # Validar días de gestación
        if 'dias_gestacion' in data and data['dias_gestacion'] is not None:
            dias = data['dias_gestacion']
            if dias < 0 or dias > 6:
                raise serializers.ValidationError({
                    'dias_gestacion': 'Los días deben estar entre 0 y 6'
                })
        
        # Validar embarazo activo
        if 'embarazo_id' in data:
            try:
                if isinstance(data['embarazo_id'], Embarazo):
                    embarazo = data['embarazo_id']
                else:
                    embarazo = Embarazo.objects.get(id=data['embarazo_id'])
                
                if embarazo.estado != 'activo':
                    raise serializers.ValidationError({
                        'embarazo_id': 'El embarazo debe estar activo para registrar controles'
                    })
                
                # Establecer automáticamente el paciente si no se proporciona
                if 'paciente' not in data or not data['paciente']:
                    data['paciente'] = embarazo.paciente
                    
            except Embarazo.DoesNotExist:
                raise serializers.ValidationError({
                    'embarazo_id': 'El embarazo especificado no existe'
                })
            except Exception as e:
                raise serializers.ValidationError({
                    'embarazo_id': f'Error al validar embarazo: {str(e)}'
                })
        
        return data
    
    def to_representation(self, instance):
        """Personalizar la representación de salida con alertas"""
        representation = super().to_representation(instance)
        
        # Formatear fechas
        if representation.get('fecha_control'):
            from datetime import datetime
            try:
                fecha = datetime.strptime(str(representation['fecha_control']), '%Y-%m-%d')
                representation['fecha_control_formatted'] = fecha.strftime('%d/%m/%Y')
            except Exception:
                pass
        
        # Agregar estado de alertas usando los métodos del modelo
        alertas = []
        
        if instance.tiene_hipertension():
            alertas.append('hipertension')
        elif instance.tiene_prehipertension():
            alertas.append('prehipertension')
        
        if instance.fcf_es_anormal():
            alertas.append('fcf_anormal')
        
        if instance.edema in ['severo', 'generalizado']:
            alertas.append('edema_severo')
        
        if instance.proteinuria in ['positiva_1', 'positiva_2', 'positiva_3', 'positiva_4']:
            alertas.append('proteinuria_positiva')
        
        if instance.movimientos_fetales == 'ausentes':
            alertas.append('movimientos_ausentes')
        
        # Alertas de IMC
        imc = instance.imc
        if imc:
            if imc < 18.5:
                alertas.append('bajo_peso')
            elif imc >= 30:
                alertas.append('obesidad')
        
        # Alerta de temperatura
        if instance.temperatura and float(instance.temperatura) >= 38:
            alertas.append('fiebre')
        
        representation['alertas'] = alertas
        representation['tiene_alertas'] = len(alertas) > 0
        
        return representation