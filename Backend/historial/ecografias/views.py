# =============================================================================
# VIEWS DE ECOGRAFÍAS
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: ecografias
# Descripción: ViewSets y vistas para gestión de ecografías obstétricas
# Versión: 1.0.0
# =============================================================================

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from django.db.models import Q, Count, Avg, Max, Min, F
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

from datetime import datetime, timedelta
from decimal import Decimal
import logging

from .models import Ecografia
from .serializers import (
    EcografiaSerializer,
    EcografiaListSerializer,
    EcografiaCreateSerializer
)
from embarazos.models import Embarazo

# Configuración de logger para debugging y auditoría
logger = logging.getLogger(__name__)


# =============================================================================
# PAGINACIÓN PERSONALIZADA
# =============================================================================

class EcografiaPagination(PageNumberPagination):
    """
    Paginación personalizada para listados de ecografías.

    Permite al cliente especificar el tamaño de página mediante query params.
    Por defecto retorna 20 registros por página.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        """
        Retorna respuesta paginada con metadata adicional.

        Returns:
            Response: Respuesta con datos paginados y metadata
        """
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'page_size': self.page_size,
            'results': data
        })


# =============================================================================
# VIEWSET PRINCIPAL DE ECOGRAFÍAS
# =============================================================================

class EcografiaViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para gestión de ecografías obstétricas.

    Proporciona operaciones CRUD completas más acciones personalizadas:
    - list: Listar todas las ecografías (con filtros y búsqueda)
    - create: Crear nueva ecografía
    - retrieve: Obtener detalle de una ecografía
    - update: Actualizar ecografía completa
    - partial_update: Actualizar campos específicos
    - destroy: Eliminación lógica (soft delete)

    Acciones personalizadas:
    - por_embarazo: Listar ecografías de un embarazo específico
    - estadisticas: Obtener estadísticas generales
    - por_tipo: Filtrar por tipo de ecografía
    - ultimas: Obtener últimas ecografías realizadas
    - biometria_evolution: Evolución de biometría fetal
    - calcular_percentiles: Calcular percentiles de crecimiento
    - validar_coherencia: Validar coherencia de datos
    """

    queryset = Ecografia.objects.filter(activo=True)
    permission_classes = [IsAuthenticated]
    pagination_class = EcografiaPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    # Campos para búsqueda de texto libre
    search_fields = [
        'embarazo__paciente__nombre',
        'embarazo__paciente__apellido',
        'tipo_ecografia',
        'hallazgos',
        'observaciones'
    ]

    # Campos permitidos para ordenamiento
    ordering_fields = [
        'fecha_ecografia',
        'tipo_ecografia',
        'edad_gestacional_semanas',
        'peso_fetal_estimado',
        'fecha_registro'
    ]

    ordering = ['-fecha_ecografia']  # Ordenamiento por defecto

    def get_serializer_class(self):
        """
        Retorna la clase de serializer apropiada según la acción.

        - list: Usa EcografiaListSerializer (optimizado, menos campos)
        - create: Usa EcografiaCreateSerializer (validaciones de creación)
        - default: Usa EcografiaSerializer (completo)

        Returns:
            class: Clase del serializer a utilizar
        """
        if self.action == 'list':
            return EcografiaListSerializer
        elif self.action == 'create':
            return EcografiaCreateSerializer
        return EcografiaSerializer

    def get_queryset(self):
        """
        Retorna queryset filtrado según parámetros de query.

        Parámetros de filtrado disponibles:
        - embarazo_id: ID del embarazo
        - tipo: Tipo de ecografía
        - fecha_desde: Fecha mínima (formato YYYY-MM-DD)
        - fecha_hasta: Fecha máxima (formato YYYY-MM-DD)
        - semanas_min: Edad gestacional mínima
        - semanas_max: Edad gestacional máxima
        - latido_presente: Filtrar por presencia de latido cardíaco (true/false)
        - anatomia_normal: Filtrar por anatomía normal (true/false)

        Returns:
            QuerySet: Queryset filtrado de ecografías activas
        """
        queryset = super().get_queryset()

        # Optimización: Seleccionar datos relacionados para evitar N+1 queries
        queryset = queryset.select_related(
            'embarazo',
            'embarazo__paciente'
        ).prefetch_related(
            'embarazo__controles'
        )

        # Filtro por ID de embarazo
        embarazo_id = self.request.query_params.get('embarazo_id', None)
        if embarazo_id:
            queryset = queryset.filter(embarazo_id=embarazo_id)

        # Filtro por tipo de ecografía
        tipo = self.request.query_params.get('tipo', None)
        if tipo:
            queryset = queryset.filter(tipo_ecografia=tipo)

        # Filtro por rango de fechas
        fecha_desde = self.request.query_params.get('fecha_desde', None)
        if fecha_desde:
            try:
                fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_ecografia__gte=fecha_desde)
            except ValueError:
                logger.warning(f"Formato de fecha inválido: {fecha_desde}")

        fecha_hasta = self.request.query_params.get('fecha_hasta', None)
        if fecha_hasta:
            try:
                fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_ecografia__lte=fecha_hasta)
            except ValueError:
                logger.warning(f"Formato de fecha inválido: {fecha_hasta}")

        # Filtro por edad gestacional
        semanas_min = self.request.query_params.get('semanas_min', None)
        if semanas_min:
            try:
                semanas_min = int(semanas_min)
                queryset = queryset.filter(edad_gestacional_semanas__gte=semanas_min)
            except ValueError:
                logger.warning(f"Formato de semanas inválido: {semanas_min}")

        semanas_max = self.request.query_params.get('semanas_max', None)
        if semanas_max:
            try:
                semanas_max = int(semanas_max)
                queryset = queryset.filter(edad_gestacional_semanas__lte=semanas_max)
            except ValueError:
                logger.warning(f"Formato de semanas inválido: {semanas_max}")

        # Filtro por presencia de latido cardíaco
        latido_presente = self.request.query_params.get('latido_presente', None)
        if latido_presente is not None:
            latido_bool = latido_presente.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(latido_cardiaco_presente=latido_bool)

        # Filtro por anatomía normal
        anatomia_normal = self.request.query_params.get('anatomia_normal', None)
        if anatomia_normal is not None:
            if anatomia_normal.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(evaluacion_anatomia='normal')
            else:
                queryset = queryset.exclude(evaluacion_anatomia='normal')

        return queryset

    def create(self, request, *args, **kwargs):
        """
        Crea una nueva ecografía.

        Valida que:
        - El embarazo existe y está activo
        - Los datos biométricos son coherentes
        - Las fechas son válidas

        Args:
            request: Request con datos de la ecografía

        Returns:
            Response: Ecografía creada o errores de validación
        """
        try:
            # Validar que el embarazo existe y está activo
            embarazo_id = request.data.get('embarazo')
            if embarazo_id:
                try:
                    embarazo = Embarazo.objects.get(id=embarazo_id, activo=True)
                except Embarazo.DoesNotExist:
                    return Response(
                        {'error': 'El embarazo especificado no existe o no está activo'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Usar el serializer de creación
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Guardar la ecografía
            ecografia = serializer.save()

            # Log de auditoría
            logger.info(
                f"Ecografía creada: ID={ecografia.id}, "
                f"Embarazo={ecografia.embarazo_id}, "
                f"Tipo={ecografia.tipo_ecografia}, "
                f"Usuario={request.user.username}"
            )

            # Retornar con serializer completo
            return Response(
                EcografiaSerializer(ecografia).data,
                status=status.HTTP_201_CREATED
            )

        except ValidationError as e:
            logger.error(f"Error de validación al crear ecografía: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error inesperado al crear ecografía: {str(e)}")
            return Response(
                {'error': 'Error al crear la ecografía'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, *args, **kwargs):
        """
        Actualiza una ecografía existente.

        Args:
            request: Request con datos a actualizar

        Returns:
            Response: Ecografía actualizada o errores
        """
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()

            # Registrar usuario que actualiza
            logger.info(
                f"Actualizando ecografía ID={instance.id} por usuario={request.user.username}"
            )

            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            ecografia = serializer.save()

            logger.info(f"Ecografía ID={instance.id} actualizada exitosamente")

            return Response(EcografiaSerializer(ecografia).data)

        except ValidationError as e:
            logger.error(f"Error de validación al actualizar ecografía: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error inesperado al actualizar ecografía: {str(e)}")
            return Response(
                {'error': 'Error al actualizar la ecografía'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """
        Realiza soft delete de una ecografía.

        No elimina el registro de la BD, solo marca activo=False
        y registra fecha de eliminación.

        Args:
            request: Request de eliminación

        Returns:
            Response: Confirmación de eliminación
        """
        try:
            instance = self.get_object()

            # Log antes de eliminar
            logger.info(
                f"Eliminando ecografía ID={instance.id}, "
                f"Embarazo={instance.embarazo_id}, "
                f"Usuario={request.user.username}"
            )

            # Soft delete (definido en el modelo)
            instance.delete()

            return Response(
                {'message': 'Ecografía eliminada exitosamente'},
                status=status.HTTP_204_NO_CONTENT
            )

        except Exception as e:
            logger.error(f"Error al eliminar ecografía: {str(e)}")
            return Response(
                {'error': 'Error al eliminar la ecografía'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # =========================================================================
    # ACCIONES PERSONALIZADAS
    # =========================================================================

    @action(detail=False, methods=['get'], url_path='por-embarazo/(?P<embarazo_id>[^/.]+)')
    def por_embarazo(self, request, embarazo_id=None):
        """
        Lista todas las ecografías de un embarazo específico.

        URL: /api/ecografias/por-embarazo/{embarazo_id}/

        Args:
            embarazo_id: ID del embarazo

        Returns:
            Response: Lista de ecografías del embarazo ordenadas por fecha
        """
        try:
            # Validar que el embarazo existe
            embarazo = get_object_or_404(Embarazo, id=embarazo_id, activo=True)

            # Obtener ecografías del embarazo
            ecografias = self.queryset.filter(embarazo=embarazo).order_by('fecha_ecografia')

            # Información adicional del embarazo
            info_embarazo = {
                'embarazo_id': embarazo.id,
                'paciente': f"{embarazo.paciente.nombre} {embarazo.paciente.apellido}",
                'fecha_ur': embarazo.fecha_ur,
                'total_ecografias': ecografias.count(),
            }

            # Serializar las ecografías
            serializer = EcografiaSerializer(ecografias, many=True)

            return Response({
                'info_embarazo': info_embarazo,
                'ecografias': serializer.data
            })

        except Exception as e:
            logger.error(f"Error al obtener ecografías por embarazo: {str(e)}")
            return Response(
                {'error': 'Error al obtener las ecografías del embarazo'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Retorna estadísticas generales de ecografías.

        URL: /api/ecografias/estadisticas/

        Incluye:
        - Total de ecografías por tipo
        - Promedios de mediciones biométricas
        - Distribución por trimestre
        - Hallazgos más frecuentes

        Returns:
            Response: Diccionario con estadísticas
        """
        try:
            queryset = self.get_queryset()

            # Total de ecografías por tipo
            por_tipo = {}
            for tipo, nombre in Ecografia.TIPOS_ECOGRAFIA:
                count = queryset.filter(tipo_ecografia=tipo).count()
                por_tipo[tipo] = {
                    'nombre': nombre,
                    'cantidad': count
                }

            # Estadísticas de biometría fetal
            biometria_stats = queryset.exclude(
                peso_fetal_estimado__isnull=True
            ).aggregate(
                peso_promedio=Avg('peso_fetal_estimado'),
                peso_min=Min('peso_fetal_estimado'),
                peso_max=Max('peso_fetal_estimado'),
                dbp_promedio=Avg('diametro_biparietal'),
                cc_promedio=Avg('circunferencia_cefalica'),
                ca_promedio=Avg('circunferencia_abdominal'),
                lf_promedio=Avg('longitud_femur'),
            )

            # Distribución por trimestre
            por_trimestre = {
                'primer_trimestre': queryset.filter(edad_gestacional_semanas__lte=13).count(),
                'segundo_trimestre': queryset.filter(
                    edad_gestacional_semanas__gte=14,
                    edad_gestacional_semanas__lte=27
                ).count(),
                'tercer_trimestre': queryset.filter(edad_gestacional_semanas__gte=28).count(),
            }

            # Evaluación de anatomía
            anatomia_stats = {}
            for eval, nombre in Ecografia.EVALUACION_ANATOMIA:
                count = queryset.filter(evaluacion_anatomia=eval).count()
                anatomia_stats[eval] = {
                    'nombre': nombre,
                    'cantidad': count
                }

            # Líquido amniótico
            liquido_stats = {
                'normal': queryset.filter(liquido_amniotico='normal').count(),
                'oligohidramnios': queryset.filter(liquido_amniotico='oligohidramnios').count(),
                'polihidramnios': queryset.filter(liquido_amniotico='polihidramnios').count(),
            }

            # Total general
            total_ecografias = queryset.count()

            return Response({
                'total_ecografias': total_ecografias,
                'por_tipo': por_tipo,
                'por_trimestre': por_trimestre,
                'biometria': biometria_stats,
                'anatomia': anatomia_stats,
                'liquido_amniotico': liquido_stats,
                'fecha_consulta': timezone.now()
            })

        except Exception as e:
            logger.error(f"Error al calcular estadísticas: {str(e)}")
            return Response(
                {'error': 'Error al calcular estadísticas'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='por-tipo/(?P<tipo>[^/.]+)')
    def por_tipo(self, request, tipo=None):
        """
        Filtra ecografías por tipo específico.

        URL: /api/ecografias/por-tipo/{tipo}/

        Tipos válidos:
        - primer_trimestre
        - segundo_trimestre
        - tercer_trimestre
        - genetica
        - doppler
        - otra

        Args:
            tipo: Tipo de ecografía a filtrar

        Returns:
            Response: Lista de ecografías del tipo especificado
        """
        try:
            # Validar que el tipo existe
            tipos_validos = [t[0] for t in Ecografia.TIPOS_ECOGRAFIA]
            if tipo not in tipos_validos:
                return Response(
                    {'error': f'Tipo inválido. Tipos válidos: {tipos_validos}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Filtrar por tipo
            ecografias = self.get_queryset().filter(tipo_ecografia=tipo)

            # Paginación
            page = self.paginate_queryset(ecografias)
            if page is not None:
                serializer = EcografiaSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = EcografiaSerializer(ecografias, many=True)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error al filtrar por tipo: {str(e)}")
            return Response(
                {'error': 'Error al filtrar ecografías'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def ultimas(self, request):
        """
        Retorna las últimas ecografías realizadas.

        URL: /api/ecografias/ultimas/?limit=10

        Query params:
        - limit: Cantidad de ecografías a retornar (default: 10, max: 50)

        Returns:
            Response: Lista de últimas ecografías
        """
        try:
            # Obtener límite del query param
            limit = int(request.query_params.get('limit', 10))
            limit = min(limit, 50)  # Máximo 50

            # Obtener últimas ecografías
            ecografias = self.get_queryset().order_by('-fecha_ecografia')[:limit]

            serializer = EcografiaSerializer(ecografias, many=True)

            return Response({
                'count': ecografias.count(),
                'limit': limit,
                'results': serializer.data
            })

        except ValueError:
            return Response(
                {'error': 'El parámetro limit debe ser un número'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error al obtener últimas ecografías: {str(e)}")
            return Response(
                {'error': 'Error al obtener ecografías'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='biometria-evolution/(?P<embarazo_id>[^/.]+)')
    def biometria_evolution(self, request, embarazo_id=None):
        """
        Retorna la evolución de la biometría fetal en un embarazo.

        URL: /api/ecografias/biometria-evolution/{embarazo_id}/

        Útil para graficar curvas de crecimiento fetal.

        Args:
            embarazo_id: ID del embarazo

        Returns:
            Response: Datos de evolución biométrica con:
                - Fechas y semanas de gestación
                - DBP, CC, CA, LF en cada ecografía
                - Peso fetal estimado
                - Percentiles calculados
        """
        try:
            # Validar que el embarazo existe
            embarazo = get_object_or_404(Embarazo, id=embarazo_id, activo=True)

            # Obtener ecografías con biometría
            ecografias = self.queryset.filter(
                embarazo=embarazo
            ).exclude(
                diametro_biparietal__isnull=True,
                circunferencia_cefalica__isnull=True,
                circunferencia_abdominal__isnull=True,
                longitud_femur__isnull=True
            ).order_by('fecha_ecografia')

            # Preparar datos de evolución
            evolution_data = []
            for eco in ecografias:
                data_point = {
                    'fecha': eco.fecha_ecografia,
                    'semanas': eco.edad_gestacional_semanas,
                    'dias': eco.edad_gestacional_dias,
                    'edad_gestacional': f"{eco.edad_gestacional_semanas}+{eco.edad_gestacional_dias}",
                    'mediciones': {
                        'dbp': float(eco.diametro_biparietal) if eco.diametro_biparietal else None,
                        'cc': float(eco.circunferencia_cefalica) if eco.circunferencia_cefalica else None,
                        'ca': float(eco.circunferencia_abdominal) if eco.circunferencia_abdominal else None,
                        'lf': float(eco.longitud_femur) if eco.longitud_femur else None,
                        'peso_fetal': float(eco.peso_fetal_estimado) if eco.peso_fetal_estimado else None,
                        'ila': float(eco.indice_liquido_amniotico) if eco.indice_liquido_amniotico else None,
                    },
                    'tipo_ecografia': eco.get_tipo_ecografia_display(),
                }
                evolution_data.append(data_point)

            return Response({
                'embarazo_id': embarazo.id,
                'paciente': f"{embarazo.paciente.nombre} {embarazo.paciente.apellido}",
                'total_ecografias': len(evolution_data),
                'evolution': evolution_data
            })

        except Exception as e:
            logger.error(f"Error al obtener evolución biométrica: {str(e)}")
            return Response(
                {'error': 'Error al calcular evolución biométrica'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def validar_coherencia(self, request, pk=None):
        """
        Valida la coherencia de los datos de una ecografía.

        URL: /api/ecografias/{id}/validar_coherencia/

        Verifica:
        - Peso fetal acorde a edad gestacional
        - Mediciones biométricas proporcionales
        - ILA dentro de rangos normales
        - Grado placentario acorde a semanas

        Args:
            pk: ID de la ecografía

        Returns:
            Response: Resultado de validación con warnings si aplica
        """
        try:
            ecografia = self.get_object()
            warnings = []
            errors = []

            # Validar peso fetal vs edad gestacional
            if ecografia.peso_fetal_estimado and ecografia.edad_gestacional_semanas:
                semanas = ecografia.edad_gestacional_semanas
                peso = float(ecografia.peso_fetal_estimado)

                # Rangos aproximados de peso por semana (percentiles 10-90)
                rangos_peso = {
                    20: (250, 450),
                    24: (500, 750),
                    28: (900, 1300),
                    32: (1500, 2200),
                    36: (2200, 3200),
                    40: (2800, 4000),
                }

                # Encontrar rango más cercano
                semana_referencia = min(rangos_peso.keys(), key=lambda x: abs(x - semanas))
                if semana_referencia in rangos_peso:
                    min_peso, max_peso = rangos_peso[semana_referencia]
                    if peso < min_peso:
                        warnings.append(
                            f"Peso fetal ({peso}g) menor al esperado para {semanas} semanas "
                            f"(rango normal: {min_peso}-{max_peso}g). Evaluar restricción del crecimiento."
                        )
                    elif peso > max_peso:
                        warnings.append(
                            f"Peso fetal ({peso}g) mayor al esperado para {semanas} semanas "
                            f"(rango normal: {min_peso}-{max_peso}g). Evaluar macrosomía."
                        )

            # Validar ILA (Índice de Líquido Amniótico)
            if ecografia.indice_liquido_amniotico:
                ila = float(ecografia.indice_liquido_amniotico)
                if ila < 5:
                    warnings.append(
                        f"ILA bajo ({ila} cm). Normal: 5-25 cm. Indicativo de oligohidramnios."
                    )
                elif ila > 25:
                    warnings.append(
                        f"ILA alto ({ila} cm). Normal: 5-25 cm. Indicativo de polihidramnios."
                    )

            # Validar grado placentario vs edad gestacional
            if ecografia.grado_placentario and ecografia.edad_gestacional_semanas:
                semanas = ecografia.edad_gestacional_semanas
                grado = ecografia.grado_placentario

                # Grado III antes de 35 semanas es prematuro
                if grado == 'III' and semanas < 35:
                    warnings.append(
                        f"Grado placentario III a las {semanas} semanas es prematuro. "
                        "Evaluar insuficiencia placentaria."
                    )

            # Validar frecuencia cardíaca fetal
            if ecografia.frecuencia_cardiaca_fetal:
                fcf = ecografia.frecuencia_cardiaca_fetal
                if fcf < 110:
                    warnings.append(
                        f"Frecuencia cardíaca fetal baja ({fcf} lpm). Normal: 110-160 lpm. "
                        "Evaluar bradicardia fetal."
                    )
                elif fcf > 160:
                    warnings.append(
                        f"Frecuencia cardíaca fetal alta ({fcf} lpm). Normal: 110-160 lpm. "
                        "Evaluar taquicardia fetal."
                    )

            # Determinar estado general
            if errors:
                estado = 'error'
            elif warnings:
                estado = 'warning'
            else:
                estado = 'ok'

            return Response({
                'ecografia_id': ecografia.id,
                'estado': estado,
                'mensaje': 'Validación completada',
                'errores': errors,
                'advertencias': warnings,
                'total_advertencias': len(warnings),
                'total_errores': len(errors),
            })

        except Exception as e:
            logger.error(f"Error al validar coherencia: {str(e)}")
            return Response(
                {'error': 'Error al validar la ecografía'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
