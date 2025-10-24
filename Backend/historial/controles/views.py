from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from django.db.models import Q, Count, Avg, Max, Min
from django.utils import timezone
from datetime import datetime, timedelta
from .models import ControlPrenatal
from .serializers import (
    ControlPrenatalSerializer, 
    ControlPrenatalListSerializer,
    ControlPrenatalCreateSerializer
)
from rest_framework import serializers as rest_serializers

class ControlPrenatalViewSet(viewsets.ModelViewSet):
    """
    ViewSet COMPLETO para gestión de Controles Prenatales
    
    ENDPOINTS DISPONIBLES:
    - GET    /api/controles/                    → Listar todos
    - GET    /api/controles/{id}/               → Ver detalle
    - POST   /api/controles/                    → Crear nuevo
    - PUT    /api/controles/{id}/               → Actualizar completo
    - PATCH  /api/controles/{id}/               → Actualización parcial
    - DELETE /api/controles/{id}/               → Eliminar
    
    ACCIONES PERSONALIZADAS:
    - GET    /api/controles/por_embarazo/       → Filtrar por embarazo
    - GET    /api/controles/{id}/alertas/       → Obtener alertas
    - GET    /api/controles/{id}/reporte/       → Reporte completo
    - GET    /api/controles/estadisticas/       → Estadísticas generales
    - GET    /api/controles/riesgos/            → Análisis de riesgos
    - GET    /api/controles/tendencias/         → Tendencias evolutivas
    - POST   /api/controles/comparar/           → Comparar controles
    """
    
    queryset = ControlPrenatal.objects.all()
    serializer_class = ControlPrenatalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar controles con parámetros opcionales"""
        queryset = super().get_queryset()
        
        # Filtrar por embarazo
        embarazo_id = self.request.query_params.get('embarazo', None)
        if embarazo_id:
            queryset = queryset.filter(embarazo_id=embarazo_id)
        
        # Filtrar por paciente
        paciente_id = self.request.query_params.get('paciente', None)
        if paciente_id:
            queryset = queryset.filter(paciente_id=paciente_id)
        
        # Filtrar por estado del embarazo
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(embarazo_id__estado=estado)
        
        # Filtrar por rango de fechas
        fecha_desde = self.request.query_params.get('fecha_desde', None)
        fecha_hasta = self.request.query_params.get('fecha_hasta', None)
        if fecha_desde:
            queryset = queryset.filter(fecha_control__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_control__lte=fecha_hasta)
        
        # Filtrar por trimestre
        trimestre = self.request.query_params.get('trimestre', None)
        if trimestre:
            if trimestre == '1':
                queryset = queryset.filter(semanas_gestacion__lt=13)
            elif trimestre == '2':
                queryset = queryset.filter(semanas_gestacion__gte=13, semanas_gestacion__lt=27)
            elif trimestre == '3':
                queryset = queryset.filter(semanas_gestacion__gte=27)
        
        # Filtrar solo con alertas
        con_alertas = self.request.query_params.get('con_alertas', None)
        if con_alertas and con_alertas.lower() == 'true':
            queryset = queryset.filter(
                Q(presion_arterial_sistolica__gte=140) |
                Q(presion_arterial_diastolica__gte=90) |
                Q(frecuencia_cardiaca_fetal__lt=110) |
                Q(frecuencia_cardiaca_fetal__gt=160) |
                Q(edema__in=['severo', 'generalizado']) |
                Q(proteinuria__in=['positiva_1', 'positiva_2', 'positiva_3', 'positiva_4']) |
                Q(movimientos_fetales='ausentes')
            )
        
        return queryset.order_by('-fecha_control', '-numero_control')
    
    def get_serializer_class(self):
        """Usar serializer apropiado según la acción"""
        if self.action == 'list':
            return ControlPrenatalListSerializer
        elif self.action == 'create':
            return ControlPrenatalCreateSerializer
        return ControlPrenatalSerializer
    
    def create(self, request, *args, **kwargs):
        """Crear control prenatal con validaciones extendidas"""
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)

            # ✅ OBTENER DATOS VALIDADOS
            validated_data = serializer.validated_data

            # ✅ ASIGNAR MÉDICO AUTOMÁTICAMENTE SI NO VIENE
            if 'medico_id' not in validated_data or not validated_data.get('medico_id'):
                from usuarios.models import Usuario

                # Intentar obtener un médico activo (preferir ID 2 o 4 que viste en el shell)
                medico = Usuario.objects.filter(rol='medico', activo=True).first()
                if medico:
                    validated_data['medico_id'] = medico
                    print(f"✅ Médico asignado automáticamente: {medico.nombre} (ID: {medico.id})")
                else:
                    validated_data['medico_id'] = None
                    print("⚠️ No se encontró médico, guardando como NULL")

            # Validaciones clínicas adicionales
            self._validar_control_prenatal(validated_data)

            # ✅ CREAR EL CONTROL MANUALMENTE
            control = ControlPrenatal(**validated_data)
            control.save()

            print(f"✅ Control creado con ID: {control.id}")

            # Serializar respuesta
            output_serializer = ControlPrenatalSerializer(control)

            return Response(
                {
                    "mensaje": "Control prenatal registrado exitosamente",
                    "data": output_serializer.data,
                    "alertas": control.get_alertas()
                },
                status=status.HTTP_201_CREATED
            )
        except rest_serializers.ValidationError as e:
            print(f"❌ Error de validación: {e.detail}")
            return Response(
                {"errores": e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as e:
            print(f"❌ Error de validación Django: {str(e)}")
            return Response(
                {"errores": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            import traceback
            print(f"❌ Error inesperado completo:")
            print(traceback.format_exc())
            return Response(
                {"error": f"Error inesperado: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, pk=None, *args, **kwargs):
        """Actualizar control prenatal"""
        partial = kwargs.pop('partial', False)
        try:
            instance = self.get_object()
            
            # ✅ USAR SERIALIZER NORMAL PARA ACTUALIZACIÓN
            serializer = ControlPrenatalSerializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            
            # Validaciones clínicas adicionales
            self._validar_control_prenatal(serializer.validated_data, is_update=True)
            
            self.perform_update(serializer)
            
            # Obtener alertas actualizadas
            instance.refresh_from_db()
            alertas = instance.get_alertas()
            
            return Response({
                "mensaje": "Control actualizado exitosamente",
                "data": serializer.data,
                "alertas": alertas
            })
        except rest_serializers.ValidationError as e:
            return Response(
                {"errores": e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as e:
            return Response(
                {"errores": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Error al actualizar: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def partial_update(self, request, *args, **kwargs):
        """Actualización parcial"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def destroy(self, request, pk=None):
        """Eliminar control prenatal"""
        try:
            control = self.get_object()
            control_info = f"Control #{control.numero_control} del {control.fecha_control}"
            control.delete()
            return Response(
                {
                    "mensaje": f"Control eliminado correctamente: {control_info}"
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Error al eliminar: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _validar_control_prenatal(self, data, is_update=False):
        """Validaciones clínicas del control prenatal"""
        errores = {}
        
        # Validar Presión Arterial
        if data.get('presion_arterial_sistolica') and data.get('presion_arterial_diastolica'):
            sistolica = data['presion_arterial_sistolica']
            diastolica = data['presion_arterial_diastolica']
            
            if sistolica <= diastolica:
                errores['presion_arterial_sistolica'] = ["PA sistólica debe ser mayor que diastólica"]
            
            if sistolica < 70 or sistolica > 220:
                errores['presion_arterial_sistolica'] = ["PA sistólica fuera de rango (70-220 mmHg)"]
            
            if diastolica < 40 or diastolica > 140:
                errores['presion_arterial_diastolica'] = ["PA diastólica fuera de rango (40-140 mmHg)"]
        
        # Validar FCF
        if data.get('frecuencia_cardiaca_fetal'):
            fcf = data['frecuencia_cardiaca_fetal']
            if fcf < 90 or fcf > 180:
                errores['frecuencia_cardiaca_fetal'] = ["FCF fuera de rango esperado (90-180 lpm)"]
        
        # Validar Peso
        if data.get('peso_actual'):
            peso = float(data['peso_actual'])
            if peso < 30 or peso > 200:
                errores['peso_actual'] = ["Peso fuera de rango esperado (30-200 kg)"]
        
        # Validar Talla
        if data.get('talla'):
            talla = float(data['talla'])
            if talla < 130 or talla > 200:
                errores['talla'] = ["Talla fuera de rango esperado (130-200 cm)"]
        
        # Validar IMC si hay peso y talla
        if data.get('peso_actual') and data.get('talla'):
            peso = float(data['peso_actual'])
            talla = float(data['talla']) / 100
            imc = peso / (talla * talla)
            
            if imc < 12 or imc > 60:
                errores['peso_actual'] = ["IMC calculado fuera de rango esperado"]
        
        # Validar semanas de gestación
        if data.get('semanas_gestacion'):
            semanas = data['semanas_gestacion']
            if semanas < 0 or semanas > 42:
                errores['semanas_gestacion'] = ["Semanas de gestación fuera de rango (0-42)"]
        
        # Validar días de gestación
        if data.get('dias_gestacion') is not None:
            dias = data['dias_gestacion']
            if dias < 0 or dias > 6:
                errores['dias_gestacion'] = ["Días de gestación deben estar entre 0 y 6"]
        
        # Validar altura uterina
        if data.get('altura_uterina'):
            au = float(data['altura_uterina'])
            if au < 0 or au > 50:
                errores['altura_uterina'] = ["Altura uterina fuera de rango (0-50 cm)"]
        
        # Validar temperatura
        if data.get('temperatura'):
            temp = float(data['temperatura'])
            if temp < 35 or temp > 42:
                errores['temperatura'] = ["Temperatura fuera de rango (35-42 °C)"]
        
        if errores:
            raise ValidationError(errores)
    
    # ========== ACCIONES PERSONALIZADAS ==========
    
    @action(detail=False, methods=['get'])
    def por_embarazo(self, request):
        """Obtener todos los controles de un embarazo específico"""
        embarazo_id = request.query_params.get('embarazo_id')
        if not embarazo_id:
            return Response(
                {"error": "Debe proporcionar embarazo_id como parámetro"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        controles = self.queryset.filter(embarazo_id=embarazo_id).order_by('numero_control')
        serializer = self.get_serializer(controles, many=True)
        
        # Calcular estadísticas del embarazo
        if controles.exists():
            stats = {
                'total_controles': controles.count(),
                'primer_control': controles.first().fecha_control,
                'ultimo_control': controles.last().fecha_control,
                'controles_con_alertas': sum(1 for c in controles if c.tiene_alertas_criticas()),
            }
        else:
            stats = {}
        
        return Response({
            'embarazo_id': embarazo_id,
            'estadisticas': stats,
            'controles': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def alertas(self, request, pk=None):
        """Generar alertas clínicas para un control específico"""
        control = self.get_object()
        alertas = control.get_alertas()
        
        # Clasificar alertas por tipo
        alertas_criticas = [a for a in alertas if a['tipo'] == 'critico']
        alertas_advertencia = [a for a in alertas if a['tipo'] == 'advertencia']
        
        return Response({
            'control_id': control.id,
            'numero_control': control.numero_control,
            'fecha_control': control.fecha_control,
            'total_alertas': len(alertas),
            'alertas_criticas': len(alertas_criticas),
            'alertas_advertencia': len(alertas_advertencia),
            'alertas_criticas_detalle': alertas_criticas,
            'alertas_advertencia_detalle': alertas_advertencia,
            'riesgo_preeclampsia': control.riesgo_preeclampsia()
        })
    
    @action(detail=True, methods=['get'])
    def reporte(self, request, pk=None):
        """Generar reporte completo del control"""
        control = self.get_object()
        reporte = control.generar_reporte_completo()
        
        return Response({
            'reporte_generado': timezone.now().isoformat(),
            'reporte': reporte
        })
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas generales de controles prenatales"""
        queryset = self.get_queryset()
        
        total_controles = queryset.count()
        
        # Contar alertas por tipo
        controles_con_hipertension = queryset.filter(
            Q(presion_arterial_sistolica__gte=140) | Q(presion_arterial_diastolica__gte=90)
        ).count()
        
        controles_con_fcf_anormal = queryset.filter(
            Q(frecuencia_cardiaca_fetal__lt=110) | Q(frecuencia_cardiaca_fetal__gt=160)
        ).count()
        
        controles_con_edema_severo = queryset.filter(edema__in=['severo', 'generalizado']).count()
        
        controles_con_proteinuria = queryset.filter(
            proteinuria__in=['positiva_1', 'positiva_2', 'positiva_3', 'positiva_4']
        ).count()
        
        controles_con_movimientos_ausentes = queryset.filter(movimientos_fetales='ausentes').count()
        
        # Estadísticas por trimestre
        primer_trimestre = queryset.filter(semanas_gestacion__lt=13).count()
        segundo_trimestre = queryset.filter(semanas_gestacion__gte=13, semanas_gestacion__lt=27).count()
        tercer_trimestre = queryset.filter(semanas_gestacion__gte=27).count()
        
        # Promedios
        promedios = queryset.aggregate(
            peso_promedio=Avg('peso_actual'),
            pa_sistolica_promedio=Avg('presion_arterial_sistolica'),
            pa_diastolica_promedio=Avg('presion_arterial_diastolica'),
            fcf_promedio=Avg('frecuencia_cardiaca_fetal'),
            altura_uterina_promedio=Avg('altura_uterina')
        )
        
        return Response({
            'total_controles': total_controles,
            'distribucion_trimestres': {
                'primer_trimestre': primer_trimestre,
                'segundo_trimestre': segundo_trimestre,
                'tercer_trimestre': tercer_trimestre
            },
            'alertas': {
                'hipertension': controles_con_hipertension,
                'fcf_anormal': controles_con_fcf_anormal,
                'edema_severo': controles_con_edema_severo,
                'proteinuria_positiva': controles_con_proteinuria,
                'movimientos_ausentes': controles_con_movimientos_ausentes
            },
            'controles_con_alertas': (
                controles_con_hipertension + 
                controles_con_fcf_anormal + 
                controles_con_edema_severo + 
                controles_con_proteinuria + 
                controles_con_movimientos_ausentes
            ),
            'promedios': promedios
        })
    
    @action(detail=False, methods=['get'])
    def riesgos(self, request):
        """Análisis de riesgos de todos los controles activos"""
        queryset = self.get_queryset()
        
        # Identificar controles de alto riesgo
        alto_riesgo = []
        for control in queryset[:50]:  # Limitar a 50 para performance
            riesgo_pe = control.riesgo_preeclampsia()
            if riesgo_pe['nivel'] in ['ALTO', 'MODERADO']:
                alto_riesgo.append({
                    'control_id': control.id,
                    'paciente': f"{control.paciente.nombre} {control.paciente.apellido_paterno}",
                    'fecha_control': control.fecha_control,
                    'riesgo_preeclampsia': riesgo_pe,
                    'alertas_criticas': len([a for a in control.get_alertas() if a['tipo'] == 'critico'])
                })
        
        return Response({
            'total_evaluados': min(queryset.count(), 50),
            'controles_alto_riesgo': len(alto_riesgo),
            'detalle_alto_riesgo': alto_riesgo
        })
    
    @action(detail=False, methods=['get'])
    def tendencias(self, request):
        """Análisis de tendencias evolutivas por embarazo"""
        embarazo_id = request.query_params.get('embarazo_id')
        if not embarazo_id:
            return Response(
                {"error": "Debe proporcionar embarazo_id"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        controles = self.queryset.filter(embarazo_id=embarazo_id).order_by('numero_control')
        
        if not controles.exists():
            return Response({
                'mensaje': 'No hay controles para este embarazo'
            })
        
        # Extraer tendencias
        tendencias = {
            'peso': [],
            'presion_arterial': [],
            'fcf': [],
            'altura_uterina': []
        }
        
        for control in controles:
            tendencias['peso'].append({
                'numero_control': control.numero_control,
                'fecha': control.fecha_control,
                'semanas': control.semanas_gestacion,
                'peso': float(control.peso_actual) if control.peso_actual else None,
                'ganancia': control.ganancia_peso
            })
            
            tendencias['presion_arterial'].append({
                'numero_control': control.numero_control,
                'fecha': control.fecha_control,
                'sistolica': control.presion_arterial_sistolica,
                'diastolica': control.presion_arterial_diastolica,
                'pam': control.presion_arterial_media
            })
            
            tendencias['fcf'].append({
                'numero_control': control.numero_control,
                'fecha': control.fecha_control,
                'fcf': control.frecuencia_cardiaca_fetal
            })
            
            tendencias['altura_uterina'].append({
                'numero_control': control.numero_control,
                'fecha': control.fecha_control,
                'semanas': control.semanas_gestacion,
                'altura_uterina': float(control.altura_uterina) if control.altura_uterina else None
            })
        
        return Response({
            'embarazo_id': embarazo_id,
            'total_controles': controles.count(),
            'tendencias': tendencias
        })
    
    @action(detail=False, methods=['post'])
    def comparar(self, request):
        """Comparar dos controles"""
        control1_id = request.data.get('control1_id')
        control2_id = request.data.get('control2_id')
        
        if not control1_id or not control2_id:
            return Response(
                {"error": "Debe proporcionar control1_id y control2_id"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            control1 = ControlPrenatal.objects.get(id=control1_id)
            control2 = ControlPrenatal.objects.get(id=control2_id)
        except ControlPrenatal.DoesNotExist:
            return Response(
                {"error": "Uno o ambos controles no existen"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        comparacion = {
            'control1': {
                'id': control1.id,
                'numero': control1.numero_control,
                'fecha': control1.fecha_control,
                'semanas': control1.edad_gestacional_texto,
                'peso': float(control1.peso_actual) if control1.peso_actual else None,
                'pa': f"{control1.presion_arterial_sistolica}/{control1.presion_arterial_diastolica}",
                'fcf': control1.frecuencia_cardiaca_fetal,
                'altura_uterina': float(control1.altura_uterina) if control1.altura_uterina else None
            },
            'control2': {
                'id': control2.id,
                'numero': control2.numero_control,
                'fecha': control2.fecha_control,
                'semanas': control2.edad_gestacional_texto,
                'peso': float(control2.peso_actual) if control2.peso_actual else None,
                'pa': f"{control2.presion_arterial_sistolica}/{control2.presion_arterial_diastolica}",
                'fcf': control2.frecuencia_cardiaca_fetal,
                'altura_uterina': float(control2.altura_uterina) if control2.altura_uterina else None
            },
            'diferencias': {}
        }
        
        # Calcular diferencias
        if control1.peso_actual and control2.peso_actual:
            comparacion['diferencias']['peso'] = float(control2.peso_actual - control1.peso_actual)
        
        if control1.presion_arterial_sistolica and control2.presion_arterial_sistolica:
            comparacion['diferencias']['pa_sistolica'] = control2.presion_arterial_sistolica - control1.presion_arterial_sistolica
            comparacion['diferencias']['pa_diastolica'] = control2.presion_arterial_diastolica - control1.presion_arterial_diastolica
        
        if control1.altura_uterina and control2.altura_uterina:
            comparacion['diferencias']['altura_uterina'] = float(control2.altura_uterina - control1.altura_uterina)
        
        return Response(comparacion)