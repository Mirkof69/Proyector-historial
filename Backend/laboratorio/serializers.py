"""Serializers module."""
from rest_framework import serializers

from .models import (
    ExamenLaboratorio,
    ImagenLaboratorio,
    ResultadoLaboratorio,
    TipoExamen,
    ValorReferencia,
)

# from controles.models import ControlPrenatal  # REMOVED to fix circular import


class TipoExamenSerializer(serializers.ModelSerializer):
    """Serializer para Tipos de Exámenes"""

    total_examenes = serializers.SerializerMethodField()
    created_by_nombre = serializers.SerializerMethodField()
    updated_by_nombre = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = TipoExamen
        fields = [
            "id",
            "nombre",
            "codigo",
            "categoria",
            "descripcion",
            "preparacion",
            "tiempo_resultado",
            "precio",
            "activo",
            "total_examenes",
            "fecha_creacion",
            "fecha_actualizacion",
            "created_by",
            "updated_by",
            "created_by_nombre",
            "updated_by_nombre",
        ]
        read_only_fields = [
            "id",
            "fecha_creacion",
            "fecha_actualizacion",
            "created_by",
            "updated_by",
        ]

    def get_total_examenes(self, obj):
        """Contar cuántos exámenes se han realizado de este tipo"""
        return obj.examenes.count()

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


class ValorReferenciaSerializer(serializers.ModelSerializer):
    """Serializer para Valores de Referencia"""

    tipo_examen_nombre = serializers.CharField(
        source="tipo_examen.nombre", read_only=True,
    )
    rango_normal = serializers.SerializerMethodField()
    created_by_nombre = serializers.SerializerMethodField()
    updated_by_nombre = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = ValorReferencia
        fields = [
            "id",
            "tipo_examen",
            "tipo_examen_nombre",
            "parametro",
            "valor_minimo",
            "valor_maximo",
            "valor_normal",
            "unidad",
            "condicion",
            "es_critico_bajo",
            "es_critico_alto",
            "rango_normal",
            "fecha_creacion",
            "fecha_modificacion",
            "created_by",
            "updated_by",
            "created_by_nombre",
            "updated_by_nombre",
        ]
        read_only_fields = [
            "fecha_creacion",
            "fecha_modificacion",
            "created_by",
            "updated_by",
        ]

    def get_rango_normal(self, obj):
        """Formatear rango normal"""
        texto = obj.rango_texto()
        if not texto:
            return None
        return f"{texto} {obj.unidad}".strip() if obj.valor_minimo is not None or obj.valor_maximo is not None else texto

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


class ResultadoLaboratorioSerializer(serializers.ModelSerializer):
    """Serializer para Resultados de Laboratorio"""

    parametro_nombre = serializers.CharField(
        source="valor_referencia.parametro", read_only=True,
    )
    unidad = serializers.CharField(source="valor_referencia.unidad", read_only=True)
    rango_referencia = serializers.SerializerMethodField()
    estado = serializers.SerializerMethodField()
    created_by_nombre = serializers.SerializerMethodField()
    updated_by_nombre = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = ResultadoLaboratorio
        fields = [
            "id",
            "examen",
            "valor_referencia",
            "parametro_nombre",
            "valor_numerico",
            "valor_texto",
            "unidad",
            "rango_referencia",
            "es_normal",
            "es_critico",
            "estado",
            "observaciones",
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

    def get_rango_referencia(self, obj):
        """Obtener rango de referencia"""
        return obj.valor_referencia.rango_texto()

    def get_estado(self, obj):
        """Determinar estado del resultado"""
        if obj.es_critico:
            return "CRÍTICO"
        if not obj.es_normal:
            return "ANORMAL"
        return "NORMAL"

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


class ImagenLaboratorioSerializer(serializers.ModelSerializer):
    """Serializer para Imágenes de Laboratorio"""

    tamano_archivo = serializers.SerializerMethodField()
    url_archivo = serializers.SerializerMethodField()
    digitalizado_por_nombre = serializers.SerializerMethodField()
    created_by_nombre = serializers.SerializerMethodField()
    updated_by_nombre = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = ImagenLaboratorio
        fields = [
            "id",
            "archivo",
            "tipo_archivo",
            "formato",
            "titulo",
            "descripcion",
            "numero_paginas",
            "calidad_digitalizacion",
            "es_documento_oficial",
            "laboratorio_externo",
            "fecha_digitalizacion",
            "digitalizado_por",
            "digitalizado_por_nombre",
            "orden",
            "es_archivo_principal",
            "tamano_archivo",
            "url_archivo",
            "created_by",
            "updated_by",
            "created_by_nombre",
            "updated_by_nombre",
        ]
        read_only_fields = ["fecha_digitalizacion", "created_by", "updated_by"]

    def validate_archivo(self, value):
        """PDF o imagen de verdad, hasta 20 MB. Antes no se validaba nada: se
        podía subir un HTML con JavaScript llamado «resultado.pdf»."""
        from django.core.exceptions import ValidationError as ErrorDjango

        from core.validacion_archivos import DOCUMENTOS, validar_archivo

        try:
            validar_archivo(value, permitidos=DOCUMENTOS, max_mb=20)
        except ErrorDjango as e:
            raise serializers.ValidationError(e.messages[0]) from e
        return value

    def get_tamano_archivo(self, obj):
        """Obtener tamaño del archivo"""
        return obj.get_tamano_archivo()

    def get_url_archivo(self, obj):
        """Obtener URL completa del archivo"""
        if obj.archivo:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.archivo.url)
            return obj.archivo.url
        return None

    def get_digitalizado_por_nombre(self, obj):
        """Obtener nombre del usuario que digitalizó"""
        if obj.digitalizado_por:
            return (
                f"{obj.digitalizado_por.nombre} {obj.digitalizado_por.apellido_paterno}"
            )
        return None

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


class ExamenLaboratorioListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""

    paciente_nombre = serializers.CharField(
        source="paciente.nombre_completo", read_only=True,
    )
    tipo_examen_nombre = serializers.CharField(
        source="tipo_examen.nombre", read_only=True,
    )
    categoria = serializers.CharField(source="tipo_examen.categoria", read_only=True)
    medico_nombre = serializers.SerializerMethodField()
    tiene_resultados = serializers.SerializerMethodField()
    resultados_anormales = serializers.SerializerMethodField()
    resumen = serializers.SerializerMethodField()
    resultados = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = ExamenLaboratorio
        fields = [
            "id",
            "paciente",
            "paciente_nombre",
            "tipo_examen",
            "tipo_examen_nombre",
            "categoria",
            "fecha_solicitud",
            "fecha_muestra",
            "fecha_resultado",
            "estado",
            "prioridad",
            "medico_nombre",
            "tiene_resultados",
            "resultados_anormales",
            "resumen",
            "resultados",
            "dias_desde_solicitud",
            "esta_vencido",
        ]

    def get_medico_nombre(self, obj):
        """Get medico nombre"""
        if obj.medico_solicitante:
            return f"{obj.medico_solicitante.nombre} {obj.medico_solicitante.apellido_paterno}"
        return "No especificado"

    def _resultados(self, obj):
        # Lee lo que el viewset ya trajo con prefetch_related: filtrar con
        # .filter()/.count() aquí lanzaba una consulta por fila del listado.
        return list(obj.resultados.all())

    def get_tiene_resultados(self, obj):
        """Get tiene resultados"""
        return bool(self._resultados(obj))

    def get_resultados_anormales(self, obj):
        """Get resultados anormales"""
        return sum(1 for r in self._resultados(obj) if not r.es_normal)

    def get_resumen(self, obj):
        """Lo mismo que el detalle: la lista y la historia clínica lo necesitan
        para no mostrar «Sin resultados» o «Normal» ante un valor crítico."""
        resultados = self._resultados(obj)
        if not resultados:
            return None
        return {
            "total_parametros": len(resultados),
            "normales": sum(1 for r in resultados if r.es_normal),
            "anormales": sum(1 for r in resultados if not r.es_normal),
            "criticos": sum(1 for r in resultados if r.es_critico),
        }

    def get_resultados(self, obj):
        """Valores medidos en forma compacta para la historia clínica."""
        filas = []
        for r in self._resultados(obj):
            ref = r.valor_referencia
            valor = r.valor_numerico if r.valor_numerico is not None else r.valor_texto
            filas.append({
                "parametro": ref.parametro,
                "valor": str(valor) if valor is not None else "",
                "unidad": ref.unidad or "",
                "rango_referencia": ref.rango_texto(),
                "estado": "CRÍTICO" if r.es_critico else ("ANORMAL" if not r.es_normal else "NORMAL"),
            })
        return filas


class ExamenLaboratorioDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado con resultados incluidos"""

    paciente_info = serializers.SerializerMethodField()
    tipo_examen_info = serializers.SerializerMethodField()
    control_prenatal_info = serializers.SerializerMethodField()
    medico_info = serializers.SerializerMethodField()
    resultados = ResultadoLaboratorioSerializer(many=True, read_only=True)
    imagenes = ImagenLaboratorioSerializer(many=True, read_only=True)
    resumen = serializers.SerializerMethodField()
    created_by_nombre = serializers.SerializerMethodField()
    updated_by_nombre = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = ExamenLaboratorio
        fields = [
            "id",
            "paciente",
            "paciente_info",
            "control_prenatal",
            "control_prenatal_info",
            "tipo_examen",
            "tipo_examen_info",
            "medico_solicitante",
            "medico_info",
            "fecha_solicitud",
            "fecha_muestra",
            "fecha_resultado",
            "estado",
            "prioridad",
            "indicaciones",
            "observaciones",
            "resultados",
            "imagenes",
            "resumen",
            "dias_desde_solicitud",
            "esta_pendiente",
            "esta_vencido",
            "fecha_creacion",
            "fecha_actualizacion",
            "created_by",
            "updated_by",
            "created_by_nombre",
            "updated_by_nombre",
        ]
        read_only_fields = [
            "id",
            "fecha_creacion",
            "fecha_actualizacion",
            "created_by",
            "updated_by",
        ]

    def get_paciente_info(self, obj):
        """Get paciente info"""
        return {
            "id": obj.paciente.id,
            "nombre_completo": obj.paciente.nombre_completo,
            "id_clinico": obj.paciente.id_clinico,
            "edad": obj.paciente.edad,
        }

    def get_tipo_examen_info(self, obj):
        """Get tipo examen info"""
        return {
            "id": obj.tipo_examen.id,
            "nombre": obj.tipo_examen.nombre,
            "codigo": obj.tipo_examen.codigo,
            "categoria": obj.tipo_examen.categoria,
            "preparacion": obj.tipo_examen.preparacion,
            "tiempo_resultado": obj.tipo_examen.tiempo_resultado,
        }

    def get_control_prenatal_info(self, obj):
        """Get control prenatal info"""
        if obj.control_prenatal:
            return {
                "id": obj.control_prenatal.id,
                "numero_control": obj.control_prenatal.numero_control,
                "fecha_control": obj.control_prenatal.fecha_control,
                "semanas_gestacion": obj.control_prenatal.semanas_gestacion,
            }
        return None

    def get_medico_info(self, obj):
        """Get medico info"""
        if obj.medico_solicitante:
            return {
                "id": obj.medico_solicitante.id,
                "nombre": f"{obj.medico_solicitante.nombre} {obj.medico_solicitante.apellido_paterno}",
                "especialidad": obj.medico_solicitante.especialidad,
            }
        return None

    def get_resumen(self, obj):
        """Resumen de resultados"""
        total = obj.resultados.count()
        normales = obj.resultados.filter(es_normal=True).count()
        anormales = obj.resultados.filter(es_normal=False).count()
        criticos = obj.resultados.filter(es_critico=True).count()

        return {
            "total_parametros": total,
            "normales": normales,
            "anormales": anormales,
            "criticos": criticos,
            "porcentaje_normalidad": round(
                (normales / total * 100) if total > 0 else 0, 1,
            ),
        }

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


class ExamenLaboratorioCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar exámenes"""

    class Meta:
        """Meta"""
        model = ExamenLaboratorio
        fields = [
            "id",
            "paciente",
            "control_prenatal",
            "tipo_examen",
            "medico_solicitante",
            "fecha_muestra",
            "fecha_resultado",
            "estado",
            "prioridad",
            "indicaciones",
            "observaciones",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        """Validaciones personalizadas"""
        # Validar que el médico solicitante sea médico
        if attrs.get("medico_solicitante"):
            if attrs["medico_solicitante"].rol != "medico":
                raise serializers.ValidationError(
                    {"medico_solicitante": "El usuario debe tener rol de médico"},
                )

        # Validar que el control prenatal pertenezca al paciente
        if attrs.get("control_prenatal") and attrs.get("paciente"):
            if attrs["control_prenatal"].paciente != attrs["paciente"]:
                raise serializers.ValidationError(
                    {
                        "control_prenatal": "El control prenatal no pertenece al paciente seleccionado",
                    },
                )

        # Validar fechas
        if attrs.get("fecha_muestra") and attrs.get("fecha_resultado"):
            if attrs["fecha_muestra"] > attrs["fecha_resultado"]:
                raise serializers.ValidationError(
                    {
                        "fecha_resultado": "La fecha de resultado no puede ser anterior a la fecha de muestra",
                    },
                )

        return attrs


class ResultadoLaboratorioCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar resultados"""

    parametro_nombre = serializers.CharField(
        source="valor_referencia.parametro", read_only=True,
    )

    class Meta:
        """Meta"""
        model = ResultadoLaboratorio
        fields = [
            "id",
            "examen",
            "valor_referencia",
            "parametro_nombre",
            "valor_numerico",
            "valor_texto",
            "observaciones",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        """Validaciones"""
        # Debe tener al menos un valor (numérico o texto)
        if not attrs.get("valor_numerico") and not attrs.get("valor_texto"):
            raise serializers.ValidationError(
                "Debe proporcionar al menos un valor (numérico o texto)",
            )

        # Validar que el valor de referencia pertenece al tipo de examen
        if attrs.get("examen") and attrs.get("valor_referencia"):
            if attrs["valor_referencia"].tipo_examen != attrs["examen"].tipo_examen:
                raise serializers.ValidationError(
                    {
                        "valor_referencia": "El parámetro no pertenece al tipo de examen seleccionado",
                    },
                )

        return attrs


class ImportacionLaboratorioSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()
    anulada_por_nombre = serializers.SerializerMethodField()
    resultados = serializers.SerializerMethodField()

    class Meta:
        from .models import ImportacionLaboratorio

        model = ImportacionLaboratorio
        fields = ["id", "nombre_archivo", "fecha", "usuario_nombre", "resumen", "resultados", "anulada",
                  "motivo_anulacion", "anulada_por_nombre", "fecha_anulacion"]

    @staticmethod
    def _nombre(u):
        return (u.get_full_name() or u.email) if u else None

    def get_usuario_nombre(self, obj):
        return self._nombre(obj.usuario)

    def get_anulada_por_nombre(self, obj):
        return self._nombre(obj.anulada_por)

    def get_resultados(self, obj):
        return len(obj.resultados_creados or [])
