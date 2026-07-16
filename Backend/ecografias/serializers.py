"""Serializers module."""
from rest_framework import serializers

from .models import (
    AnatomiaFetal,
    AnexosFetales,
    BiometriaFetal,
    Ecografia,
    ImagenEcografia,
)

# from embarazos.models import Embarazo  # REMOVED to fix circular import


class BiometriaFetalSerializer(serializers.ModelSerializer):
    """Serializer para Biometría Fetal"""

    evaluacion_crecimiento = serializers.SerializerMethodField()
    peso_calculado = serializers.SerializerMethodField()
    created_by_nombre = serializers.SerializerMethodField()
    updated_by_nombre = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = BiometriaFetal
        fields = [
            "id",
            "diametro_biparietal",
            "circunferencia_cefalica",
            "diametro_occipito_frontal",
            "circunferencia_abdominal",
            "diametro_abdominal_transverso",
            "longitud_femur",
            "longitud_humero",
            "longitud_tibia",
            "longitud_radio",
            "peso_fetal_estimado",
            "percentil_peso",
            "diametro_transverso_cerebelo",
            "cisterna_magna",
            "relacion_cc_ca",
            "relacion_lf_ca",
            "evaluacion_crecimiento",
            "peso_calculado",
            "fecha_registro",
            "fecha_modificacion",
            "created_by",
            "updated_by",
            "created_by_nombre",
            "updated_by_nombre",
        ]
        read_only_fields = [
            "fecha_registro",
            "fecha_modificacion",
            "created_by",
            "updated_by",
        ]

    def get_evaluacion_crecimiento(self, obj):
        """Obtener evaluación del crecimiento"""
        return obj.get_evaluacion_crecimiento()

    def get_peso_calculado(self, obj):
        """Obtener peso calculado con Hadlock"""
        return obj.calcular_peso_fetal_hadlock()

    def get_created_by_nombre(self, obj):
        """Obtener nombre del usuario que creó"""
        if obj.created_by:
            return f"{obj.created_by.nombre} {obj.created_by.apellido_paterno}"
        return None

    def get_updated_by_nombre(self, obj):
        """Obtener nombre del usuario que modificó"""
        if obj.updated_by:
            return f"{obj.updated_by.nombre} {obj.updated_by.apellido_paterno}"
        return None


class AnatomiaFetalSerializer(serializers.ModelSerializer):
    """Serializer para Anatomía Fetal"""

    evaluacion_anatomica = serializers.SerializerMethodField()
    riesgo_cromosomopatias = serializers.SerializerMethodField()
    created_by_nombre = serializers.SerializerMethodField()
    updated_by_nombre = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = AnatomiaFetal
        fields = [
            "id",
            "craneo_normal",
            "cerebro_normal",
            "cerebelo_normal",
            "perfil_facial_normal",
            "labios_normales",
            "corazon_normal",
            "pulmones_normales",
            "estomago_normal",
            "rinones_normales",
            "vejiga_normal",
            "columna_normal",
            "extremidades_superiores_normales",
            "extremidades_inferiores_normales",
            "genitales_visibles",
            "sexo_fetal",
            "translucencia_nucal",
            "hueso_nasal_presente",
            "hallazgos_anormales",
            "evaluacion_anatomica",
            "riesgo_cromosomopatias",
            "fecha_registro",
            "fecha_modificacion",
            "created_by",
            "updated_by",
            "created_by_nombre",
            "updated_by_nombre",
        ]
        read_only_fields = [
            "fecha_registro",
            "fecha_modificacion",
            "created_by",
            "updated_by",
        ]

    def get_evaluacion_anatomica(self, obj):
        """Obtener evaluación anatómica general"""
        return obj.get_evaluacion_anatomica()

    def get_riesgo_cromosomopatias(self, obj):
        """Obtener riesgo de cromosomopatías"""
        return obj.get_riesgo_cromosomopatias()

    def get_created_by_nombre(self, obj):
        """Obtener nombre del usuario que creó"""
        if obj.created_by:
            return f"{obj.created_by.nombre} {obj.created_by.apellido_paterno}"
        return None

    def get_updated_by_nombre(self, obj):
        """Obtener nombre del usuario que modificó"""
        if obj.updated_by:
            return f"{obj.updated_by.nombre} {obj.updated_by.apellido_paterno}"
        return None


