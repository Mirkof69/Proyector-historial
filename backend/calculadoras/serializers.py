"""=============================================================================
SERIALIZERS - CALCULADORAS MÉDICAS
=============================================================================
"""

from rest_framework import serializers

from .models import (
    BiomarcadorMOM,
    CalculadoraRiesgo,
    MedicionEcografica,
)

try:
    from .models_doppler import DopplerMaterno
except ImportError:
    DopplerMaterno = None  # type: ignore
try:
    from .models_historial import CalculoHistorial
except ImportError:
    CalculoHistorial = None  # type: ignore
from pacientes.serializers import PacienteSerializer


class BiomarcadorMOMSerializer(serializers.ModelSerializer):
    """Serializer para biomarcadores MoM"""

    marcador_display = serializers.CharField(
        source="get_marcador_display", read_only=True,
    )

    class Meta:
        """Meta"""
        model = BiomarcadorMOM
        fields = [
            "id",
            "marcador",
            "marcador_display",
            "valor_crudo",
            "unidad",
            "mediana_esperada",
            "mediana_base",
            "mom_calculado",
            "correccion_peso",
            "correccion_etnia",
            "correccion_tabaco",
            "correccion_diabetes",
            "dentro_rango",
            "interpretacion",
            "fecha_medicion",
        ]
        read_only_fields = [
            "mediana_esperada",
            "mediana_base",
            "mom_calculado",
            "correccion_peso",
            "correccion_etnia",
            "correccion_tabaco",
            "correccion_diabetes",
            "dentro_rango",
            "interpretacion",
        ]


class MedicionEcograficaSerializer(serializers.ModelSerializer):
    """Serializer para mediciones ecográficas"""

    class Meta:
        """Meta"""
        model = MedicionEcografica
        fields = [
            "id",
            "crl_mm",
            "nt_mm",
            "fcf_lpm",
            "bpd_mm",
            "hc_mm",
            "ac_mm",
            "fl_mm",
            "efw_gramos",
            "nt_percentil",
            "efw_percentil",
            "crl_percentil",
            "longitud_cervical_mm",
            "fecha_medicion",
        ]

    def validate_valor(self, value):
        if value is not None and (value < 0 or value > 100000):
            raise serializers.ValidationError(
                "El valor está fuera del rango médico permitido",
            )
        return value

    def validate(self, data):
        ranges = {
            "crl_mm": (0, 120),
            "nt_mm": (0, 15),
            "fcf_lpm": (60, 220),
            "bpd_mm": (0, 120),
            "hc_mm": (0, 400),
            "ac_mm": (0, 400),
            "fl_mm": (0, 100),
            "efw_gramos": (0, 6000),
            "nt_percentil": (0, 100),
            "efw_percentil": (0, 100),
            "crl_percentil": (0, 100),
            "longitud_cervical_mm": (0, 60),
        }
        for field, (min_val, max_val) in ranges.items():
            val = data.get(field)
            if val is not None and (val < min_val or val > max_val):
                raise serializers.ValidationError(
                    {field: f"El valor debe estar entre {min_val} y {max_val}"},
                )
        return data


# Doppler Materno
if DopplerMaterno is not None:

    class DopplerMaternoSerializer(serializers.ModelSerializer):
        """Serializer para doppler materno"""

        lado_display = serializers.CharField(source="get_lado_display", read_only=True)
        clasificacion_display = serializers.CharField(
            source="get_clasificacion_display", read_only=True,
        )
        paciente_nombre = serializers.SerializerMethodField()

        class Meta:
            """Meta"""
            model = DopplerMaterno
            fields = [
                "id",
                "paciente",
                "paciente_nombre",
                "embarazo",
                "fecha_examen",
                "edad_gestacional_semanas",
                "edad_gestacional_dias",
                "lado",
                "lado_display",
                "ps_cm_s",
                "ed_cm_s",
                "ri",
                "ip",
                "s_d_ratio",
                "escotadura_diastolica",
                "clasificacion",
                "clasificacion_display",
                "realizado_por",
                "fecha_registro",
                "notas",
                "es_alto_riesgo",
            ]
            read_only_fields = ["ri", "s_d_ratio", "es_alto_riesgo"]

        def get_paciente_nombre(self, obj):
            """Get paciente nombre"""
            return obj.paciente.nombre_completo if obj.paciente else None


