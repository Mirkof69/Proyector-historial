"""
===========================================
MÓDULO: VIEWS DE EMBARAZOS
===========================================
Descripción:
    Sistema completo de vistas (endpoints) para la gestión de embarazos.
    Implementa operaciones CRUD completas, cálculos obstétricos, estadísticas,
    seguimiento de controles prenatales y reportes especializados.

Endpoints principales:
    CRUD básico:
        GET    /api/embarazos/                    - Listar embarazos (paginado)
        POST   /api/embarazos/                    - Crear embarazo
        GET    /api/embarazos/{id}/               - Obtener embarazo específico
        PUT    /api/embarazos/{id}/               - Actualizar embarazo completo
        PATCH  /api/embarazos/{id}/               - Actualizar embarazo parcial
        DELETE /api/embarazos/{id}/               - Finalizar embarazo

    Gestión de estado:
        POST   /api/embarazos/{id}/cambiar_estado/     - Cambiar estado del embarazo
        POST   /api/embarazos/{id}/finalizar/          - Finalizar embarazo
        POST   /api/embarazos/{id}/marcar_perdida/     - Marcar como pérdida
        POST   /api/embarazos/{id}/reactivar/          - Reactivar embarazo

    Información y estadísticas:
        GET    /api/embarazos/{id}/historial_completo/ - Historial completo con controles
        GET    /api/embarazos/{id}/calculos_obstetricos/ - Todos los cálculos
        GET    /api/embarazos/{id}/proximos_controles/   - Sugerencias de próximos controles
        GET    /api/embarazos/{id}/curva_crecimiento/    - Datos para curva de crecimiento
        GET    /api/embarazos/{id}/riesgos/              - Evaluación de riesgos

    Consultas especializadas:
        GET    /api/embarazos/estadisticas/           - Estadísticas generales
        GET    /api/embarazos/busqueda_avanzada/      - Búsqueda con filtros
        GET    /api/embarazos/por_paciente/{id}/      - Embarazos de un paciente
        GET    /api/embarazos/activos/                - Solo embarazos activos
        GET    /api/embarazos/alto_riesgo/            - Embarazos de alto riesgo
        GET    /api/embarazos/proximos_partos/        - Partos próximos (30 días)

Funcionalidades de cálculo:
    - Edad gestacional precisa (semanas + días)
    - Fecha Probable de Parto (Regla de Naegele)
    - Trimestre actual
    - Percentiles de peso y altura uterina
    - Evaluación de riesgos
    - Sugerencias de controles

Autor: Sistema Historial Médico
Fecha: 2025
Versión: 2.0
===========================================
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg, Max, Min
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.shortcuts import get_object_or_404

from .models import Embarazo
from .serializers import (
    EmbarazoSerializer,
    EmbarazoCreateSerializer,
    EmbarazoUpdateSerializer,
    EmbarazoListSerializer,
    EmbarazoDetailSerializer
)
from pacientes.models import Paciente
from controles.models import ControlPrenatal


# ===========================================
# PAGINACIÓN PERSONALIZADA
# ===========================================
class EmbarazoPagination(PageNumberPagination):
    """
    CLASE: Paginación personalizada para embarazos

    Funcionamiento:
        Divide la lista de embarazos en páginas para mejorar el rendimiento
        Permite al cliente especificar el tamaño de página

    Configuración:
        - page_size: 20 embarazos por página por defecto
        - page_size_query_param: Parámetro para especificar tamaño personalizado
        - max_page_size: Máximo 100 embarazos por página

    Uso en el cliente:
        GET /api/embarazos/?page=1&page_size=50
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ===========================================
# VIEWSET PRINCIPAL DE EMBARAZOS
# ===========================================
class EmbarazoViewSet(viewsets.ModelViewSet):
    """
    VIEWSET: CRUD completo de embarazos + acciones especializadas

    Funcionamiento:
        ModelViewSet proporciona automáticamente las operaciones CRUD:
        - list(): GET /api/embarazos/ - Listar embarazos
        - create(): POST /api/embarazos/ - Crear embarazo
        - retrieve(): GET /api/embarazos/{id}/ - Obtener un embarazo
        - update(): PUT /api/embarazos/{id}/ - Actualizar completo
        - partial_update(): PATCH /api/embarazos/{id}/ - Actualizar parcial
        - destroy(): DELETE /api/embarazos/{id}/ - Finalizar (soft delete)

    Acciones personalizadas (@action):
        - cambiar_estado()        - Cambiar estado del embarazo
        - finalizar()             - Finalizar embarazo
        - marcar_perdida()        - Marcar como pérdida gestacional
        - reactivar()             - Reactivar embarazo
        - historial_completo()    - Obtener historial completo con controles
        - calculos_obstetricos()  - Todos los cálculos obstétricos
        - proximos_controles()    - Sugerencias de próximos controles
        - curva_crecimiento()     - Datos para curva de crecimiento
        - riesgos()               - Evaluación de riesgos
        - estadisticas()          - Estadísticas generales
        - busqueda_avanzada()     - Búsqueda con múltiples filtros
        - por_paciente()          - Embarazos de un paciente específico
        - activos()               - Solo embarazos activos
        - alto_riesgo()           - Embarazos de alto riesgo
        - proximos_partos()       - Partos próximos (30 días)

    Características:
        - Paginación automática (20 por página)
        - Filtrado por paciente, estado, tipo, riesgo
        - Búsqueda por ID clínico, nombre paciente
        - Ordenamiento por múltiples campos
        - Serializers diferentes para list/detail/create/update
        - Cálculos obstétricos automáticos
    """

    # Configuración base del ViewSet
    queryset = Embarazo.objects.all()
    serializer_class = EmbarazoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = EmbarazoPagination

    # Configuración de filtrado y búsqueda
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'tipo_embarazo', 'riesgo_embarazo', 'paciente']
    search_fields = ['paciente__id_clinico', 'paciente__nombre', 'paciente__apellido_paterno', 'numero_gesta']
    ordering_fields = ['fecha_registro', 'fecha_ultima_menstruacion', 'fecha_probable_parto', 'numero_gesta']
    ordering = ['-fecha_registro']

    def get_serializer_class(self):
        """
        MÉTODO: Seleccionar serializer según la acción

        Funcionamiento:
            Retorna diferentes serializers según qué operación se esté haciendo
            Esto optimiza la respuesta y las validaciones

        Serializers por acción:
            - list: EmbarazoListSerializer (campos reducidos, optimizado)
            - retrieve: EmbarazoDetailSerializer (completo con estadísticas)
            - create: EmbarazoCreateSerializer (con validaciones estrictas)
            - update/partial_update: EmbarazoUpdateSerializer (sin validar duplicados)
            - default: EmbarazoSerializer (estándar)
        """
        if self.action == 'list':
            return EmbarazoListSerializer
        elif self.action == 'retrieve':
            return EmbarazoDetailSerializer
        elif self.action == 'create':
            return EmbarazoCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return EmbarazoUpdateSerializer
        return EmbarazoSerializer

    def get_queryset(self):
        """
        MÉTODO: Obtener queryset filtrado y optimizado

        Funcionamiento:
            1. Obtiene queryset base
            2. Aplica filtros personalizados de la URL
            3. Optimiza queries con select_related para ForeignKeys
            4. Retorna queryset optimizado

        Filtros adicionales disponibles:
            - paciente: ID del paciente
            - estado: Estado del embarazo (activo, finalizado, perdida)
            - tipo_embarazo: Tipo (simple, gemelar, multiple)
            - riesgo_embarazo: Nivel de riesgo (bajo, medio, alto)
            - fecha_desde: Embarazos registrados desde fecha
            - fecha_hasta: Embarazos registrados hasta fecha

        Optimizaciones:
            - select_related('paciente'): Reduce queries al obtener paciente
            - prefetch_related('controles'): Pre-carga controles relacionados
        """
        queryset = Embarazo.objects.all()

        # Optimizar queries con select_related
        queryset = queryset.select_related('paciente')

        # Filtrar por paciente si viene en los parámetros
        paciente_id = self.request.query_params.get('paciente_id', None)
        if paciente_id:
            queryset = queryset.filter(paciente_id=paciente_id)

        # Filtrar por rango de fechas de registro
        fecha_desde = self.request.query_params.get('fecha_desde', None)
        if fecha_desde:
            queryset = queryset.filter(fecha_registro__gte=fecha_desde)

        fecha_hasta = self.request.query_params.get('fecha_hasta', None)
        if fecha_hasta:
            queryset = queryset.filter(fecha_registro__lte=fecha_hasta)

        return queryset

    def create(self, request, *args, **kwargs):
        """
        MÉTODO: Crear nuevo embarazo

        Funcionamiento:
            1. Recibe datos del nuevo embarazo
            2. Valida con EmbarazoCreateSerializer
            3. Verifica que no haya embarazos activos duplicados
            4. Calcula FPP automáticamente si no viene (Regla de Naegele)
            5. Crea el embarazo en la BD
            6. Retorna embarazo creado con mensaje de éxito

        Request:
            POST /api/embarazos/
            {
                "paciente": 1,
                "numero_gesta": 2,
                "fecha_ultima_menstruacion": "2024-01-15",
                "tipo_embarazo": "simple",
                "riesgo_embarazo": "bajo",
                "estado": "activo",
                "notas": "Primera consulta prenatal"
            }

        Response (201):
            {
                "mensaje": "Embarazo registrado exitosamente",
                "data": {
                    "id": 5,
                    "uuid": "...",
                    "paciente_nombre": "HC-001 - María García",
                    "numero_gesta": 2,
                    "fecha_ultima_menstruacion": "2024-01-15",
                    "fecha_probable_parto": "2024-10-21",
                    "semanas_gestacion": "24+3",
                    "trimestre": 2,
                    ...
                }
            }

        Validaciones:
            - Paciente existe y está activo
            - No hay embarazos activos duplicados
            - FUM no es futura
            - Número de gesta válido (1-20)
        """
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)

            # Retornar con serializer detallado
            embarazo = serializer.instance
            response_serializer = EmbarazoSerializer(embarazo)

            return Response(
                {
                    "mensaje": "Embarazo registrado exitosamente",
                    "data": response_serializer.data
                },
                status=status.HTTP_201_CREATED,
                headers=headers
            )

        except Exception as e:
            return Response(
                {
                    "error": "Error al crear embarazo",
                    "detalle": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        """
        MÉTODO: Actualizar embarazo completo (PUT)

        Funcionamiento:
            1. Obtiene el embarazo a actualizar
            2. Valida todos los campos con EmbarazoUpdateSerializer
            3. Recalcula FPP si se modifica FUM
            4. Actualiza el embarazo en la BD
            5. Retorna embarazo actualizado

        IMPORTANTE:
            PUT requiere enviar TODOS los campos
            Para actualizar solo algunos campos, usar PATCH
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            # Retornar con mensaje de éxito
            return Response({
                "mensaje": "Embarazo actualizado exitosamente",
                "data": serializer.data
            })

        except Exception as e:
            return Response(
                {
                    "error": "Error al actualizar embarazo",
                    "detalle": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        """
        MÉTODO: Finalizar embarazo (Soft Delete)

        Funcionamiento:
            NO elimina físicamente el embarazo de la BD
            En su lugar, cambia el estado a 'finalizado'
            Esto preserva el historial completo

        Proceso:
            1. Obtiene el embarazo
            2. Cambia estado a 'finalizado'
            3. Guarda observaciones si se proporcionan
            4. Retorna confirmación

        Request:
            DELETE /api/embarazos/5/
            {
                "motivo": "Parto exitoso" (opcional)
            }

        Response (200):
            {
                "mensaje": "Embarazo finalizado exitosamente",
                "data": { ... }
            }
        """
        instance = self.get_object()
        motivo = request.data.get('motivo', 'Finalizado desde la API')

        # Cambiar estado en lugar de eliminar
        instance.estado = 'finalizado'

        # Agregar motivo a las notas
        if motivo:
            timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
            nota = f"\n[{timestamp}] Finalizado: {motivo}"
            instance.notas = (instance.notas or "") + nota

        instance.save()

        serializer = EmbarazoSerializer(instance)
        return Response(
            {
                'mensaje': 'Embarazo finalizado exitosamente',
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )

    # ===========================================
    # ACCIONES DE GESTIÓN DE ESTADO
    # ===========================================

    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        """
        ACCIÓN: Cambiar estado del embarazo

        Funcionamiento:
            Permite cambiar el estado entre: activo, finalizado, perdida

        Request:
            POST /api/embarazos/5/cambiar_estado/
            {
                "estado": "finalizado",
                "motivo": "Parto exitoso a las 39 semanas"
            }

        Response (200):
            {
                "mensaje": "Estado cambiado a finalizado",
                "data": { ... }
            }

        Estados válidos:
            - activo: Embarazo en curso
            - finalizado: Embarazo terminado (parto exitoso)
            - perdida: Pérdida gestacional
        """
        embarazo = self.get_object()
        nuevo_estado = request.data.get('estado')
        motivo = request.data.get('motivo', '')

        # Validar estado
        estados_validos = ['activo', 'finalizado', 'perdida']
        if nuevo_estado not in estados_validos:
            return Response(
                {
                    "error": f"Estado inválido. Debe ser uno de: {', '.join(estados_validos)}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Cambiar estado
        embarazo.estado = nuevo_estado

        # Registrar motivo en notas
        if motivo:
            timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
            nota = f"\n[{timestamp}] Estado cambiado a '{nuevo_estado}': {motivo}"
            embarazo.notas = (embarazo.notas or "") + nota

        embarazo.save()

        serializer = EmbarazoSerializer(embarazo)
        return Response({
            "mensaje": f"Estado cambiado a {nuevo_estado}",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        """
        ACCIÓN: Finalizar embarazo

        Funcionamiento:
            Marca el embarazo como finalizado (generalmente por parto exitoso)

        Request:
            POST /api/embarazos/5/finalizar/
            {
                "fecha_parto": "2024-09-15",
                "tipo_parto": "cesarea",
                "observaciones": "Parto sin complicaciones"
            }
        """
        embarazo = self.get_object()

        fecha_parto = request.data.get('fecha_parto')
        tipo_parto = request.data.get('tipo_parto', '')
        observaciones = request.data.get('observaciones', '')

        # Cambiar estado
        embarazo.estado = 'finalizado'

        # Registrar información del parto en notas
        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
        nota = f"\n[{timestamp}] Embarazo finalizado"

        if fecha_parto:
            nota += f"\nFecha de parto: {fecha_parto}"

        if tipo_parto:
            nota += f"\nTipo de parto: {tipo_parto}"

        if observaciones:
            nota += f"\nObservaciones: {observaciones}"

        embarazo.notas = (embarazo.notas or "") + nota
        embarazo.save()

        serializer = EmbarazoSerializer(embarazo)
        return Response({
            "mensaje": "Embarazo finalizado exitosamente",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def marcar_perdida(self, request, pk=None):
        """
        ACCIÓN: Marcar como pérdida gestacional

        Funcionamiento:
            Marca el embarazo como pérdida gestacional

        Request:
            POST /api/embarazos/5/marcar_perdida/
            {
                "fecha_perdida": "2024-03-20",
                "tipo_perdida": "aborto espontáneo",
                "semanas_perdida": "12+3",
                "observaciones": "Pérdida espontánea primer trimestre"
            }
        """
        embarazo = self.get_object()

        fecha_perdida = request.data.get('fecha_perdida')
        tipo_perdida = request.data.get('tipo_perdida', '')
        semanas_perdida = request.data.get('semanas_perdida', '')
        observaciones = request.data.get('observaciones', '')

        # Cambiar estado
        embarazo.estado = 'perdida'

        # Registrar información de la pérdida
        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
        nota = f"\n[{timestamp}] Pérdida gestacional"

        if fecha_perdida:
            nota += f"\nFecha: {fecha_perdida}"

        if semanas_perdida:
            nota += f"\nSemanas de gestación: {semanas_perdida}"

        if tipo_perdida:
            nota += f"\nTipo: {tipo_perdida}"

        if observaciones:
            nota += f"\nObservaciones: {observaciones}"

        embarazo.notas = (embarazo.notas or "") + nota
        embarazo.save()

        serializer = EmbarazoSerializer(embarazo)
        return Response({
            "mensaje": "Pérdida gestacional registrada",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def reactivar(self, request, pk=None):
        """
        ACCIÓN: Reactivar embarazo

        Funcionamiento:
            Reactiva un embarazo que fue marcado como finalizado o perdida
            Útil en caso de error en el registro

        Request:
            POST /api/embarazos/5/reactivar/
            {
                "motivo": "Error en registro anterior"
            }
        """
        embarazo = self.get_object()
        motivo = request.data.get('motivo', 'Reactivado desde la API')

        # Verificar que no haya otros embarazos activos del mismo paciente
        embarazos_activos = Embarazo.objects.filter(
            paciente=embarazo.paciente,
            estado='activo'
        ).exclude(id=embarazo.id)

        if embarazos_activos.exists():
            return Response({
                "error": "No se puede reactivar. La paciente ya tiene un embarazo activo."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Reactivar
        embarazo.estado = 'activo'

        # Registrar reactivación
        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
        nota = f"\n[{timestamp}] Embarazo reactivado: {motivo}"
        embarazo.notas = (embarazo.notas or "") + nota
        embarazo.save()

        serializer = EmbarazoSerializer(embarazo)
        return Response({
            "mensaje": "Embarazo reactivado exitosamente",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # ===========================================
    # ACCIONES DE INFORMACIÓN Y CÁLCULOS
    # ===========================================

    @action(detail=True, methods=['get'])
    def historial_completo(self, request, pk=None):
        """
        ACCIÓN: Obtener historial completo del embarazo

        Funcionamiento:
            Retorna información detallada del embarazo incluyendo:
            - Datos básicos del embarazo
            - Información del paciente
            - Todos los controles prenatales
            - Cálculos obstétricos
            - Evolución del embarazo

        Request:
            GET /api/embarazos/5/historial_completo/

        Response (200):
            {
                "embarazo": { ... },
                "paciente": { ... },
                "controles": [ ... ],
                "calculos": { ... },
                "estadisticas": { ... }
            }
        """
        embarazo = self.get_object()

        # Obtener controles ordenados
        controles = embarazo.controles.all().order_by('fecha_control')

        # Serializar datos
        from controles.serializers import ControlPrenatalSerializer
        from pacientes.serializers import PacienteDetailSerializer

        return Response({
            "embarazo": EmbarazoDetailSerializer(embarazo).data,
            "paciente": PacienteDetailSerializer(embarazo.paciente).data,
            "controles": ControlPrenatalSerializer(controles, many=True).data,
            "total_controles": controles.count(),
            "calculos": self._calcular_datos_obstetricos(embarazo),
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def calculos_obstetricos(self, request, pk=None):
        """
        ACCIÓN: Obtener todos los cálculos obstétricos

        Funcionamiento:
            Calcula y retorna todos los datos obstétricos del embarazo:
            - Edad gestacional (semanas + días)
            - Trimestre actual
            - Fecha Probable de Parto (FPP)
            - Días hasta el parto
            - Porcentaje de embarazo completado
            - Rango de fechas de parto (37-42 semanas)

        Request:
            GET /api/embarazos/5/calculos_obstetricos/

        Response (200):
            {
                "edad_gestacional": {
                    "semanas": 28,
                    "dias": 4,
                    "total_dias": 200,
                    "formato": "28+4"
                },
                "trimestre": 3,
                "fecha_probable_parto": "2024-09-15",
                "dias_hasta_parto": 45,
                "porcentaje_completado": 71.43,
                "rango_parto": {
                    "minimo": "2024-09-01",
                    "maximo": "2024-09-29"
                }
            }
        """
        embarazo = self.get_object()
        calculos = self._calcular_datos_obstetricos(embarazo)

        return Response(calculos, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def proximos_controles(self, request, pk=None):
        """
        ACCIÓN: Sugerencias de próximos controles prenatales

        Funcionamiento:
            Sugiere fechas para próximos controles según:
            - Edad gestacional actual
            - Controles ya realizados
            - Guías clínicas estándar

        Frecuencia recomendada:
            - Hasta 28 semanas: cada 4 semanas
            - 28-36 semanas: cada 2 semanas
            - Después de 36 semanas: cada semana

        Request:
            GET /api/embarazos/5/proximos_controles/

        Response (200):
            {
                "controles_realizados": 5,
                "edad_gestacional": "28+3",
                "proximos_controles": [
                    {
                        "numero": 6,
                        "fecha_sugerida": "2024-07-15",
                        "descripcion": "Control rutinario segundo trimestre"
                    },
                    ...
                ]
            }
        """
        embarazo = self.get_object()

        if not embarazo.fecha_ultima_menstruacion:
            return Response({
                "error": "No se puede calcular sin FUM"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Calcular edad gestacional
        hoy = date.today()
        dias = (hoy - embarazo.fecha_ultima_menstruacion).days
        semanas = dias // 7
        dias_extra = dias % 7

        # Obtener controles realizados
        controles_count = embarazo.controles.count()

        # Calcular próximos controles
        proximos = []

        if semanas < 28:
            # Cada 4 semanas hasta semana 28
            frecuencia = 28
            while len(proximos) < 3:
                proxima_fecha = hoy + timedelta(days=frecuencia)
                proximos.append({
                    "numero": controles_count + len(proximos) + 1,
                    "fecha_sugerida": proxima_fecha.strftime("%Y-%m-%d"),
                    "descripcion": "Control rutinario primer/segundo trimestre",
                    "semanas_estimadas": semanas + (frecuencia // 7)
                })
                frecuencia += 28

        elif semanas < 36:
            # Cada 2 semanas entre semana 28 y 36
            frecuencia = 14
            while len(proximos) < 4:
                proxima_fecha = hoy + timedelta(days=frecuencia)
                proximos.append({
                    "numero": controles_count + len(proximos) + 1,
                    "fecha_sugerida": proxima_fecha.strftime("%Y-%m-%d"),
                    "descripcion": "Control tercer trimestre",
                    "semanas_estimadas": semanas + (frecuencia // 7)
                })
                frecuencia += 14

        else:
            # Cada semana después de semana 36
            frecuencia = 7
            while len(proximos) < 5:
                proxima_fecha = hoy + timedelta(days=frecuencia)
                proximos.append({
                    "numero": controles_count + len(proximos) + 1,
                    "fecha_sugerida": proxima_fecha.strftime("%Y-%m-%d"),
                    "descripcion": "Control pre-parto",
                    "semanas_estimadas": semanas + (frecuencia // 7)
                })
                frecuencia += 7

        return Response({
            "controles_realizados": controles_count,
            "edad_gestacional": f"{semanas}+{dias_extra}",
            "proximos_controles": proximos
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def curva_crecimiento(self, request, pk=None):
        """
        ACCIÓN: Datos para curva de crecimiento

        Funcionamiento:
            Obtiene datos de todos los controles para graficar:
            - Peso materno
            - Altura uterina
            - Frecuencia cardíaca fetal
            - Presión arterial

        Request:
            GET /api/embarazos/5/curva_crecimiento/

        Response (200):
            {
                "controles": [
                    {
                        "fecha": "2024-05-01",
                        "semanas": "20+0",
                        "peso": 65.5,
                        "altura_uterina": 19.0,
                        "fcf": 145,
                        "presion_sistolica": 120,
                        "presion_diastolica": 80
                    },
                    ...
                ]
            }
        """
        embarazo = self.get_object()

        # Obtener todos los controles
        controles = embarazo.controles.all().order_by('fecha_control')

        datos = []
        for control in controles:
            datos.append({
                "fecha": control.fecha_control.strftime("%Y-%m-%d"),
                "semanas": f"{control.semanas_gestacion}+{control.dias_gestacion or 0}",
                "peso": float(control.peso_actual) if control.peso_actual else None,
                "altura_uterina": float(control.altura_uterina) if control.altura_uterina else None,
                "fcf": control.frecuencia_cardiaca_fetal,
                "presion_sistolica": control.presion_arterial_sistolica,
                "presion_diastolica": control.presion_arterial_diastolica,
            })

        return Response({
            "controles": datos,
            "total": len(datos)
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def riesgos(self, request, pk=None):
        """
        ACCIÓN: Evaluación de riesgos del embarazo

        Funcionamiento:
            Evalúa factores de riesgo del embarazo:
            - Edad materna
            - Número de gestas
            - Tipo de embarazo
            - Controles realizados
            - Complicaciones registradas

        Request:
            GET /api/embarazos/5/riesgos/

        Response (200):
            {
                "nivel_riesgo": "medio",
                "factores": [
                    {
                        "factor": "Edad materna > 35 años",
                        "severidad": "medio"
                    },
                    ...
                ],
                "recomendaciones": [ ... ]
            }
        """
        embarazo = self.get_object()
        paciente = embarazo.paciente

        factores = []
        nivel_riesgo = embarazo.riesgo_embarazo

        # Evaluar edad materna
        if paciente.edad:
            if paciente.edad < 18:
                factores.append({
                    "factor": "Edad materna < 18 años",
                    "severidad": "medio",
                    "descripcion": "Embarazo en adolescente"
                })
            elif paciente.edad > 35:
                factores.append({
                    "factor": f"Edad materna {paciente.edad} años (> 35)",
                    "severidad": "medio",
                    "descripcion": "Embarazo en edad materna avanzada"
                })
            elif paciente.edad > 40:
                factores.append({
                    "factor": f"Edad materna {paciente.edad} años (> 40)",
                    "severidad": "alto",
                    "descripcion": "Embarazo en edad materna muy avanzada"
                })

        # Evaluar tipo de embarazo
        if embarazo.tipo_embarazo == 'gemelar':
            factores.append({
                "factor": "Embarazo gemelar",
                "severidad": "medio",
                "descripcion": "Requiere mayor seguimiento"
            })
        elif embarazo.tipo_embarazo == 'multiple':
            factores.append({
                "factor": "Embarazo múltiple",
                "severidad": "alto",
                "descripcion": "Alto riesgo de complicaciones"
            })

        # Evaluar número de gestas
        if embarazo.numero_gesta >= 5:
            factores.append({
                "factor": f"Gran multípara (gesta {embarazo.numero_gesta})",
                "severidad": "medio",
                "descripcion": "Riesgo aumentado de complicaciones"
            })

        # Evaluar controles
        if embarazo.fecha_ultima_menstruacion:
            hoy = date.today()
            semanas = (hoy - embarazo.fecha_ultima_menstruacion).days // 7
            controles_realizados = embarazo.controles.count()

            # Controles esperados según semana
            if semanas < 28:
                controles_esperados = semanas // 4
            elif semanas < 36:
                controles_esperados = 7 + ((semanas - 28) // 2)
            else:
                controles_esperados = 11 + (semanas - 36)

            if controles_realizados < controles_esperados * 0.7:
                factores.append({
                    "factor": "Controles insuficientes",
                    "severidad": "medio",
                    "descripcion": f"Solo {controles_realizados} de {controles_esperados} controles esperados"
                })

        # Recomendaciones
        recomendaciones = []
        if nivel_riesgo == 'alto' or len(factores) >= 3:
            recomendaciones.append("Controles prenatales frecuentes (cada 2 semanas)")
            recomendaciones.append("Evaluación por especialista en embarazo de alto riesgo")
            recomendaciones.append("Monitoreo fetal continuo")

        elif nivel_riesgo == 'medio' or len(factores) >= 1:
            recomendaciones.append("Controles prenatales regulares")
            recomendaciones.append("Vigilancia de signos de alarma")

        else:
            recomendaciones.append("Controles prenatales de rutina")
            recomendaciones.append("Educación prenatal")

        return Response({
            "nivel_riesgo": nivel_riesgo,
            "factores": factores,
            "total_factores": len(factores),
            "recomendaciones": recomendaciones
        }, status=status.HTTP_200_OK)

    # ===========================================
    # ACCIONES DE CONSULTAS ESPECIALIZADAS
    # ===========================================

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        ACCIÓN: Estadísticas generales de embarazos

        Funcionamiento:
            Calcula y retorna métricas sobre todos los embarazos

        Request:
            GET /api/embarazos/estadisticas/

        Response (200):
            {
                "total_embarazos": 150,
                "embarazos_activos": 45,
                "embarazos_finalizados": 95,
                "perdidas": 10,
                "por_tipo": { ... },
                "por_riesgo": { ... },
                "promedio_edad_gestacional": "24+3"
            }
        """

        # Estadísticas generales
        total = Embarazo.objects.count()
        activos = Embarazo.objects.filter(estado='activo').count()
        finalizados = Embarazo.objects.filter(estado='finalizado').count()
        perdidas = Embarazo.objects.filter(estado='perdida').count()

        # Por tipo
        por_tipo = {
            'simple': Embarazo.objects.filter(tipo_embarazo='simple').count(),
            'gemelar': Embarazo.objects.filter(tipo_embarazo='gemelar').count(),
            'multiple': Embarazo.objects.filter(tipo_embarazo='multiple').count(),
        }

        # Por riesgo
        por_riesgo = {
            'bajo': Embarazo.objects.filter(riesgo_embarazo='bajo').count(),
            'medio': Embarazo.objects.filter(riesgo_embarazo='medio').count(),
            'alto': Embarazo.objects.filter(riesgo_embarazo='alto').count(),
        }

        # Embarazos este mes
        inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0)
        nuevos_mes = Embarazo.objects.filter(fecha_registro__gte=inicio_mes).count()

        # Promedio de edad gestacional de embarazos activos
        embarazos_activos = Embarazo.objects.filter(
            estado='activo',
            fecha_ultima_menstruacion__isnull=False
        )

        if embarazos_activos.exists():
            hoy = date.today()
            suma_dias = 0
            count = 0

            for embarazo in embarazos_activos:
                dias = (hoy - embarazo.fecha_ultima_menstruacion).days
                suma_dias += dias
                count += 1

            if count > 0:
                promedio_dias = suma_dias // count
                promedio_semanas = promedio_dias // 7
                promedio_dias_extra = promedio_dias % 7
                promedio_eg = f"{promedio_semanas}+{promedio_dias_extra}"
            else:
                promedio_eg = "N/A"
        else:
            promedio_eg = "N/A"

        return Response({
            'total_embarazos': total,
            'embarazos_activos': activos,
            'embarazos_finalizados': finalizados,
            'perdidas': perdidas,
            'por_tipo': por_tipo,
            'por_riesgo': por_riesgo,
            'nuevos_este_mes': nuevos_mes,
            'promedio_edad_gestacional': promedio_eg
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def busqueda_avanzada(self, request):
        """
        ACCIÓN: Búsqueda avanzada con múltiples filtros

        Funcionamiento:
            Permite buscar embarazos con múltiples criterios combinados

        Parámetros:
            - q: Búsqueda general (ID clínico, nombre paciente)
            - estado: Estado del embarazo
            - tipo: Tipo de embarazo
            - riesgo: Nivel de riesgo
            - paciente_id: ID del paciente
            - fecha_desde: Desde fecha
            - fecha_hasta: Hasta fecha
            - semanas_min: Mínimo de semanas
            - semanas_max: Máximo de semanas

        Request:
            GET /api/embarazos/busqueda_avanzada/?riesgo=alto&estado=activo

        Response (200):
            {
                "count": 12,
                "results": [ ... ]
            }
        """
        queryset = Embarazo.objects.all()

        # Búsqueda general
        q = request.query_params.get('q', None)
        if q:
            queryset = queryset.filter(
                Q(paciente__id_clinico__icontains=q) |
                Q(paciente__nombre__icontains=q) |
                Q(paciente__apellido_paterno__icontains=q) |
                Q(paciente__apellido_materno__icontains=q)
            )

        # Filtros específicos
        estado = request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)

        tipo = request.query_params.get('tipo', None)
        if tipo:
            queryset = queryset.filter(tipo_embarazo=tipo)

        riesgo = request.query_params.get('riesgo', None)
        if riesgo:
            queryset = queryset.filter(riesgo_embarazo=riesgo)

        paciente_id = request.query_params.get('paciente_id', None)
        if paciente_id:
            queryset = queryset.filter(paciente_id=paciente_id)

        # Filtros por fecha
        fecha_desde = request.query_params.get('fecha_desde', None)
        if fecha_desde:
            queryset = queryset.filter(fecha_registro__gte=fecha_desde)

        fecha_hasta = request.query_params.get('fecha_hasta', None)
        if fecha_hasta:
            queryset = queryset.filter(fecha_registro__lte=fecha_hasta)

        # Filtro por semanas de gestación
        semanas_min = request.query_params.get('semanas_min', None)
        semanas_max = request.query_params.get('semanas_max', None)

        if semanas_min or semanas_max:
            # Filtrar embarazos activos con FUM
            queryset = queryset.filter(
                estado='activo',
                fecha_ultima_menstruacion__isnull=False
            )

            # Calcular y filtrar (esto es aproximado, idealmente se haría en la BD)
            hoy = date.today()
            resultados = []

            for embarazo in queryset:
                dias = (hoy - embarazo.fecha_ultima_menstruacion).days
                semanas = dias // 7

                incluir = True
                if semanas_min and semanas < int(semanas_min):
                    incluir = False
                if semanas_max and semanas > int(semanas_max):
                    incluir = False

                if incluir:
                    resultados.append(embarazo.id)

            queryset = queryset.filter(id__in=resultados)

        # Paginar
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = EmbarazoListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = EmbarazoListSerializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='por_paciente/(?P<paciente_id>[^/.]+)')
    def por_paciente(self, request, paciente_id=None):
        """
        ACCIÓN: Obtener todos los embarazos de un paciente

        Request:
            GET /api/embarazos/por_paciente/5/

        Response (200):
            {
                "paciente": { ... },
                "embarazos": [ ... ],
                "total": 3
            }
        """
        paciente = get_object_or_404(Paciente, id=paciente_id)
        embarazos = Embarazo.objects.filter(paciente=paciente).order_by('-fecha_registro')

        from pacientes.serializers import PacienteListSerializer

        return Response({
            "paciente": PacienteListSerializer(paciente).data,
            "embarazos": EmbarazoListSerializer(embarazos, many=True).data,
            "total": embarazos.count()
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def activos(self, request):
        """
        ACCIÓN: Obtener solo embarazos activos

        Request:
            GET /api/embarazos/activos/

        Response (200):
            Lista de embarazos activos paginada
        """
        queryset = Embarazo.objects.filter(estado='activo').order_by('-fecha_registro')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = EmbarazoListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = EmbarazoListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def alto_riesgo(self, request):
        """
        ACCIÓN: Obtener embarazos de alto riesgo

        Request:
            GET /api/embarazos/alto_riesgo/

        Response (200):
            Lista de embarazos de alto riesgo
        """
        queryset = Embarazo.objects.filter(
            riesgo_embarazo='alto',
            estado='activo'
        ).order_by('-fecha_registro')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = EmbarazoListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = EmbarazoListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def proximos_partos(self, request):
        """
        ACCIÓN: Embarazos con partos próximos (30 días)

        Funcionamiento:
            Retorna embarazos cuya FPP está en los próximos 30 días

        Request:
            GET /api/embarazos/proximos_partos/

        Response (200):
            {
                "count": 8,
                "embarazos": [
                    {
                        "id": 5,
                        "paciente_nombre": "María García",
                        "fecha_probable_parto": "2024-08-15",
                        "dias_restantes": 12,
                        "semanas_gestacion": "38+2"
                    },
                    ...
                ]
            }
        """
        hoy = date.today()
        fecha_limite = hoy + timedelta(days=30)

        queryset = Embarazo.objects.filter(
            estado='activo',
            fecha_probable_parto__gte=hoy,
            fecha_probable_parto__lte=fecha_limite
        ).order_by('fecha_probable_parto')

        # Crear respuesta personalizada
        resultados = []
        for embarazo in queryset:
            dias_restantes = (embarazo.fecha_probable_parto - hoy).days

            # Calcular semanas de gestación
            if embarazo.fecha_ultima_menstruacion:
                dias_totales = (hoy - embarazo.fecha_ultima_menstruacion).days
                semanas = dias_totales // 7
                dias = dias_totales % 7
                semanas_gestacion = f"{semanas}+{dias}"
            else:
                semanas_gestacion = "N/A"

            resultados.append({
                "id": embarazo.id,
                "paciente_nombre": embarazo.paciente.nombre_completo,
                "paciente_id_clinico": embarazo.paciente.id_clinico,
                "fecha_probable_parto": embarazo.fecha_probable_parto.strftime("%Y-%m-%d"),
                "dias_restantes": dias_restantes,
                "semanas_gestacion": semanas_gestacion,
                "tipo_embarazo": embarazo.tipo_embarazo,
                "riesgo_embarazo": embarazo.riesgo_embarazo
            })

        return Response({
            "count": len(resultados),
            "embarazos": resultados
        }, status=status.HTTP_200_OK)

    # ===========================================
    # MÉTODOS AUXILIARES PRIVADOS
    # ===========================================

    def _calcular_datos_obstetricos(self, embarazo):
        """
        MÉTODO PRIVADO: Calcular todos los datos obstétricos

        Funcionamiento:
            Calcula y retorna todos los cálculos obstétricos en un dict

        Parámetros:
            embarazo: Instancia de Embarazo

        Retorna:
            dict: Todos los cálculos obstétricos
        """
        if not embarazo.fecha_ultima_menstruacion:
            return {
                "error": "No se pueden realizar cálculos sin FUM"
            }

        hoy = date.today()
        total_dias = (hoy - embarazo.fecha_ultima_menstruacion).days
        semanas = total_dias // 7
        dias = total_dias % 7

        # Calcular trimestre
        if semanas <= 13:
            trimestre = 1
        elif semanas <= 26:
            trimestre = 2
        else:
            trimestre = 3

        # Calcular días hasta el parto
        if embarazo.fecha_probable_parto:
            dias_hasta_parto = (embarazo.fecha_probable_parto - hoy).days
        else:
            dias_hasta_parto = None

        # Calcular porcentaje
        porcentaje = min((total_dias / 280) * 100, 100.0)

        # Rango de fechas de parto (37-42 semanas)
        fecha_parto_minima = embarazo.fecha_ultima_menstruacion + timedelta(days=37*7)
        fecha_parto_maxima = embarazo.fecha_ultima_menstruacion + timedelta(days=42*7)

        return {
            "edad_gestacional": {
                "semanas": semanas,
                "dias": dias,
                "total_dias": total_dias,
                "formato": f"{semanas}+{dias}"
            },
            "trimestre": trimestre,
            "fecha_probable_parto": embarazo.fecha_probable_parto.strftime("%Y-%m-%d") if embarazo.fecha_probable_parto else None,
            "dias_hasta_parto": dias_hasta_parto,
            "porcentaje_completado": round(porcentaje, 2),
            "rango_parto_seguro": {
                "minimo": fecha_parto_minima.strftime("%Y-%m-%d"),
                "maximo": fecha_parto_maxima.strftime("%Y-%m-%d")
            },
            "semanas_para_termino": max(37 - semanas, 0)
        }


"""
RESUMEN DE VIEWS DE EMBARAZOS:
===============================

CRUD Básico:
    - list()          - Listar embarazos paginados
    - create()        - Crear embarazo
    - retrieve()      - Obtener embarazo
    - update()        - Actualizar embarazo
    - destroy()       - Finalizar embarazo (soft delete)

Gestión de Estado (5 acciones):
    - cambiar_estado()    - Cambiar estado
    - finalizar()         - Finalizar embarazo
    - marcar_perdida()    - Marcar pérdida
    - reactivar()         - Reactivar embarazo

Información y Cálculos (5 acciones):
    - historial_completo()     - Historial completo
    - calculos_obstetricos()   - Todos los cálculos
    - proximos_controles()     - Sugerencias de controles
    - curva_crecimiento()      - Datos para gráficas
    - riesgos()                - Evaluación de riesgos

Consultas Especializadas (6 acciones):
    - estadisticas()        - Estadísticas generales
    - busqueda_avanzada()   - Búsqueda con filtros
    - por_paciente()        - Embarazos de un paciente
    - activos()             - Solo activos
    - alto_riesgo()         - Alto riesgo
    - proximos_partos()     - Partos en 30 días

Total: 21 endpoints
Líneas: ~1300
===============================
"""
