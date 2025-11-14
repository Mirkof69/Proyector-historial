# =============================================================================
# VIEWS DE CONTROLES PRENATALES
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: controles
# Descripción: ViewSets completos para controles prenatales con endpoints
#              avanzados: alertas, estadísticas, evolución, exportación.
# Versión: 2.0.0
# Última actualización: 2025-11-14
# =============================================================================

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from django.db.models import Q, Avg, Max, Min, Count, F
from django.utils import timezone
from django.http import HttpResponse
from datetime import datetime, timedelta
from decimal import Decimal
import csv
import json

from .models import ControlPrenatal
from .serializers import (
    ControlPrenatalSerializer,
    ControlPrenatalCreateSerializer,
    ControlPrenatalUpdateSerializer,
    ControlPrenatalListSerializer,
    ControlPrenatalEstadisticasSerializer,
    ControlPrenatalExportSerializer,
)
from embarazos.models import Embarazo
from pacientes.models import Paciente


# =============================================================================
# VIEWSET PRINCIPAL DE CONTROLES PRENATALES
# =============================================================================

class ControlPrenatalViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para controles prenatales.

    Endpoints:
    - GET /controles/ - Lista de controles
    - POST /controles/ - Crear control
    - GET /controles/{id}/ - Detalle de control
    - PUT/PATCH /controles/{id}/ - Actualizar control
    - DELETE /controles/{id}/ - Eliminar control

    Acciones personalizadas:
    - GET /controles/por_embarazo/ - Controles de un embarazo
    - GET /controles/{id}/alertas/ - Alertas del control
    - GET /controles/con_alertas/ - Controles con alertas
    - GET /controles/estadisticas/ - Estadísticas generales
    - GET /controles/evolucion/ - Evolución de parámetros
    - GET /controles/comparar/ - Comparar controles
    - GET /controles/exportar/ - Exportar a CSV/Excel
    - GET /controles/reporte_paciente/ - Reporte individual
    """

    queryset = ControlPrenatal.objects.select_related(
        'embarazo',
        'embarazo__paciente',
        'medico',
        'enfermero'
    ).all()

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Seleccionar serializer según la acción"""
        if self.action == 'create':
            return ControlPrenatalCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ControlPrenatalUpdateSerializer
        elif self.action == 'list':
            return ControlPrenatalListSerializer
        elif self.action in ['exportar', 'exportar_csv']:
            return ControlPrenatalExportSerializer
        return ControlPrenatalSerializer

    def get_queryset(self):
        """
        Filtrar controles con parámetros opcionales.

        Parámetros:
        - embarazo: ID del embarazo
        - paciente: ID del paciente
        - estado: Estado del embarazo
        - fecha_desde: Fecha inicio
        - fecha_hasta: Fecha fin
        - con_alertas: true/false
        - medico: ID del médico
        """
        queryset = super().get_queryset()

        # Filtrar por embarazo
        embarazo_id = self.request.query_params.get('embarazo')
        if embarazo_id:
            queryset = queryset.filter(embarazo_id=embarazo_id)

        # Filtrar por paciente
        paciente_id = self.request.query_params.get('paciente')
        if paciente_id:
            queryset = queryset.filter(embarazo__paciente_id=paciente_id)

        # Filtrar por estado del embarazo
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(embarazo__estado=estado)

        # Filtrar por rango de fechas
        fecha_desde = self.request.query_params.get('fecha_desde')
        if fecha_desde:
            queryset = queryset.filter(fecha_control__gte=fecha_desde)

        fecha_hasta = self.request.query_params.get('fecha_hasta')
        if fecha_hasta:
            queryset = queryset.filter(fecha_control__lte=fecha_hasta)

        # Filtrar por médico
        medico_id = self.request.query_params.get('medico')
        if medico_id:
            queryset = queryset.filter(medico_id=medico_id)

        # Filtrar controles con alertas
        con_alertas = self.request.query_params.get('con_alertas')
        if con_alertas and con_alertas.lower() == 'true':
            queryset = queryset.filter(
                Q(presion_arterial_sistolica__gte=140) |
                Q(presion_arterial_diastolica__gte=90) |
                Q(frecuencia_cardiaca_fetal__lt=110) |
                Q(frecuencia_cardiaca_fetal__gt=160) |
                Q(proteinuria__in=['positiva_1', 'positiva_2', 'positiva_3']) |
                Q(edema='severo') |
                Q(movimientos_fetales='ausentes')
            ).distinct()

        return queryset.order_by('-fecha_control')

    # =========================================================================
    # CRUD OPERATIONS
    # =========================================================================

    def list(self, request, *args, **kwargs):
        """Lista de controles prenatales"""
        queryset = self.filter_queryset(self.get_queryset())

        # Paginación
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'total': queryset.count(),
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        """Detalle de un control prenatal"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        """Crear nuevo control prenatal"""
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)

            # Asignar usuario que crea
            control = serializer.save(
                creado_por=request.user if hasattr(request, 'user') else None
            )

            # Obtener representación completa
            response_serializer = ControlPrenatalSerializer(control)

            return Response({
                'success': True,
                'message': 'Control prenatal creado exitosamente',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({
                'success': False,
                'errors': e.detail
            }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """Actualizar control prenatal"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        try:
            serializer.is_valid(raise_exception=True)

            # Asignar usuario que modifica
            control = serializer.save(
                modificado_por=request.user if hasattr(request, 'user') else None,
                fecha_modificacion=timezone.now()
            )

            # Obtener representación completa
            response_serializer = ControlPrenatalSerializer(control)

            return Response({
                'success': True,
                'message': 'Control actualizado exitosamente',
                'data': response_serializer.data
            })

        except ValidationError as e:
            return Response({
                'success': False,
                'errors': e.detail
            }, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        """Actualización parcial"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Eliminar control prenatal"""
        instance = self.get_object()
        control_info = {
            'numero_control': instance.numero_control,
            'fecha_control': str(instance.fecha_control)
        }
        instance.delete()

        return Response({
            'success': True,
            'message': f"Control #{control_info['numero_control']} eliminado correctamente",
            'data': control_info
        }, status=status.HTTP_200_OK)

    # =========================================================================
    # ACCIONES PERSONALIZADAS - CONSULTAS
    # =========================================================================

    @action(detail=False, methods=['get'])
    def por_embarazo(self, request):
        """
        Obtener todos los controles de un embarazo específico.

        Parámetros:
        - embarazo_id: ID del embarazo (requerido)
        """
        embarazo_id = request.query_params.get('embarazo_id')
        if not embarazo_id:
            return Response({
                'success': False,
                'error': 'Debe proporcionar embarazo_id como parámetro'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            embarazo = Embarazo.objects.get(id=embarazo_id)
        except Embarazo.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Embarazo con ID {embarazo_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

        controles = self.queryset.filter(embarazo_id=embarazo_id).order_by('numero_control')
        serializer = ControlPrenatalSerializer(controles, many=True)

        return Response({
            'success': True,
            'embarazo_id': embarazo_id,
            'total_controles': controles.count(),
            'data': serializer.data
        })

    @action(detail=True, methods=['get'])
    def alertas(self, request, pk=None):
        """
        Obtener todas las alertas médicas de un control específico.

        Retorna alertas categorizadas por severidad.
        """
        control = self.get_object()
        serializer = ControlPrenatalSerializer(control)
        alertas = serializer.data.get('alertas', [])

        # Categorizar alertas
        alertas_criticas = [a for a in alertas if a.get('severidad') == 'crítica']
        alertas_altas = [a for a in alertas if a.get('severidad') == 'alta']
        alertas_moderadas = [a for a in alertas if a.get('severidad') == 'moderada']

        return Response({
            'success': True,
            'control_id': control.id,
            'numero_control': control.numero_control,
            'fecha_control': str(control.fecha_control),
            'resumen': {
                'total_alertas': len(alertas),
                'criticas': len(alertas_criticas),
                'altas': len(alertas_altas),
                'moderadas': len(alertas_moderadas),
                'requiere_atencion_inmediata': serializer.data.get('requiere_atencion_inmediata', False),
                'nivel_riesgo': serializer.data.get('nivel_riesgo', 'bajo'),
            },
            'alertas': {
                'criticas': alertas_criticas,
                'altas': alertas_altas,
                'moderadas': alertas_moderadas,
            }
        })

    @action(detail=False, methods=['get'])
    def con_alertas(self, request):
        """
        Obtener todos los controles que tienen alertas médicas.

        Parámetros opcionales:
        - severidad: critica, alta, moderada
        - tipo: hipertension, fcf, proteinuria, etc.
        """
        queryset = self.get_queryset().filter(
            Q(presion_arterial_sistolica__gte=140) |
            Q(presion_arterial_diastolica__gte=90) |
            Q(frecuencia_cardiaca_fetal__lt=110) |
            Q(frecuencia_cardiaca_fetal__gt=160) |
            Q(proteinuria__in=['positiva_1', 'positiva_2', 'positiva_3']) |
            Q(edema='severo') |
            Q(movimientos_fetales='ausentes')
        ).distinct()

        serializer = ControlPrenatalListSerializer(queryset, many=True)

        return Response({
            'success': True,
            'total_con_alertas': queryset.count(),
            'data': serializer.data
        })

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Estadísticas generales de controles prenatales.

        Incluye:
        - Totales generales
        - Promedios de parámetros vitales
        - Alertas por tipo
        - Distribución por trimestre
        """
        queryset = self.get_queryset()
        total_controles = queryset.count()

        # Promedios de parámetros
        promedios = queryset.aggregate(
            promedio_pas=Avg('presion_arterial_sistolica'),
            promedio_pad=Avg('presion_arterial_diastolica'),
            promedio_fcf=Avg('frecuencia_cardiaca_fetal'),
            promedio_peso=Avg('peso_actual'),
            promedio_au=Avg('altura_uterina'),
        )

        # Contar alertas por tipo
        alertas = {
            'hipertension': queryset.filter(
                Q(presion_arterial_sistolica__gte=140) |
                Q(presion_arterial_diastolica__gte=90)
            ).count(),
            'hipertension_severa': queryset.filter(
                Q(presion_arterial_sistolica__gte=160) |
                Q(presion_arterial_diastolica__gte=110)
            ).count(),
            'fcf_anormal': queryset.filter(
                Q(frecuencia_cardiaca_fetal__lt=110) |
                Q(frecuencia_cardiaca_fetal__gt=160)
            ).count(),
            'bradicardia': queryset.filter(frecuencia_cardiaca_fetal__lt=110).count(),
            'taquicardia': queryset.filter(frecuencia_cardiaca_fetal__gt=160).count(),
            'proteinuria': queryset.filter(
                proteinuria__in=['positiva_1', 'positiva_2', 'positiva_3']
            ).count(),
            'edema_severo': queryset.filter(edema='severo').count(),
            'movimientos_ausentes': queryset.filter(movimientos_fetales='ausentes').count(),
        }

        # Distribución por trimestre
        trimestres = {
            'primer_trimestre': queryset.filter(semanas_gestacion__lte=13).count(),
            'segundo_trimestre': queryset.filter(
                semanas_gestacion__gt=13,
                semanas_gestacion__lte=27
            ).count(),
            'tercer_trimestre': queryset.filter(semanas_gestacion__gt=27).count(),
        }

        return Response({
            'success': True,
            'total_controles': total_controles,
            'promedios': {
                'presion_arterial_sistolica': round(promedios['promedio_pas'], 1) if promedios['promedio_pas'] else None,
                'presion_arterial_diastolica': round(promedios['promedio_pad'], 1) if promedios['promedio_pad'] else None,
                'frecuencia_cardiaca_fetal': round(promedios['promedio_fcf'], 1) if promedios['promedio_fcf'] else None,
                'peso': round(promedios['promedio_peso'], 1) if promedios['promedio_peso'] else None,
                'altura_uterina': round(promedios['promedio_au'], 1) if promedios['promedio_au'] else None,
            },
            'alertas': alertas,
            'distribucion_trimestres': trimestres,
            'porcentaje_con_alertas': round(
                (sum(alertas.values()) / total_controles * 100), 1
            ) if total_controles > 0 else 0
        })

    @action(detail=False, methods=['get'])
    def evolucion(self, request):
        """
        Evolución de parámetros a lo largo de los controles de un embarazo.

        Parámetros:
        - embarazo_id: ID del embarazo (requerido)
        - parametro: peso, pa, fcf, au (opcional, por defecto todos)

        Retorna datos listos para graficar.
        """
        embarazo_id = request.query_params.get('embarazo_id')
        if not embarazo_id:
            return Response({
                'success': False,
                'error': 'Debe proporcionar embarazo_id'
            }, status=status.HTTP_400_BAD_REQUEST)

        controles = self.queryset.filter(embarazo_id=embarazo_id).order_by('numero_control')

        if not controles.exists():
            return Response({
                'success': False,
                'error': 'No se encontraron controles para este embarazo'
            }, status=status.HTTP_404_NOT_FOUND)

        # Preparar datos para gráficas
        evolucion_peso = []
        evolucion_pa = []
        evolucion_fcf = []
        evolucion_au = []
        evolucion_imc = []

        for control in controles:
            punto_base = {
                'numero_control': control.numero_control,
                'fecha': str(control.fecha_control),
                'semanas': f"{control.semanas_gestacion}+{control.dias_gestacion or 0}" if control.semanas_gestacion else None
            }

            # Peso
            if control.peso_actual:
                evolucion_peso.append({
                    **punto_base,
                    'peso': float(control.peso_actual),
                    'imc': float(control.calcular_imc()) if control.calcular_imc() else None
                })

            # Presión Arterial
            if control.presion_arterial_sistolica and control.presion_arterial_diastolica:
                pam = control.calcular_pam()
                evolucion_pa.append({
                    **punto_base,
                    'sistolica': control.presion_arterial_sistolica,
                    'diastolica': control.presion_arterial_diastolica,
                    'pam': round(pam, 1) if pam else None,
                    'alerta': control.presion_arterial_sistolica >= 140 or control.presion_arterial_diastolica >= 90
                })

            # FCF
            if control.frecuencia_cardiaca_fetal:
                evolucion_fcf.append({
                    **punto_base,
                    'fcf': control.frecuencia_cardiaca_fetal,
                    'alerta': control.frecuencia_cardiaca_fetal < 110 or control.frecuencia_cardiaca_fetal > 160
                })

            # Altura Uterina
            if control.altura_uterina:
                evolucion_au.append({
                    **punto_base,
                    'altura_uterina': float(control.altura_uterina),
                    'concordancia': abs(control.altura_uterina - control.semanas_gestacion) <= 2 if control.semanas_gestacion else None
                })

        return Response({
            'success': True,
            'embarazo_id': int(embarazo_id),
            'total_controles': controles.count(),
            'evolucion': {
                'peso': evolucion_peso,
                'presion_arterial': evolucion_pa,
                'frecuencia_cardiaca_fetal': evolucion_fcf,
                'altura_uterina': evolucion_au,
            }
        })

    @action(detail=False, methods=['get'])
    def comparar(self, request):
        """
        Comparar dos controles prenatales.

        Parámetros:
        - control1_id: ID del primer control
        - control2_id: ID del segundo control
        """
        control1_id = request.query_params.get('control1_id')
        control2_id = request.query_params.get('control2_id')

        if not control1_id or not control2_id:
            return Response({
                'success': False,
                'error': 'Debe proporcionar control1_id y control2_id'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            control1 = self.queryset.get(id=control1_id)
            control2 = self.queryset.get(id=control2_id)
        except ControlPrenatal.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Uno o ambos controles no encontrados'
            }, status=status.HTTP_404_NOT_FOUND)

        # Serializar ambos controles
        serializer1 = ControlPrenatalSerializer(control1)
        serializer2 = ControlPrenatalSerializer(control2)

        # Calcular diferencias
        diferencias = {}

        if control1.peso_actual and control2.peso_actual:
            diferencias['peso'] = {
                'diferencia': round(float(control2.peso_actual - control1.peso_actual), 2),
                'porcentaje': round((control2.peso_actual - control1.peso_actual) / control1.peso_actual * 100, 1)
            }

        if control1.presion_arterial_sistolica and control2.presion_arterial_sistolica:
            diferencias['pa_sistolica'] = control2.presion_arterial_sistolica - control1.presion_arterial_sistolica
            diferencias['pa_diastolica'] = control2.presion_arterial_diastolica - control1.presion_arterial_diastolica

        if control1.altura_uterina and control2.altura_uterina:
            diferencias['altura_uterina'] = round(float(control2.altura_uterina - control1.altura_uterina), 1)

        return Response({
            'success': True,
            'control1': serializer1.data,
            'control2': serializer2.data,
            'diferencias': diferencias,
            'tiempo_entre_controles_dias': (control2.fecha_control - control1.fecha_control).days if control2.fecha_control > control1.fecha_control else 0
        })

    @action(detail=False, methods=['get'])
    def reporte_paciente(self, request):
        """
        Reporte completo de controles de un paciente específico.

        Parámetros:
        - paciente_id: ID del paciente
        """
        paciente_id = request.query_params.get('paciente_id')
        if not paciente_id:
            return Response({
                'success': False,
                'error': 'Debe proporcionar paciente_id'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            paciente = Paciente.objects.get(id=paciente_id)
        except Paciente.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Paciente no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

        # Obtener todos los embarazos del paciente
        embarazos = Embarazo.objects.filter(paciente=paciente).order_by('-fecha_creacion')

        reporte_embarazos = []
        for embarazo in embarazos:
            controles = self.queryset.filter(embarazo=embarazo).order_by('numero_control')
            controles_data = ControlPrenatalListSerializer(controles, many=True).data

            reporte_embarazos.append({
                'embarazo_id': embarazo.id,
                'numero_gesta': embarazo.numero_gesta if hasattr(embarazo, 'numero_gesta') else None,
                'estado': embarazo.estado if hasattr(embarazo, 'estado') else None,
                'total_controles': controles.count(),
                'controles': controles_data,
            })

        return Response({
            'success': True,
            'paciente': {
                'id': paciente.id,
                'nombre': f"{paciente.nombres} {paciente.apellidos}",
                'cedula': paciente.cedula_identidad,
            },
            'total_embarazos': embarazos.count(),
            'embarazos': reporte_embarazos
        })

    # =========================================================================
    # EXPORTACIÓN DE DATOS
    # =========================================================================

    @action(detail=False, methods=['get'])
    def exportar_csv(self, request):
        """
        Exportar controles a archivo CSV.

        Parámetros opcionales:
        - embarazo_id: Filtrar por embarazo
        - paciente_id: Filtrar por paciente
        - fecha_desde, fecha_hasta: Rango de fechas
        """
        queryset = self.get_queryset()

        # Aplicar filtros adicionales si se proporcionan
        embarazo_id = request.query_params.get('embarazo_id')
        if embarazo_id:
            queryset = queryset.filter(embarazo_id=embarazo_id)

        # Crear respuesta CSV
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="controles_prenatales_{timezone.now().strftime("%Y%m%d")}.csv"'

        # BOM para Excel
        response.write('\ufeff')

        writer = csv.writer(response)
        writer.writerow([
            'ID',
            'Número Control',
            'Fecha',
            'Paciente',
            'Cédula',
            'Edad Gestacional',
            'Peso (kg)',
            'IMC',
            'PA Sistólica',
            'PA Diastólica',
            'PAM',
            'FC Materna',
            'Temperatura',
            'Altura Uterina',
            'FCF',
            'Presentación',
            'Movimientos',
            'Edema',
            'Proteinuria',
        ])

        for control in queryset:
            paciente = control.embarazo.paciente if control.embarazo else None
            writer.writerow([
                control.id,
                control.numero_control,
                control.fecha_control.strftime('%d/%m/%Y') if control.fecha_control else '',
                f"{paciente.nombres} {paciente.apellidos}" if paciente else '',
                paciente.cedula_identidad if paciente else '',
                f"{control.semanas_gestacion}+{control.dias_gestacion or 0}" if control.semanas_gestacion else '',
                control.peso_actual or '',
                round(control.calcular_imc(), 2) if control.calcular_imc() else '',
                control.presion_arterial_sistolica or '',
                control.presion_arterial_diastolica or '',
                round(control.calcular_pam(), 1) if control.calcular_pam() else '',
                control.frecuencia_cardiaca or '',
                control.temperatura or '',
                control.altura_uterina or '',
                control.frecuencia_cardiaca_fetal or '',
                control.presentacion_fetal or '',
                control.movimientos_fetales or '',
                control.edema or '',
                control.proteinuria or '',
            ])

        return response

    @action(detail=False, methods=['post'])
    def batch_create(self, request):
        """
        Crear múltiples controles en lote.

        Body: Array de controles
        """
        if not isinstance(request.data, list):
            return Response({
                'success': False,
                'error': 'Se espera un array de controles'
            }, status=status.HTTP_400_BAD_REQUEST)

        creados = []
        errores = []

        for idx, control_data in enumerate(request.data):
            serializer = ControlPrenatalCreateSerializer(data=control_data)

            if serializer.is_valid():
                control = serializer.save(
                    creado_por=request.user if hasattr(request, 'user') else None
                )
                creados.append({
                    'index': idx,
                    'id': control.id,
                    'numero_control': control.numero_control
                })
            else:
                errores.append({
                    'index': idx,
                    'errors': serializer.errors
                })

        return Response({
            'success': len(errores) == 0,
            'total_procesados': len(request.data),
            'creados': len(creados),
            'errores': len(errores),
            'detalles_creados': creados,
            'detalles_errores': errores
        }, status=status.HTTP_201_CREATED if len(errores) == 0 else status.HTTP_207_MULTI_STATUS)

    # =========================================================================
    # ANÁLISIS AVANZADO
    # =========================================================================

    @action(detail=False, methods=['get'])
    def tendencias(self, request):
        """
        Análisis de tendencias para un embarazo.

        Detecta:
        - Tendencia de PA (subiendo, estable, bajando)
        - Tendencia de peso (adecuada, excesiva, insuficiente)
        - Evolución de FCF

        Parámetros:
        - embarazo_id: ID del embarazo
        """
        embarazo_id = request.query_params.get('embarazo_id')
        if not embarazo_id:
            return Response({
                'success': False,
                'error': 'Debe proporcionar embarazo_id'
            }, status=status.HTTP_400_BAD_REQUEST)

        controles = self.queryset.filter(embarazo_id=embarazo_id).order_by('numero_control')

        if controles.count() < 2:
            return Response({
                'success': False,
                'error': 'Se requieren al menos 2 controles para análisis de tendencias'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Analizar tendencia de PA
        pas_values = [c.presion_arterial_sistolica for c in controles if c.presion_arterial_sistolica]
        if len(pas_values) >= 2:
            diferencia_pa = pas_values[-1] - pas_values[0]
            if diferencia_pa > 10:
                tendencia_pa = 'ASCENDENTE - PREOCUPANTE'
                alerta_pa = True
            elif diferencia_pa > 5:
                tendencia_pa = 'Levemente ascendente'
                alerta_pa = False
            elif diferencia_pa < -10:
                tendencia_pa = 'Descendente - favorable'
                alerta_pa = False
            else:
                tendencia_pa = 'Estable'
                alerta_pa = False
        else:
            tendencia_pa = 'Datos insuficientes'
            alerta_pa = False

        # Analizar tendencia de peso
        pesos = [c.peso_actual for c in controles if c.peso_actual]
        if len(pesos) >= 2:
            ganancia_total = float(pesos[-1] - pesos[0])
            semanas_transcurridas = controles.last().semanas_gestacion - controles.first().semanas_gestacion if controles.first().semanas_gestacion and controles.last().semanas_gestacion else 0

            if semanas_transcurridas > 0:
                ganancia_semanal = ganancia_total / semanas_transcurridas

                if ganancia_semanal > 0.7:
                    tendencia_peso = 'Ganancia excesiva'
                    alerta_peso = True
                elif ganancia_semanal < 0.2:
                    tendencia_peso = 'Ganancia insuficiente'
                    alerta_peso = True
                else:
                    tendencia_peso = 'Ganancia adecuada'
                    alerta_peso = False
            else:
                tendencia_peso = 'Período muy corto para evaluar'
                alerta_peso = False
        else:
            tendencia_peso = 'Datos insuficientes'
            alerta_peso = False

        return Response({
            'success': True,
            'embarazo_id': int(embarazo_id),
            'controles_analizados': controles.count(),
            'tendencias': {
                'presion_arterial': {
                    'tendencia': tendencia_pa,
                    'alerta': alerta_pa,
                    'valores': pas_values,
                },
                'peso': {
                    'tendencia': tendencia_peso,
                    'alerta': alerta_peso,
                    'ganancia_total_kg': round(ganancia_total, 2) if len(pesos) >= 2 else None,
                }
            }
        })

    @action(detail=False, methods=['get'])
    def proximos_controles(self, request):
        """
        Lista de próximos controles programados.

        Muestra controles con proxima_cita en los próximos días.
        """
        hoy = timezone.now().date()
        dias_adelante = int(request.query_params.get('dias', 30))
        fecha_limite = hoy + timedelta(days=dias_adelante)

        controles_con_cita = self.queryset.filter(
            proxima_cita__gte=hoy,
            proxima_cita__lte=fecha_limite
        ).select_related('embarazo__paciente').order_by('proxima_cita')

        resultado = []
        for control in controles_con_cita:
            dias_restantes = (control.proxima_cita - hoy).days
            resultado.append({
                'control_id': control.id,
                'paciente_id': control.embarazo.paciente.id if control.embarazo and control.embarazo.paciente else None,
                'paciente_nombre': f"{control.embarazo.paciente.nombres} {control.embarazo.paciente.apellidos}" if control.embarazo and control.embarazo.paciente else None,
                'embarazo_id': control.embarazo.id if control.embarazo else None,
                'ultimo_control': str(control.fecha_control),
                'proxima_cita': str(control.proxima_cita),
                'dias_restantes': dias_restantes,
                'urgente': dias_restantes <= 3,
            })

        return Response({
            'success': True,
            'total': len(resultado),
            'fecha_actual': str(hoy),
            'rango_dias': dias_adelante,
            'proximas_citas': resultado
        })

    @action(detail=True, methods=['get'])
    def historial_completo(self, request, pk=None):
        """
        Historial completo de un control con contexto del embarazo.
        """
        control = self.get_object()
        serializer = ControlPrenatalSerializer(control)

        # Obtener todos los controles del embarazo para contexto
        controles_embarazo = self.queryset.filter(
            embarazo=control.embarazo
        ).order_by('numero_control')

        return Response({
            'success': True,
            'control_actual': serializer.data,
            'contexto_embarazo': {
                'total_controles': controles_embarazo.count(),
                'numero_control_actual': control.numero_control,
                'controles_previos': controles_embarazo.filter(
                    numero_control__lt=control.numero_control
                ).count(),
                'controles_posteriores': controles_embarazo.filter(
                    numero_control__gt=control.numero_control
                ).count(),
            }
        })
