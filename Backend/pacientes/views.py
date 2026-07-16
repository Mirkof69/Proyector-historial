"""Views module."""
import hashlib
import hmac as _hmac
from datetime import date, datetime, timedelta

from django.conf import settings as _settings
from django.core.cache import cache
from django.db.models import Count, Q
from django.http import HttpResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from antecedentes.serializers import (
    AntecedenteGinecoObstetricoSerializer,
    AntecedentePatologicoSerializer,
)
from core.permissions import FetalMedicalPermission
from laboratorio.models import ExamenLaboratorio
from partos.models import Parto

from .models import Paciente
from .pdf_service import PDFService
from .serializers import (
    PacienteCreateUpdateSerializer,
    PacienteListSerializer,
    PacienteSerializer,
)

# Inicializar servicio PDF
pdf_service = PDFService()


class PacienteViewSet(viewsets.ModelViewSet):
    """ViewSet for comprehensive Patient management.

    Manages patient registration, clinical history, advanced search,
    and integrated medical records.

    **Endpoints:**
    - `GET /api/pacientes/` - List all patients (paginated)
    - `POST /api/pacientes/` - Create new patient
    - `GET /api/pacientes/{id}/` - Get patient details
    - `PUT /api/pacientes/{id}/` - Update patient (full)
    - `PATCH /api/pacientes/{id}/` - Update patient (partial)
    - `DELETE /api/pacientes/{id}/` - Delete patient (hard delete, admin only)
    - `GET /api/pacientes/buscar/q=text` - Global search
    - `POST /api/pacientes/busqueda-avanzada/` - Advanced multi-criteria search
    - `GET /api/pacientes/estadisticas/` - General statistics
    - `GET /api/pacientes/{id}/embarazos/` - Get patient pregnancies
    - `POST /api/pacientes/{id}/activar/` - Reactivate inactive patient
    - `GET /api/pacientes/{id}/historia-clinica/` - Get integrated clinical history (PDF)

    **Authentication:** JWT Bearer token required
    **Permissions:** Authenticated users (admin required for delete)
    """

    queryset = Paciente.objects.all().order_by("-fecha_registro")
    permission_classes = [FetalMedicalPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["genero", "activo"]
    search_fields = ["nombre", "apellido_paterno", "apellido_materno", "id_clinico"]
    ordering_fields = ["fecha_registro", "nombre", "apellido_paterno"]

    @extend_schema(
        summary="List all patients",
        description="Retrieve a paginated list of all patients with optional filtering by gender and active status.",
        responses={200: PacienteListSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        """List"""
        return super().list(request, *args, **kwargs)

    # Método create extraído y unificado más abajo

    @extend_schema(
        summary="Retrieve patient details",
        description="Get full details of a specific patient.",
        responses={200: PacienteSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        """Retrieve"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Update patient",
        description="Update patient information (full or partial).",
        request=PacienteCreateUpdateSerializer,
        responses={200: PacienteSerializer},
    )
    def update(self, request, *args, **kwargs):
        """Update"""
        return super().update(request, *args, **kwargs)

    def get_serializer_class(self):
        """Returns the appropriate serializer based on action."""
        if self.action == "list":
            return PacienteListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return PacienteCreateUpdateSerializer
        return PacienteSerializer

    def perform_create(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar created_by al crear"""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar updated_by al actualizar"""
        serializer.save(updated_by=self.request.user)

    def get_queryset(self):
        """Filtra el queryset según parámetros y optimiza la carga en detalle."""
        queryset = super().get_queryset()

        # Optimización: en el detalle precargar relaciones para evitar N+1
        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                "embarazos",
                "controles_prenatales",
                "ecografias",
                "citas",
                "examenes_laboratorio",
                "antecedentes_patologicos",
            ).select_related("created_by", "updated_by")

        # Filtrar solo activos si se especifica
        solo_activos = self.request.query_params.get("solo_activos", None)
        if solo_activos == "true":
            queryset = queryset.filter(activo=True)

        # Filtrar por rango de edad
        edad_min = self.request.query_params.get("edad_min", None)
        edad_max = self.request.query_params.get("edad_max", None)

        if edad_min or edad_max:
            today = timezone.localdate()

            if edad_max:
                fecha_min = today - timedelta(days=int(edad_max) * 365.25)
                queryset = queryset.filter(fecha_nacimiento__gte=fecha_min)

            if edad_min:
                fecha_max = today - timedelta(days=int(edad_min) * 365.25)
                queryset = queryset.filter(fecha_nacimiento__lte=fecha_max)

        return queryset

    def _generar_id_clinico(self) -> str:
        """Genera ID clinico unico formato PAC-YYYY-NNNN."""
        from django.utils import timezone as tz
        anio_actual = tz.localdate().year
        ultimo = (
            Paciente.objects.filter(id_clinico__startswith=f"PAC-{anio_actual}")
            .order_by("-id_clinico")
            .first()
        )
        num = int(ultimo.id_clinico.split("-")[-1]) + 1 if ultimo else 1
        return f"PAC-{anio_actual}-{num:04d}"

    @extend_schema(
        summary="Create a new patient",
        description="Create a new patient record with automatic clinical ID generation.",
        request=PacienteCreateUpdateSerializer,
        responses={201: PacienteSerializer},
    )
    def create(self, request, *args, **kwargs):
        """Crea un nuevo paciente con ID clínico automático"""
        # Agregar ID clínico a los datos
        data = request.data.copy()
        data["id_clinico"] = self._generar_id_clinico()

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Retornar con serializer completo
        assert serializer.instance is not None
        paciente = Paciente.objects.get(id=serializer.instance.id)
        return_serializer = PacienteSerializer(paciente)

        headers = self.get_success_headers(return_serializer.data)
        return Response(
            return_serializer.data, status=status.HTTP_201_CREATED, headers=headers,
        )

    def destroy(self, request, *args, **kwargs):
        """Baja lógica del paciente (soft delete). Nunca elimina físicamente el registro médico.
        Cumple DS 1793/2013 y RM 1328 — retención obligatoria 10 años.
        Solo administradores pueden desactivar pacientes.
        """
        from django.utils import timezone as tz

        # Solo administradores pueden desactivar pacientes
        if not getattr(request.user, 'is_superuser', False) and getattr(request.user, "rol", "") != "administrador":
            return Response(
                {"error": "Solo administradores pueden desactivar pacientes del sistema."},
                status=status.HTTP_403_FORBIDDEN,
            )

        instance = self.get_object()
        nombre_paciente = getattr(instance, "nombre_completo", str(instance))
        instance.activo = False
        instance.updated_by = request.user
        if hasattr(instance, "fecha_baja"):
            instance.fecha_baja = tz.now()
        instance.save()

        try:
            from auditoria.models import RegistroAuditoria

            RegistroAuditoria.registrar(
                usuario=request.user,
                accion="DESACTIVAR_PACIENTE",
                modulo="Paciente",
                registro_id=str(instance.id),
                detalle=f"Paciente {nombre_paciente} desactivado. ID clínico: {instance.id_clinico}",
                request=request,
            )
        except Exception:
            pass

        return Response(
            {"mensaje": "Paciente desactivado correctamente (baja lógica)"},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="buscar")
    @extend_schema(
        summary="Search patients",
        description="Global search across patient name, clinical ID, CI, and email.",
        parameters=[
            OpenApiParameter(
                name="q", type=str, description="Search term", required=True,
            ),
        ],
        responses={200: OpenApiResponse(description="Search results with count")},
    )
    def buscar(self, request):
        """Búsqueda global de pacientes
        Parámetros:
            pass
        - q: texto a buscar
        """
        query = request.query_params.get("q", "")

        if not query:
            return Response(
                {"error": 'Debe proporcionar un parámetro de búsqueda "q"'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # id_clinico es CharField plano: el filtro SQL real funciona.
        # nombre/apellido_paterno/apellido_materno son EncryptedCharField
        # (cada cifrado usa un IV/nonce aleatorio) — un LIKE contra esas
        # columnas nunca puede coincidir con el texto plano de la búsqueda.
        # Para mantener búsqueda PARCIAL real (no solo coincidencia exacta
        # vía hash), se descifra y filtra en Python sobre pacientes activos.
        # from_db_value() en EncryptedFieldMixin ya descifra automáticamente
        # al acceder a paciente.nombre, no hace falta llamar a decrypt_value.
        ids_por_id_clinico = set(
            Paciente.objects.filter(id_clinico__icontains=query).values_list(
                "id", flat=True,
            ),
        )

        query_lower = query.lower()
        ids_por_nombre = {
            p.id
            for p in Paciente.objects.filter(activo=True).only(
                "id", "nombre", "apellido_paterno", "apellido_materno",
            )
            if query_lower in (p.nombre or "").lower()
            or query_lower in (p.apellido_paterno or "").lower()
            or query_lower in (p.apellido_materno or "").lower()
        }

        pacientes = Paciente.objects.filter(
            id__in=ids_por_id_clinico | ids_por_nombre,
        )

        serializer = PacienteListSerializer(pacientes, many=True)
        return Response({"count": pacientes.count(), "results": serializer.data})

    @action(
        detail=False,
        methods=["get"],
        url_path="buscar-por-cedula",
        permission_classes=[IsAuthenticated],
    )
    def buscar_por_cedula(self, request):
        """Búsqueda exacta de paciente por CI usando HMAC-SHA256 (ci_hash)."""
        ci = request.query_params.get("ci", "").strip()
        if not ci:
            return Response(
                {"error": "Parámetro ci requerido"}, status=status.HTTP_400_BAD_REQUEST,
            )
        try:

            key = str(getattr(_settings, "SEARCH_HMAC_KEY", _settings.SECRET_KEY)).encode()
            ci_hash = _hmac.new(key, ci.upper().encode(), hashlib.sha256).hexdigest()
            paciente = Paciente.objects.get(ci_hash=ci_hash, activo=True)
            return Response(self.get_serializer(paciente).data)
        except Paciente.DoesNotExist:
            return Response(
                {"error": "Paciente no encontrado"}, status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=["get"],
        url_path="buscar-por-id-clinico",
        permission_classes=[IsAuthenticated],
    )
    def buscar_por_id_clinico(self, request):
        """Búsqueda exacta de paciente por ID clínico (PAC-YYYY-NNNN)."""
        id_clinico = request.query_params.get("id_clinico", "").strip()
        if not id_clinico:
            return Response(
                {"error": "Parámetro id_clinico requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            paciente = Paciente.objects.get(id_clinico=id_clinico, activo=True)
            return Response(self.get_serializer(paciente).data)
        except Paciente.DoesNotExist:
            return Response(
                {"error": "Paciente no encontrado"}, status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["get"])
    @extend_schema(
        summary="Get patient statistics",
        description="Retrieve general statistics about patients (total, active, by gender, etc.).",
        responses={200: OpenApiResponse(description="Patient statistics")},
    )
    def estadisticas(self, request):
        """Estadisticas generales de pacientes. Cached for 60 seconds."""
        cache_key = f"patient_stats:globales:user_{request.user.id}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return Response(cached_result)

        total = Paciente.objects.count()
        activos = Paciente.objects.filter(activo=True).count()
        inactivos = total - activos

        # Por genero
        por_genero = (
            Paciente.objects.filter(activo=True)
            .values("genero")
            .annotate(total=Count("id"))
        )

        # Con embarazos activos
        con_embarazos = (
            Paciente.objects.filter(embarazos__estado="activo", activo=True)
            .distinct()
            .count()
        )

        result = {
            "total_pacientes": total,
            "activos": activos,
            "inactivos": inactivos,
            "por_genero": list(por_genero),
            "con_embarazos_activos": con_embarazos,
        }

        # Cache for 60 seconds
        cache.set(cache_key, result, timeout=60)
        return Response(result)

    @action(detail=True, methods=["get"])
    def embarazos(self, _request, pk=None):
        """Obtener todos los embarazos de un paciente"""
        paciente = self.get_object()
        embarazos = paciente.embarazos.all().order_by("-fecha_registro")

        from embarazos.serializers import EmbarazoSerializer

        serializer = EmbarazoSerializer(embarazos, many=True)

        return Response(
            {
                "paciente": PacienteSerializer(paciente).data,
                "embarazos": serializer.data,
            },
        )

    @action(detail=False, methods=["post"], url_path="busqueda-avanzada")
    @extend_schema(
        summary="Advanced patient search",
        description="Multi-criteria search with fuzzy matching, date ranges, age filters, and pregnancy status.",
        request=OpenApiParameter(
            name="body", type=dict, description="Search criteria object",
        ),
        responses={200: OpenApiResponse(description="Search results with count")},
    )
    def busqueda_avanzada(self, request):
        """✨ BÚSQUEDA AVANZADA - Multi-criterio con fuzzy search

        POST /api/pacientes/busqueda-avanzada/
        Body: {
            "nombre": "string",  # Fuzzy search
            "id_clinico": "string",
            "ci": "string",
            "fecha_desde": "YYYY-MM-DD",
            "fecha_hasta": "YYYY-MM-DD",
            "edad_min": int,
            "edad_max": int,
            "genero": "femenino|masculino",
            "estado_civil": "string",
            "embarazo_activo": bool,
            "riesgo_alto": bool
        }
        """

        # Obtener parámetros
        nombre = request.data.get("nombre", "").strip()
        id_clinico = request.data.get("id_clinico", "").strip()
        ci = request.data.get("ci", "").strip()
        fecha_desde = request.data.get("fecha_desde")
        fecha_hasta = request.data.get("fecha_hasta")
        edad_min = request.data.get("edad_min")
        edad_max = request.data.get("edad_max")
        genero = request.data.get("genero")
        estado_civil = request.data.get("estado_civil")
        embarazo_activo = request.data.get("embarazo_activo")
        riesgo_alto = request.data.get("riesgo_alto")

        # Iniciar queryset
        queryset = Paciente.objects.filter(activo=True)

        # ID Clínico
        if id_clinico:
            queryset = queryset.filter(id_clinico__icontains=id_clinico)

        # CI — campo cifrado, buscar por hash exacto (HMAC-SHA256)
        if ci:

            key = str(getattr(_settings, "SEARCH_HMAC_KEY", _settings.SECRET_KEY)).encode()
            ci_hash = _hmac.new(key, ci.upper().encode(), hashlib.sha256).hexdigest()
            queryset = queryset.filter(ci_hash=ci_hash)

        # Rango de fechas de registro
        if fecha_desde:
            queryset = queryset.filter(fecha_registro__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_registro__lte=fecha_hasta)

        # Edad
        if edad_min or edad_max:
            today = timezone.localdate()
            if edad_max:
                fecha_min = today - timedelta(days=int(edad_max) * 365.25)
                queryset = queryset.filter(fecha_nacimiento__gte=fecha_min)
            if edad_min:
                fecha_max = today - timedelta(days=int(edad_min) * 365.25)
                queryset = queryset.filter(fecha_nacimiento__lte=fecha_max)

        # Género
        if genero:
            queryset = queryset.filter(genero=genero)

        # Estado civil
        if estado_civil:
            queryset = queryset.filter(estado_civil=estado_civil)

        # Embarazo activo
        if embarazo_activo is not None:
            if embarazo_activo:
                queryset = queryset.filter(embarazos__estado="activo").distinct()
            else:
                queryset = queryset.exclude(embarazos__estado="activo").distinct()

        # Riesgo alto
        if riesgo_alto is not None and riesgo_alto:
            queryset = queryset.filter(
                embarazos__riesgo_embarazo="alto", embarazos__estado="activo",
            ).distinct()

        # Ordenar por fecha registro descendente
        queryset = queryset.order_by("-fecha_registro")  # Sin límite de resultados

        # Fuzzy search en nombre (contiene). nombre/apellidos son
        # EncryptedCharField — un icontains en SQL nunca coincide (mismo
        # motivo que en buscar()). Se filtra en Python sobre el queryset
        # YA acotado por los demás criterios (fecha, edad, género, etc.)
        # para no descifrar más registros de los necesarios.
        if nombre:
            nombre_parts = [p.lower() for p in nombre.split()]
            queryset = [
                p
                for p in queryset
                if all(
                    part in (p.nombre or "").lower()
                    or part in (p.apellido_paterno or "").lower()
                    or part in (p.apellido_materno or "").lower()
                    for part in nombre_parts
                )
            ]
            total = len(queryset)
        else:
            total = queryset.count()

        serializer = PacienteListSerializer(queryset, many=True)

        return Response({"count": total, "results": serializer.data})

    @action(detail=True, methods=["post"])
    @extend_schema(
        summary="Activate patient",
        description="Reactivate an inactive patient.",
        responses={200: OpenApiResponse(description="Patient activated successfully")},
    )
    def activar(self, _request, pk=None):
        """Reactivar un paciente inactivo"""
        paciente = self.get_object()
        paciente.activo = True
        paciente.save()

        return Response(
            {
                "message": "Paciente activado correctamente",
                "paciente": PacienteSerializer(paciente).data,
            },
        )

    @action(detail=True, methods=["get"], url_path="historia-clinica")
    @extend_schema(
        summary="Get integrated clinical history",
        description="Retrieve complete clinical history as PDF, consolidating all pregnancies, prenatal controls, "
        "ultrasounds, laboratory results, and deliveries in a timeline format.",
        responses={
            200: OpenApiResponse(description="PDF file with clinical history"),
        },
    )
    def historia_clinica(self, _request, pk=None):
        """✨ NUEVA FUNCIONALIDAD: Historia Clínica Integrada Completa

        Consolida TODOS los datos del embarazo en una vista Timeline:
            pass
        - Embarazos
        - Controles Prenatales
        - Ecografías
        - Laboratorios
        - Partos
        - Indicadores y métricas

        Endpoint: GET /api/pacientes/{id}/historia-clinica/
        """
        paciente = self.get_object()

        # Importar serializers necesarios
        from controles.serializers import ControlPrenatalSerializer
        from ecografias.serializers import EcografiaSerializer
        from embarazos.serializers import EmbarazoSerializer
        from laboratorio.serializers import ExamenLaboratorioDetailSerializer
        from partos.serializers import PartoSerializer

        # Obtener todos los embarazos del paciente
        embarazos = paciente.embarazos.all().order_by("-fecha_registro")

        # Construir timeline completa
        timeline = []

        for embarazo in embarazos:
            # Datos del embarazo
            embarazo_data = EmbarazoSerializer(embarazo).data
            embarazo_data["tipo_evento"] = "embarazo"
            embarazo_data["fecha_evento"] = embarazo.fecha_registro
            timeline.append(embarazo_data)

            # Controles prenatales del embarazo
            controles = embarazo.controles.all().order_by("fecha_control")
            for control in controles:
                control_data = ControlPrenatalSerializer(control).data
                control_data["tipo_evento"] = "control_prenatal"
                control_data["fecha_evento"] = control.fecha_control
                control_data["embarazo_id"] = embarazo.id
                timeline.append(control_data)

            # Ecografías del embarazo
            ecografias = embarazo.ecografias.all().order_by("fecha_ecografia")
            for eco in ecografias:
                eco_data = EcografiaSerializer(eco).data
                eco_data["tipo_evento"] = "ecografia"
                eco_data["fecha_evento"] = eco.fecha_ecografia
                eco_data["embarazo_id"] = embarazo.id
                timeline.append(eco_data)

            # Laboratorios del embarazo
            laboratorios = (
                ExamenLaboratorio.objects.filter(
                    Q(control_prenatal__embarazo=embarazo) | Q(paciente=paciente),
                )
                .distinct()
                .order_by("fecha_solicitud")
            )
            for lab in laboratorios:
                lab_data = ExamenLaboratorioDetailSerializer(lab).data
                lab_data["tipo_evento"] = "laboratorio"
                lab_data["fecha_evento"] = lab.fecha_solicitud
                lab_data["embarazo_id"] = embarazo.id
                timeline.append(lab_data)

            # Partos del embarazo
            partos = Parto.objects.filter(embarazo=embarazo).order_by("fecha_parto")
            for parto in partos:
                parto_data = PartoSerializer(parto).data
                parto_data["tipo_evento"] = "parto"
                parto_data["fecha_evento"] = parto.fecha_parto
                parto_data["embarazo_id"] = embarazo.id
                timeline.append(parto_data)

        # Ordenar timeline por fecha. Los eventos mezclan date (controles/ecos)
        # y datetime (laboratorios/partos): normalizamos todo a date para que
        # la comparación no explote (datetime vs date no son comparables).
        def _clave_fecha(evento):
            valor = evento.get("fecha_evento")
            if isinstance(valor, datetime):
                return valor.date()
            if isinstance(valor, date):
                return valor
            return date.min

        timeline.sort(key=_clave_fecha, reverse=True)

        # Calcular estadísticas
        estadisticas = {
            "total_embarazos": embarazos.count(),
            "embarazos_activos": embarazos.filter(estado="activo").count(),
            "total_controles": sum(e.controles.count() for e in embarazos),
            "total_ecografias": sum(e.ecografias.count() for e in embarazos),
            "total_laboratorios": sum(
                ExamenLaboratorio.objects.filter(
                    Q(control_prenatal__embarazo=e) | Q(paciente=paciente),
                )
                .distinct()
                .count()
                for e in embarazos
            ),
            "total_partos": sum(
                Parto.objects.filter(embarazo=e).count() for e in embarazos
            ),
            "total_eventos": len(timeline),
        }

        # Generar PDF
        paciente_data = PacienteSerializer(paciente).data
        embarazos_data = EmbarazoSerializer(embarazos, many=True).data

        pdf_buffer = pdf_service.generar_historia_clinica(
            paciente_data=paciente_data,
            timeline_data=timeline,
            _embarazos_data=embarazos_data,
            estadisticas=estadisticas,
        )

        # Preparar respuesta HTTP
        response = HttpResponse(pdf_buffer.getvalue(), content_type="application/pdf")
        filename = (
            f"Historia_Clinica_{paciente.id_clinico}_{paciente.apellido_paterno}.pdf"
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response

    @extend_schema(
        summary="Obtener o actualizar antecedentes personales",
        description="Obtiene o actualiza los antecedentes patológicos de tipo personal del paciente. Crea uno en blanco si no existe.",
        responses={200: AntecedentePatologicoSerializer},
    )
    @action(detail=True, methods=["get", "post"], url_path="antecedentes-personales")
    def antecedentes_personales(self, request, pk=None):
        paciente = self.get_object()
        from antecedentes.models import AntecedentePatologico

        antecedente, created = AntecedentePatologico.objects.get_or_create(
            paciente=paciente,
            tipo="personal",
            defaults={"registrado_por": request.user}
        )

        if request.method == "POST":
            serializer = AntecedentePatologicoSerializer(antecedente, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(registrado_por=request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = AntecedentePatologicoSerializer(antecedente)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Obtener o actualizar antecedentes familiares",
        description="Obtiene o actualiza los antecedentes patológicos de tipo heredofamiliar del paciente. Crea uno en blanco si no existe.",
        responses={200: AntecedentePatologicoSerializer},
    )
    @action(detail=True, methods=["get", "post"], url_path="antecedentes-familiares")
    def antecedentes_familiares(self, request, pk=None):
        paciente = self.get_object()
        from antecedentes.models import AntecedentePatologico

        antecedente, created = AntecedentePatologico.objects.get_or_create(
            paciente=paciente,
            tipo="heredofamiliar",
            defaults={"registrado_por": request.user}
        )

        if request.method == "POST":
            serializer = AntecedentePatologicoSerializer(antecedente, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(registrado_por=request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = AntecedentePatologicoSerializer(antecedente)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Obtener o actualizar antecedentes obstétricos",
        description="Obtiene o actualiza los antecedentes gineco-obstétricos de tipo obstétrico (GPAC) del paciente. Crea uno en blanco si no existe.",
        responses={200: AntecedenteGinecoObstetricoSerializer},
    )
    @action(detail=True, methods=["get", "post"], url_path="antecedentes-obstetricos")
    def antecedentes_obstetricos(self, request, pk=None):
        paciente = self.get_object()
        from antecedentes.models import AntecedenteGinecoObstetrico

        antecedente, created = AntecedenteGinecoObstetrico.objects.get_or_create(
            paciente=paciente,
            defaults={"modificado_por": request.user}
        )

        if request.method == "POST":
            serializer = AntecedenteGinecoObstetricoSerializer(antecedente, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(modificado_por=request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = AntecedenteGinecoObstetricoSerializer(antecedente)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Obtener o actualizar antecedentes ginecológicos",
        description="Obtiene o actualiza los antecedentes gineco-obstétricos de tipo ginecológico del paciente. Crea uno en blanco si no existe.",
        responses={200: AntecedenteGinecoObstetricoSerializer},
    )
    @action(detail=True, methods=["get", "post"], url_path="antecedentes-ginecologicos")
    def antecedentes_ginecologicos(self, request, pk=None):
        paciente = self.get_object()
        from antecedentes.models import AntecedenteGinecoObstetrico

        antecedente, created = AntecedenteGinecoObstetrico.objects.get_or_create(
            paciente=paciente,
            defaults={"modificado_por": request.user}
        )

        if request.method == "POST":
            serializer = AntecedenteGinecoObstetricoSerializer(antecedente, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(modificado_por=request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = AntecedenteGinecoObstetricoSerializer(antecedente)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def controles(self, _request, pk=None):
        paciente = self.get_object()
        from controles.models import ControlPrenatal
        from controles.serializers import ControlPrenatalSerializer
        controles_qs = ControlPrenatal.objects.filter(
            paciente=paciente
        ).select_related("embarazo").order_by("-fecha_control")
        serializer = ControlPrenatalSerializer(controles_qs, many=True)
        return Response({"total": controles_qs.count(), "controles": serializer.data})

    @action(detail=True, methods=["get"])
    def ecografias(self, _request, pk=None):
        paciente = self.get_object()
        from ecografias.models import Ecografia
        from ecografias.serializers import EcografiaListSerializer
        ecografias_qs = Ecografia.objects.filter(paciente=paciente).order_by("-fecha_ecografia")
        serializer = EcografiaListSerializer(ecografias_qs, many=True)
        return Response({"total": ecografias_qs.count(), "ecografias": serializer.data})

    @action(detail=True, methods=["get"], url_path="examenes-laboratorio")
    def examenes_laboratorio(self, _request, pk=None):
        paciente = self.get_object()
        from laboratorio.models import ExamenLaboratorio
        from laboratorio.serializers import ExamenLaboratorioListSerializer
        examenes = ExamenLaboratorio.objects.filter(paciente=paciente).order_by("-fecha_solicitud")
        serializer = ExamenLaboratorioListSerializer(examenes, many=True)
        return Response({"total": examenes.count(), "examenes": serializer.data})

    @action(detail=True, methods=["get"])
    def citas(self, _request, pk=None):
        paciente = self.get_object()
        from citas.models import Cita
        from citas.serializers import CitaListSerializer
        citas_qs = Cita.objects.filter(paciente=paciente).order_by("-fecha_cita")
        serializer = CitaListSerializer(citas_qs, many=True)
        return Response({"total": citas_qs.count(), "citas": serializer.data})

    @action(detail=True, methods=["get"])
    def partos(self, _request, pk=None):
        paciente = self.get_object()
        from partos.models import Parto
        from partos.serializers import PartoSerializer
        partos_qs = Parto.objects.filter(paciente=paciente).order_by("-fecha_parto")
        serializer = PartoSerializer(partos_qs, many=True)
        return Response({"total": partos_qs.count(), "partos": serializer.data})

    @action(detail=True, methods=["get"], url_path="estadisticas")
    def estadisticas_paciente(self, _request, pk=None):
        paciente = self.get_object()
        from controles.models import ControlPrenatal
        from ecografias.models import Ecografia
        from embarazos.models import Embarazo
        total_embarazos = Embarazo.objects.filter(paciente=paciente).count()
        activos = Embarazo.objects.filter(paciente=paciente, estado="activo").count()
        total_ecografias = Ecografia.objects.filter(paciente=paciente).count()
        total_controles = ControlPrenatal.objects.filter(paciente=paciente).count()
        return Response({
            "total_embarazos": total_embarazos,
            "embarazos_activos": activos,
            "total_ecografias": total_ecografias,
            "total_controles": total_controles,
        })

    @action(detail=True, methods=["get"], url_path="evaluar-riesgos")
    def evaluar_riesgos(self, _request, pk=None):
        paciente = self.get_object()
        factores = []
        if paciente.edad and paciente.edad >= 35:
            factores.append({"factor": "Edad materna avanzada", "valor": paciente.edad, "nivel": "medio"})
        if paciente.peso_kg and paciente.altura_cm:
            imc = paciente.peso_kg / ((paciente.altura_cm / 100) ** 2)
            if imc >= 30:
                factores.append({"factor": "Obesidad", "valor": round(imc, 1), "nivel": "alto"})
            elif imc < 18.5:
                factores.append({"factor": "Bajo peso", "valor": round(imc, 1), "nivel": "medio"})
        if paciente.tipo_sangre and "Negativo" in paciente.tipo_sangre:
            factores.append({"factor": "Rh negativo", "valor": paciente.tipo_sangre, "nivel": "medio"})
        return Response({
            "paciente_id": paciente.id,
            "total_factores": len(factores),
            "factores": factores,
            "nivel_general": "alto" if any(f["nivel"] == "alto" for f in factores) else "bajo",
        })

    @action(detail=True, methods=["get"], url_path="historial-completo")
    def historial_completo(self, _request, pk=None):
        paciente = self.get_object()
        from embarazos.serializers import EmbarazoSerializer
        embarazos = paciente.embarazos.all().order_by("-fecha_registro")
        return Response({
            "paciente": self.get_serializer(paciente).data,
            "embarazos": EmbarazoSerializer(embarazos, many=True).data,
        })

    @action(detail=True, methods=["get"], url_path="reporte-pdf")
    def reporte_pdf(self, _request, pk=None):
        return self.historia_clinica(_request, pk)

    @action(detail=True, methods=["get"], url_path="exportar-excel")
    def exportar_excel_paciente(self, request, pk=None):
        paciente = self.get_object()
        try:
            from io import BytesIO

            import openpyxl
            from django.http import HttpResponse
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Paciente"
            ws.append(["Campo", "Valor"])
            ws.append(["ID Clínico", paciente.id_clinico])
            ws.append(["Nombre", paciente.nombre_completo])
            ws.append(["CI", paciente.ci])
            ws.append(["Fecha Nacimiento", str(paciente.fecha_nacimiento or "")])
            ws.append(["Teléfono", paciente.telefono or ""])
            output = BytesIO()
            wb.save(output)
            output.seek(0)
            response = HttpResponse(output.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            response["Content-Disposition"] = f"attachment; filename=paciente_{paciente.id}.xlsx"
            return response
        except ImportError:
            return Response({"error": "openpyxl no instalado"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"], url_path="exportar-excel")
    def exportar_lista_excel(self, request):
        try:
            from io import BytesIO

            import openpyxl
            from django.http import HttpResponse
            queryset = self.filter_queryset(self.get_queryset())
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Pacientes"
            ws.append(["ID", "ID Clínico", "Nombre", "CI", "Teléfono", "Email"])
            for p in queryset:
                ws.append([p.id, p.id_clinico, p.nombre_completo, p.ci, p.telefono, p.email])
            output = BytesIO()
            wb.save(output)
            output.seek(0)
            response = HttpResponse(output.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            response["Content-Disposition"] = "attachment; filename=pacientes.xlsx"
            return response
        except ImportError:
            return Response({"error": "openpyxl no instalado"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"], url_path="exportar-pdf")
    def exportar_pdf(self, request):
        """Exporta listado de pacientes a PDF
        GET /api/pacientes/exportar-pdf/
        """
        try:
            import pdfkit
            from django.http import HttpResponse
            from django.template.loader import render_to_string
            queryset = self.filter_queryset(self.get_queryset())
            html = render_to_string("pacientes/listado_pacientes_pdf.html", {
                "pacientes": queryset,
                "total": queryset.count(),
            })
            pdf = pdfkit.from_string(html, False)
            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = 'attachment; filename="listado_pacientes.pdf"'
            return response
        except ImportError:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response({"mensaje": "PDF no disponible. Instale pdfkit: pip install pdfkit", "total": queryset.count(), "datos": serializer.data})
        except Exception as e:
            return Response({"error": f"Error generando PDF: {e}"}, status=500)