class CalculadoraRiesgoSerializer(serializers.ModelSerializer):
    """Serializer principal para calculadora de riesgo"""

    paciente = PacienteSerializer(read_only=True)
    paciente_id = serializers.IntegerField(write_only=True)
    embarazo_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True,
    )

    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    categoria_display = serializers.CharField(
        source="get_categoria_riesgo_display", read_only=True,
    )
    etnia_display = serializers.CharField(source="get_etnia_display", read_only=True)

    edad_gestacional_texto = serializers.CharField(read_only=True)

    # Nested
    biomarcadores = BiomarcadorMOMSerializer(many=True, read_only=True)
    mediciones_eco = MedicionEcograficaSerializer(many=True, read_only=True)

    class Meta:
        """Meta"""
        model = CalculadoraRiesgo
        fields = [
            "id",
            "paciente",
            "paciente_id",
            "embarazo",
            "embarazo_id",
            "tipo",
            "tipo_display",
            "edad_gestacional_semanas",
            "edad_gestacional_dias",
            "edad_gestacional_texto",
            "edad_materna",
            "peso_kg",
            "talla_cm",
            "imc",
            "etnia",
            "etnia_display",
            "tabaquismo",
            "hta_cronica",
            "diabetes_previa",
            "diabetes_tipo",
            "lupus",
            "sindrome_antifosfolipido",
            "preeclampsia_previa",
            "diabetes_gestacional_previa",
            "parto_pretermino_previo",
            "macrosomia_previa",
            "historia_familiar_diabetes",
            "madre_con_preeclampsia",
            "paridad",
            "intervalo_interembarazo_meses",
            "metodo_concepcion",
            "riesgo_porcentaje",
            "riesgo_ratio",
            "categoria_riesgo",
            "categoria_display",
            "interpretacion_clinica",
            "recomendaciones",
            "conducta_sugerida",
            "fecha_calculo",
            "calculado_por",
            "notas_adicionales",
            "biomarcadores",
            "mediciones_eco",
        ]
        read_only_fields = [
            "imc",
            "edad_gestacional_texto",
            "riesgo_porcentaje",
            "riesgo_ratio",
            "categoria_riesgo",
            "interpretacion_clinica",
            "recomendaciones",
            "conducta_sugerida",
            "fecha_calculo",
        ]