class AnexosFetalesSerializer(serializers.ModelSerializer):
    """Serializer para Anexos Fetales"""

    evaluacion_cordon = serializers.SerializerMethodField()
    evaluacion_cervix = serializers.SerializerMethodField()
    created_by_nombre = serializers.SerializerMethodField()
    updated_by_nombre = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = AnexosFetales
        fields = [
            "id",
            "placenta_localizacion",
            "placenta_grosor",
            "placenta_insercion_cordon",  # ✅ CORREGIDO: era 'placenta_inserccion_cordon'
            "placenta_previa",
            "numero_vasos_cordon",
            "circular_cordon",
            "liquido_amniotico_normal",
            "polihidramnios",
            "oligohidramnios",
            "longitud_cervical",
            "evaluacion_cordon",
            "evaluacion_cervix",
            "fecha_registro",
            "fecha_modificacion",
            "created_by",
            "updated_by",
            "created_by_nombre",
            "updated_by_nombre",
        ]
        read_only_fields = [
            "fecha_registro",
            "fecha_modificacion",
            "created_by",
            "updated_by",
        ]

    def get_evaluacion_cordon(self, obj):
        """Obtener evaluación del cordón"""
        return obj.get_evaluacion_cordon()

    def get_evaluacion_cervix(self, obj):
        """Obtener evaluación del cérvix"""
        return obj.get_evaluacion_cervix()

    def get_created_by_nombre(self, obj):
        """Obtener nombre del usuario que creó"""
        if obj.created_by:
            return f"{obj.created_by.nombre} {obj.created_by.apellido_paterno}"
        return None

    def get_updated_by_nombre(self, obj):
        """Obtener nombre del usuario que modificó"""
        if obj.updated_by:
            return f"{obj.updated_by.nombre} {obj.updated_by.apellido_paterno}"
        return None


class ImagenEcografiaSerializer(serializers.ModelSerializer):
    """Serializer para Imágenes de Ecografía"""

    tamano_archivo = serializers.SerializerMethodField()
    dimensiones = serializers.SerializerMethodField()
    url_imagen = serializers.SerializerMethodField()
    created_by_nombre = serializers.SerializerMethodField()
    updated_by_nombre = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = ImagenEcografia
        fields = [
            "id",
            "imagen",
            "tipo_imagen",
            "titulo",
            "descripcion",
            "calidad_imagen",
            "mediciones_incluidas",
            "analisis_ia",
            "fecha_captura",
            "orden",
            "es_imagen_principal",
            "tamano_archivo",
            "dimensiones",
            "url_imagen",
            "created_by",
            "updated_by",
            "created_by_nombre",
            "updated_by_nombre",
        ]
        read_only_fields = ["fecha_captura", "analisis_ia", "created_by", "updated_by"]

    def get_tamano_archivo(self, obj):
        """Obtener tamaño del archivo"""
        return obj.get_tamano_archivo()

    def get_dimensiones(self, obj):
        """Obtener dimensiones de la imagen"""
        return obj.get_dimensiones()

    def get_url_imagen(self, obj):
        """Obtener URL completa de la imagen"""
        if obj.imagen:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.imagen.url)
            return obj.imagen.url
        return None

    def get_created_by_nombre(self, obj):
        """Obtener nombre del usuario que subió"""
        if obj.created_by:
            return f"{obj.created_by.nombre} {obj.created_by.apellido_paterno}"
        return None

    def get_updated_by_nombre(self, obj):
        """Obtener nombre del usuario que modificó"""
        if obj.updated_by:
            return f"{obj.updated_by.nombre} {obj.updated_by.apellido_paterno}"
        return None


