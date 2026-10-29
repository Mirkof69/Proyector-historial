"""Views module."""
import logging
from datetime import date, datetime, timedelta

from django.core.cache import cache
from django.db.models import Count, Exists, OuterRef, Prefetch, Q
from django.db.models.functions import ExtractMonth
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
from controles.models import ControlPrenatal
from core.exportacion import ExportarExcelMixin
from core.permissions import FetalMedicalPermission
from embarazos.models import Embarazo
from laboratorio.models import ExamenLaboratorio
from partos.models import Parto

from .models import Paciente
from .pdf_service import PDFService
from .serializers import (
    PacienteCreateUpdateSerializer,
    PacienteListSerializer,
    PacienteSerializer,
)

logger = logging.getLogger(__name__)

# Inicializar servicio PDF
pdf_service = PDFService()


def _clave_fecha(evento):
    """Fecha comparable de un evento del timeline.

    Los eventos mezclan `date` (controles, ecografías) con `datetime`
    (laboratorios, partos), y en Python no se pueden comparar entre sí: todo
    se normaliza a `date`.
    """
    valor = evento.get("fecha_evento")
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    return date.min


def _antecedente_vigente(modelo, defaults, **filtro):
    """El antecedente más reciente de la paciente; uno en blanco si no tiene.

    No es get_or_create: el formulario de Antecedentes registra uno nuevo cada
    vez, así que una paciente puede tener varios del mismo tipo y get_or_create
    respondía 500 (MultipleObjectsReturned) en todas las pantallas que muestran
    sus datos clínicos. Manda el último que se cargó.
    """
    antecedente = modelo.objects.filter(**filtro).order_by("-pk").first()
    if antecedente is None:
        antecedente = modelo.objects.create(**filtro, **defaults)
    return antecedente


def construir_historia_clinica(paciente):
    """Timeline y contadores de la historia clínica de una paciente.

    Devuelve `(timeline, estadisticas)`. Está fuera del ViewSet a propósito:
    es la lógica clínica del informe y se puede probar sin HTTP, sin permisos
    y sin generar el PDF.

    Sobre los laboratorios
    ----------------------
    Se consultan UNA vez para toda la paciente, no dentro del bucle de
    embarazos. Antes la consulta era
    `Q(control_prenatal__embarazo=embarazo) | Q(paciente=paciente)` ejecutada
    por cada embarazo: la segunda mitad del OR trae todos los análisis de la
    paciente, así que con 3 embarazos cada análisis aparecía 3 veces en el
    timeline y el contador `total_laboratorios` reportaba el triple. En un
    documento clínico eso es un dato falso, no una molestia estética.
    """
    from controles.serializers import ControlPrenatalSerializer
    from ecografias.serializers import EcografiaSerializer
    from embarazos.serializers import EmbarazoSerializer
    from laboratorio.serializers import ExamenLaboratorioDetailSerializer
    from partos.serializers import PartoSerializer

    embarazos = list(
        paciente.embarazos.all()
        .order_by("-fecha_registro")
        .prefetch_related("controles", "ecografias"),
    )
    ids_embarazos = [e.id for e in embarazos]

    timeline = []
    total_controles = total_ecografias = 0

    for embarazo in embarazos:
        embarazo_data = EmbarazoSerializer(embarazo).data
        embarazo_data["tipo_evento"] = "embarazo"
        embarazo_data["fecha_evento"] = embarazo.fecha_registro
        timeline.append(embarazo_data)

        controles = sorted(embarazo.controles.all(), key=lambda c: c.fecha_control or date.min)
        total_controles += len(controles)
        for control in controles:
            control_data = ControlPrenatalSerializer(control).data
            control_data["tipo_evento"] = "control_prenatal"
            control_data["fecha_evento"] = control.fecha_control
            control_data["embarazo_id"] = embarazo.id
            timeline.append(control_data)

        ecografias = sorted(
            embarazo.ecografias.all(), key=lambda e: e.fecha_ecografia or date.min,
        )
        total_ecografias += len(ecografias)
        for eco in ecografias:
            eco_data = EcografiaSerializer(eco).data
            eco_data["tipo_evento"] = "ecografia"
            eco_data["fecha_evento"] = eco.fecha_ecografia
            eco_data["embarazo_id"] = embarazo.id
            timeline.append(eco_data)

    # Laboratorios: una sola consulta para toda la paciente. Cada análisis se
    # atribuye al embarazo de su control prenatal cuando lo tiene; si es un
    # análisis suelto de la paciente, queda sin `embarazo_id` en vez de
    # repetirse en todos.
    laboratorios = (
        ExamenLaboratorio.objects.filter(
            Q(control_prenatal__embarazo_id__in=ids_embarazos) | Q(paciente=paciente),
        )
        .select_related("control_prenatal")
        .distinct()
        .order_by("fecha_solicitud")
    )
    for lab in laboratorios:
        lab_data = ExamenLaboratorioDetailSerializer(lab).data
        lab_data["tipo_evento"] = "laboratorio"
        lab_data["fecha_evento"] = lab.fecha_solicitud
        control = getattr(lab, "control_prenatal", None)
        lab_data["embarazo_id"] = getattr(control, "embarazo_id", None)
        timeline.append(lab_data)

    partos = (
        Parto.objects.filter(embarazo_id__in=ids_embarazos)
        .distinct()
        .order_by("fecha_parto")
    )
    for parto in partos:
        parto_data = PartoSerializer(parto).data
        parto_data["tipo_evento"] = "parto"
        parto_data["fecha_evento"] = parto.fecha_parto
        parto_data["embarazo_id"] = parto.embarazo_id
        timeline.append(parto_data)

    timeline.sort(key=_clave_fecha, reverse=True)

    estadisticas = {
        "total_embarazos": len(embarazos),
        "embarazos_activos": sum(1 for e in embarazos if e.estado == "activo"),
        "total_controles": total_controles,
        "total_ecografias": total_ecografias,
        "total_laboratorios": len(laboratorios),
        "total_partos": len(partos),
        "total_eventos": len(timeline),
    }
    return timeline, estadisticas