class CalculadoraRiesgoCreateSerializer(serializers.Serializer):
    """Serializer para crear nueva calculadora con cálculo automático"""

    # Datos básicos
    paciente_id = serializers.IntegerField()
    embarazo_id = serializers.IntegerField(required=False, allow_null=True)
    tipo = serializers.ChoiceField(choices=CalculadoraRiesgo.TIPO_CALCULADORA)
    edad_gestacional_semanas = serializers.IntegerField(min_value=7, max_value=42)
    edad_gestacional_dias = serializers.IntegerField(
        min_value=0, max_value=6, default=0,
    )

    # Datos maternos
    edad_materna = serializers.IntegerField(min_value=10, max_value=60)
    peso_kg = serializers.DecimalField(max_digits=5, decimal_places=2)
    talla_cm = serializers.DecimalField(max_digits=5, decimal_places=2)
    etnia = serializers.ChoiceField(choices=CalculadoraRiesgo.ETNIA_CHOICES)
    tabaquismo = serializers.BooleanField(default=False)

    # Historia médica
    hta_cronica = serializers.BooleanField(default=False)
    diabetes_previa = serializers.BooleanField(default=False)
    diabetes_tipo = serializers.ChoiceField(
        choices=[("tipo1", "Tipo 1"), ("tipo2", "Tipo 2"), ("ninguna", "Ninguna")],
        default="ninguna",
    )
    lupus = serializers.BooleanField(default=False)
    sindrome_antifosfolipido = serializers.BooleanField(default=False)

    # Historia obstétrica
    preeclampsia_previa = serializers.BooleanField(default=False)
    diabetes_gestacional_previa = serializers.BooleanField(default=False)
    macrosomia_previa = serializers.BooleanField(default=False)
    historia_familiar_diabetes = serializers.BooleanField(default=False)
    madre_con_preeclampsia = serializers.BooleanField(default=False)
    paridad = serializers.IntegerField(min_value=0, default=0)
    intervalo_interembarazo_meses = serializers.IntegerField(
        required=False, allow_null=True,
    )
    metodo_concepcion = serializers.ChoiceField(
        choices=[("espontaneo", "Espontáneo"), ("iv", "FIV"), ("otro", "Otro")],
        default="espontaneo",
    )

    # Biomarcadores (valores crudos - se convertirán a MoM)
    pam_crudo = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, allow_null=True,
    )
    utpi_crudo = serializers.DecimalField(
        max_digits=4, decimal_places=2, required=False, allow_null=True,
    )
    plgf_crudo = serializers.DecimalField(
        max_digits=8, decimal_places=2, required=False, allow_null=True,
    )
    sflt1_crudo = serializers.DecimalField(
        max_digits=8, decimal_places=2, required=False, allow_null=True,
    )
    pappa_crudo = serializers.DecimalField(
        max_digits=8, decimal_places=2, required=False, allow_null=True,
    )
    bhcg_crudo = serializers.DecimalField(
        max_digits=8, decimal_places=2, required=False, allow_null=True,
    )

    # Mediciones ecográficas
    nt_mm = serializers.DecimalField(
        max_digits=4, decimal_places=2, required=False, allow_null=True,
    )
    fcf_lpm = serializers.IntegerField(required=False, allow_null=True)
    crl_mm = serializers.DecimalField(
        max_digits=6, decimal_places=2, required=False, allow_null=True,
    )

    # Doppler
    pas_mmhg = serializers.IntegerField(required=False, allow_null=True)
    pad_mmhg = serializers.IntegerField(required=False, allow_null=True)
    utpi_izquierda = serializers.DecimalField(
        max_digits=4, decimal_places=2, required=False, allow_null=True,
    )
    utpi_derecha = serializers.DecimalField(
        max_digits=4, decimal_places=2, required=False, allow_null=True,
    )

    # Notas
    notas_adicionales = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        return instance


