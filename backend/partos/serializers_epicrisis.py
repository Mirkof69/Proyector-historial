"""Serializers de la epicrisis y de sus campos configurables."""
from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models_epicrisis import CampoAdicionalEpicrisis, Epicrisis


class CampoAdicionalEpicrisisSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampoAdicionalEpicrisis
        fields = ["id", "clave", "etiqueta", "tipo", "opciones", "obligatorio", "ayuda", "orden", "activo"]

    def validate(self, attrs):
        tipo = attrs.get("tipo", getattr(self.instance, "tipo", "texto"))
        opciones = attrs.get("opciones", getattr(self.instance, "opciones", []))
        if tipo == "opcion" and not (isinstance(opciones, list) and opciones):
            raise serializers.ValidationError({"opciones": "Un campo de tipo «opción» necesita al menos una opción."})
        return attrs


class EpicrisisSerializer(serializers.ModelSerializer):
    dias_internacion = serializers.IntegerField(read_only=True)
    paciente_nombre = serializers.SerializerMethodField()
    medico_nombre = serializers.SerializerMethodField()
    fecha_ingreso = serializers.SerializerMethodField()

    class Meta:
        model = Epicrisis
        fields = [
            "id", "parto", "fecha_ingreso", "fecha_egreso", "dias_internacion",
            "diagnostico_ingreso", "cie10_ingreso", "diagnostico_egreso", "cie10_egreso",
            "resumen_clinico", "examenes_relevantes", "tratamiento_recibido", "procedimientos", "complicaciones",
            "condicion_materna_egreso", "tipo_egreso", "establecimiento_referencia",
            "consejeria_anticoncepcion", "metodo_anticonceptivo", "lactancia_materna_exclusiva",
            "indicaciones_alta", "signos_alarma_explicados", "proximo_control", "lugar_proximo_control",
            "pronostico", "matricula_profesional", "campos_adicionales",
            "estado", "fecha_firma", "medico", "medico_nombre", "paciente_nombre",
            "fecha_creacion", "fecha_modificacion",
        ]
        read_only_fields = ["estado", "fecha_firma", "medico", "fecha_creacion", "fecha_modificacion"]

    def get_paciente_nombre(self, obj):
        p = obj.parto.paciente
        return getattr(p, "nombre_completo", None) or f"{p.nombre} {p.apellido_paterno}"

    def get_medico_nombre(self, obj):
        if not obj.medico:
            return None
        return obj.medico.get_full_name() if hasattr(obj.medico, "get_full_name") else str(obj.medico)

    def get_fecha_ingreso(self, obj):
        inicio = obj.parto.fecha_ingreso or obj.parto.fecha_parto
        return inicio.isoformat() if inicio else None

    def validate(self, attrs):
        """Las reglas viven en el modelo (`Epicrisis.clean`): se aplican aquí para
        que la API y el admin rechacen exactamente lo mismo."""
        if self.instance is not None and self.instance.estado == "firmada":
            raise serializers.ValidationError("La epicrisis está firmada y ya no se puede modificar.")
        if self.instance is not None and "parto" in attrs and attrs["parto"] != self.instance.parto:
            raise serializers.ValidationError({"parto": "No se puede cambiar el parto de una epicrisis."})
        provisional = Epicrisis(**{**{f: getattr(self.instance, f) for f in
                                      [c.attname for c in Epicrisis._meta.concrete_fields]}} if self.instance else {})
        for campo, valor in attrs.items():
            setattr(provisional, campo, valor)
        try:
            provisional.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict) from e
        for campo in ("cie10_ingreso", "cie10_egreso"):
            if campo in attrs:
                attrs[campo] = getattr(provisional, campo)
        return attrs
