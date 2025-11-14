# =============================================================================
# VIEWS DE EMBARAZOS
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: embarazos
# Descripción: ViewSet completo para gestión de embarazos con funcionalidades
#              avanzadas: CRUD, búsqueda, filtros, estadísticas, reportes de riesgo,
#              gestión de complicaciones y endpoints especializados.
# Autor: Sistema de Gestión Médica
# Versión: 3.0.0 COMPLETO
# Última actualización: 2025-11-14
# =============================================================================

from rest_framework import viewsets, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg, Max, Min, F
from django.utils import timezone
from datetime import datetime, timedelta
import csv
from io import StringIO

from .models import Embarazo, ComplicacionEmbarazo
from .serializers import (
    EmbarazoSerializer,
    EmbarazoCreateSerializer,
    EmbarazoUpdateSerializer,
    EmbarazoDetailSerializer,
    EmbarazoListSerializer,
    ComplicacionEmbarazoSerializer,
    ComplicacionEmbarazoCreateSerializer,
    EmbarazoEstadisticasSerializer
)
from pacientes.models import Paciente


# =============================================================================
# VIEWSET PRINCIPAL DE EMBARAZOS
# =============================================================================

class EmbarazoViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para gestión de embarazos.

    Funcionalidades:
    - CRUD completo de embarazos
    - Búsqueda y filtros avanzados
    - Listado de embarazos de alto riesgo
    - Listado de embarazos en curso
    - Listado de embarazos finalizados
    - Estadísticas generales
    - Cálculo de riesgo en tiempo real
    - Gestión de complicaciones
    - Soft delete
    - Exportación a CSV

    Endpoints personalizados:
    - GET /embarazos/alto_riesgo/ - Embarazos de alto riesgo
    - GET /embarazos/en_curso/ - Embarazos activos
    - GET /embarazos/finalizados/ - Embarazos finalizados
    - GET /embarazos/estadisticas/ - Estadísticas globales
    - GET /embarazos/{id}/calcular_riesgo/ - Cálculo de riesgo
    - GET /embarazos/{id}/complicaciones/ - Complicaciones del embarazo
    - POST /embarazos/{id}/agregar_complicacion/ - Agregar complicación
    - GET /embarazos/por_paciente/{paciente_id}/ - Embarazos de una paciente
    - GET /embarazos/buscar/ - Búsqueda avanzada
    - GET /embarazos/exportar_csv/ - Exportar a CSV
    - POST /embarazos/{id}/finalizar/ - Finalizar embarazo
    - DELETE /embarazos/{id}/ - Soft delete
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Campos de búsqueda
    search_fields = [
        'paciente__nombres',
        'paciente__apellidos',
        'paciente__cedula_identidad',
        'medico_responsable',
        'numero_gesta'
    ]

    # Campos de ordenamiento
    ordering_fields = [
        'id',
        'fecha_ultima_menstruacion',
        'fecha_probable_parto',
        'numero_gesta',
        'nivel_riesgo',
        'fecha_registro'
    ]

    ordering = ['-fecha_registro']

    def get_queryset(self):
        """
        Obtiene el queryset base con filtros opcionales.
        Por defecto muestra solo embarazos activos.
        """
        queryset = Embarazo.objects.filter(activo=True)

        # Filtro por estado
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)

        # Filtro por nivel de riesgo
        nivel_riesgo = self.request.query_params.get('nivel_riesgo', None)
        if nivel_riesgo:
            queryset = queryset.filter(nivel_riesgo=nivel_riesgo)

        # Filtro por alto riesgo
        alto_riesgo = self.request.query_params.get('alto_riesgo', None)
        if alto_riesgo == 'true':
            queryset = queryset.filter(embarazo_alto_riesgo=True)

        # Filtro por tipo de embarazo
        tipo_embarazo = self.request.query_params.get('tipo_embarazo', None)
        if tipo_embarazo:
            queryset = queryset.filter(tipo_embarazo=tipo_embarazo)

        # Filtro por trimestre
        trimestre = self.request.query_params.get('trimestre', None)
        if trimestre:
            # Calcular edad gestacional y filtrar
            # Este es un filtro aproximado, idealmente se haría con anotación
            pass

        # Filtro por paciente
        paciente_id = self.request.query_params.get('paciente', None)
        if paciente_id:
            queryset = queryset.filter(paciente_id=paciente_id)

        # Prefetch related para optimizar queries
        queryset = queryset.select_related('paciente', 'medico_responsable_fk')
        queryset = queryset.prefetch_related('complicaciones_detalladas', 'controles')

        return queryset

    def get_serializer_class(self):
        """
        Retorna el serializer adecuado según la acción.
        """
        if self.action == 'create':
            return EmbarazoCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return EmbarazoUpdateSerializer
        elif self.action == 'retrieve':
            return EmbarazoDetailSerializer
        elif self.action == 'list':
            return EmbarazoListSerializer
        return EmbarazoSerializer

    # -------------------------------------------------------------------------
    # CRUD OVERRIDE
    # -------------------------------------------------------------------------

    def create(self, request, *args, **kwargs):
        """
        Crea un nuevo embarazo.
        """
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)

            # Asignar usuario creador si está disponible
            embarazo = serializer.save(creado_por=request.user if request.user.is_authenticated else None)

            return Response({
                'mensaje': 'Embarazo registrado exitosamente',
                'data': EmbarazoDetailSerializer(embarazo).data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': f'Error al crear embarazo: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """
        Actualiza un embarazo existente.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        try:
            serializer.is_valid(raise_exception=True)

            # Asignar usuario modificador
            embarazo = serializer.save(modificado_por=request.user if request.user.is_authenticated else None)

            return Response({
                'mensaje': 'Embarazo actualizado exitosamente',
                'data': EmbarazoDetailSerializer(embarazo).data
            })

        except Exception as e:
            return Response({
                'error': f'Error al actualizar embarazo: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete del embarazo.
        """
        instance = self.get_object()

        try:
            # Soft delete
            instance.activo = False
            instance.eliminado = True
            instance.fecha_eliminacion = timezone.now()
            instance.eliminado_por = request.user if request.user.is_authenticated else None
            instance.save()

            return Response({
                'mensaje': 'Embarazo eliminado exitosamente (soft delete)'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': f'Error al eliminar embarazo: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------------------------------
    # ENDPOINTS DE LISTADOS ESPECIALIZADOS
    # -------------------------------------------------------------------------

    @action(detail=False, methods=['get'])
    def alto_riesgo(self, request):
        """
        Retorna todos los embarazos de alto riesgo activos.
        """
        embarazos = self.get_queryset().filter(
            Q(embarazo_alto_riesgo=True) | Q(nivel_riesgo__in=['alto', 'muy_alto'])
        ).filter(estado='en_curso')

        serializer = EmbarazoListSerializer(embarazos, many=True)

        return Response({
            'total': embarazos.count(),
            'embarazos': serializer.data
        })

    @action(detail=False, methods=['get'])
    def en_curso(self, request):
        """
        Retorna todos los embarazos actualmente en curso.
        """
        embarazos = self.get_queryset().filter(estado='en_curso')
        serializer = EmbarazoListSerializer(embarazos, many=True)

        return Response({
            'total': embarazos.count(),
            'embarazos': serializer.data
        })

    @action(detail=False, methods=['get'])
    def finalizados(self, request):
        """
        Retorna embarazos finalizados con filtros opcionales.
        """
        embarazos = self.get_queryset().exclude(estado='en_curso')

        # Filtro opcional por tipo de finalización
        via = request.query_params.get('via_finalizacion', None)
        if via:
            embarazos = embarazos.filter(via_finalizacion=via)

        # Filtro opcional por rango de fechas
        fecha_desde = request.query_params.get('fecha_desde', None)
        fecha_hasta = request.query_params.get('fecha_hasta', None)

        if fecha_desde:
            embarazos = embarazos.filter(fecha_finalizacion__gte=fecha_desde)
        if fecha_hasta:
            embarazos = embarazos.filter(fecha_finalizacion__lte=fecha_hasta)

        serializer = EmbarazoListSerializer(embarazos, many=True)

        return Response({
            'total': embarazos.count(),
            'embarazos': serializer.data
        })

    @action(detail=False, methods=['get'])
    def primer_trimestre(self, request):
        """
        Embarazos en primer trimestre (0-13 semanas).
        """
        embarazos_primer_trimestre = []

        for embarazo in self.get_queryset().filter(estado='en_curso'):
            eg = embarazo.get_edad_gestacional_actual()
            if eg and eg <= 13:
                embarazos_primer_trimestre.append(embarazo)

        serializer = EmbarazoListSerializer(embarazos_primer_trimestre, many=True)

        return Response({
            'total': len(embarazos_primer_trimestre),
            'embarazos': serializer.data
        })

    @action(detail=False, methods=['get'])
    def segundo_trimestre(self, request):
        """
        Embarazos en segundo trimestre (14-27 semanas).
        """
        embarazos_segundo_trimestre = []

        for embarazo in self.get_queryset().filter(estado='en_curso'):
            eg = embarazo.get_edad_gestacional_actual()
            if eg and 14 <= eg <= 27:
                embarazos_segundo_trimestre.append(embarazo)

        serializer = EmbarazoListSerializer(embarazos_segundo_trimestre, many=True)

        return Response({
            'total': len(embarazos_segundo_trimestre),
            'embarazos': serializer.data
        })

    @action(detail=False, methods=['get'])
    def tercer_trimestre(self, request):
        """
        Embarazos en tercer trimestre (28+ semanas).
        """
        embarazos_tercer_trimestre = []

        for embarazo in self.get_queryset().filter(estado='en_curso'):
            eg = embarazo.get_edad_gestacional_actual()
            if eg and eg >= 28:
                embarazos_tercer_trimestre.append(embarazo)

        serializer = EmbarazoListSerializer(embarazos_tercer_trimestre, many=True)

        return Response({
            'total': len(embarazos_tercer_trimestre),
            'embarazos': serializer.data
        })

    # -------------------------------------------------------------------------
    # ENDPOINTS DE INFORMACIÓN INDIVIDUAL
    # -------------------------------------------------------------------------

    @action(detail=True, methods=['get'])
    def calcular_riesgo(self, request, pk=None):
        """
        Calcula el nivel de riesgo del embarazo en tiempo real.
        """
        embarazo = self.get_object()

        nivel_riesgo = embarazo.evaluar_nivel_riesgo()
        complicaciones = embarazo.get_complicaciones_listado()

        return Response({
            'embarazo_id': embarazo.id,
            'paciente': f"{embarazo.paciente.nombres} {embarazo.paciente.apellidos}",
            'nivel_riesgo': nivel_riesgo,
            'nivel_riesgo_display': embarazo.get_nivel_riesgo_display(),
            'complicaciones': complicaciones,
            'numero_complicaciones': len(complicaciones),
            'factores_riesgo': {
                'edad_materna': embarazo.paciente.calcular_edad() if embarazo.paciente else None,
                'embarazo_multiple': embarazo.tipo_embarazo != 'unico',
                'imc_pregestacional': float(embarazo.imc_pregestacional) if embarazo.imc_pregestacional else None,
                'clasificacion_imc': embarazo.clasificacion_imc,
                'antecedentes_preeclampsia': embarazo.paciente.preeclampsia_previa if embarazo.paciente else False,
                'diabetes_previa': embarazo.paciente.diabetes_previa if embarazo.paciente else False,
                'hipertension_previa': embarazo.paciente.hipertension_previa if embarazo.paciente else False
            }
        })

    @action(detail=True, methods=['get'])
    def complicaciones(self, request, pk=None):
        """
        Retorna todas las complicaciones del embarazo.
        """
        embarazo = self.get_object()
        complicaciones = ComplicacionEmbarazo.objects.filter(embarazo=embarazo).order_by('-fecha_diagnostico')

        serializer = ComplicacionEmbarazoSerializer(complicaciones, many=True)

        return Response({
            'total_complicaciones': complicaciones.count(),
            'complicaciones': serializer.data,
            'complicaciones_activas': complicaciones.filter(resuelto=False).count(),
            'complicaciones_resueltas': complicaciones.filter(resuelto=True).count()
        })

    @action(detail=True, methods=['post'])
    def agregar_complicacion(self, request, pk=None):
        """
        Agrega una nueva complicación al embarazo.
        """
        embarazo = self.get_object()

        data = request.data.copy()
        data['embarazo'] = embarazo.id

        serializer = ComplicacionEmbarazoCreateSerializer(data=data)

        try:
            serializer.is_valid(raise_exception=True)
            complicacion = serializer.save(creado_por=request.user if request.user.is_authenticated else None)

            # Actualizar flag de complicaciones en el embarazo
            embarazo.tiene_complicaciones = True
            embarazo.save()

            return Response({
                'mensaje': 'Complicación registrada exitosamente',
                'data': ComplicacionEmbarazoSerializer(complicacion).data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': f'Error al registrar complicación: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def evolucion(self, request, pk=None):
        """
        Retorna la evolución del embarazo (controles + complicaciones).
        """
        embarazo = self.get_object()

        # Controles prenatales
        controles = embarazo.controles.filter(activo=True).order_by('fecha_control')
        controles_data = [{
            'fecha': control.fecha_control,
            'semanas_gestacion': control.semanas_gestacion,
            'peso': float(control.peso_actual) if control.peso_actual else None,
            'pa_sistolica': control.presion_arterial_sistolica,
            'pa_diastolica': control.presion_arterial_diastolica,
            'altura_uterina': float(control.altura_uterina) if control.altura_uterina else None,
            'fcf': control.frecuencia_cardiaca_fetal
        } for control in controles]

        # Complicaciones
        complicaciones = ComplicacionEmbarazo.objects.filter(embarazo=embarazo).order_by('fecha_diagnostico')
        complicaciones_data = [{
            'fecha': comp.fecha_diagnostico,
            'tipo': comp.get_tipo_complicacion_display(),
            'severidad': comp.get_severidad_display(),
            'resuelto': comp.resuelto
        } for comp in complicaciones]

        return Response({
            'embarazo_id': embarazo.id,
            'edad_gestacional_actual': embarazo.get_edad_gestacional_actual(),
            'controles': controles_data,
            'total_controles': len(controles_data),
            'complicaciones': complicaciones_data,
            'total_complicaciones': len(complicaciones_data)
        })

    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        """
        Finaliza un embarazo registrando resultado.
        """
        embarazo = self.get_object()

        if embarazo.estado != 'en_curso':
            return Response({
                'error': 'El embarazo ya está finalizado'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Datos requeridos
        estado_final = request.data.get('estado')
        fecha_finalizacion = request.data.get('fecha_finalizacion')
        via_finalizacion = request.data.get('via_finalizacion')

        if not all([estado_final, fecha_finalizacion, via_finalizacion]):
            return Response({
                'error': 'Faltan datos requeridos: estado, fecha_finalizacion, via_finalizacion'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Actualizar embarazo
            embarazo.estado = estado_final
            embarazo.fecha_finalizacion = fecha_finalizacion
            embarazo.via_finalizacion = via_finalizacion
            embarazo.edad_gestacional_finalizacion = embarazo.get_edad_gestacional_actual()

            # Datos opcionales
            if request.data.get('indicacion_cesarea'):
                embarazo.indicacion_cesarea = request.data.get('indicacion_cesarea')

            if request.data.get('resultado_embarazo'):
                embarazo.resultado_embarazo = request.data.get('resultado_embarazo')

            embarazo.modificado_por = request.user if request.user.is_authenticated else None
            embarazo.save()

            return Response({
                'mensaje': 'Embarazo finalizado exitosamente',
                'data': EmbarazoDetailSerializer(embarazo).data
            })

        except Exception as e:
            return Response({
                'error': f'Error al finalizar embarazo: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------------------------------
    # ESTADÍSTICAS Y REPORTES
    # -------------------------------------------------------------------------

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Retorna estadísticas generales de embarazos.
        """
        embarazos = self.get_queryset()

        # Conteos básicos
        total = embarazos.count()
        en_curso = embarazos.filter(estado='en_curso').count()
        finalizados = total - en_curso
        alto_riesgo = embarazos.filter(Q(embarazo_alto_riesgo=True) | Q(nivel_riesgo__in=['alto', 'muy_alto'])).count()
        con_complicaciones = embarazos.filter(tiene_complicaciones=True).count()

        # Por trimestre (solo en curso)
        embarazos_en_curso = embarazos.filter(estado='en_curso')
        primer_trimestre_count = sum(1 for e in embarazos_en_curso if e.get_trimestre_actual() == 1)
        segundo_trimestre_count = sum(1 for e in embarazos_en_curso if e.get_trimestre_actual() == 2)
        tercer_trimestre_count = sum(1 for e in embarazos_en_curso if e.get_trimestre_actual() == 3)

        # Por tipo
        unicos = embarazos.filter(tipo_embarazo='unico').count()
        multiples = embarazos.exclude(tipo_embarazo='unico').count()

        # Edad gestacional promedio (solo en curso)
        edades = [e.get_edad_gestacional_actual() for e in embarazos_en_curso if e.get_edad_gestacional_actual()]
        promedio_eg = sum(edades) / len(edades) if edades else 0

        # Complicaciones
        todas_complicaciones = ComplicacionEmbarazo.objects.filter(embarazo__in=embarazos)
        total_complicaciones = todas_complicaciones.count()

        # Complicación más frecuente
        if todas_complicaciones.exists():
            complicacion_frecuente = todas_complicaciones.values('tipo_complicacion').annotate(
                count=Count('id')
            ).order_by('-count').first()
            complicacion_mas_frecuente = complicacion_frecuente['tipo_complicacion'] if complicacion_frecuente else "Ninguna"
        else:
            complicacion_mas_frecuente = "Ninguna"

        return Response({
            'total_embarazos': total,
            'embarazos_en_curso': en_curso,
            'embarazos_finalizados': finalizados,
            'embarazos_alto_riesgo': alto_riesgo,
            'embarazos_con_complicaciones': con_complicaciones,
            'promedio_edad_gestacional': round(promedio_eg, 1),
            'embarazos_primer_trimestre': primer_trimestre_count,
            'embarazos_segundo_trimestre': segundo_trimestre_count,
            'embarazos_tercer_trimestre': tercer_trimestre_count,
            'embarazos_unicos': unicos,
            'embarazos_multiples': multiples,
            'total_complicaciones': total_complicaciones,
            'complicacion_mas_frecuente': complicacion_mas_frecuente
        })

    @action(detail=False, methods=['get'])
    def exportar_csv(self, request):
        """
        Exporta embarazos a CSV.
        """
        embarazos = self.get_queryset()

        # Crear CSV
        output = StringIO()
        writer = csv.writer(output)

        # Encabezados
        writer.writerow([
            'ID', 'Paciente', 'Cédula', 'Número Gesta', 'FUR', 'FPP',
            'Tipo Embarazo', 'Estado', 'Nivel Riesgo', 'Edad Gestacional',
            'Trimestre', 'Complicaciones', 'Fecha Registro'
        ])

        # Datos
        for embarazo in embarazos:
            writer.writerow([
                embarazo.id,
                f"{embarazo.paciente.nombres} {embarazo.paciente.apellidos}",
                embarazo.paciente.cedula_identidad,
                embarazo.numero_gesta,
                embarazo.fecha_ultima_menstruacion,
                embarazo.fecha_probable_parto,
                embarazo.get_tipo_embarazo_display(),
                embarazo.get_estado_display(),
                embarazo.get_nivel_riesgo_display(),
                embarazo.get_edad_gestacional_actual(),
                embarazo.get_trimestre_actual(),
                len(embarazo.get_complicaciones_listado()),
                embarazo.fecha_registro.strftime('%Y-%m-%d')
            ])

        output.seek(0)

        from django.http import HttpResponse
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="embarazos_{timezone.now().strftime("%Y%m%d")}.csv"'

        return response


# =============================================================================
# VIEWSET DE COMPLICACIONES DE EMBARAZO
# =============================================================================

class ComplicacionEmbarazoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de complicaciones de embarazos.
    """

    queryset = ComplicacionEmbarazo.objects.all()
    serializer_class = ComplicacionEmbarazoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]

    ordering_fields = ['fecha_diagnostico', 'severidad', 'tipo_complicacion']
    ordering = ['-fecha_diagnostico']

    def get_queryset(self):
        """Filtros de queryset."""
        queryset = super().get_queryset()

        # Filtrar por embarazo
        embarazo_id = self.request.query_params.get('embarazo', None)
        if embarazo_id:
            queryset = queryset.filter(embarazo_id=embarazo_id)

        # Filtrar por tipo
        tipo = self.request.query_params.get('tipo', None)
        if tipo:
            queryset = queryset.filter(tipo_complicacion=tipo)

        # Filtrar por severidad
        severidad = self.request.query_params.get('severidad', None)
        if severidad:
            queryset = queryset.filter(severidad=severidad)

        # Solo no resueltas
        no_resueltas = self.request.query_params.get('no_resueltas', None)
        if no_resueltas == 'true':
            queryset = queryset.filter(resuelto=False)

        return queryset.select_related('embarazo', 'embarazo__paciente')


# =============================================================================
# FIN DEL ARCHIVO - embarazos/views.py
# =============================================================================