class CorreccionMOMParametrosSerializer(serializers.Serializer):
    """Serializer para parámetros de corrección MoM"""

    peso = serializers.DecimalField(max_digits=5, decimal_places=2)
    etnia = serializers.ChoiceField(
        choices=["caucasico", "afroamericano", "asiatico", "mestizo", "otro"],
    )
    fumadora = serializers.BooleanField()
    diabetes = serializers.BooleanField()

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        return instance

    def validate_parametros(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Los parámetros deben ser un diccionario")
        return value

    def validate(self, data):
        peso = data.get("peso")
        if peso is not None and (peso < 30 or peso > 200):
            raise serializers.ValidationError(
                {"peso": "El peso debe estar entre 30 y 200 kg"},
            )
        return data


# =============================================================================
# SERIALIZERS LABORATORIO CLÍNICO
# =============================================================================

from .models_laboratorio import Bioquimica, Hemograma, MarcadorEmbarazo


class HemogramaSerializer(serializers.ModelSerializer):
    """Serializer para hemograma completo"""

    paciente_nombre = serializers.CharField(
        source="paciente.nombre_completo", read_only=True,
    )
    medico_nombre = serializers.CharField(
        source="medico_solicitante.get_full_name", read_only=True,
    )
    clasificacion_display = serializers.CharField(
        source="get_clasificacion_display", read_only=True,
    )

    class Meta:
        """Meta"""
        model = Hemograma
        fields = [
            "id",
            "paciente",
            "paciente_nombre",
            "embarazo",
            "medico_solicitante",
            "medico_nombre",
            "fecha_toma",
            "fecha_resultado",
            "semanas_gestacion",
            # Eritrograma
            "hemoglobina",
            "hematocrito",
            "eritrocitos",
            "vcm",
            "hcm",
            "chcm",
            "rdw",
            # Leucograma
            "leucocitos",
            "neutrofilos",
            "linfocitos",
            "monocitos",
            "eosinofilos",
            "basofilos",
            # Plaquetas
            "plaquetas",
            "vpm",
            # Clasificación
            "clasificacion",
            "clasificacion_display",
            "es_critico",
            "alertas",
            "interpretacion_automatica",
            "observaciones_medicas",
            # Auditoría
            "activo",
            "fecha_creacion",
            "fecha_modificacion",
        ]
        read_only_fields = [
            "clasificacion",
            "es_critico",
            "alertas",
            "interpretacion_automatica",
            "fecha_resultado",
            "fecha_creacion",
            "fecha_modificacion",
        ]


class HemogramaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado"""

    paciente_nombre = serializers.CharField(
        source="paciente.nombre_completo", read_only=True,
    )
    clasificacion_display = serializers.CharField(
        source="get_clasificacion_display", read_only=True,
    )

    class Meta:
        """Meta"""
        model = Hemograma
        fields = [
            "id",
            "paciente_nombre",
            "fecha_toma",
            "hemoglobina",
            "leucocitos",
            "plaquetas",
            "clasificacion_display",
            "es_critico",
            "semanas_gestacion",
        ]


class BioquimicaSerializer(serializers.ModelSerializer):
    """Serializer para bioquímica completa"""

    paciente_nombre = serializers.CharField(
        source="paciente.nombre_completo", read_only=True,
    )
    medico_nombre = serializers.CharField(
        source="medico_solicitante.get_full_name", read_only=True,
    )

    class Meta:
        """Meta"""
        model = Bioquimica
        fields = [
            "id",
            "paciente",
            "paciente_nombre",
            "embarazo",
            "medico_solicitante",
            "medico_nombre",
            "fecha_toma",
            "fecha_resultado",
            "semanas_gestacion",
            # Glucosa
            "glucosa_ayunas",
            "glucosa_postprandial",
            "hba1c",
            # Renal
            "creatinina",
            "urea",
            "acido_urico",
            # Hepática
            "got_ast",
            "gpt_alt",
            "bilirrubina_total",
            "bilirrubina_directa",
            "fosfatasa_alcalina",
            "albumina",
            # Electrolitos
            "sodio",
            "potasio",
            "cloro",
            "calcio",
            "magnesio",
            # Lípidos
            "colesterol_total",
            "ldl",
            "hdl",
            "trigliceridos",
            # Otros
            "proteinas_totales",
            "ldh",
            # Clasificación
            "clasificacion",
            "alertas",
            "es_critico",
            "interpretacion_automatica",
            "observaciones_medicas",
            # Auditoría
            "activo",
            "fecha_creacion",
            "fecha_modificacion",
        ]
        read_only_fields = [
            "clasificacion",
            "alertas",
            "es_critico",
            "interpretacion_automatica",
            "fecha_resultado",
            "fecha_creacion",
            "fecha_modificacion",
        ]


class BioquimicaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado"""

    paciente_nombre = serializers.CharField(
        source="paciente.nombre_completo", read_only=True,
    )

    class Meta:
        """Meta"""
        model = Bioquimica
        fields = [
            "id",
            "paciente_nombre",
            "fecha_toma",
            "glucosa_ayunas",
            "creatinina",
            "got_ast",
            "es_critico",
            "semanas_gestacion",
        ]


class MarcadorEmbarazoSerializer(serializers.ModelSerializer):
    """Serializer para marcadores de embarazo con MoM"""

    paciente_nombre = serializers.CharField(
        source="paciente.nombre_completo", read_only=True,
    )
    medico_nombre = serializers.CharField(
        source="medico_solicitante.get_full_name", read_only=True,
    )
    edad_gestacional = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = MarcadorEmbarazo
        fields = [
            "id",
            "paciente",
            "paciente_nombre",
            "embarazo",
            "medico_solicitante",
            "medico_nombre",
            "fecha_toma",
            "semanas_gestacion",
            "dias_adicionales",
            "edad_gestacional",
            # Marcadores crudos
            "beta_hcg",
            "papp_a",
            "free_bhcg",
            "plgf",
            "sflt1",
            # Valores MoM
            "beta_hcg_mom",
            "papp_a_mom",
            "free_bhcg_mom",
            "plgf_mom",
            "sflt1_mom",
            # Ratio
            "ratio_sflt_plgf",
            # Clasificación
            "clasificacion",
            "alertas",
            "interpretacion_automatica",
            # Auditoría
            "activo",
            "fecha_creacion",
        ]
        read_only_fields = [
            "beta_hcg_mom",
            "papp_a_mom",
            "free_bhcg_mom",
            "plgf_mom",
            "sflt1_mom",
            "ratio_sflt_plgf",
            "clasificacion",
            "alertas",
            "interpretacion_automatica",
            "fecha_creacion",
        ]

    def get_edad_gestacional(self, obj):
        """Retorna edad gestacional en formato legible"""
        return f"{obj.semanas_gestacion}+{obj.dias_adicionales} semanas"


class MarcadorEmbarazoCreateSerializer(serializers.Serializer):
    """Serializer para crear marcador con cálculo automático de MoM"""

    # IDs
    paciente_id = serializers.IntegerField()
    embarazo_id = serializers.IntegerField()
    medico_solicitante_id = serializers.IntegerField()

    # Contexto
    fecha_toma = serializers.DateTimeField()
    semanas_gestacion = serializers.IntegerField(min_value=10, max_value=40)
    dias_adicionales = serializers.IntegerField(min_value=0, max_value=6, default=0)

    # Marcadores crudos
    beta_hcg = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True,
    )
    papp_a = serializers.DecimalField(
        max_digits=8, decimal_places=3, required=False, allow_null=True,
    )
    free_bhcg = serializers.DecimalField(
        max_digits=8, decimal_places=3, required=False, allow_null=True,
    )
    plgf = serializers.DecimalField(
        max_digits=8, decimal_places=2, required=False, allow_null=True,
    )
    sflt1 = serializers.DecimalField(
        max_digits=8, decimal_places=2, required=False, allow_null=True,
    )

    # Datos para corrección MoM
    peso_kg = serializers.DecimalField(max_digits=5, decimal_places=2)
    etnia = serializers.ChoiceField(
        choices=["caucasico", "afroamericano", "asiatico", "mestizo", "otro"],
    )
    fumadora = serializers.BooleanField(default=False)
    diabetes = serializers.BooleanField(default=False)
    fiv = serializers.BooleanField(default=False)
    altitud_bolivia = serializers.BooleanField(default=True)

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        return instance


