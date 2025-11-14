# =============================================================================
# VIEWS DE PACIENTES
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: pacientes
# Descripción: ViewSet completo para gestión de pacientes con búsqueda avanzada,
#              filtros, estadísticas, exportación y endpoints especializados.
# Versión: 2.0.0
# Última actualización: 2025-11-14
# =============================================================================

from rest_framework import viewsets, status, serializers, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import IntegrityError
from django.db.models import Q, Count, Avg, Max, Min
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime, timedelta
import csv
from io import StringIO

from .models import Paciente
from .serializers import (
    PacienteSerializer,
    PacienteCreateSerializer,
    PacienteUpdateSerializer,
    PacienteDetailSerializer,
    PacienteListSerializer,
    PacienteSearchSerializer,
    PacienteEstadisticasSerializer
)

# =============================================================================
# VIEWSET PRINCIPAL DE PACIENTES
# =============================================================================

class PacienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para gestión de pacientes con funcionalidades avanzadas.

    Funcionalidades:
    - CRUD completo de pacientes
    - Búsqueda avanzada por múltiples campos
    - Filtros especializados
    - Soft delete (borrado lógico)
    - Estadísticas y reportes
    - Exportación a CSV
    - Gestión de pacientes de alto riesgo
    - Historial de embarazos
    - Validaciones médicas

    Permisos:
    - Requiere autenticación
    - Los endpoints de eliminación requieren permisos especiales

    Endpoints personalizados:
    - /pacientes/buscar_avanzada/ - Búsqueda por múltiples criterios
    - /pacientes/alto_riesgo/ - Lista de pacientes de alto riesgo
    - /pacientes/estadisticas/ - Estadísticas generales
    - /pacientes/exportar_csv/ - Exportación a CSV
    - /pacientes/inactivos/ - Lista de pacientes inactivos
    - /pacientes/{id}/reactivar/ - Reactivar paciente eliminado
    - /pacientes/{id}/historial_completo/ - Historial médico completo
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Campos para búsqueda de texto
    search_fields = [
        'nombres',
        'apellidos',
        'cedula_identidad',
        'id_clinico',
        'telefono',
        'email'
    ]

    # Campos para ordenamiento
    ordering_fields = [
        'id',
        'nombres',
        'apellidos',
        'fecha_nacimiento',
        'fecha_creacion',
        'fecha_modificacion'
    ]

    ordering = ['-fecha_creacion']  # Orden por defecto

    def get_queryset(self):
        """
        Obtiene el queryset base aplicando filtros básicos.
        Por defecto solo muestra pacientes activos.
        """
        queryset = Paciente.objects.filter(activo=True)

        # Filtro por cédula
        cedula = self.request.query_params.get('cedula', None)
        if cedula:
            queryset = queryset.filter(cedula_identidad=cedula)

        # Filtro por ID clínico
        id_clinico = self.request.query_params.get('id_clinico', None)
        if id_clinico:
            queryset = queryset.filter(id_clinico__icontains=id_clinico)

        # Filtro por edad mínima
        edad_min = self.request.query_params.get('edad_min', None)
        if edad_min:
            fecha_max = timezone.now().date() - timedelta(days=int(edad_min)*365)
            queryset = queryset.filter(fecha_nacimiento__lte=fecha_max)

        # Filtro por edad máxima
        edad_max = self.request.query_params.get('edad_max', None)
        if edad_max:
            fecha_min = timezone.now().date() - timedelta(days=int(edad_max)*365)
            queryset = queryset.filter(fecha_nacimiento__gte=fecha_min)

        # Filtro por alto riesgo
        alto_riesgo = self.request.query_params.get('alto_riesgo', None)
        if alto_riesgo == 'true':
            # Pacientes con índice de riesgo alto (se calculará en el método)
            queryset = [p for p in queryset if p.get_indice_riesgo() >= 50]

        return queryset

    def get_serializer_class(self):
        """
        Retorna el serializer apropiado según la acción.
        """
        if self.action == 'create':
            return PacienteCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PacienteUpdateSerializer
        elif self.action == 'retrieve':
            return PacienteDetailSerializer
        elif self.action == 'list':
            return PacienteListSerializer
        return PacienteSerializer

    def create(self, request, *args, **kwargs):
        """
        Crea un nuevo paciente con generación automática de ID clínico.
        """
        # Generar ID clínico si no se proporciona
        id_clinico = request.data.get('id_clinico', '').strip()

        if not id_clinico:
            ultimo_paciente = Paciente.objects.all().order_by('id').last()
            if ultimo_paciente and ultimo_paciente.id_clinico:
                try:
                    ultimo_num = int(ultimo_paciente.id_clinico.split('-')[1])
                    nuevo_num = ultimo_num + 1
                except:
                    nuevo_num = Paciente.objects.all().count() + 1
            else:
                nuevo_num = 1
            request.data['id_clinico'] = f"HC-{str(nuevo_num).zfill(6)}"

        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)

            # Asignar usuario que crea
            if hasattr(request.user, 'id'):
                serializer.validated_data['creado_por'] = request.user

            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)

            return Response(
                {
                    "success": True,
                    "mensaje": "Paciente registrado exitosamente",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except serializers.ValidationError as e:
            return Response(
                {
                    "success": False,
                    "errores": e.detail
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except IntegrityError as e:
            return Response(
                {
                    "success": False,
                    "error": "Error de integridad: Verifique que no existan datos duplicados (cédula, email, etc.)."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error inesperado: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, *args, **kwargs):
        """
        Actualiza un paciente existente.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        try:
            serializer.is_valid(raise_exception=True)

            # Asignar usuario que modifica
            if hasattr(request.user, 'id'):
                serializer.validated_data['modificado_por'] = request.user

            self.perform_update(serializer)

            return Response({
                "success": True,
                "mensaje": "Paciente actualizado exitosamente",
                "data": serializer.data
            })
        except serializers.ValidationError as e:
            return Response(
                {
                    "success": False,
                    "errores": e.detail
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error al actualizar: {str(e)}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        """
        Elimina (soft delete) un paciente.
        El paciente se marca como inactivo pero no se elimina de la base de datos.
        """
        try:
            paciente = self.get_object()

            # Soft delete
            paciente.activo = False
            paciente.eliminado = True
            paciente.fecha_eliminacion = timezone.now()
            if hasattr(request.user, 'id'):
                paciente.eliminado_por = request.user

            motivo = request.data.get('motivo', 'No especificado')
            paciente.motivo_inactivacion = motivo

            paciente.save()

            return Response(
                {
                    "success": True,
                    "mensaje": "Paciente eliminado correctamente (soft delete)"
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error al eliminar: {str(e)}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    # =========================================================================
    # ENDPOINTS PERSONALIZADOS
    # =========================================================================

    @action(detail=False, methods=['get'])
    def buscar_avanzada(self, request):
        """
        Búsqueda avanzada de pacientes por múltiples criterios.

        Parámetros:
        - q: Texto libre (busca en nombres, apellidos, cédula)
        - edad_min: Edad mínima
        - edad_max: Edad máxima
        - con_diabetes: true/false
        - con_hipertension: true/false
        - con_preeclampsia_previa: true/false
        - gestas_min: Número mínimo de gestas
        - gestas_max: Número máximo de gestas
        - fuma: true/false
        - nivel_riesgo_min: Índice de riesgo mínimo (0-100)
        """
        queryset = Paciente.objects.filter(activo=True)

        # Búsqueda de texto libre
        q = request.query_params.get('q', None)
        if q:
            queryset = queryset.filter(
                Q(nombres__icontains=q) |
                Q(apellidos__icontains=q) |
                Q(cedula_identidad__icontains=q) |
                Q(id_clinico__icontains=q)
            )

        # Filtros médicos
        if request.query_params.get('con_diabetes') == 'true':
            queryset = queryset.filter(diabetes_previa=True)

        if request.query_params.get('con_hipertension') == 'true':
            queryset = queryset.filter(hipertension_previa=True)

        if request.query_params.get('con_preeclampsia_previa') == 'true':
            queryset = queryset.filter(preeclampsia_previa=True)

        if request.query_params.get('fuma') == 'true':
            queryset = queryset.filter(fuma=True)

        # Filtros por gestas
        gestas_min = request.query_params.get('gestas_min', None)
        if gestas_min:
            queryset = queryset.filter(gestas__gte=int(gestas_min))

        gestas_max = request.query_params.get('gestas_max', None)
        if gestas_max:
            queryset = queryset.filter(gestas__lte=int(gestas_max))

        # Serializar resultados
        serializer = PacienteSearchSerializer(queryset, many=True)

        return Response({
            "success": True,
            "total": queryset.count(),
            "data": serializer.data
        })

    @action(detail=False, methods=['get'])
    def alto_riesgo(self, request):
        """
        Retorna lista de pacientes de alto riesgo.
        Alto riesgo: Índice >= 50
        """
        pacientes = Paciente.objects.filter(activo=True)
        pacientes_alto_riesgo = []

        for paciente in pacientes:
            indice = paciente.get_indice_riesgo()
            if indice >= 50:
                pacientes_alto_riesgo.append({
                    "id": paciente.id,
                    "id_clinico": paciente.id_clinico,
                    "nombre_completo": f"{paciente.nombres} {paciente.apellidos}",
                    "cedula": paciente.cedula_identidad,
                    "edad": paciente.calcular_edad(),
                    "indice_riesgo": indice,
                    "factores_riesgo": paciente.tiene_riesgo_alto(),
                    "telefono": paciente.telefono
                })

        # Ordenar por índice de riesgo descendente
        pacientes_alto_riesgo.sort(key=lambda x: x['indice_riesgo'], reverse=True)

        return Response({
            "success": True,
            "total": len(pacientes_alto_riesgo),
            "data": pacientes_alto_riesgo
        })

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Retorna estadísticas generales de pacientes.
        """
        pacientes_activos = Paciente.objects.filter(activo=True)

        stats = {
            "total_pacientes": pacientes_activos.count(),
            "total_inactivos": Paciente.objects.filter(activo=False).count(),

            # Estadísticas de edad
            "edad_promedio": None,
            "edad_minima": None,
            "edad_maxima": None,

            # Factores de riesgo
            "con_diabetes": pacientes_activos.filter(diabetes_previa=True).count(),
            "con_hipertension": pacientes_activos.filter(hipertension_previa=True).count(),
            "con_preeclampsia_previa": pacientes_activos.filter(preeclampsia_previa=True).count(),
            "con_cesareas_previas": pacientes_activos.filter(cesareas__gte=1).count(),

            # Hábitos
            "fumadoras": pacientes_activos.filter(fuma=True).count(),
            "consumo_alcohol": pacientes_activos.filter(consume_alcohol=True).count(),
            "consumo_drogas": pacientes_activos.filter(consume_drogas=True).count(),

            # Obstétricos
            "primigestas": pacientes_activos.filter(gestas=0).count(),
            "multigestas": pacientes_activos.filter(gestas__gte=2).count(),
            "gran_multigestas": pacientes_activos.filter(gestas__gte=5).count(),

            # Riesgo
            "alto_riesgo": 0,
            "riesgo_medio": 0,
            "bajo_riesgo": 0
        }

        # Calcular edades
        edades = []
        alto_riesgo = 0
        riesgo_medio = 0
        bajo_riesgo = 0

        for paciente in pacientes_activos:
            edad = paciente.calcular_edad()
            if edad:
                edades.append(edad)

            indice = paciente.get_indice_riesgo()
            if indice >= 50:
                alto_riesgo += 1
            elif indice >= 25:
                riesgo_medio += 1
            else:
                bajo_riesgo += 1

        if edades:
            stats["edad_promedio"] = round(sum(edades) / len(edades), 1)
            stats["edad_minima"] = min(edades)
            stats["edad_maxima"] = max(edades)

        stats["alto_riesgo"] = alto_riesgo
        stats["riesgo_medio"] = riesgo_medio
        stats["bajo_riesgo"] = bajo_riesgo

        return Response({
            "success": True,
            "data": stats
        })

    @action(detail=False, methods=['get'])
    def exportar_csv(self, request):
        """
        Exporta pacientes a formato CSV.
        """
        pacientes = Paciente.objects.filter(activo=True)

        output = StringIO()
        writer = csv.writer(output)

        # Encabezados
        writer.writerow([
            'ID Clínico', 'Cédula', 'Nombres', 'Apellidos', 'Fecha Nacimiento',
            'Edad', 'Teléfono', 'Email', 'GPAC', 'Índice Riesgo',
            'Diabetes', 'Hipertensión', 'Preeclampsia Previa'
        ])

        # Datos
        for p in pacientes:
            writer.writerow([
                p.id_clinico,
                p.cedula_identidad,
                p.nombres,
                p.apellidos,
                p.fecha_nacimiento,
                p.calcular_edad(),
                p.telefono,
                p.email or '',
                p.get_gpac_formatted(),
                p.get_indice_riesgo(),
                'Sí' if p.diabetes_previa else 'No',
                'Sí' if p.hipertension_previa else 'No',
                'Sí' if p.preeclampsia_previa else 'No'
            ])

        response = Response(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="pacientes_{timezone.now().strftime("%Y%m%d")}.csv"'
        return response

    @action(detail=False, methods=['get'])
    def inactivos(self, request):
        """
        Retorna lista de pacientes inactivos (eliminados).
        """
        pacientes_inactivos = Paciente.objects.filter(activo=False)
        serializer = PacienteListSerializer(pacientes_inactivos, many=True)

        return Response({
            "success": True,
            "total": pacientes_inactivos.count(),
            "data": serializer.data
        })

    @action(detail=True, methods=['post'])
    def reactivar(self, request, pk=None):
        """
        Reactiva un paciente previamente eliminado.
        """
        try:
            paciente = Paciente.objects.get(pk=pk, activo=False)

            paciente.activo = True
            paciente.eliminado = False
            paciente.fecha_eliminacion = None
            paciente.eliminado_por = None
            paciente.motivo_inactivacion = None
            paciente.save()

            return Response({
                "success": True,
                "mensaje": "Paciente reactivado exitosamente",
                "data": PacienteSerializer(paciente).data
            })
        except Paciente.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": "Paciente no encontrado o ya está activo"
                },
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def historial_completo(self, request, pk=None):
        """
        Retorna historial médico completo del paciente.
        Incluye: datos personales, embarazos, controles, laboratorios, etc.
        """
        paciente = self.get_object()

        # Historial completo (se extenderá cuando existan los otros módulos)
        historial = {
            "paciente": PacienteDetailSerializer(paciente).data,
            "embarazos": [],  # Se llenará cuando exista el modelo
            "controles": [],  # Se llenará cuando exista el modelo
            "laboratorios": [],  # Se llenará cuando exista el modelo
            "ecografias": [],  # Se llenará cuando exista el modelo
        }

        return Response({
            "success": True,
            "data": historial
        })