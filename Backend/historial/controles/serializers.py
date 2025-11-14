from rest_framework import serializers
from .models import ControlPrenatal
from embarazos.models import Embarazo
from pacientes.models import Paciente

class ControlPrenatalSerializer(serializers.ModelSerializer):
    # Campos calculados y de lectura
    paciente_nombre = serializers.SerializerMethodField()
    edad_gestacional = serializers.SerializerMethodField()
    imc_actual = serializers.SerializerMethodField()
    clasificacion_imc = serializers.SerializerMethodField()
    presion_arterial = serializers.SerializerMethodField()
    presion_arterial_media = serializers.SerializerMethodField()
    ganancia_peso = serializers.SerializerMethodField()
    
    # Campos de relación con información adicional
    embarazo_info = serializers.SerializerMethodField()
    
    class Meta:
        model = ControlPrenatal
        fields = [
            'id',
            'embarazo',  # ✅ Cambiado de embarazo_id a embarazo (ForeignKey)
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
            'medico',      # ✅ Cambiado de medico_id a medico (ForeignKey)
            'enfermero',   # ✅ Añadido enfermero (ForeignKey)
            'fecha_registro',
        ]
        read_only_fields = ['id', 'fecha_registro']
    
    def get_paciente_nombre(self, obj):
        """Obtener nombre completo del paciente"""
        try:
            if obj.embarazo and obj.embarazo.paciente:
                paciente = obj.embarazo.paciente
                return f"{paciente.nombre} {paciente.apellido_paterno} {paciente.apellido_materno or ''}".strip()
            elif obj.paciente:
                return f"{obj.paciente.nombre} {obj.paciente.apellido_paterno} {obj.paciente.apellido_materno or ''}".strip()
            return None
        except:
            return None
    
    def get_edad_gestacional(self, obj):
        """Formatear edad gestacional"""
        if obj.dias_gestacion:
            return f"{obj.semanas_gestacion}+{obj.dias_gestacion}"
        return f"{obj.semanas_gestacion}+0"
    
    def get_imc_actual(self, obj):
        """Calcular IMC actual"""
        if obj.peso_actual and obj.talla:
            try:
                talla_m = float(obj.talla) / 100
                imc = float(obj.peso_actual) / (talla_m * talla_m)
                return round(imc, 2)
            except:
                return None
        return None
    
    def get_clasificacion_imc(self, obj):
        """Clasificar IMC según OMS"""
        imc = self.get_imc_actual(obj)
        if imc:
            if imc < 18.5:
                return "Bajo peso"
            elif imc < 25:
                return "Normal"
            elif imc < 30:
                return "Sobrepeso"
            else:
                return "Obesidad"
        return None
    
    def get_presion_arterial(self, obj):
        """Formatear presión arterial"""
        if obj.presion_arterial_sistolica and obj.presion_arterial_diastolica:
            return f"{obj.presion_arterial_sistolica}/{obj.presion_arterial_diastolica}"
        return None
    
    def get_presion_arterial_media(self, obj):
        """Calcular Presión Arterial Media (PAM)"""
        if obj.presion_arterial_sistolica and obj.presion_arterial_diastolica:
            try:
                pam = (obj.presion_arterial_sistolica + (2 * obj.presion_arterial_diastolica)) / 3
                return round(pam, 2)
            except:
                return None
        return None
    
    def get_ganancia_peso(self, obj):
        """Calcular ganancia de peso"""
        if obj.peso_actual and obj.peso_pregestacional:
            try:
                ganancia = float(obj.peso_actual) - float(obj.peso_pregestacional)
                return round(ganancia, 1)
            except:
                return None
        return None
    
    def get_embarazo_info(self, obj):
        """Información adicional del embarazo"""
        # ✅ Ahora usa la relación ForeignKey directamente
        try:
            if obj.embarazo:
                embarazo = obj.embarazo
                return {
                    'id': embarazo.id,
                    'paciente_id': embarazo.paciente.id,
                    'paciente_nombre': f"{embarazo.paciente.nombre} {embarazo.paciente.apellido_paterno}",
                    'numero_gesta': embarazo.numero_gesta,
                    'fecha_ultima_menstruacion': str(embarazo.fecha_ultima_menstruacion),
                    'fecha_probable_parto': str(embarazo.fecha_probable_parto) if embarazo.fecha_probable_parto else None,
                    'estado': embarazo.estado,
                }
        except Exception as e:
            pass
        return None
    
    def validate(self, data):
        """Validaciones adicionales"""
        # Validar que la PA sistólica sea mayor que la diastólica
        if 'presion_arterial_sistolica' in data and 'presion_arterial_diastolica' in data:
            if data['presion_arterial_sistolica'] <= data['presion_arterial_diastolica']:
                raise serializers.ValidationError({
                    'presion_arterial_sistolica': 'La presión sistólica debe ser mayor que la diastólica'
                })
        
        # Validar FCF
        if 'frecuencia_cardiaca_fetal' in data:
            fcf = data['frecuencia_cardiaca_fetal']
            if fcf < 90 or fcf > 180:
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
        if 'dias_gestacion' in data:
            dias = data['dias_gestacion']
            if dias < 0 or dias > 6:
                raise serializers.ValidationError({
                    'dias_gestacion': 'Los días deben estar entre 0 y 6'
                })
        
        return data
    
    def to_representation(self, instance):
        """Personalizar la representación de salida"""
        representation = super().to_representation(instance)
        
        # Formatear fechas
        if representation.get('fecha_control'):
            from datetime import datetime
            try:
                fecha = datetime.strptime(representation['fecha_control'], '%Y-%m-%d')
                representation['fecha_control_formatted'] = fecha.strftime('%d/%m/%Y')
            except:
                pass
        
        # Agregar estado de alertas
        alertas = []
        
        if instance.presion_arterial_sistolica and instance.presion_arterial_diastolica:
            if instance.presion_arterial_sistolica >= 140 or instance.presion_arterial_diastolica >= 90:
                alertas.append('hipertension')
            elif instance.presion_arterial_sistolica >= 120 or instance.presion_arterial_diastolica >= 80:
                alertas.append('prehipertension')
        
        if instance.frecuencia_cardiaca_fetal:
            if instance.frecuencia_cardiaca_fetal < 110 or instance.frecuencia_cardiaca_fetal > 160:
                alertas.append('fcf_anormal')
        
        if instance.edema == 'severo':
            alertas.append('edema_severo')
        
        if instance.proteinuria in ['positiva_1', 'positiva_2', 'positiva_3']:
            alertas.append('proteinuria_positiva')
        
        if instance.movimientos_fetales == 'ausentes':
            alertas.append('movimientos_ausentes')
        
        imc = representation.get('imc_actual')
        if imc:
            if imc < 18.5:
                alertas.append('bajo_peso')
            elif imc >= 30:
                alertas.append('obesidad')
        
        representation['alertas'] = alertas
        representation['tiene_alertas'] = len(alertas) > 0
        
        return representation


class ControlPrenatalListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas"""
    paciente_nombre = serializers.SerializerMethodField()
    edad_gestacional = serializers.SerializerMethodField()
    presion_arterial = serializers.SerializerMethodField()
    tiene_alertas = serializers.SerializerMethodField()

    class Meta:
        model = ControlPrenatal
        fields = [
            'id',
            'embarazo',  # ✅ Cambiado de embarazo_id a embarazo
            'paciente_nombre',
            'numero_control',
            'fecha_control',
            'edad_gestacional',
            'presion_arterial',
            'frecuencia_cardiaca_fetal',
            'tiene_alertas',
        ]
    
    def get_paciente_nombre(self, obj):
        try:
            if obj.embarazo and obj.embarazo.paciente:
                paciente = obj.embarazo.paciente
                return f"{paciente.nombre} {paciente.apellido_paterno}"
            return None
        except:
            return None
    
    def get_edad_gestacional(self, obj):
        return f"{obj.semanas_gestacion}+{obj.dias_gestacion or 0}"
    
    def get_presion_arterial(self, obj):
        if obj.presion_arterial_sistolica and obj.presion_arterial_diastolica:
            return f"{obj.presion_arterial_sistolica}/{obj.presion_arterial_diastolica}"
        return None
    
    def get_tiene_alertas(self, obj):
        """Verificar si tiene alertas críticas"""
        alertas = False
        
        if obj.presion_arterial_sistolica and obj.presion_arterial_diastolica:
            if obj.presion_arterial_sistolica >= 140 or obj.presion_arterial_diastolica >= 90:
                alertas = True
        
        if obj.frecuencia_cardiaca_fetal:
            if obj.frecuencia_cardiaca_fetal < 110 or obj.frecuencia_cardiaca_fetal > 160:
                alertas = True
        
        if obj.edema == 'severo':
            alertas = True
        
        if obj.proteinuria in ['positiva_1', 'positiva_2', 'positiva_3']:
            alertas = True
        
        if obj.movimientos_fetales == 'ausentes':
            alertas = True
        
        return alertas


class ControlPrenatalCreateSerializer(serializers.ModelSerializer):
    """Serializer específico para creación de controles"""

    class Meta:
        model = ControlPrenatal
        fields = [
            'embarazo',  # ✅ Cambiado de embarazo_id a embarazo
            'paciente',
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
            'observaciones',
            'medico',     # ✅ Cambiado de medico_id a medico
            'enfermero',  # ✅ Añadido enfermero
        ]

    def validate(self, data):
        """Validaciones específicas para creación"""
        # ✅ Validar que el embarazo exista y esté activo (ahora usa ForeignKey)
        if 'embarazo' in data:
            embarazo = data['embarazo']
            if embarazo.estado != 'activo':
                raise serializers.ValidationError({
                    'embarazo': 'El embarazo debe estar activo para registrar controles'
                })
            # Establecer automáticamente el paciente si no se proporciona
            if 'paciente' not in data:
                data['paciente'] = embarazo.paciente

        # ✅ Validar que no exista otro control con el mismo número (ahora usa ForeignKey)
        if 'embarazo' in data and 'numero_control' in data:
            exists = ControlPrenatal.objects.filter(
                embarazo=data['embarazo'],
                numero_control=data['numero_control']
            ).exists()
            if exists:
                raise serializers.ValidationError({
                    'numero_control': f"Ya existe un control #{data['numero_control']} para este embarazo"
                })

        return super().validate(data)