# =============================================================================
# HISTORIAL DE CALCULADORAS SIMPLES
# =============================================================================


class CalculoHistorialSerializer(serializers.ModelSerializer):
    """Serializer para el historial de las 8 calculadoras simples del frontend"""

    paciente_nombre = serializers.SerializerMethodField()
    tipo_calculadora_display = serializers.CharField(
        source="get_tipo_calculadora_display", read_only=True,
    )
    calculado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = CalculoHistorial
        fields = [
            "id",
            "paciente",
            "paciente_nombre",
            "embarazo",
            "tipo_calculadora",
            "tipo_calculadora_display",
            "inputs_json",
            "resultado_json",
            "resultado_resumen",
            "fecha_calculo",
            "calculado_por",
            "calculado_por_nombre",
        ]
        read_only_fields = ["id", "fecha_calculo", "calculado_por"]

    def get_paciente_nombre(self, obj):
        """Nombre completo del paciente, si hay uno asociado"""
        if not obj.paciente:
            return None
        return getattr(obj.paciente, "nombre_completo", None) or str(obj.paciente)

    def get_calculado_por_nombre(self, obj):
        """Nombre de quien hizo el cálculo"""
        if not obj.calculado_por:
            return None
        return getattr(obj.calculado_por, "get_full_name", lambda: None)() or obj.calculado_por.email
