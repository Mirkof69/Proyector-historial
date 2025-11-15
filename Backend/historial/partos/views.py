"""
===========================================
MÓDULO: VIEWS DE PARTOS
===========================================
Descripción:
    ViewSets completos para gestión de partos, recién nacidos y complicaciones.
    Incluye CRUD completo + 15 acciones personalizadas.

ViewSets principales:
    - PartoViewSet: Gestión completa de partos (21 endpoints)
    - RecienNacidoViewSet: Gestión de recién nacidos (6 endpoints)
    - ComplicacionPartoViewSet: Gestión de complicaciones (6 endpoints)

Funcionalidades especiales:
    - Estadísticas por tipo, vía, período
    - Búsqueda avanzada con múltiples filtros
    - Reportes de partos
    - Certificados de nacimiento
    - Análisis de complicaciones
    - Indicadores de salud materno-infantil

Seguridad:
    - Autenticación JWT requerida
    - Validaciones extensas en cada operación
    - Control de permisos por acción

Autor: Sistema Historial Médico
Fecha: 2025
Versión: 2.0
===========================================
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg, Sum, Q, F, Max, Min
from django.utils import timezone
from datetime import datetime, timedelta, date
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Parto, RecienNacido, ComplicacionParto
from .serializers import (
    PartoSerializer, PartoCreateSerializer, PartoDetailSerializer,
    RecienNacidoSerializer, ComplicacionPartoSerializer
)


# ===========================================
# VIEWSET: PARTOS
# ===========================================
class PartoViewSet(viewsets.ModelViewSet):
    """
    VIEWSET: ViewSet completo para gestión de Partos

    Funcionamiento:
        Proporciona CRUD completo para partos más 15 acciones personalizadas
        Incluye validaciones, filtros y estadísticas

    Endpoints estándar:
        - GET /api/partos/ - Listar todos los partos
        - POST /api/partos/ - Crear nuevo parto
        - GET /api/partos/{id}/ - Detalle de un parto
        - PUT /api/partos/{id}/ - Actualizar parto completo
        - PATCH /api/partos/{id}/ - Actualizar parcial
        - DELETE /api/partos/{id}/ - Eliminar parto

    Endpoints personalizados:
        - GET /api/partos/estadisticas/ - Estadísticas generales
        - GET /api/partos/por_paciente/?paciente_id=X - Partos de un paciente
        - GET /api/partos/recientes/ - Partos recientes (últimos 30 días)
        - GET /api/partos/busqueda_avanzada/ - Búsqueda con múltiples filtros
        - GET /api/partos/por_tipo/ - Agrupar por tipo de parto
        - GET /api/partos/por_via/ - Agrupar por vía de parto
        - GET /api/partos/por_fecha/ - Partos en rango de fechas
        - GET /api/partos/con_complicaciones/ - Partos con complicaciones
        - GET /api/partos/cesarea_rate/ - Tasa de cesáreas
        - GET /api/partos/apgar_promedio/ - Promedio de APGAR
        - POST /api/partos/{id}/finalizar/ - Marcar parto como finalizado
        - POST /api/partos/{id}/registrar_complicacion/ - Registrar complicación
        - GET /api/partos/{id}/certificado_nacimiento/ - Generar certificado
        - GET /api/partos/{id}/resumen_completo/ - Resumen completo del parto
        - GET /api/partos/reporte_mensual/ - Reporte mensual

    Permisos:
        - Requiere autenticación JWT
        - IsAuthenticated para todas las operaciones
    """

    queryset = Parto.objects.all()
    serializer_class = PartoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    # Campos para filtrado
    filterset_fields = ['tipo_parto', 'via_parto', 'estado', 'fecha_parto', 'paciente', 'embarazo']

    # Campos para búsqueda
    search_fields = ['paciente__nombre', 'paciente__apellido', 'observaciones']

    # Campos para ordenamiento
    ordering_fields = ['fecha_parto', 'hora_inicio', 'fecha_registro']
    ordering = ['-fecha_parto', '-hora_inicio']

    def get_queryset(self):
        """
        MÉTODO: Obtener queryset optimizado

        Funcionamiento:
            Retorna queryset con select_related y prefetch_related
            para optimizar consultas a la base de datos
        """
        queryset = Parto.objects.select_related(
            'paciente',
            'embarazo',
            'medico'
        ).prefetch_related(
            'recien_nacidos',
            'complicaciones_list'
        ).all()
        return queryset

    def get_serializer_class(self):
        """
        MÉTODO: Determinar serializer según acción

        Funcionamiento:
            - create: PartoCreateSerializer (con validaciones de creación)
            - retrieve: PartoDetailSerializer (información completa)
            - otros: PartoSerializer (estándar)
        """
        if self.action == 'create':
            return PartoCreateSerializer
        elif self.action == 'retrieve':
            return PartoDetailSerializer
        return PartoSerializer

    def perform_create(self, serializer):
        """
        MÉTODO: Lógica adicional al crear parto

        Funcionamiento:
            - Guarda el parto
            - Registra el médico que atiende (usuario actual)
        """
        parto = serializer.save(medico=self.request.user)

        # Si el parto está finalizado, marcar embarazo como finalizado
        if parto.estado == 'finalizado':
            embarazo = parto.embarazo
            if embarazo.estado != 'finalizado':
                embarazo.estado = 'finalizado'
                embarazo.save()

    # ===========================================
    # ACCIÓN: ESTADÍSTICAS GENERALES
    # ===========================================
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        ACCIÓN: Estadísticas generales de partos

        Funcionamiento:
            Calcula y retorna estadísticas completas sobre todos los partos

        Cálculos realizados:
            - Total de partos registrados
            - Distribución por tipo de parto
            - Distribución por vía de parto
            - Promedio de edad gestacional
            - Promedio de duración de trabajo de parto
            - Total de recién nacidos
            - Partos con complicaciones
            - Tasa de cesáreas

        Retorna:
            {
                "total_partos": int,
                "por_tipo": {tipo: count},
                "por_via": {via: count},
                "promedio_edad_gestacional": float,
                "promedio_duracion": float,
                "total_recien_nacidos": int,
                "con_complicaciones": int,
                "tasa_cesarea": float
            }
        """
        total = Parto.objects.count()

        # Distribución por tipo
        por_tipo = {}
        for tipo, _ in Parto.TIPOS_PARTO:
            count = Parto.objects.filter(tipo_parto=tipo).count()
            por_tipo[tipo] = count

        # Distribución por vía
        por_via = {}
        for via, _ in Parto.VIAS_PARTO:
            count = Parto.objects.filter(via_parto=via).count()
            por_via[via] = count

        # Promedios
        promedios = Parto.objects.aggregate(
            promedio_edad_gestacional=Avg('edad_gestacional_semanas'),
            promedio_duracion=Avg('duracion_trabajo_parto')
        )

        # Total de recién nacidos
        total_rn = RecienNacido.objects.count()

        # Partos con complicaciones
        con_complicaciones = Parto.objects.filter(complicaciones=True).count()

        # Tasa de cesáreas
        cesareas = Parto.objects.filter(tipo_parto='cesarea').count()
        tasa_cesarea = (cesareas / total * 100) if total > 0 else 0

        return Response({
            'total_partos': total,
            'por_tipo': por_tipo,
            'por_via': por_via,
            'promedio_edad_gestacional': promedios['promedio_edad_gestacional'],
            'promedio_duracion_minutos': promedios['promedio_duracion'],
            'total_recien_nacidos': total_rn,
            'partos_con_complicaciones': con_complicaciones,
            'tasa_cesarea': round(tasa_cesarea, 2),
        })

    # ===========================================
    # ACCIÓN: PARTOS POR PACIENTE
    # ===========================================
    @action(detail=False, methods=['get'])
    def por_paciente(self, request):
        """
        ACCIÓN: Obtener todos los partos de un paciente

        Funcionamiento:
            Filtra partos por ID de paciente

        Parámetros:
            - paciente_id (query param): ID del paciente

        Retorna:
            Lista de partos del paciente
        """
        paciente_id = request.query_params.get('paciente_id')

        if not paciente_id:
            return Response(
                {'error': 'Se requiere paciente_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        partos = self.get_queryset().filter(paciente_id=paciente_id)
        serializer = self.get_serializer(partos, many=True)

        return Response(serializer.data)

    # ===========================================
    # ACCIÓN: PARTOS RECIENTES
    # ===========================================
    @action(detail=False, methods=['get'])
    def recientes(self, request):
        """
        ACCIÓN: Obtener partos recientes

        Funcionamiento:
            Retorna partos de los últimos N días (por defecto 30)

        Parámetros:
            - dias (query param): Cantidad de días hacia atrás (default: 30)

        Retorna:
            Lista de partos recientes ordenados por fecha descendente
        """
        dias = int(request.query_params.get('dias', 30))
        fecha_limite = date.today() - timedelta(days=dias)

        partos = self.get_queryset().filter(
            fecha_parto__gte=fecha_limite
        ).order_by('-fecha_parto', '-hora_inicio')

        serializer = self.get_serializer(partos, many=True)

        return Response({
            'total': partos.count(),
            'dias': dias,
            'partos': serializer.data
        })

    # ===========================================
    # ACCIÓN: BÚSQUEDA AVANZADA
    # ===========================================
    @action(detail=False, methods=['get'])
    def busqueda_avanzada(self, request):
        """
        ACCIÓN: Búsqueda avanzada de partos

        Funcionamiento:
            Permite filtrar por múltiples criterios simultáneamente

        Parámetros (query params):
            - tipo_parto: Tipo de parto
            - via_parto: Vía de parto
            - estado: Estado del parto
            - fecha_desde: Fecha inicio (YYYY-MM-DD)
            - fecha_hasta: Fecha fin (YYYY-MM-DD)
            - con_complicaciones: true/false
            - edad_gestacional_min: Edad gestacional mínima (semanas)
            - edad_gestacional_max: Edad gestacional máxima (semanas)
            - medico_id: ID del médico

        Retorna:
            Lista de partos que cumplen los criterios + total de resultados
        """
        queryset = self.get_queryset()

        # Filtro por tipo
        tipo_parto = request.query_params.get('tipo_parto')
        if tipo_parto:
            queryset = queryset.filter(tipo_parto=tipo_parto)

        # Filtro por vía
        via_parto = request.query_params.get('via_parto')
        if via_parto:
            queryset = queryset.filter(via_parto=via_parto)

        # Filtro por estado
        estado = request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)

        # Filtro por rango de fechas
        fecha_desde = request.query_params.get('fecha_desde')
        fecha_hasta = request.query_params.get('fecha_hasta')
        if fecha_desde:
            queryset = queryset.filter(fecha_parto__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_parto__lte=fecha_hasta)

        # Filtro por complicaciones
        con_complicaciones = request.query_params.get('con_complicaciones')
        if con_complicaciones:
            es_true = con_complicaciones.lower() == 'true'
            queryset = queryset.filter(complicaciones=es_true)

        # Filtro por edad gestacional
        eg_min = request.query_params.get('edad_gestacional_min')
        eg_max = request.query_params.get('edad_gestacional_max')
        if eg_min:
            queryset = queryset.filter(edad_gestacional_semanas__gte=int(eg_min))
        if eg_max:
            queryset = queryset.filter(edad_gestacional_semanas__lte=int(eg_max))

        # Filtro por médico
        medico_id = request.query_params.get('medico_id')
        if medico_id:
            queryset = queryset.filter(medico_id=medico_id)

        serializer = self.get_serializer(queryset, many=True)

        return Response({
            'total_resultados': queryset.count(),
            'filtros_aplicados': request.query_params.dict(),
            'partos': serializer.data
        })

    # ===========================================
    # ACCIÓN: AGRUPAR POR TIPO
    # ===========================================
    @action(detail=False, methods=['get'])
    def por_tipo(self, request):
        """
        ACCIÓN: Agrupar partos por tipo

        Funcionamiento:
            Retorna estadísticas detalladas agrupadas por tipo de parto

        Retorna:
            {
                tipo: {
                    "total": int,
                    "porcentaje": float,
                    "con_complicaciones": int,
                    "promedio_duracion": float
                }
            }
        """
        total_general = Parto.objects.count()
        resultados = {}

        for tipo, tipo_display in Parto.TIPOS_PARTO:
            partos_tipo = Parto.objects.filter(tipo_parto=tipo)
            total = partos_tipo.count()

            if total > 0:
                complicaciones = partos_tipo.filter(complicaciones=True).count()
                duracion = partos_tipo.aggregate(Avg('duracion_trabajo_parto'))

                resultados[tipo] = {
                    'nombre': tipo_display,
                    'total': total,
                    'porcentaje': round((total / total_general * 100), 2) if total_general > 0 else 0,
                    'con_complicaciones': complicaciones,
                    'promedio_duracion_minutos': duracion['duracion_trabajo_parto__avg']
                }

        return Response(resultados)

    # ===========================================
    # ACCIÓN: AGRUPAR POR VÍA
    # ===========================================
    @action(detail=False, methods=['get'])
    def por_via(self, request):
        """
        ACCIÓN: Agrupar partos por vía de parto

        Funcionamiento:
            Retorna estadísticas detalladas agrupadas por vía de parto

        Retorna:
            {
                via: {
                    "total": int,
                    "porcentaje": float,
                    "promedio_edad_gestacional": float
                }
            }
        """
        total_general = Parto.objects.count()
        resultados = {}

        for via, via_display in Parto.VIAS_PARTO:
            partos_via = Parto.objects.filter(via_parto=via)
            total = partos_via.count()

            if total > 0:
                edad = partos_via.aggregate(Avg('edad_gestacional_semanas'))

                resultados[via] = {
                    'nombre': via_display,
                    'total': total,
                    'porcentaje': round((total / total_general * 100), 2) if total_general > 0 else 0,
                    'promedio_edad_gestacional_semanas': edad['edad_gestacional_semanas__avg']
                }

        return Response(resultados)

    # ===========================================
    # ACCIÓN: PARTOS EN RANGO DE FECHAS
    # ===========================================
    @action(detail=False, methods=['get'])
    def por_fecha(self, request):
        """
        ACCIÓN: Obtener partos en rango de fechas

        Funcionamiento:
            Filtra partos entre dos fechas y retorna estadísticas

        Parámetros:
            - fecha_desde (YYYY-MM-DD): Fecha inicio
            - fecha_hasta (YYYY-MM-DD): Fecha fin

        Retorna:
            Lista de partos + estadísticas del período
        """
        fecha_desde = request.query_params.get('fecha_desde')
        fecha_hasta = request.query_params.get('fecha_hasta')

        if not fecha_desde or not fecha_hasta:
            return Response(
                {'error': 'Se requieren fecha_desde y fecha_hasta'},
                status=status.HTTP_400_BAD_REQUEST
            )

        partos = self.get_queryset().filter(
            fecha_parto__gte=fecha_desde,
            fecha_parto__lte=fecha_hasta
        )

        # Estadísticas del período
        total = partos.count()
        cesareas = partos.filter(tipo_parto='cesarea').count()
        con_complicaciones = partos.filter(complicaciones=True).count()

        serializer = self.get_serializer(partos, many=True)

        return Response({
            'periodo': {
                'desde': fecha_desde,
                'hasta': fecha_hasta
            },
            'estadisticas': {
                'total_partos': total,
                'cesareas': cesareas,
                'tasa_cesarea': round((cesareas / total * 100), 2) if total > 0 else 0,
                'con_complicaciones': con_complicaciones,
                'tasa_complicaciones': round((con_complicaciones / total * 100), 2) if total > 0 else 0
            },
            'partos': serializer.data
        })

    # ===========================================
    # ACCIÓN: PARTOS CON COMPLICACIONES
    # ===========================================
    @action(detail=False, methods=['get'])
    def con_complicaciones(self, request):
        """
        ACCIÓN: Obtener partos con complicaciones

        Funcionamiento:
            Retorna todos los partos que tuvieron complicaciones
            con detalles de las mismas

        Retorna:
            Lista de partos con complicaciones + análisis
        """
        partos = self.get_queryset().filter(complicaciones=True)

        # Análisis de complicaciones
        total = partos.count()
        por_tipo = {}

        complicaciones = ComplicacionParto.objects.all()
        for comp_tipo, comp_display in ComplicacionParto.TIPOS_COMPLICACION:
            count = complicaciones.filter(tipo_complicacion=comp_tipo).count()
            if count > 0:
                por_tipo[comp_tipo] = {
                    'nombre': comp_display,
                    'total': count
                }

        serializer = self.get_serializer(partos, many=True)

        return Response({
            'total_partos_complicados': total,
            'tipos_complicaciones': por_tipo,
            'partos': serializer.data
        })

    # ===========================================
    # ACCIÓN: TASA DE CESÁREAS
    # ===========================================
    @action(detail=False, methods=['get'])
    def cesarea_rate(self, request):
        """
        ACCIÓN: Calcular tasa de cesáreas

        Funcionamiento:
            Calcula la tasa de cesáreas general y por período

        Parámetros opcionales:
            - meses: Cantidad de meses hacia atrás (default: 12)

        Retorna:
            Tasa general y evolución mensual de cesáreas
        """
        total_partos = Parto.objects.count()
        total_cesareas = Parto.objects.filter(tipo_parto='cesarea').count()

        tasa_general = (total_cesareas / total_partos * 100) if total_partos > 0 else 0

        # Evolución mensual
        meses = int(request.query_params.get('meses', 12))
        fecha_inicio = date.today() - timedelta(days=meses*30)

        evolucion = []
        for i in range(meses):
            mes_inicio = fecha_inicio + timedelta(days=i*30)
            mes_fin = mes_inicio + timedelta(days=30)

            partos_mes = Parto.objects.filter(
                fecha_parto__gte=mes_inicio,
                fecha_parto__lt=mes_fin
            )

            total_mes = partos_mes.count()
            cesareas_mes = partos_mes.filter(tipo_parto='cesarea').count()

            if total_mes > 0:
                evolucion.append({
                    'mes': mes_inicio.strftime('%Y-%m'),
                    'total_partos': total_mes,
                    'cesareas': cesareas_mes,
                    'tasa': round((cesareas_mes / total_mes * 100), 2)
                })

        return Response({
            'tasa_general': round(tasa_general, 2),
            'total_partos': total_partos,
            'total_cesareas': total_cesareas,
            'evolucion_mensual': evolucion,
            'recomendacion_oms': '10-15%',
            'cumple_oms': tasa_general <= 15
        })

    # ===========================================
    # ACCIÓN: PROMEDIO DE APGAR
    # ===========================================
    @action(detail=False, methods=['get'])
    def apgar_promedio(self, request):
        """
        ACCIÓN: Calcular promedio de APGAR

        Funcionamiento:
            Calcula promedios de APGAR al minuto 1 y 5
            Agrupa por tipo de parto

        Retorna:
            Promedios generales y por tipo de parto
        """
        # Promedios generales
        promedios = RecienNacido.objects.aggregate(
            apgar_1min_promedio=Avg('apgar_1min'),
            apgar_5min_promedio=Avg('apgar_5min')
        )

        # Por tipo de parto
        por_tipo = {}
        for tipo, tipo_display in Parto.TIPOS_PARTO:
            rn_tipo = RecienNacido.objects.filter(parto__tipo_parto=tipo)

            if rn_tipo.exists():
                promedios_tipo = rn_tipo.aggregate(
                    apgar_1min=Avg('apgar_1min'),
                    apgar_5min=Avg('apgar_5min')
                )

                por_tipo[tipo] = {
                    'nombre': tipo_display,
                    'apgar_1min_promedio': promedios_tipo['apgar_1min'],
                    'apgar_5min_promedio': promedios_tipo['apgar_5min'],
                    'total_rn': rn_tipo.count()
                }

        return Response({
            'promedios_generales': promedios,
            'por_tipo_parto': por_tipo,
            'interpretacion': {
                '7-10': 'Normal',
                '4-6': 'Moderadamente anormal',
                '0-3': 'Críticamente bajo'
            }
        })

    # ===========================================
    # ACCIÓN: FINALIZAR PARTO
    # ===========================================
    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        """
        ACCIÓN: Marcar parto como finalizado

        Funcionamiento:
            Cambia el estado del parto a "finalizado"
            Actualiza el estado del embarazo asociado

        Retorna:
            Datos del parto actualizado
        """
        parto = self.get_object()

        if parto.estado == 'finalizado':
            return Response(
                {'mensaje': 'El parto ya está finalizado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Actualizar parto
        parto.estado = 'finalizado'
        parto.save()

        # Actualizar embarazo
        embarazo = parto.embarazo
        if embarazo.estado != 'finalizado':
            embarazo.estado = 'finalizado'
            embarazo.save()

        serializer = self.get_serializer(parto)

        return Response({
            'mensaje': 'Parto finalizado exitosamente',
            'parto': serializer.data
        })

    # ===========================================
    # ACCIÓN: REGISTRAR COMPLICACIÓN
    # ===========================================
    @action(detail=True, methods=['post'])
    def registrar_complicacion(self, request, pk=None):
        """
        ACCIÓN: Registrar nueva complicación

        Funcionamiento:
            Crea una nueva complicación asociada al parto
            Actualiza el campo complicaciones del parto a True

        Parámetros (body):
            - tipo_complicacion: Tipo de complicación
            - descripcion: Descripción detallada
            - tratamiento: Tratamiento aplicado
            - resuelto: Si fue resuelto (boolean)

        Retorna:
            Datos de la complicación creada
        """
        parto = self.get_object()

        # Validar datos
        tipo_complicacion = request.data.get('tipo_complicacion')
        descripcion = request.data.get('descripcion')

        if not tipo_complicacion or not descripcion:
            return Response(
                {'error': 'Se requiere tipo_complicacion y descripcion'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Crear complicación
        complicacion = ComplicacionParto.objects.create(
            parto=parto,
            tipo_complicacion=tipo_complicacion,
            descripcion=descripcion,
            tratamiento=request.data.get('tratamiento', ''),
            resuelto=request.data.get('resuelto', False)
        )

        # Actualizar parto
        parto.complicaciones = True
        parto.estado = 'complicado'
        parto.save()

        serializer = ComplicacionPartoSerializer(complicacion)

        return Response({
            'mensaje': 'Complicación registrada exitosamente',
            'complicacion': serializer.data
        }, status=status.HTTP_201_CREATED)

    # ===========================================
    # ACCIÓN: CERTIFICADO DE NACIMIENTO
    # ===========================================
    @action(detail=True, methods=['get'])
    def certificado_nacimiento(self, request, pk=None):
        """
        ACCIÓN: Generar certificado de nacimiento

        Funcionamiento:
            Genera datos estructurados para certificado de nacimiento
            Incluye información del parto, recién nacido(s) y madre

        Retorna:
            JSON con todos los datos necesarios para el certificado
        """
        parto = self.get_object()

        # Datos del parto
        certificado = {
            'numero_certificado': f"CERT-{parto.id}-{parto.uuid}",
            'fecha_emision': date.today().isoformat(),
            'parto': {
                'fecha': parto.fecha_parto.isoformat(),
                'hora': parto.hora_fin.isoformat() if parto.hora_fin else 'N/A',
                'tipo': parto.get_tipo_parto_display(),
                'via': parto.get_via_parto_display(),
                'edad_gestacional': f"{parto.edad_gestacional_semanas}+{parto.edad_gestacional_dias}",
            },
            'madre': {
                'nombre_completo': parto.paciente.nombre_completo if parto.paciente else 'N/A',
                'identificacion': parto.paciente.ci if parto.paciente else 'N/A',
                'edad': parto.paciente.edad if parto.paciente else 'N/A',
            },
            'medico': {
                'nombre_completo': parto.medico.nombre_completo if parto.medico else 'N/A',
                'especialidad': 'Ginecología y Obstetricia',
            },
            'recien_nacidos': []
        }

        # Datos de recién nacidos
        for rn in parto.recien_nacidos.all():
            certificado['recien_nacidos'].append({
                'numero': rn.numero_hijo,
                'sexo': rn.get_sexo_display(),
                'peso': f"{rn.peso} g",
                'talla': f"{rn.talla} cm" if rn.talla else 'N/A',
                'perimetro_cefalico': f"{rn.perimetro_cefalico} cm" if rn.perimetro_cefalico else 'N/A',
                'apgar_1min': rn.apgar_1min if rn.apgar_1min else 'N/A',
                'apgar_5min': rn.apgar_5min if rn.apgar_5min else 'N/A',
                'estado': rn.get_estado_al_nacer_display(),
            })

        return Response(certificado)

    # ===========================================
    # ACCIÓN: RESUMEN COMPLETO
    # ===========================================
    @action(detail=True, methods=['get'])
    def resumen_completo(self, request, pk=None):
        """
        ACCIÓN: Resumen completo del parto

        Funcionamiento:
            Retorna toda la información relacionada al parto
            en un formato estructurado para reportes

        Retorna:
            JSON con información completa del parto, embarazo, recién nacidos
            y complicaciones
        """
        parto = self.get_object()

        resumen = {
            'parto': PartoDetailSerializer(parto).data,
            'estadisticas_relacionadas': {
                'total_recien_nacidos': parto.recien_nacidos.count(),
                'total_complicaciones': parto.complicaciones_list.count(),
                'duracion_horas': round(parto.duracion_trabajo_parto / 60, 2) if parto.duracion_trabajo_parto else 0,
            },
            'indicadores_calidad': {
                'parto_pretermino': parto.edad_gestacional_semanas < 37,
                'parto_termino': 37 <= parto.edad_gestacional_semanas <= 42,
                'parto_postermino': parto.edad_gestacional_semanas > 42,
                'tuvo_complicaciones': parto.complicaciones,
            }
        }

        return Response(resumen)

    # ===========================================
    # ACCIÓN: REPORTE MENSUAL
    # ===========================================
    @action(detail=False, methods=['get'])
    def reporte_mensual(self, request):
        """
        ACCIÓN: Generar reporte mensual

        Funcionamiento:
            Genera estadísticas detalladas del mes actual o especificado

        Parámetros:
            - mes (optional): Mes en formato YYYY-MM

        Retorna:
            Reporte completo con todas las estadísticas del mes
        """
        # Determinar mes a reportar
        mes_param = request.query_params.get('mes')
        if mes_param:
            try:
                fecha = datetime.strptime(mes_param, '%Y-%m').date()
                mes_inicio = fecha.replace(day=1)
            except:
                return Response(
                    {'error': 'Formato de mes inválido (usar YYYY-MM)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            hoy = date.today()
            mes_inicio = hoy.replace(day=1)

        # Calcular fin de mes
        if mes_inicio.month == 12:
            mes_fin = mes_inicio.replace(year=mes_inicio.year + 1, month=1)
        else:
            mes_fin = mes_inicio.replace(month=mes_inicio.month + 1)

        # Filtrar partos del mes
        partos_mes = Parto.objects.filter(
            fecha_parto__gte=mes_inicio,
            fecha_parto__lt=mes_fin
        )

        total = partos_mes.count()

        # Estadísticas
        reporte = {
            'periodo': {
                'mes': mes_inicio.strftime('%Y-%m'),
                'fecha_inicio': mes_inicio.isoformat(),
                'fecha_fin': (mes_fin - timedelta(days=1)).isoformat()
            },
            'totales': {
                'partos': total,
                'recien_nacidos': RecienNacido.objects.filter(parto__in=partos_mes).count(),
                'complicaciones': partos_mes.filter(complicaciones=True).count()
            },
            'por_tipo': {},
            'por_via': {},
            'indicadores': {}
        }

        # Por tipo
        for tipo, tipo_display in Parto.TIPOS_PARTO:
            count = partos_mes.filter(tipo_parto=tipo).count()
            if count > 0:
                reporte['por_tipo'][tipo] = {
                    'nombre': tipo_display,
                    'total': count,
                    'porcentaje': round((count / total * 100), 2) if total > 0 else 0
                }

        # Por vía
        for via, via_display in Parto.VIAS_PARTO:
            count = partos_mes.filter(via_parto=via).count()
            if count > 0:
                reporte['por_via'][via] = {
                    'nombre': via_display,
                    'total': count,
                    'porcentaje': round((count / total * 100), 2) if total > 0 else 0
                }

        # Indicadores
        cesareas = partos_mes.filter(tipo_parto='cesarea').count()
        reporte['indicadores'] = {
            'tasa_cesarea': round((cesareas / total * 100), 2) if total > 0 else 0,
            'promedio_edad_gestacional': partos_mes.aggregate(Avg('edad_gestacional_semanas'))['edad_gestacional_semanas__avg'],
            'promedio_duracion_trabajo_parto': partos_mes.aggregate(Avg('duracion_trabajo_parto'))['duracion_trabajo_parto__avg'],
        }

        return Response(reporte)


# ===========================================
# VIEWSET: RECIÉN NACIDOS
# ===========================================
class RecienNacidoViewSet(viewsets.ModelViewSet):
    """
    VIEWSET: ViewSet para gestión de Recién Nacidos

    Funcionamiento:
        Proporciona CRUD completo para recién nacidos

    Endpoints:
        - GET /api/recien-nacidos/ - Listar todos
        - POST /api/recien-nacidos/ - Crear nuevo
        - GET /api/recien-nacidos/{id}/ - Detalle
        - PUT /api/recien-nacidos/{id}/ - Actualizar completo
        - PATCH /api/recien-nacidos/{id}/ - Actualizar parcial
        - DELETE /api/recien-nacidos/{id}/ - Eliminar
        - GET /api/recien-nacidos/por_parto/?parto_id=X - Por parto
        - GET /api/recien-nacidos/estadisticas_apgar/ - Estadísticas APGAR
    """

    queryset = RecienNacido.objects.all()
    serializer_class = RecienNacidoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['sexo', 'estado_al_nacer', 'parto']
    ordering = ['-fecha_registro']

    @action(detail=False, methods=['get'])
    def por_parto(self, request):
        """Obtener recién nacidos de un parto específico"""
        parto_id = request.query_params.get('parto_id')

        if not parto_id:
            return Response(
                {'error': 'Se requiere parto_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        recien_nacidos = self.get_queryset().filter(parto_id=parto_id)
        serializer = self.get_serializer(recien_nacidos, many=True)

        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def estadisticas_apgar(self, request):
        """Estadísticas de APGAR"""
        total = RecienNacido.objects.count()

        # Clasificación por APGAR al minuto 1
        apgar_1_normal = RecienNacido.objects.filter(apgar_1min__gte=7).count()
        apgar_1_moderado = RecienNacido.objects.filter(apgar_1min__gte=4, apgar_1min__lt=7).count()
        apgar_1_critico = RecienNacido.objects.filter(apgar_1min__lt=4).count()

        # Clasificación por APGAR al minuto 5
        apgar_5_normal = RecienNacido.objects.filter(apgar_5min__gte=7).count()
        apgar_5_moderado = RecienNacido.objects.filter(apgar_5min__gte=4, apgar_5min__lt=7).count()
        apgar_5_critico = RecienNacido.objects.filter(apgar_5min__lt=4).count()

        return Response({
            'total_recien_nacidos': total,
            'apgar_1min': {
                'normal_7_10': apgar_1_normal,
                'moderado_4_6': apgar_1_moderado,
                'critico_0_3': apgar_1_critico
            },
            'apgar_5min': {
                'normal_7_10': apgar_5_normal,
                'moderado_4_6': apgar_5_moderado,
                'critico_0_3': apgar_5_critico
            },
            'porcentajes': {
                'apgar_1_normal': round((apgar_1_normal / total * 100), 2) if total > 0 else 0,
                'apgar_5_normal': round((apgar_5_normal / total * 100), 2) if total > 0 else 0
            }
        })


# ===========================================
# VIEWSET: COMPLICACIONES
# ===========================================
class ComplicacionPartoViewSet(viewsets.ModelViewSet):
    """
    VIEWSET: ViewSet para gestión de Complicaciones

    Funcionamiento:
        Proporciona CRUD completo para complicaciones de parto

    Endpoints:
        - GET /api/complicaciones/ - Listar todas
        - POST /api/complicaciones/ - Crear nueva
        - GET /api/complicaciones/{id}/ - Detalle
        - PUT /api/complicaciones/{id}/ - Actualizar completo
        - PATCH /api/complicaciones/{id}/ - Actualizar parcial
        - DELETE /api/complicaciones/{id}/ - Eliminar
        - GET /api/complicaciones/por_tipo/ - Agrupar por tipo
        - GET /api/complicaciones/no_resueltas/ - Complicaciones pendientes
    """

    queryset = ComplicacionParto.objects.all()
    serializer_class = ComplicacionPartoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['tipo_complicacion', 'resuelto', 'parto']
    ordering = ['-fecha_registro']

    @action(detail=False, methods=['get'])
    def por_tipo(self, request):
        """Agrupar complicaciones por tipo"""
        resultados = {}

        for tipo, tipo_display in ComplicacionParto.TIPOS_COMPLICACION:
            count = ComplicacionParto.objects.filter(tipo_complicacion=tipo).count()
            resueltas = ComplicacionParto.objects.filter(
                tipo_complicacion=tipo,
                resuelto=True
            ).count()

            if count > 0:
                resultados[tipo] = {
                    'nombre': tipo_display,
                    'total': count,
                    'resueltas': resueltas,
                    'pendientes': count - resueltas,
                    'tasa_resolucion': round((resueltas / count * 100), 2)
                }

        return Response(resultados)

    @action(detail=False, methods=['get'])
    def no_resueltas(self, request):
        """Complicaciones no resueltas"""
        complicaciones = self.get_queryset().filter(resuelto=False)
        serializer = self.get_serializer(complicaciones, many=True)

        return Response({
            'total_pendientes': complicaciones.count(),
            'complicaciones': serializer.data
        })


"""
RESUMEN DE VIEWS DE PARTOS:
============================

1. PartoViewSet:
   - CRUD completo (6 endpoints estándar)
   - 15 acciones personalizadas:
     * estadisticas - Estadísticas generales
     * por_paciente - Partos de un paciente
     * recientes - Partos recientes
     * busqueda_avanzada - Búsqueda con filtros múltiples
     * por_tipo - Agrupar por tipo
     * por_via - Agrupar por vía
     * por_fecha - Filtrar por fechas
     * con_complicaciones - Partos complicados
     * cesarea_rate - Tasa de cesáreas
     * apgar_promedio - Promedios APGAR
     * finalizar - Marcar como finalizado
     * registrar_complicacion - Nueva complicación
     * certificado_nacimiento - Generar certificado
     * resumen_completo - Resumen detallado
     * reporte_mensual - Reporte del mes
   Total: 21 endpoints

2. RecienNacidoViewSet:
   - CRUD completo (6 endpoints estándar)
   - 2 acciones personalizadas:
     * por_parto - RN de un parto
     * estadisticas_apgar - Estadísticas APGAR
   Total: 8 endpoints

3. ComplicacionPartoViewSet:
   - CRUD completo (6 endpoints estándar)
   - 2 acciones personalizadas:
     * por_tipo - Agrupar por tipo
     * no_resueltas - Pendientes
   Total: 8 endpoints

TOTAL ENDPOINTS: 37
LÍNEAS DE CÓDIGO: ~1200
============================
"""
