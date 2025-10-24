from rest_framework import viewsets, status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from .models import ControlPrenatal
from .serializers import ControlPrenatalSerializer
from django.db.models import Q

class ControlPrenatalViewSet(viewsets.ModelViewSet):
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
            queryset = queryset.filter(embarazo__estado=estado)
        
        return queryset.order_by('-fecha_control')
    
    def create(self, request, *args, **kwargs):
        """Crear control prenatal con validaciones"""
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            
            # Validaciones clínicas adicionales
            self._validar_control_prenatal(serializer.validated_data)
            
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            
            return Response(
                {
                    "mensaje": "Control prenatal registrado exitosamente",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except serializers.ValidationError as e:
            return Response(
                {"errores": e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as e:
            return Response(
                {"errores": e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Error inesperado: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, pk=None, *args, **kwargs):
        """Actualizar control prenatal"""
        partial = kwargs.pop('partial', False)
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            
            # Validaciones clínicas adicionales
            self._validar_control_prenatal(serializer.validated_data, is_update=True)
            
            self.perform_update(serializer)
            
            return Response({
                "mensaje": "Control actualizado exitosamente",
                "data": serializer.data
            })
        except serializers.ValidationError as e:
            return Response(
                {"errores": e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as e:
            return Response(
                {"errores": e.detail},
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
        if data.get('dias_gestacion'):
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
        
        return Response({
            "total": controles.count(),
            "embarazo_id": embarazo_id,
            "controles": serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def alertas(self, request, pk=None):
        """Generar alertas clínicas para un control específico"""
        control = self.get_object()
        alertas = []
        
        # Alertas de Presión Arterial
        if control.presion_arterial_sistolica and control.presion_arterial_diastolica:
            sistolica = control.presion_arterial_sistolica
            diastolica = control.presion_arterial_diastolica
            
            if sistolica >= 140 or diastolica >= 90:
                alertas.append({
                    'tipo': 'critico',
                    'categoria': 'presion_arterial',
                    'mensaje': 'HIPERTENSIÓN DETECTADA',
                    'valor': f'{sistolica}/{diastolica} mmHg',
                    'recomendacion': 'Evaluar preeclampsia. Considerar manejo hospitalario. Solicitar proteinuria 24h.'
                })
            elif sistolica >= 120 or diastolica >= 80:
                alertas.append({
                    'tipo': 'advertencia',
                    'categoria': 'presion_arterial',
                    'mensaje': 'Pre-hipertensión',
                    'valor': f'{sistolica}/{diastolica} mmHg',
                    'recomendacion': 'Monitoreo estrecho de PA. Control en 1 semana.'
                })
        
        # Alertas de FCF
        if control.frecuencia_cardiaca_fetal:
            fcf = control.frecuencia_cardiaca_fetal
            if fcf < 110 or fcf > 160:
                alertas.append({
                    'tipo': 'critico',
                    'categoria': 'fcf',
                    'mensaje': 'FCF ANORMAL',
                    'valor': f'{fcf} lpm',
                    'recomendacion': 'Realizar NST inmediatamente. Evaluar sufrimiento fetal. Considerar hospitalización.'
                })
        
        # Alertas de Edema
        if control.edema == 'severo':
            alertas.append({
                'tipo': 'critico',
                'categoria': 'edema',
                'mensaje': 'EDEMA SEVERO',
                'valor': 'Severo',
                'recomendacion': 'Alto riesgo de preeclampsia. Evaluar PA, proteinuria y función renal.'
            })
        elif control.edema == 'moderado':
            alertas.append({
                'tipo': 'advertencia',
                'categoria': 'edema',
                'mensaje': 'Edema moderado',
                'valor': 'Moderado',
                'recomendacion': 'Vigilar evolución. Control en 3-5 días.'
            })
        
        # Alertas de Proteinuria
        if control.proteinuria in ['positiva_1', 'positiva_2', 'positiva_3']:
            nivel = control.proteinuria.replace('positiva_1', '+').replace('positiva_2', '++').replace('positiva_3', '+++')
            alertas.append({
                'tipo': 'critico',
                'categoria': 'proteinuria',
                'mensaje': f'PROTEINURIA POSITIVA ({nivel})',
                'valor': nivel,
                'recomendacion': 'Alto riesgo de preeclampsia. Solicitar proteinuria 24h, función renal. Considerar hospitalización.'
            })
        
        # Alertas de Movimientos Fetales
        if control.movimientos_fetales == 'ausentes':
            alertas.append({
                'tipo': 'critico',
                'categoria': 'movimientos_fetales',
                'mensaje': 'MOVIMIENTOS FETALES AUSENTES',
                'valor': 'Ausentes',
                'recomendacion': 'EMERGENCIA: Realizar NST y ecografía inmediatamente. Descartar sufrimiento fetal.'
            })
        elif control.movimientos_fetales == 'disminuidos':
            alertas.append({
                'tipo': 'advertencia',
                'categoria': 'movimientos_fetales',
                'mensaje': 'Movimientos fetales disminuidos',
                'valor': 'Disminuidos',
                'recomendacion': 'Realizar conteo de movimientos y NST. Reevaluar en 24h.'
            })
        
        # Calcular y alertas de IMC
        if control.peso_actual and control.talla:
            talla_m = control.talla / 100
            imc = control.peso_actual / (talla_m * talla_m)
            
            if imc < 18.5:
                alertas.append({
                    'tipo': 'advertencia',
                    'categoria': 'imc',
                    'mensaje': 'BAJO PESO',
                    'valor': f'IMC: {imc:.2f}',
                    'recomendacion': 'Evaluación nutricional urgente. Suplementación vitamínica. Mayor riesgo de RCIU.'
                })
            elif imc >= 30:
                alertas.append({
                    'tipo': 'advertencia',
                    'categoria': 'imc',
                    'mensaje': 'OBESIDAD',
                    'valor': f'IMC: {imc:.2f}',
                    'recomendacion': 'Mayor riesgo de diabetes gestacional, preeclampsia y complicaciones. Dieta y ejercicio supervisado.'
                })
        
        # Alertas de Temperatura
        if control.temperatura:
            temp = float(control.temperatura)
            if temp >= 38:
                alertas.append({
                    'tipo': 'critico',
                    'categoria': 'temperatura',
                    'mensaje': 'FIEBRE',
                    'valor': f'{temp} °C',
                    'recomendacion': 'Investigar foco infeccioso. Considerar infección urinaria, corioamnionitis.'
                })
        
        return Response({
            'control_id': control.id,
            'numero_control': control.numero_control,
            'fecha_control': control.fecha_control,
            'total_alertas': len(alertas),
            'alertas_criticas': len([a for a in alertas if a['tipo'] == 'critico']),
            'alertas_advertencia': len([a for a in alertas if a['tipo'] == 'advertencia']),
            'alertas': alertas
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
        
        controles_con_edema_severo = queryset.filter(edema='severo').count()
        
        controles_con_proteinuria = queryset.filter(
            proteinuria__in=['positiva_1', 'positiva_2', 'positiva_3']
        ).count()
        
        return Response({
            'total_controles': total_controles,
            'alertas': {
                'hipertension': controles_con_hipertension,
                'fcf_anormal': controles_con_fcf_anormal,
                'edema_severo': controles_con_edema_severo,
                'proteinuria_positiva': controles_con_proteinuria
            }
        })