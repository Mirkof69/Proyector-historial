"""=============================================================================
ANTECEDENTES - SERIALIZERS
=============================================================================
Serializers para antecedentes gineco-obstétricos y patológicos
=============================================================================
"""

from rest_framework import serializers

from .models import AntecedenteGinecoObstetrico, AntecedentePatologico


class AntecedenteGinecoObstetricoSerializer(serializers.ModelSerializer):
    """Serializer para antecedentes gineco-obstétricos
    """

    # Información expandida del paciente (read-only)
    paciente_info = serializers.SerializerMethodField()
    modificado_por_info = serializers.SerializerMethodField()

    # Campos calculados
    formula_obstetrica = serializers.SerializerMethodField()
    edad_menarquia_texto = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = AntecedenteGinecoObstetrico
        fields = [
            "id",
            "paciente",
            "paciente_info",
            # Menstruales
            "menarquia_edad",
            "ciclos_menstruales",
            "duracion_ciclo_dias",
            "duracion_menstruacion_dias",
            "fecha_ultima_menstruacion",
            # GPAC
            "gestas",
            "partos",
            "abortos",
            "cesareas",
            "hijos_vivos",
            # Anticoncepción
            "metodo_anticonceptivo_actual",
            "tiempo_uso_anticonceptivo_meses",
            "fecha_suspension_anticonceptivo",
            # Vida sexual
            "inicio_vida_sexual_edad",
            "numero_parejas_sexuales",
            # Calculados
            "formula_obstetrica",
            "edad_menarquia_texto",
            # Metadata
            "fecha_registro",
            "fecha_modificacion",
            "modificado_por",
            "modificado_por_info",
        ]
        read_only_fields = [
            "fecha_registro",
            "fecha_modificacion",
            "formula_obstetrica",
        ]

    def get_paciente_info(self, obj):
        """Información del paciente"""
        if not obj.paciente:
            return None
        return {
            "id": obj.paciente.id,
            "nombre_completo": obj.paciente.nombre_completo,
            "id_clinico": obj.paciente.id_clinico,
            "ci": obj.paciente.ci,
        }

    def get_modificado_por_info(self, obj):
        """Información del usuario que modificó"""
        if not obj.modificado_por:
            return None
        return {
            "id": obj.modificado_por.id,
            "nombre": obj.modificado_por.nombre,
            "email": obj.modificado_por.email,
        }

    def get_formula_obstetrica(self, obj):
        """Fórmula obstétrica GPAC"""
        return obj.get_formula_obstetrica()

    def get_edad_menarquia_texto(self, obj):
        """Texto descriptivo de menarquia"""
        if obj.menarquia_edad:
            if obj.menarquia_edad < 11:
                return f"{obj.menarquia_edad} años (precoz)"
            if obj.menarquia_edad > 16:
                return f"{obj.menarquia_edad} años (tardía)"
            return f"{obj.menarquia_edad} años (normal)"
        return None


class AntecedentePatologicoSerializer(serializers.ModelSerializer):
    """Serializer para antecedentes patológicos
    """

    # Información expandida
    paciente_info = serializers.SerializerMethodField()
    registrado_por_info = serializers.SerializerMethodField()

    # Campos calculados
    tiene_factores_riesgo_calculado = serializers.SerializerMethodField()
    resumen_enfermedades = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = AntecedentePatologico
        fields = [
            "id",
            "paciente",
            "paciente_info",
            "tipo",
            # Alergias
            "tiene_alergias",
            "alergias_medicamentos",
            "alergias_alimentos",
            "alergias_otras",
            # Enfermedades crónicas
            "diabetes",
            "diabetes_tipo",
            "hipertension",
            "cardiopatias",
            "cardiopatia_detalle",
            "nefropatias",
            "nefropatia_detalle",
            "trastornos_coagulacion",
            "anemia",
            "lupus",
            "artritis_reumatoide",
            "asma",
            # Antecedentes obstétricos
            "preeclampsia_previa",
            "eclampsia_previa",
            "diabetes_gestacional_previa",
            "hemorragia_postparto_previa",
            # Otros
            "otras_enfermedades",
            "cirugiasanteriores",
            # Calculados
            "tiene_factores_riesgo_calculado",
            "resumen_enfermedades",
            # Metadata
            "fecha_registro",
            "fecha_modificacion",
            "registrado_por",
            "registrado_por_info",
        ]
        read_only_fields = ["fecha_registro", "fecha_modificacion"]

    def get_paciente_info(self, obj):
        """Información del paciente"""
        if not obj.paciente:
            return None
        return {
            "id": obj.paciente.id,
            "nombre_completo": obj.paciente.nombre_completo,
            "id_clinico": obj.paciente.id_clinico,
        }

    def get_registrado_por_info(self, obj):
        """Información del usuario que registró"""
        if not obj.registrado_por:
            return None
        return {
            "id": obj.registrado_por.id,
            "nombre": obj.registrado_por.nombre,
            "email": obj.registrado_por.email,
        }

    def get_tiene_factores_riesgo_calculado(self, obj):
        """Verifica si tiene factores de riesgo"""
        return obj.tiene_factores_riesgo()

    def get_resumen_enfermedades(self, obj):
        """Resumen de enfermedades presentes"""
        enfermedades = []

        if obj.diabetes:
            tipo = obj.get_diabetes_tipo_display() if obj.diabetes_tipo else "Diabetes"
            enfermedades.append(tipo)
        if obj.hipertension:
            enfermedades.append("Hipertensión")
        if obj.cardiopatias:
            enfermedades.append("Cardiopatías")
        if obj.nefropatias:
            enfermedades.append("Nefropatías")
        if obj.asma:
            enfermedades.append("Asma")
        if obj.lupus:
            enfermedades.append("Lupus")
        if obj.artritis_reumatoide:
            enfermedades.append("Artritis Reumatoide")
        if obj.preeclampsia_previa:
            enfermedades.append("Preeclampsia previa")
        if obj.eclampsia_previa:
            enfermedades.append("Eclampsia previa")

        return enfermedades or ["Sin enfermedades registradas"]
