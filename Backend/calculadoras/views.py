"""=============================================================================
VIEWSETS Y ENDPOINTS - CALCULADORAS MÉDICAS FMF
=============================================================================
Sistema completo de calculadoras obstétricas según protocolos FMF
Adaptado para condiciones de altura (La Paz, Bolivia - 3600-4000m)
=============================================================================
"""

from django.db.models import Avg, Count
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from core.permissions import FetalMedicalPermission
from rest_framework.response import Response

from .models import (
    BiomarcadorMOM,
    CalculadoraRiesgo,
    MedicionEcografica,
)
from .models_doppler import DopplerMaterno
from .serializers import (
    CalculadoraRiesgoCreateSerializer,
    CalculadoraRiesgoSerializer,
)
from .services.mom_converter import MOMConverter
from .services.risk_calculator import RiskCalculator


class CalculadoraRiesgoViewSet(viewsets.ModelViewSet):
    """ViewSet for obstetric risk calculators based on FMF protocols.

    Provides risk calculations for preeclampsia, trisomies, and gestational diabetes
    using Bayesian models adjusted for high-altitude conditions (La Paz, Bolivia).

    **Endpoints:**
    - `POST /api/calculadoras/calcular-preeclampsia/` - Calculate preeclampsia risk
    - `POST /api/calculadoras/calcular-trisomias/` - Calculate trisomy 21, 18, 13 risk
    - `POST /api/calculadoras/calcular-diabetes/` - Calculate gestational diabetes risk
    - `GET  /api/calculadoras/` - List all risk calculations
    - `GET  /api/calculadoras/{id}/` - Get specific calculation details

    **Authentication:** JWT Bearer token required
    **Permissions:** Authenticated users
    """

    queryset = CalculadoraRiesgo.objects.all()
    serializer_class = CalculadoraRiesgoSerializer
    permission_classes = [FetalMedicalPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "paciente",
        "tipo",
        "categoria_riesgo",
        "edad_gestacional_semanas",
    ]
    search_fields = ["paciente__nombre", "paciente__apellido_paterno", "tipo"]
    ordering_fields = ["fecha_calculo", "riesgo_porcentaje"]
    ordering = ["-fecha_calculo"]

    @extend_schema(
        summary="Calculate preeclampsia risk",
        description="Calculate preeclampsia risk using Bayesian FMF model with biomarker MoM conversion. "
        "Accepts maternal factors, biomarkers (PAM, UTPI, PLGF, sFLT1, PAPP-A), and Doppler measurements.",
        tags=["Risk Calculators"],
        request=OpenApiParameter(
            name="body", type=dict, description="Risk calculation parameters",
        ),
        responses={
            201: OpenApiResponse(description="Preeclampsia risk calculation completed"),
            400: OpenApiResponse(description="Bad Request - Invalid input data"),
        },
    )
    @action(detail=False, methods=["post"], url_path="calcular-preeclampsia")
    def calcular_preeclampsia(self, request):
        """Calcula riesgo de preeclampsia usando modelo Bayesiano FMF

        Parámetros:
            pass
        - paciente_id: ID del paciente
        - embarazo_id: ID del embarazo (opcional)
        - edad_gestacional_semanas: 7-42
        - edad_gestacional_dias: 0-6
        - edad_materna: 10-60 años
        - peso_kg, talla_cm, etnia, tabaquismo
        - Historia: hta_cronica, diabetes_previa, preeclampsia_previa, etc.
        - Biomarcadores: pam_crudo, utpi_crudo, plgf_crudo, sflt1_crudo, pappa_crudo
        - Doppler: pas_mmhg, pad_mmhg, utpi_izquierda, utpi_derecha

        Returns:
            pass
        - Calculadora completa con riesgo, interpretación y recomendaciones

        """
        serializer = CalculadoraRiesgoCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        # 1. Convertir biomarcadores a MoM
        mom_converter = MOMConverter()
        edad_gestacional_dias_total = (data["edad_gestacional_semanas"] * 7) + data.get(
            "edad_gestacional_dias", 0,
        )

        # Calcular MoMs
        biomarcadores_mom = {}

        if data.get("pam_crudo"):
            resultado_pam = mom_converter.calcular_mom(
                marcador="pam",
                valor_crudo=float(data["pam_crudo"]),
                edad_gestacional_dias=edad_gestacional_dias_total,
                peso_kg=float(data["peso_kg"]),
                etnia=data["etnia"],
                tabaquismo=data.get("tabaquismo", False),
                diabetes_tipo=data.get("diabetes_tipo"),
            )
            biomarcadores_mom["pam"] = resultado_pam

        if data.get("utpi_crudo"):
            resultado_utpi = mom_converter.calcular_mom(
                marcador="utpi",
                valor_crudo=float(data["utpi_crudo"]),
                edad_gestacional_dias=edad_gestacional_dias_total,
                peso_kg=float(data["peso_kg"]),
                etnia=data["etnia"],
                tabaquismo=data.get("tabaquismo", False),
            )
            biomarcadores_mom["utpi"] = resultado_utpi

        if data.get("plgf_crudo"):
            resultado_plgf = mom_converter.calcular_mom(
                marcador="plgf",
                valor_crudo=float(data["plgf_crudo"]),
                edad_gestacional_dias=edad_gestacional_dias_total,
                peso_kg=float(data["peso_kg"]),
                etnia=data["etnia"],
                tabaquismo=data.get("tabaquismo", False),
            )
            biomarcadores_mom["plgf"] = resultado_plgf

        if data.get("sflt1_crudo"):
            resultado_sflt1 = mom_converter.calcular_mom(
                marcador="sflt1",
                valor_crudo=float(data["sflt1_crudo"]),
                edad_gestacional_dias=edad_gestacional_dias_total,
                peso_kg=float(data["peso_kg"]),
                etnia=data["etnia"],
                tabaquismo=data.get("tabaquismo", False),
            )
            biomarcadores_mom["sflt1"] = resultado_sflt1

        if data.get("pappa_crudo"):
            resultado_pappa = mom_converter.calcular_mom(
                marcador="pappa",
                valor_crudo=float(data["pappa_crudo"]),
                edad_gestacional_dias=edad_gestacional_dias_total,
                peso_kg=float(data["peso_kg"]),
                etnia=data["etnia"],
                tabaquismo=data.get("tabaquismo", False),
            )
            biomarcadores_mom["pappa"] = resultado_pappa

        # 2. Calcular riesgo de preeclampsia
        risk_calc = RiskCalculator()

        resultado_riesgo = risk_calc.calcular_riesgo_preeclampsia(
            edad_materna=data["edad_materna"],
            imc=float(data["peso_kg"]) / (float(data["talla_cm"]) / 100) ** 2,
            etnia=data["etnia"],
            hta_cronica=data.get("hta_cronica", False),
            preeclampsia_previa=data.get("preeclampsia_previa", False),
            diabetes=data.get("diabetes_previa", False),
            lupus=data.get("lupus", False),
            sindrome_antifosfolipido=data.get("sindrome_antifosfolipido", False),
            madre_con_pe=data.get("madre_con_preeclampsia", False),
            paridad=data.get("paridad", 0),
            intervalo_meses=data.get("intervalo_interembarazo_meses"),
            metodo_concepcion=data.get("metodo_concepcion", "espontaneo"),
            pam_mom=biomarcadores_mom.get("pam", {}).get("mom", 1.0),
            utpi_mom=biomarcadores_mom.get("utpi", {}).get("mom", 1.0),
            plgf_mom=biomarcadores_mom.get("plgf", {}).get("mom")
            if "plgf" in biomarcadores_mom
            else None,
            sflt1_mom=biomarcadores_mom.get("sflt1", {}).get("mom")
            if "sflt1" in biomarcadores_mom
            else None,
            pappa_mom=biomarcadores_mom.get("pappa", {}).get("mom")
            if "pappa" in biomarcadores_mom
            else None,
            edad_gestacional_semanas=data["edad_gestacional_semanas"],
        )

        # 3. Crear registro de calculadora
        calculadora = CalculadoraRiesgo.objects.create(
            paciente_id=data["paciente_id"],
            embarazo_id=data.get("embarazo_id"),
            tipo="preeclampsia",
            edad_gestacional_semanas=data["edad_gestacional_semanas"],
            edad_gestacional_dias=data.get("edad_gestacional_dias", 0),
            edad_materna=data["edad_materna"],
            peso_kg=data["peso_kg"],
            talla_cm=data["talla_cm"],
            etnia=data["etnia"],
            tabaquismo=data.get("tabaquismo", False),
            hta_cronica=data.get("hta_cronica", False),
            diabetes_previa=data.get("diabetes_previa", False),
            diabetes_tipo=data.get("diabetes_tipo", "ninguna"),
            lupus=data.get("lupus", False),
            sindrome_antifosfolipido=data.get("sindrome_antifosfolipido", False),
            preeclampsia_previa=data.get("preeclampsia_previa", False),
            madre_con_preeclampsia=data.get("madre_con_preeclampsia", False),
            paridad=data.get("paridad", 0),
            intervalo_interembarazo_meses=data.get("intervalo_interembarazo_meses"),
            metodo_concepcion=data.get("metodo_concepcion", "espontaneo"),
            riesgo_porcentaje=resultado_riesgo["riesgo_porcentaje"],
            riesgo_ratio=resultado_riesgo["riesgo_ratio"],
            categoria_riesgo=resultado_riesgo["categoria_riesgo"],
            interpretacion_clinica=resultado_riesgo["interpretacion_clinica"],
            recomendaciones="\n".join(resultado_riesgo["recomendaciones"]),
            conducta_sugerida=resultado_riesgo["conducta_sugerida"],
            calculado_por=request.user,
            notas_adicionales=data.get("notas_adicionales", ""),
        )

        # 4. Guardar biomarcadores MoM
        for marcador_nombre, resultado in biomarcadores_mom.items():
            BiomarcadorMOM.objects.create(
                calculadora=calculadora,
                marcador=marcador_nombre,
                valor_crudo=resultado["valor_crudo"],
                unidad=resultado.get("unidad", ""),
                mediana_esperada=resultado["mediana_ajustada"],
                mediana_base=resultado["mediana_base"],
                mom_calculado=resultado["mom"],
                correccion_peso=resultado["correcciones"].get("peso", 1.0),
                correccion_etnia=resultado["correcciones"].get("etnia", 1.0),
                correccion_tabaco=resultado["correcciones"].get("tabaco", 1.0),
                correccion_diabetes=resultado["correcciones"].get("diabetes", 1.0),
            )

        # 5. Guardar doppler si existe
        if data.get("pas_mmhg") and data.get("pad_mmhg"):
            DopplerMaterno.objects.create(
                calculadora=calculadora,
                pas_mmhg=data["pas_mmhg"],
                pad_mmhg=data["pad_mmhg"],
                utpi_izquierda=data.get("utpi_izquierda"),
                utpi_derecha=data.get("utpi_derecha"),
            )

        # 6. Serializar y devolver
        serializer_output = CalculadoraRiesgoSerializer(calculadora)

        return Response(
            {
                "success": True,
                "message": "Cálculo de riesgo de preeclampsia completado exitosamente",
                "data": serializer_output.data,
                "resumen_riesgo": {
                    "porcentaje": resultado_riesgo["riesgo_porcentaje"],
                    "ratio": resultado_riesgo["riesgo_ratio"],
                    "categoria": resultado_riesgo["categoria_riesgo"],
                    "semaforo": resultado_riesgo["semaforo"],
                    "likelihood_ratios": resultado_riesgo["likelihood_ratios"],
                },
            },
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Calculate trisomy risk",
        description="Calculate risk for trisomies 21, 18, and 13 (First Trimester Combined Screening). "
        "Requires nuchal translucency measurement and biomarkers (PAPP-A, beta-hCG).",
        tags=["Risk Calculators"],
        request=OpenApiParameter(
            name="body", type=dict, description="Trisomy screening parameters",
        ),
        responses={
            201: OpenApiResponse(description="Trisomy screening completed"),
            400: OpenApiResponse(description="Bad Request - Invalid input data"),
        },
    )
    @action(detail=False, methods=["post"], url_path="calcular-trisomias")
    def calcular_trisomias(self, request):
        """Calcula riesgo de trisomías 21, 18 y 13 (Cribado Combinado 1º Trimestre)

        Parámetros:
            pass
        - edad_materna, edad_gestacional (11-13+6 semanas)
        - nt_mm: Translucencia nucal (mm)
        - fcf_lpm: Frecuencia cardíaca fetal (opcional)
        - pappa_crudo: PAPP-A valor crudo
        - bhcg_crudo: β-hCG libre valor crudo

        Returns:
            pass
        - Riesgos para T21, T18, T13 con interpretación

        """
        serializer = CalculadoraRiesgoCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        # Validar edad gestacional (11-13+6 semanas para NT)
        eg_dias_total = (data["edad_gestacional_semanas"] * 7) + data.get(
            "edad_gestacional_dias", 0,
        )
        if eg_dias_total < 77 or eg_dias_total > 97:
            return Response(
                {
                    "success": False,
                    "error": "La edad gestacional debe estar entre 11+0 y 13+6 semanas para cribado combinado",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Convertir biomarcadores a MoM
        mom_converter = MOMConverter()

        pappa_result = mom_converter.calcular_mom(
            marcador="pappa",
            valor_crudo=float(data.get("pappa_crudo", 1.0)),
            edad_gestacional_dias=eg_dias_total,
            peso_kg=float(data["peso_kg"]),
            etnia=data["etnia"],
            tabaquismo=data.get("tabaquismo", False),
        )
        pappa_mom = pappa_result["mom"]

        bhcg_result = mom_converter.calcular_mom(
            marcador="bhcg",
            valor_crudo=float(data.get("bhcg_crudo", 1.0)),
            edad_gestacional_dias=eg_dias_total,
            peso_kg=float(data["peso_kg"]),
            etnia=data["etnia"],
            tabaquismo=data.get("tabaquismo", False),
        )
        bhcg_mom = bhcg_result["mom"]

        # Calcular riesgo
        risk_calc = RiskCalculator()

        resultado = risk_calc.calcular_riesgo_trisomias(
            edad_materna=data["edad_materna"],
            edad_gestacional_dias=eg_dias_total,
            nt_mm=float(data.get("nt_mm", 1.5)),
            fcf_lpm=data.get("fcf_lpm"),
            pappa_mom=pappa_mom,
            bhcg_mom=bhcg_mom,
        )

        # Crear registro
        calc = CalculadoraRiesgo.objects.create(
            paciente_id=data["paciente_id"],
            embarazo_id=data.get("embarazo_id"),
            tipo="trisomias",
            edad_gestacional_semanas=data["edad_gestacional_semanas"],
            edad_gestacional_dias=data.get("edad_gestacional_dias", 0),
            edad_materna=data["edad_materna"],
            peso_kg=data["peso_kg"],
            talla_cm=data["talla_cm"],
            etnia=data["etnia"],
            tabaquismo=data.get("tabaquismo", False),
            paridad=data.get("paridad", 0),
            riesgo_porcentaje=resultado["trisomia_21"]["riesgo_porcentaje"],
            riesgo_ratio=resultado["trisomia_21"]["riesgo_ratio"],
            categoria_riesgo="alto"
            if resultado["trisomia_21"]["categoria"] == "alto_riesgo"
            else "bajo",
            interpretacion_clinica=resultado["interpretacion_clinica"],
            recomendaciones="\n".join(resultado["recomendaciones"]),
            calculado_por=request.user,
        )

        # Guardar biomarcadores
        BiomarcadorMOM.objects.create(
            calculadora=calc,
            marcador="pappa",
            valor_crudo=data.get("pappa_crudo"),
            unidad="mIU/mL",
            mediana_esperada=pappa_result["mediana_ajustada"],
            mediana_base=pappa_result["mediana_base"],
            mom_calculado=pappa_mom,
            correccion_peso=pappa_result["correcciones"]["peso"],
            correccion_etnia=pappa_result["correcciones"]["etnia"],
        )

        BiomarcadorMOM.objects.create(
            calculadora=calc,
            marcador="bhcg",
            valor_crudo=data.get("bhcg_crudo"),
            unidad="ng/mL",
            mediana_esperada=bhcg_result["mediana_ajustada"],
            mediana_base=bhcg_result["mediana_base"],
            mom_calculado=bhcg_mom,
            correccion_peso=bhcg_result["correcciones"]["peso"],
            correccion_etnia=bhcg_result["correcciones"]["etnia"],
        )

        # Guardar medición NT
        if data.get("nt_mm"):
            MedicionEcografica.objects.create(
                calculadora=calc,
                nt_mm=data["nt_mm"],
                fcf_lpm=data.get("fcf_lpm"),
                crl_mm=data.get("crl_mm"),
            )

        serializer_output = CalculadoraRiesgoSerializer(calc)

        return Response(
            {
                "success": True,
                "message": "Cribado combinado de trisomías completado",
                "data": serializer_output.data,
                "riesgos_detallados": {
                    "trisomia_21": resultado["trisomia_21"],
                    "trisomia_18": resultado["trisomia_18"],
                    "trisomia_13": resultado["trisomia_13"],
                },
            },
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Calculate gestational diabetes risk",
        description="Calculate gestational diabetes risk based on maternal factors and medical history.",
        tags=["Risk Calculators"],
        request=OpenApiParameter(
            name="body", type=dict, description="Diabetes risk parameters",
        ),
        responses={
            201: OpenApiResponse(description="Diabetes risk calculation completed"),
            400: OpenApiResponse(description="Bad Request - Invalid input data"),
        },
    )
    @action(detail=False, methods=["post"], url_path="calcular-diabetes")
    def calcular_diabetes(self, request):
        """Calcula riesgo de diabetes gestacional

        Parámetros:
            pass
        - edad_materna, peso_kg, talla_cm, etnia
        - historia_familiar_diabetes: Boolean
        - diabetes_gestacional_previa: Boolean
        - macrosomia_previa: Boolean

        Returns:
            pass
        - Riesgo de diabetes gestacional con recomendaciones OGTT

        """
        serializer = CalculadoraRiesgoCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        # Calcular riesgo
        risk_calc = RiskCalculator()

        resultado = risk_calc.calcular_riesgo_diabetes_gestacional(
            edad_materna=data["edad_materna"],
            imc=float(data["peso_kg"]) / (float(data["talla_cm"]) / 100) ** 2,
            etnia=data["etnia"],
            diabetes_familiar=data.get("historia_familiar_diabetes", False),
            diabetes_gestacional_previa=data.get("diabetes_gestacional_previa", False),
            macrosomia_previa=data.get("macrosomia_previa", False),
        )

        # Crear registro
        calc = CalculadoraRiesgo.objects.create(
            paciente_id=data["paciente_id"],
            embarazo_id=data.get("embarazo_id"),
            tipo="diabetes_gestacional",
            edad_gestacional_semanas=data["edad_gestacional_semanas"],
            edad_gestacional_dias=data.get("edad_gestacional_dias", 0),
            edad_materna=data["edad_materna"],
            peso_kg=data["peso_kg"],
            talla_cm=data["talla_cm"],
            etnia=data["etnia"],
            historia_familiar_diabetes=data.get("historia_familiar_diabetes", False),
            diabetes_gestacional_previa=data.get("diabetes_gestacional_previa", False),
            macrosomia_previa=data.get("macrosomia_previa", False),
            paridad=data.get("paridad", 0),
            riesgo_porcentaje=resultado["riesgo_porcentaje"],
            riesgo_ratio=resultado["riesgo_ratio"],
            categoria_riesgo=resultado["categoria_riesgo"],
            interpretacion_clinica=resultado["interpretacion_clinica"],
            recomendaciones="\n".join(resultado["recomendaciones"]),
            calculado_por=request.user,
        )

        serializer_output = CalculadoraRiesgoSerializer(calc)

        return Response(
            {
                "success": True,
                "message": "Evaluación de riesgo de diabetes gestacional completada",
                "data": serializer_output.data,
            },
            status=status.HTTP_201_CREATED,
        )


# =============================================================================
# VIEWSETS DE LABORATORIO CLÍNICO
# =============================================================================

from .models_laboratorio import Bioquimica, Hemograma, MarcadorEmbarazo
from .serializers import (
    BioquimicaListSerializer,
    BioquimicaSerializer,
    HemogramaListSerializer,
    HemogramaSerializer,
    MarcadorEmbarazoCreateSerializer,
    MarcadorEmbarazoSerializer,
)
from .services.calculador_mom import CalculadorMoM


class HemogramaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de hemogramas completos

    Endpoints:
        pass
    - GET    /api/calculadoras/hemogramas/
    - POST   /api/calculadoras/hemogramas/
    - GET    /api/calculadoras/hemogramas/{id}/
    - PUT    /api/calculadoras/hemogramas/{id}/
    - DELETE /api/calculadoras/hemogramas/{id}/
    - GET    /api/calculadoras/hemogramas/por_paciente/paciente_id=X
    - GET    /api/calculadoras/hemogramas/por_embarazo/embarazo_id=X
    - GET    /api/calculadoras/hemogramas/criticos/
    - GET    /api/calculadoras/hemogramas/estadisticas/
    """

    queryset = Hemograma.objects.filter(activo=True)
    permission_classes = [FetalMedicalPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["paciente", "embarazo", "clasificacion", "es_critico"]
    search_fields = ["paciente__nombre", "paciente__apellido_paterno"]
    ordering_fields = ["fecha_toma", "hemoglobina", "leucocitos", "plaquetas"]
    ordering = ["-fecha_toma"]

    def get_serializer_class(self):
        """Get serializer class"""
        if self.action == "list":
            return HemogramaListSerializer
        return HemogramaSerializer

    def perform_create(self, serializer):
        """✅ TRAZABILIDAD: Crear hemograma y asignar médico solicitante y created_by"""
        serializer.save(
            medico_solicitante=self.request.user, created_by=self.request.user,
        )

    def perform_update(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar updated_by al actualizar"""
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=["get"], url_path="por_paciente")
    def por_paciente(self, request):
        """Obtener hemogramas de un paciente específico"""
        paciente_id = request.query_params.get("paciente_id")
        if not paciente_id:
            return Response(
                {"error": "paciente_id es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        hemogramas = self.queryset.filter(paciente_id=paciente_id)
        serializer = HemogramaSerializer(hemogramas, many=True)

        return Response(
            {
                "success": True,
                "count": hemogramas.count(),
                "data": serializer.data,
            },
        )

    @action(detail=False, methods=["get"], url_path="por_embarazo")
    def por_embarazo(self, request):
        """Obtener hemogramas de un embarazo específico"""
        embarazo_id = request.query_params.get("embarazo_id")
        if not embarazo_id:
            return Response(
                {"error": "embarazo_id es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        hemogramas = self.queryset.filter(embarazo_id=embarazo_id)
        serializer = HemogramaSerializer(hemogramas, many=True)

        return Response(
            {
                "success": True,
                "count": hemogramas.count(),
                "data": serializer.data,
            },
        )

    @action(detail=False, methods=["get"], url_path="criticos")
    def criticos(self, _request):
        """Obtener todos los hemogramas con valores críticos"""
        hemogramas = self.queryset.filter(es_critico=True)
        serializer = HemogramaSerializer(hemogramas, many=True)

        return Response(
            {
                "success": True,
                "count": hemogramas.count(),
                "data": serializer.data,
            },
        )

    @action(detail=False, methods=["get"], url_path="estadisticas")
    def estadisticas(self, _request):
        """Estadísticas generales de hemogramas"""

        total = self.queryset.count()
        criticos = self.queryset.filter(es_critico=True).count()

        por_clasificacion = (
            self.queryset.values("clasificacion")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        promedios = self.queryset.aggregate(
            hemoglobina_promedio=Avg("hemoglobina"),
            leucocitos_promedio=Avg("leucocitos"),
            plaquetas_promedio=Avg("plaquetas"),
        )

        return Response(
            {
                "success": True,
                "total": total,
                "criticos": criticos,
                "porcentaje_criticos": round((criticos / total * 100), 2)
                if total > 0
                else 0,
                "por_clasificacion": list(por_clasificacion),
                "promedios": promedios,
            },
        )


class BioquimicaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de bioquímicas completas

    Endpoints similares a HemogramaViewSet
    """

    queryset = Bioquimica.objects.filter(activo=True)
    permission_classes = [FetalMedicalPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["paciente", "embarazo", "es_critico"]
    search_fields = ["paciente__nombre", "paciente__apellido_paterno"]
    ordering_fields = ["fecha_toma", "glucosa_ayunas", "creatinina"]
    ordering = ["-fecha_toma"]

    def get_serializer_class(self):
        """Get serializer class"""
        if self.action == "list":
            return BioquimicaListSerializer
        return BioquimicaSerializer

    def perform_create(self, serializer):
        """✅ TRAZABILIDAD: Crear bioquímica y asignar médico solicitante y created_by"""
        serializer.save(
            medico_solicitante=self.request.user, created_by=self.request.user,
        )

    def perform_update(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar updated_by al actualizar"""
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=["get"], url_path="por_paciente")
    def por_paciente(self, request):
        """Obtener bioquímicas de un paciente"""
        paciente_id = request.query_params.get("paciente_id")
        if not paciente_id:
            return Response(
                {"error": "paciente_id es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bioquimicas = self.queryset.filter(paciente_id=paciente_id)
        serializer = BioquimicaSerializer(bioquimicas, many=True)

        return Response(
            {
                "success": True,
                "count": bioquimicas.count(),
                "data": serializer.data,
            },
        )

    @action(detail=False, methods=["get"], url_path="por_embarazo")
    def por_embarazo(self, request):
        """Obtener bioquímicas de un embarazo"""
        embarazo_id = request.query_params.get("embarazo_id")
        if not embarazo_id:
            return Response(
                {"error": "embarazo_id es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bioquimicas = self.queryset.filter(embarazo_id=embarazo_id)
        serializer = BioquimicaSerializer(bioquimicas, many=True)

        return Response(
            {
                "success": True,
                "count": bioquimicas.count(),
                "data": serializer.data,
            },
        )

    @action(detail=False, methods=["get"], url_path="criticos")
    def criticos(self, _request):
        """Obtener bioquímicas con valores críticos"""
        bioquimicas = self.queryset.filter(es_critico=True)
        serializer = BioquimicaSerializer(bioquimicas, many=True)

        return Response(
            {
                "success": True,
                "count": bioquimicas.count(),
                "data": serializer.data,
            },
        )


class MarcadorEmbarazoViewSet(viewsets.ModelViewSet):
    """ViewSet para marcadores de embarazo con cálculo automático de MoM

    Endpoints:
        pass
    - POST   /api/calculadoras/marcadores-embarazo/ - Crea con cálculo MoM
    - GET    /api/calculadoras/marcadores-embarazo/
    - GET    /api/calculadoras/marcadores-embarazo/{id}/
    - GET    /api/calculadoras/marcadores-embarazo/por_embarazo/embarazo_id=X
    - POST   /api/calculadoras/marcadores-embarazo/calcular_mom/ - Solo cálculo
    """

    queryset = MarcadorEmbarazo.objects.filter(activo=True)
    permission_classes = [FetalMedicalPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["paciente", "embarazo"]
    search_fields = ["paciente__nombre", "paciente__apellido_paterno"]
    ordering_fields = ["fecha_toma", "semanas_gestacion"]
    ordering = ["-fecha_toma"]

    def get_serializer_class(self):
        """Get serializer class"""
        if self.action == "create":
            return MarcadorEmbarazoCreateSerializer
        return MarcadorEmbarazoSerializer

    def create(self, request, *args, **kwargs):
        """Crear marcador con cálculo automático de MoM"""
        serializer = MarcadorEmbarazoCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        # Calcular MoM para cada marcador
        calculador_mom = CalculadorMoM()

        # Crear el marcador base
        marcador = MarcadorEmbarazo(
            paciente_id=data["paciente_id"],
            embarazo_id=data["embarazo_id"],
            medico_solicitante_id=data["medico_solicitante_id"],
            fecha_toma=data["fecha_toma"],
            semanas_gestacion=data["semanas_gestacion"],
            dias_adicionales=data.get("dias_adicionales", 0),
        )

        # Asignar valores crudos
        marcador.beta_hcg = data.get("beta_hcg")
        marcador.papp_a = data.get("papp_a")
        marcador.free_bhcg = data.get("free_bhcg")
        marcador.plgf = data.get("plgf")
        marcador.sflt1 = data.get("sflt1")

        # Calcular MoM para PAPP-A
        if marcador.papp_a:
            resultado_pappa = calculador_mom.calcular_mom(
                valor_medido=float(marcador.papp_a),
                marcador="PAPP-A",
                semanas=data["semanas_gestacion"],
                peso_kg=float(data["peso_kg"]),
                etnia=data.get("etnia", "mestizo"),
                fumadora=data.get("fumadora", False),
                diabetes=data.get("diabetes", False),
                fiv=data.get("fiv", False),
                altitud_bolivia=data.get("altitud_bolivia", True),
            )
            marcador.papp_a_mom = resultado_pappa

        # Calcular MoM para free β-hCG
        if marcador.free_bhcg:
            resultado_bhcg = calculador_mom.calcular_mom(
                valor_medido=float(marcador.free_bhcg),
                marcador="free_bhcg",
                semanas=data["semanas_gestacion"],
                peso_kg=float(data["peso_kg"]),
                etnia=data.get("etnia", "mestizo"),
                fumadora=data.get("fumadora", False),
                diabetes=data.get("diabetes", False),
                fiv=data.get("fiv", False),
                altitud_bolivia=data.get("altitud_bolivia", True),
            )
            marcador.free_bhcg_mom = resultado_bhcg

        # Calcular MoM para PlGF
        if marcador.plgf:
            resultado_plgf = calculador_mom.calcular_mom(
                valor_medido=float(marcador.plgf),
                marcador="PlGF",
                semanas=data["semanas_gestacion"],
                peso_kg=float(data["peso_kg"]),
                etnia=data.get("etnia", "mestizo"),
                fumadora=data.get("fumadora", False),
                diabetes=data.get("diabetes", False),
                fiv=data.get("fiv", False),
                altitud_bolivia=data.get("altitud_bolivia", True),
            )
            marcador.plgf_mom = resultado_plgf

        # Calcular MoM para sFlt-1
        if marcador.sflt1:
            resultado_sflt = calculador_mom.calcular_mom(
                valor_medido=float(marcador.sflt1),
                marcador="sFlt-1",
                semanas=data["semanas_gestacion"],
                peso_kg=float(data["peso_kg"]),
                etnia=data.get("etnia", "mestizo"),
                fumadora=data.get("fumadora", False),
                diabetes=data.get("diabetes", False),
                fiv=data.get("fiv", False),
                altitud_bolivia=data.get("altitud_bolivia", True),
            )
            marcador.sflt1_mom = resultado_sflt

        # Calcular ratio sFlt-1/PlGF
        if marcador.sflt1 and marcador.plgf:
            marcador.ratio_sflt_plgf = marcador.sflt1 / marcador.plgf

        # Clasificar
        marcador.clasificar()

        # Guardar
        marcador.save()

        # Serializar y retornar
        output_serializer = MarcadorEmbarazoSerializer(marcador)

        return Response(
            {
                "success": True,
                "message": "Marcador de embarazo creado con MoM calculados",
                "data": output_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"], url_path="por_embarazo")
    def por_embarazo(self, request):
        """Obtener marcadores de un embarazo"""
        embarazo_id = request.query_params.get("embarazo_id")
        if not embarazo_id:
            return Response(
                {"error": "embarazo_id es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        marcadores = self.queryset.filter(embarazo_id=embarazo_id)
        serializer = MarcadorEmbarazoSerializer(marcadores, many=True)

        return Response(
            {
                "success": True,
                "count": marcadores.count(),
                "data": serializer.data,
            },
        )

    @action(detail=False, methods=["post"], url_path="calcular_mom")
    def calcular_mom(self, request):
        """Calcular solo MoM sin guardar registro"""
        data = request.data

        if not all(
            [data.get("valor_medido"), data.get("marcador"), data.get("semanas")],
        ):
            return Response(
                {"error": "valor_medido, marcador y semanas son requeridos"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        calculador_mom = CalculadorMoM()

        resultado = calculador_mom.calcular_mom(
            valor_medido=float(data["valor_medido"]),
            marcador=data["marcador"],
            semanas=int(data["semanas"]),
            peso_kg=float(data.get("peso_kg", 70.0)),
            etnia=data.get("etnia", "mestizo"),
            fumadora=data.get("fumadora", False),
            diabetes=data.get("diabetes", False),
            fiv=data.get("fiv", False),
            altitud_bolivia=data.get("altitud_bolivia", True),
        )

        clasificacion_mom = calculador_mom.clasificar_mom(resultado)

        return Response(
            {
                "success": True,
                "mom_calculado": resultado,
                "clasificacion": clasificacion_mom,
            },
        )


# =============================================================================
# DOPPLER MATERNO
# =============================================================================


class DopplerMaternoViewSet(viewsets.ModelViewSet):
    """ViewSet para Doppler de Arterias Uterinas Maternas"""

    if DopplerMaterno is not None:
        queryset = DopplerMaterno.objects.select_related(
            "paciente", "embarazo", "realizado_por",
        )
        from .serializers import DopplerMaternoSerializer

        serializer_class = DopplerMaternoSerializer
    permission_classes = [FetalMedicalPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["paciente", "embarazo", "lado", "clasificacion"]
    search_fields = ["paciente__nombre", "paciente__apellido_paterno"]
    ordering_fields = ["fecha_examen", "edad_gestacional_semanas"]
    ordering = ["-fecha_examen"]

    @action(detail=False, methods=["get"], url_path="por-paciente")
    def por_paciente(self, request):
        """Dopplers por paciente específico"""
        paciente_id = request.query_params.get("paciente_id")
        if not paciente_id:
            return Response(
                {"error": "paciente_id requerido"}, status=status.HTTP_400_BAD_REQUEST,
            )
        dopplers = self.queryset.filter(paciente_id=paciente_id)
        serializer = self.serializer_class(dopplers, many=True)
        return Response(
            {"success": True, "count": dopplers.count(), "data": serializer.data},
        )

    @action(detail=False, methods=["get"], url_path="alto-riesgo")
    def alto_riesgo(self, _request):
        """Dopplers con alto riesgo de preeclampsia"""
        dopplers = self.queryset.filter(escotadura_diastolica=True)
        serializer = self.serializer_class(dopplers, many=True)
        return Response(
            {"success": True, "count": dopplers.count(), "data": serializer.data},
        )

    @action(detail=False, methods=["get"], url_path="estadisticas")
    def estadisticas(self, _request):
        """Estadísticas de dopplers maternos"""
        total = self.queryset.count()
        alto_riesgo = self.queryset.filter(escotadura_diastolica=True).count()
        por_clasificacion = (
            self.queryset.values("clasificacion")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        promedio_ip = self.queryset.aggregate(ip_promedio=Avg("ip"))
        return Response(
            {
                "success": True,
                "total": total,
                "alto_riesgo": alto_riesgo,
                "por_clasificacion": list(por_clasificacion),
                "promedios": promedio_ip,
            },
        )