class EcografiaSerializer(serializers.ModelSerializer):
    """Serializer completo para Ecografía"""

    # Campos de solo lectura
    paciente_nombre = serializers.SerializerMethodField()
    medico_nombre = serializers.SerializerMethodField()
    edad_gestacional_texto = serializers.SerializerMethodField()
    edad_gestacional_completa = serializers.ReadOnlyField()
    percentil_ila = serializers.SerializerMethodField()
    estado_liquido_amniotico = serializers.SerializerMethodField()
    evaluacion_fcf = serializers.SerializerMethodField()
    created_by_nombre = serializers.SerializerMethodField()
    updated_by_nombre = serializers.SerializerMethodField()

    # Relaciones anidadas
    biometria = BiometriaFetalSerializer(required=False, allow_null=True)
    anatomia = AnatomiaFetalSerializer(required=False, allow_null=True)
    anexos = AnexosFetalesSerializer(required=False, allow_null=True)
    imagenes = ImagenEcografiaSerializer(many=True, read_only=True)

    class Meta:
        """Meta"""
        model = Ecografia
        fields = [
            "id",
            "embarazo",
            "paciente",
            "paciente_nombre",
            "medico",
            "medico_nombre",
            "fecha_ecografia",
            "tipo_ecografia",
            "indicacion",
            "edad_gestacional_semanas",
            "edad_gestacional_dias",
            "edad_gestacional_texto",
            "edad_gestacional_completa",
            "numero_fetos",
            "vitalidad_fetal",
            "frecuencia_cardiaca_fetal",
            "evaluacion_fcf",
            "indice_liquido_amniotico",
            "bolsillo_maximo",
            "percentil_ila",
            "estado_liquido_amniotico",
            "localizacion_placenta",
            "grado_madurez_placenta",
            "calidad_estudio",
            "limitaciones_tecnicas",
            "diagnostico",
            "observaciones",
            "requiere_seguimiento",
            "proxima_ecografia_recomendada",
            "biometria",
            "anatomia",
            "anexos",
            "imagenes",
            "fecha_registro",
            "fecha_modificacion",
            "created_by",
            "updated_by",
            "created_by_nombre",
            "updated_by_nombre",
        ]
        read_only_fields = [
            "id",
            "fecha_registro",
            "fecha_modificacion",
            "created_by",
            "updated_by",
        ]

    def get_paciente_nombre(self, obj):
        """Obtener nombre completo del paciente"""
        if obj.paciente:
            return obj.paciente.nombre_completo
        return None

    def get_medico_nombre(self, obj):
        """Obtener nombre completo del médico"""
        if obj.medico:
            return f"{obj.medico.nombre} {obj.medico.apellido_paterno}"
        return None

    def get_edad_gestacional_texto(self, obj):
        """Obtener edad gestacional en formato texto"""
        return obj.get_edad_gestacional_texto()

    def get_percentil_ila(self, obj):
        """Obtener percentil de ILA"""
        return obj.get_percentil_ila()

    def get_estado_liquido_amniotico(self, obj):
        """Obtener estado del líquido amniótico"""
        return obj.get_estado_liquido_amniotico()

    def get_evaluacion_fcf(self, obj):
        """Obtener evaluación de FCF"""
        return obj.get_evaluacion_fcf()

    def get_created_by_nombre(self, obj):
        """Obtener nombre del usuario que creó"""
        if obj.created_by:
            return f"{obj.created_by.nombre} {obj.created_by.apellido_paterno}"
        return None

    def get_updated_by_nombre(self, obj):
        """Obtener nombre del usuario que modificó"""
        if obj.updated_by:
            return f"{obj.updated_by.nombre} {obj.updated_by.apellido_paterno}"
        return None

    def create(self, validated_data):
        """Crear ecografía con relaciones anidadas"""
        # Extraer datos anidados
        biometria_data = validated_data.pop("biometria", None)
        anatomia_data = validated_data.pop("anatomia", None)
        anexos_data = validated_data.pop("anexos", None)

        # Crear ecografía principal
        ecografia = Ecografia.objects.create(**validated_data)

        # Crear relaciones si existen
        if biometria_data:
            # Extraer created_by/updated_by de validated_data si existen
            user = validated_data.get("created_by")
            biometria_data["created_by"] = user
            biometria_data["updated_by"] = user
            BiometriaFetal.objects.create(ecografia=ecografia, **biometria_data)

        if anatomia_data:
            user = validated_data.get("created_by")
            anatomia_data["created_by"] = user
            anatomia_data["updated_by"] = user
            AnatomiaFetal.objects.create(ecografia=ecografia, **anatomia_data)

        if anexos_data:
            user = validated_data.get("created_by")
            anexos_data["created_by"] = user
            anexos_data["updated_by"] = user
            AnexosFetales.objects.create(ecografia=ecografia, **anexos_data)

        return ecografia

    def update(self, instance, validated_data):
        """Actualizar ecografía con relaciones anidadas"""
        # Extraer datos anidados
        biometria_data = validated_data.pop("biometria", None)
        anatomia_data = validated_data.pop("anatomia", None)
        anexos_data = validated_data.pop("anexos", None)

        # Actualizar ecografía principal
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Obtener usuario del contexto del request (no de validated_data)
        request = self.context.get("request")
        user = request.user if request else None

        # Actualizar o crear biometría
        if biometria_data:
            biometria_data["updated_by"] = user
            biometria, created = BiometriaFetal.objects.update_or_create(
                ecografia=instance, defaults=biometria_data,
            )
            if created and user:
                biometria.created_by = user
                biometria.save()

        # Actualizar o crear anatomía
        if anatomia_data:
            anatomia_data["updated_by"] = user
            anatomia, created = AnatomiaFetal.objects.update_or_create(
                ecografia=instance, defaults=anatomia_data,
            )
            if created and user:
                anatomia.created_by = user
                anatomia.save()

        # Actualizar o crear anexos
        if anexos_data:
            anexos_data["updated_by"] = user
            anexos, created = AnexosFetales.objects.update_or_create(
                ecografia=instance, defaults=anexos_data,
            )
            if created and user:
                anexos.created_by = user
                anexos.save()

        return instance

    def validate(self, attrs):
        """Validaciones adicionales"""
        # Validar que el embarazo esté activo
        if "embarazo" in attrs:
            embarazo = attrs["embarazo"]
            if embarazo.estado != "activo":
                raise serializers.ValidationError(
                    {
                        "embarazo": "Solo se pueden registrar ecografías en embarazos activos",
                    },
                )

        # Validar edad gestacional
        if "edad_gestacional_semanas" in attrs:
            semanas = attrs["edad_gestacional_semanas"]
            if semanas < 4 or semanas > 42:
                raise serializers.ValidationError(
                    {"edad_gestacional_semanas": "Las semanas deben estar entre 4 y 42"},
                )

        # Validar días de gestación
        if "edad_gestacional_dias" in attrs:
            dias = attrs["edad_gestacional_dias"]
            if dias < 0 or dias > 6:
                raise serializers.ValidationError(
                    {"edad_gestacional_dias": "Los días deben estar entre 0 y 6"},
                )

        # Validar FCF
        if attrs.get("frecuencia_cardiaca_fetal"):
            fcf = attrs["frecuencia_cardiaca_fetal"]
            if fcf < 90 or fcf > 180:
                raise serializers.ValidationError(
                    {"frecuencia_cardiaca_fetal": "FCF debe estar entre 90 y 180 lpm"},
                )

        # Validar número de fetos
        if "numero_fetos" in attrs:
            if attrs["numero_fetos"] < 1 or attrs["numero_fetos"] > 5:
                raise serializers.ValidationError(
                    {"numero_fetos": "Número de fetos debe estar entre 1 y 5"},
                )

        return attrs


class EcografiaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas"""

    paciente_nombre = serializers.SerializerMethodField()
    medico_nombre = serializers.SerializerMethodField()
    edad_gestacional = serializers.SerializerMethodField()
    tiene_imagenes = serializers.SerializerMethodField()
    tiene_analisis_ia = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = Ecografia
        fields = [
            "id",
            "paciente_nombre",
            "medico_nombre",
            "fecha_ecografia",
            "tipo_ecografia",
            "edad_gestacional",
            "edad_gestacional_semanas",
            "edad_gestacional_dias",
            "numero_fetos",
            "vitalidad_fetal",
            "diagnostico",
            "tiene_imagenes",
            "tiene_analisis_ia",
        ]

    def get_paciente_nombre(self, obj):
        """Obtener nombre del paciente"""
        if obj.paciente:
            return obj.paciente.nombre_completo
        return None

    def get_medico_nombre(self, obj):
        """Obtener nombre del médico"""
        if obj.medico:
            return f"{obj.medico.nombre} {obj.medico.apellido_paterno}"
        return None

    def get_edad_gestacional(self, obj):
        """Obtener edad gestacional formateada"""
        return f"{obj.edad_gestacional_semanas}+{obj.edad_gestacional_dias}"

    def get_tiene_imagenes(self, obj):
        """Verificar si tiene imágenes"""
        return obj.imagenes.exists()

    def get_tiene_analisis_ia(self, obj):
        """Verificar si alguna imagen tiene análisis IA"""
        for img in obj.imagenes.all():
            if img.analisis_ia and isinstance(img.analisis_ia, dict) and img.analisis_ia.get("procesado"):
                return True
        return False


class EcografiaCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar ecografías"""

    # Relaciones anidadas opcionales
    biometria = BiometriaFetalSerializer(required=False, allow_null=True)
    anatomia = AnatomiaFetalSerializer(required=False, allow_null=True)
    anexos = AnexosFetalesSerializer(required=False, allow_null=True)

    class Meta:
        """Meta"""
        model = Ecografia
        fields = [
            "id",
            "embarazo",
            "paciente",
            "medico",
            "fecha_ecografia",
            "tipo_ecografia",
            "indicacion",
            "edad_gestacional_semanas",
            "edad_gestacional_dias",
            "numero_fetos",
            "vitalidad_fetal",
            "frecuencia_cardiaca_fetal",
            "indice_liquido_amniotico",
            "bolsillo_maximo",
            "localizacion_placenta",
            "grado_madurez_placenta",
            "calidad_estudio",
            "limitaciones_tecnicas",
            "diagnostico",
            "observaciones",
            "requiere_seguimiento",
            "proxima_ecografia_recomendada",
            "biometria",
            "anatomia",
            "anexos",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        """Crear ecografía con relaciones"""
        biometria_data = validated_data.pop("biometria", None)
        anatomia_data = validated_data.pop("anatomia", None)
        anexos_data = validated_data.pop("anexos", None)

        ecografia = Ecografia.objects.create(**validated_data)

        if biometria_data:
            user = validated_data.get("created_by")
            biometria_data["created_by"] = user
            biometria_data["updated_by"] = user
            BiometriaFetal.objects.create(ecografia=ecografia, **biometria_data)

        if anatomia_data:
            user = validated_data.get("created_by")
            anatomia_data["created_by"] = user
            anatomia_data["updated_by"] = user
            AnatomiaFetal.objects.create(ecografia=ecografia, **anatomia_data)

        if anexos_data:
            user = validated_data.get("created_by")
            anexos_data["created_by"] = user
            anexos_data["updated_by"] = user
            AnexosFetales.objects.create(ecografia=ecografia, **anexos_data)

        return ecografia

    def update(self, instance, validated_data):
        """Actualizar ecografía"""
        biometria_data = validated_data.pop("biometria", None)
        anatomia_data = validated_data.pop("anatomia", None)
        anexos_data = validated_data.pop("anexos", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if biometria_data:
            user = validated_data.get("updated_by")
            biometria_data["updated_by"] = user
            biometria, created = BiometriaFetal.objects.update_or_create(
                ecografia=instance, defaults=biometria_data,
            )
            if created and user:
                biometria.created_by = user
                biometria.save()

        if anatomia_data:
            user = validated_data.get("updated_by")
            anatomia_data["updated_by"] = user
            anatomia, created = AnatomiaFetal.objects.update_or_create(
                ecografia=instance, defaults=anatomia_data,
            )
            if created and user:
                anatomia.created_by = user
                anatomia.save()

        if anexos_data:
            user = validated_data.get("updated_by")
            anexos_data["updated_by"] = user
            anexos, created = AnexosFetales.objects.update_or_create(
                ecografia=instance, defaults=anexos_data,
            )
            if created and user:
                anexos.created_by = user
                anexos.save()

        return instance

    def validate(self, attrs):
        """Validaciones completas"""
        # Validar embarazo activo
        if "embarazo" in attrs:
            if attrs["embarazo"].estado != "activo":
                raise serializers.ValidationError(
                    {
                        "embarazo": "Solo se pueden registrar ecografías en embarazos activos",
                    },
                )

        # Validar edad gestacional
        if "edad_gestacional_semanas" in attrs and (
            attrs["edad_gestacional_semanas"] < 4
            or attrs["edad_gestacional_semanas"] > 42
        ):
            raise serializers.ValidationError(
                {"edad_gestacional_semanas": "Debe estar entre 4 y 42 semanas"},
            )

        return attrs