class PacienteViewSet(ExportarExcelMixin, viewsets.ModelViewSet):
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
    # SIN SearchFilter a propósito: hacía `icontains` en SQL sobre nombre,
    # apellidos y ci, que son EncryptedCharField, o sea LIKE contra texto
    # cifrado -> 0 resultados siempre. El parámetro `search` lo resuelve
    # _filtrar_por_busqueda() en get_queryset(); si se reactivara este
    # backend volvería a vaciar los resultados por encima de ese filtro.
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
    ]
    # Sin filtro por genero: todas las pacientes son femeninas.
    filterset_fields = ["activo"]
    # Sin «nombre» ni «apellido_paterno»: están cifrados con IV aleatorio y
    # ordenar por ellos en SQL ordenaba por el texto CIFRADO (un orden
    # aleatorio que además cambiaba de página entre peticiones).
    ordering_fields = ["fecha_registro", "id_clinico", "fecha_nacimiento"]

    # Excel del listado con los MISMOS filtros que la pantalla y auditado.
    # Antes era un openpyxl a mano sin auditoría, y la pantalla armaba otro
    # Excel en el navegador con solo lo que había descargado.
    excel_nombre = "pacientes"
    excel_columnas = [
        ("ID clínico", "id_clinico"),
        ("Nombre completo", "nombre_completo"),
        ("CI", "ci"),
        ("Fecha de nacimiento", "fecha_nacimiento"),
        ("Edad", "edad"),
        ("Teléfono", "telefono"),
        ("Email", "email"),
        ("Dirección", "direccion"),
        ("Ciudad", "ciudad"),
        ("Estado civil", "estado_civil"),
        ("Ocupación", "ocupacion"),
        ("Grupo sanguíneo", "tipo_sangre"),
        ("Activa", "activo"),
        ("Fecha de registro", "fecha_registro"),
    ]

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
        """TRAZABILIDAD: Auto-asignar created_by al crear"""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """TRAZABILIDAD: Auto-asignar updated_by al actualizar"""
        serializer.save(updated_by=self.request.user)

    @staticmethod
    def optimizar_para_listado(queryset):
        """Precarga las relaciones que `PacienteListSerializer` recorre.

        El serializer del listado calcula 8 campos obstétricos leyendo
        `embarazos`, `controles_prenatales` y `partos`. Sin esto cada paciente
        dispara ~8 consultas: 200 pacientes costaban 1601 consultas y 1717 ms.

        Las relaciones se precargan YA ORDENADAS porque el serializer necesita
        "el último": así puede tomar el primer elemento de la caché en Python.
        Un `.order_by()` o un `.filter()` sobre la relación en el serializer
        anularía esta caché y volvería a disparar una consulta por paciente.
        """
        return queryset.prefetch_related(
            Prefetch("embarazos", queryset=Embarazo.objects.order_by("-fecha_registro")),
            Prefetch(
                "controles_prenatales",
                queryset=ControlPrenatal.objects.order_by("-fecha_control"),
            ),
            Prefetch("partos", queryset=Parto.objects.order_by("-fecha_parto")),
        )

    def get_queryset(self):
        """Filtra el queryset según parámetros y precarga relaciones."""
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
        elif self.action == "list":
            queryset = self.optimizar_para_listado(queryset)

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

        queryset = self._filtrar_por_filtros_de_pantalla(queryset)
        queryset = self._filtrar_por_busqueda(queryset)

        return queryset

    def _filtrar_por_filtros_de_pantalla(self, queryset):
        """Filtros del listado de pacientes que antes se aplicaban en el navegador.

        La pantalla descargaba TODAS las pacientes (17 peticiones para 3.200)
        para filtrar por ciudad / embarazo activo / estado obstétrico en el
        cliente. Ahora se resuelven aquí y la tabla pide solo la página visible.

        - `?ciudad=` : contiene, sin distinguir mayúsculas (ciudad NO está cifrada).
        - `?con_embarazo_activo=true`
        - `?estado_obstetrico=gestando|sin_embarazo|con_historial`
        """
        params = self.request.query_params
        if ciudad := (params.get("ciudad") or "").strip():
            queryset = queryset.filter(ciudad__icontains=ciudad)

        activo = Embarazo.objects.filter(paciente=OuterRef("pk"), estado="activo")
        cualquiera = Embarazo.objects.filter(paciente=OuterRef("pk"))
        if params.get("con_embarazo_activo") == "true":
            queryset = queryset.filter(Exists(activo))

        estado_obstetrico = params.get("estado_obstetrico")
        if estado_obstetrico == "gestando":
            queryset = queryset.filter(Exists(activo))
        elif estado_obstetrico == "sin_embarazo":
            queryset = queryset.filter(~Exists(cualquiera))
        elif estado_obstetrico == "con_historial":
            queryset = queryset.filter(Exists(cualquiera)).exclude(Exists(activo))
        return queryset

    def _filtrar_por_busqueda(self, queryset):
        """Aplica `?search=` usando el buscador canónico de pacientes.

        La lógica vive en pacientes/busqueda.py porque la comparten las 12
        vistas que buscan pacientes (embarazos, controles, citas, partos...)
        a través de BusquedaClinicaFilter; aquí solo se acota el queryset
        propio para que la paginación siga ocurriendo en la base.
        """
        termino = (self.request.query_params.get("search") or "").strip()
        if not termino:
            return queryset
        from .busqueda import ids_pacientes_que_coinciden

        return queryset.filter(pk__in=ids_pacientes_que_coinciden(termino))

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

    @action(detail=False, methods=["get"], url_path="plantilla-excel")
    def plantilla_excel(self, _request):
        """Plantilla .xlsx para importar pacientes, con una hoja de instrucciones."""
        from .importacion_excel import generar_plantilla

        respuesta = HttpResponse(
            generar_plantilla(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        respuesta["Content-Disposition"] = 'attachment; filename="plantilla_pacientes.xlsx"'
        return respuesta

    @action(detail=False, methods=["post"], url_path="importar-excel")
    def importar_excel(self, request):
        """Importa pacientes desde la plantilla.

        Sin `confirmar`: solo vista previa (qué filas se crearían y cuáles
        tienen errores). Con `confirmar=1`: crea las filas válidas.
        """
        from .importacion_excel import leer_filas, procesar

        archivo = request.FILES.get("archivo")
        if not archivo:
            return Response({"error": "Adjunte el archivo Excel en el campo «archivo»."},
                            status=status.HTTP_400_BAD_REQUEST)
        if archivo.size > 5 * 1024 * 1024:
            return Response({"error": "El archivo supera 5 MB."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            filas = leer_filas(archivo)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        if not filas:
            return Response({"error": "El archivo no tiene filas con datos."}, status=status.HTTP_400_BAD_REQUEST)

        confirmar = str(request.data.get("confirmar", "")).lower() in ("1", "true", "si", "sí")
        resultado = procesar(filas, {"request": request}, confirmar)
        if confirmar:
            try:
                from auditoria.models import RegistroAuditoria

                RegistroAuditoria.registrar(
                    usuario=request.user, accion="CREAR", modulo="Paciente",
                    detalle=f"Importación Excel «{archivo.name}»: {resultado['resumen']['creada']} creadas, "
                            f"{resultado['resumen']['error']} con error, {resultado['resumen']['duplicada']} duplicadas.",
                    request=request,
                )
            except Exception:
                logger.exception("No se pudo auditar la importación de pacientes")
        return Response(resultado)

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
            # MISMO hash que usa el modelo al guardar (compute_search_hash con
            # ENCRYPTION_KEY, sin upper). La implementación anterior usaba
            # SECRET_KEY + upper(): claves distintas → el hash JAMÁS coincidía
            # y la búsqueda por cédula devolvía 404 para pacientes existentes.
            from .fields import compute_search_hash

            paciente = Paciente.objects.get(
                ci_hash=compute_search_hash(ci), activo=True,
            )
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
    def resumen(self, _request):
        """Cifras de la pantalla de pacientes, con los MISMOS filtros que el listado.

        GET /api/pacientes/resumen/?search=&ciudad=&activo=&con_embarazo_activo=

        Antes la pantalla bajaba todas las pacientes para calcular total,
        activas, nuevas del mes, embarazadas y edad promedio en el navegador.
        La edad sale de `fecha_nacimiento`, que NO está cifrada, así que el
        promedio y la distribución por edades se calculan sobre todas las
        pacientes filtradas y no sobre una página.
        """
        qs = self.filter_queryset(self.get_queryset()).order_by()
        hoy = timezone.localdate()
        con_embarazo = Exists(Embarazo.objects.filter(paciente=OuterRef("pk"), estado="activo"))

        rangos = {"<15": 0, "15-19": 0, "20-24": 0, "25-29": 0, "30-34": 0, "35-39": 0, ">=40": 0}
        suma_edades = 0
        con_edad = 0
        anosas_gestando = 0
        for nacimiento, gestando in qs.annotate(gestando=con_embarazo).values_list("fecha_nacimiento", "gestando"):
            if not nacimiento:
                continue
            edad = hoy.year - nacimiento.year - ((hoy.month, hoy.day) < (nacimiento.month, nacimiento.day))
            suma_edades += edad
            con_edad += 1
            if gestando and edad >= 35:
                anosas_gestando += 1
            if edad < 15:
                rangos["<15"] += 1
            elif edad >= 40:
                rangos[">=40"] += 1
            else:
                inicio = 15 if edad < 20 else edad - edad % 5
                rangos[f"{inicio}-{inicio + 4}"] += 1

        por_mes = dict(
            qs.filter(fecha_registro__year=hoy.year)
            .annotate(mes=ExtractMonth("fecha_registro")).values_list("mes")
            .annotate(n=Count("id")),
        )
        por_ciudad = (
            qs.exclude(ciudad__isnull=True).exclude(ciudad="")
            .values("ciudad").annotate(n=Count("id")).order_by("-n")
        )
        return Response({
            "total": qs.count(),
            "activos": qs.filter(activo=True).count(),
            "nuevos_mes": qs.filter(fecha_registro__year=hoy.year, fecha_registro__month=hoy.month).count(),
            "embarazadas": qs.filter(con_embarazo).count(),
            "promedio_edad": round(suma_edades / con_edad) if con_edad else 0,
            "rangos_edad": rangos,
            "anosas_gestando": anosas_gestando,
            "registros_por_mes": [por_mes.get(m, 0) for m in range(1, 13)],
            "por_ciudad": [{"ciudad": c["ciudad"], "total": c["n"]} for c in por_ciudad],
        })

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

        # Con embarazos activos
        con_embarazos = (
            Paciente.objects.filter(embarazos__estado="activo", activo=True)
            .distinct()
            .count()
        )

        # Sin desglose por genero: el sistema es exclusivamente gineco-obstetrico,
        # todas las pacientes son femeninas (agrupacion de un solo valor).
        result = {
            "total_pacientes": total,
            "activos": activos,
            "inactivos": inactivos,
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
        """BÚSQUEDA AVANZADA - Multi-criterio con fuzzy search

        POST /api/pacientes/busqueda-avanzada/
        Body: {
            "nombre": "string",  # Fuzzy search
            "id_clinico": "string",
            "ci": "string",
            "fecha_desde": "YYYY-MM-DD",
            "fecha_hasta": "YYYY-MM-DD",
            "edad_min": int,
            "edad_max": int,
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
        estado_civil = request.data.get("estado_civil")
        embarazo_activo = request.data.get("embarazo_activo")
        riesgo_alto = request.data.get("riesgo_alto")

        # Iniciar queryset
        queryset = Paciente.objects.filter(activo=True)

        # ID Clínico
        if id_clinico:
            queryset = queryset.filter(id_clinico__icontains=id_clinico)

        # CI — campo cifrado, buscar por hash exacto (el MISMO del modelo)
        if ci:
            from .fields import compute_search_hash

            queryset = queryset.filter(ci_hash=compute_search_hash(ci))

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
    def activar(self, request, pk=None):
        """Reactivar un paciente inactivo"""
        paciente = self.get_object()
        paciente.activo = True
        paciente.save()

        # Reactivar es tan sensible como dar de baja: devuelve a circulacion
        # una historia clinica que alguien habia retirado, y hay que poder
        # reconstruir quien lo hizo.
        try:
            from auditoria.models import RegistroAuditoria

            RegistroAuditoria.registrar(
                usuario=request.user if getattr(request.user, "is_authenticated", False) else None,
                accion="ACTIVAR",
                modulo="Paciente",
                registro_id=str(paciente.id),
                detalle=f"Paciente reactivada. ID clinico: {paciente.id_clinico}",
                request=request,
            )
        except Exception:
            logger.warning("No se pudo auditar la reactivacion", exc_info=True)

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
        """NUEVA FUNCIONALIDAD: Historia Clínica Integrada Completa

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

        # La construcción del timeline y los contadores vive en
        # `construir_historia_clinica` para poder probarla sin HTTP ni PDF.
        timeline, estadisticas = construir_historia_clinica(paciente)

        # Generar PDF
        from embarazos.serializers import EmbarazoSerializer

        paciente_data = PacienteSerializer(paciente).data
        embarazos_data = EmbarazoSerializer(
            paciente.embarazos.all().order_by("-fecha_registro"), many=True,
        ).data

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

        antecedente = _antecedente_vigente(
            AntecedentePatologico, {"registrado_por": request.user}, paciente=paciente, tipo="personal",
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

        antecedente = _antecedente_vigente(
            AntecedentePatologico, {"registrado_por": request.user}, paciente=paciente, tipo="heredofamiliar",
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
            imc = round(float(paciente.peso_kg) / ((float(paciente.altura_cm) / 100) ** 2), 2)
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

    @action(detail=False, methods=["get"], url_path="exportar-csv")
    def exportar_lista_csv(self, request):
        """Listado de pacientes como CSV (mismas columnas que el Excel/PDF)."""
        from reportes.csv_clinico import respuesta_csv

        queryset = self.filter_queryset(self.get_queryset())
        return respuesta_csv("pacientes", [
            {"titulo": f"Listado de pacientes (total: {queryset.count()})",
             "encabezados": ["ID Clínico", "Nombre completo", "Edad", "CI", "Teléfono", "Ciudad", "Estado"],
             "filas": [[
                 p.id_clinico,
                 p.nombre_completo,
                 getattr(p, "edad", None),
                 p.ci,
                 p.telefono,
                 getattr(p, "ciudad", None),
                 "Activa" if p.activo else "Inactiva",
             ] for p in queryset]},
        ])

    @action(detail=False, methods=["get"], url_path="exportar-pdf")
    def exportar_pdf(self, request):
        """Listado de pacientes en PDF institucional, con distribución etaria.
        GET /api/pacientes/exportar-pdf/
        """
        from django.http import HttpResponse

        from reportes.pdf_clinico import PdfClinico

        queryset = self.filter_queryset(self.get_queryset())
        pacientes = list(queryset)

        pdf = PdfClinico("Listado de Pacientes", f"Total: {len(pacientes)} pacientes")
        pdf.seccion("Pacientes")
        pdf.tabla(
            ["ID Clínico", "Nombre completo", "Edad", "Teléfono", "Ciudad", "Estado"],
            [[
                p.id_clinico,
                p.nombre_completo,
                getattr(p, "edad", None),
                p.telefono,
                getattr(p, "ciudad", None),
                "Activa" if p.activo else "Inactiva",
            ] for p in pacientes[:200]],
        )

        edades = [p.edad for p in pacientes if getattr(p, "edad", None)]
        if edades:
            rangos = {"< 20": 0, "20–29": 0, "30–39": 0, "≥ 40": 0}
            for e in edades:
                if e < 20:
                    rangos["< 20"] += 1
                elif e < 30:
                    rangos["20–29"] += 1
                elif e < 40:
                    rangos["30–39"] += 1
                else:
                    rangos["≥ 40"] += 1
            pdf.grafico_barras("Distribución etaria de las pacientes", list(rangos), [float(v) for v in rangos.values()])
            pdf.explicacion(
                "Los extremos etarios (<20 y ≥40 años) concentran mayor riesgo "
                "obstétrico y ayudan a dimensionar la demanda de control prenatal "
                "de alto riesgo de la clínica.",
            )

        buffer = pdf.generar()
        response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="listado_pacientes.pdf"'
        return response
