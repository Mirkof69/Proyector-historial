from rest_framework import serializers
from .models import TipoExamen, ExamenLaboratorio, ValorReferencia, ResultadoLaboratorio
from pacientes.models import Paciente
from controles.models import ControlPrenatal
from usuarios.models import Usuario


class TipoExamenSerializer(serializers.ModelSerializer):
    """Serializer para Tipos de Exámenes"""
    
    total_examenes = serializers.SerializerMethodField()
    
    class Meta:
        model = TipoExamen
        fields = [
            'id',
            'nombre',
            'codigo',
            'categoria',
            'descripcion',
            'preparacion',
            'tiempo_resultado',
            'precio',
            'activo',
            'total_examenes',
            'fecha_creacion',
            'fecha_actualizacion',
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']
    
    def get_total_examenes(self, obj):
        """Contar cuántos exámenes se han realizado de este tipo"""
        return obj.examenes.count()


class ValorReferenciaSerializer(serializers.ModelSerializer):
    """Serializer para Valores de Referencia"""
    
    tipo_examen_nombre = serializers.CharField(source='tipo_examen.nombre', read_only=True)
    rango_normal = serializers.SerializerMethodField()
    
    class Meta:
        model = ValorReferencia
        fields = [
            'id',
            'tipo_examen',
            'tipo_examen_nombre',
            'parametro',
            'valor_minimo',
            'valor_maximo',
            'valor_normal',
            'unidad',
            'condicion',
            'es_critico_bajo',
            'es_critico_alto',
            'rango_normal',
        ]
    
    def get_rango_normal(self, obj):
        """Formatear rango normal"""
        if obj.valor_minimo and obj.valor_maximo:
            return f"{obj.valor_minimo} - {obj.valor_maximo} {obj.unidad}"
        elif obj.valor_normal:
            return obj.valor_normal
        return None


class ResultadoLaboratorioSerializer(serializers.ModelSerializer):
    """Serializer para Resultados de Laboratorio"""
    
    parametro_nombre = serializers.CharField(source='valor_referencia.parametro', read_only=True)
    unidad = serializers.CharField(source='valor_referencia.unidad', read_only=True)
    rango_referencia = serializers.SerializerMethodField()
    estado = serializers.SerializerMethodField()
    
    class Meta:
        model = ResultadoLaboratorio
        fields = [
            'id',
            'examen',
            'valor_referencia',
            'parametro_nombre',
            'valor_numerico',
            'valor_texto',
            'unidad',
            'rango_referencia',
            'es_normal',
            'es_critico',
            'estado',
            'observaciones',
            'fecha_registro',
        ]
        read_only_fields = ['id', 'fecha_registro']
    
    def get_rango_referencia(self, obj):
        """Obtener rango de referencia"""
        ref = obj.valor_referencia
        if ref.valor_minimo and ref.valor_maximo:
            return f"{ref.valor_minimo} - {ref.valor_maximo}"
        return ref.valor_normal
    
    def get_estado(self, obj):
        """Determinar estado del resultado"""
        if obj.es_critico:
            return 'CRÍTICO'
        elif not obj.es_normal:
            return 'ANORMAL'
        return 'NORMAL'


class ExamenLaboratorioListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    
    paciente_nombre = serializers.CharField(source='paciente.nombre_completo', read_only=True)
    tipo_examen_nombre = serializers.CharField(source='tipo_examen.nombre', read_only=True)
    categoria = serializers.CharField(source='tipo_examen.categoria', read_only=True)
    medico_nombre = serializers.SerializerMethodField()
    tiene_resultados = serializers.SerializerMethodField()
    resultados_anormales = serializers.SerializerMethodField()
    
    class Meta:
        model = ExamenLaboratorio
        fields = [
            'id',
            'paciente',
            'paciente_nombre',
            'tipo_examen',
            'tipo_examen_nombre',
            'categoria',
            'fecha_solicitud',
            'fecha_resultado',
            'estado',
            'prioridad',
            'medico_nombre',
            'tiene_resultados',
            'resultados_anormales',
            'dias_desde_solicitud',
            'esta_vencido',
        ]
    
    def get_medico_nombre(self, obj):
        if obj.medico_solicitante:
            return f"{obj.medico_solicitante.nombre} {obj.medico_solicitante.apellido_paterno}"
        return "No especificado"
    
    def get_tiene_resultados(self, obj):
        return obj.resultados.exists()
    
    def get_resultados_anormales(self, obj):
        return obj.resultados.filter(es_normal=False).count()


class ExamenLaboratorioDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado con resultados incluidos"""
    
    paciente_info = serializers.SerializerMethodField()
    tipo_examen_info = serializers.SerializerMethodField()
    control_prenatal_info = serializers.SerializerMethodField()
    medico_info = serializers.SerializerMethodField()
    resultados = ResultadoLaboratorioSerializer(many=True, read_only=True)
    resumen = serializers.SerializerMethodField()
    
    class Meta:
        model = ExamenLaboratorio
        fields = [
            'id',
            'paciente',
            'paciente_info',
            'control_prenatal',
            'control_prenatal_info',
            'tipo_examen',
            'tipo_examen_info',
            'medico_solicitante',
            'medico_info',
            'fecha_solicitud',
            'fecha_muestra',
            'fecha_resultado',
            'estado',
            'prioridad',
            'indicaciones',
            'observaciones',
            'resultados',
            'resumen',
            'dias_desde_solicitud',
            'esta_pendiente',
            'esta_vencido',
            'fecha_creacion',
            'fecha_actualizacion',
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']
    
    def get_paciente_info(self, obj):
        return {
            'id': obj.paciente.id,
            'nombre_completo': obj.paciente.nombre_completo,
            'id_clinico': obj.paciente.id_clinico,
            'edad': obj.paciente.edad,
        }
    
    def get_tipo_examen_info(self, obj):
        return {
            'id': obj.tipo_examen.id,
            'nombre': obj.tipo_examen.nombre,
            'codigo': obj.tipo_examen.codigo,
            'categoria': obj.tipo_examen.categoria,
            'preparacion': obj.tipo_examen.preparacion,
            'tiempo_resultado': obj.tipo_examen.tiempo_resultado,
        }
    
    def get_control_prenatal_info(self, obj):
        if obj.control_prenatal:
            return {
                'id': obj.control_prenatal.id,
                'numero_control': obj.control_prenatal.numero_control,
                'fecha_control': obj.control_prenatal.fecha_control,
                'semanas_gestacion': obj.control_prenatal.semanas_gestacion,
            }
        return None
    
    def get_medico_info(self, obj):
        if obj.medico_solicitante:
            return {
                'id': obj.medico_solicitante.id,
                'nombre': f"{obj.medico_solicitante.nombre} {obj.medico_solicitante.apellido_paterno}",
                'especialidad': obj.medico_solicitante.especialidad,
            }
        return None
    
    def get_resumen(self, obj):
        """Resumen de resultados"""
        total = obj.resultados.count()
        normales = obj.resultados.filter(es_normal=True).count()
        anormales = obj.resultados.filter(es_normal=False).count()
        criticos = obj.resultados.filter(es_critico=True).count()
        
        return {
            'total_parametros': total,
            'normales': normales,
            'anormales': anormales,
            'criticos': criticos,
            'porcentaje_normalidad': round((normales / total * 100) if total > 0 else 0, 1),
        }


class ExamenLaboratorioCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar exámenes"""
    
    class Meta:
        model = ExamenLaboratorio
        fields = [
            'id',
            'paciente',
            'control_prenatal',
            'tipo_examen',
            'medico_solicitante',
            'fecha_muestra',
            'fecha_resultado',
            'estado',
            'prioridad',
            'indicaciones',
            'observaciones',
        ]
        read_only_fields = ['id']
    
    def validate(self, data):
        """Validaciones personalizadas"""
        
        # Validar que el médico solicitante sea médico
        if data.get('medico_solicitante'):
            if data['medico_solicitante'].rol != 'medico':
                raise serializers.ValidationError({
                    'medico_solicitante': 'El usuario debe tener rol de médico'
                })
        
        # Validar que el control prenatal pertenezca al paciente
        if data.get('control_prenatal') and data.get('paciente'):
            if data['control_prenatal'].paciente != data['paciente']:
                raise serializers.ValidationError({
                    'control_prenatal': 'El control prenatal no pertenece al paciente seleccionado'
                })
        
        # Validar fechas
        if data.get('fecha_muestra') and data.get('fecha_resultado'):
            if data['fecha_muestra'] > data['fecha_resultado']:
                raise serializers.ValidationError({
                    'fecha_resultado': 'La fecha de resultado no puede ser anterior a la fecha de muestra'
                })
        
        return data


class ResultadoLaboratorioCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar resultados"""
    
    parametro_nombre = serializers.CharField(source='valor_referencia.parametro', read_only=True)
    
    class Meta:
        model = ResultadoLaboratorio
        fields = [
            'id',
            'examen',
            'valor_referencia',
            'parametro_nombre',
            'valor_numerico',
            'valor_texto',
            'observaciones',
        ]
        read_only_fields = ['id']
    
    def validate(self, data):
        """Validaciones"""
        
        # Debe tener al menos un valor (numérico o texto)
        if not data.get('valor_numerico') and not data.get('valor_texto'):
            raise serializers.ValidationError(
                'Debe proporcionar al menos un valor (numérico o texto)'
            )
        
        # Validar que el valor de referencia pertenece al tipo de examen
        if data.get('examen') and data.get('valor_referencia'):
            if data['valor_referencia'].tipo_examen != data['examen'].tipo_examen:
                raise serializers.ValidationError({
                    'valor_referencia': 'El parámetro no pertenece al tipo de examen seleccionado'
                })
        
        return data