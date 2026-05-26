"""=============================================================================
MÓDULO: PARTOS - FILTROS PERSONALIZADOS V2.0 CON FOREIGNKEY
=============================================================================
Filtros avanzados actualizados para trabajar con ForeignKey
=============================================================================
"""

from django.db.models import Q
from django_filters import rest_framework as filters

from .models import Parto, PartogramaRegistro, RecienNacido


class PartoFilter(filters.FilterSet):
    """Filtro avanzado para partos con ForeignKey"""

    # Filtros por rango de fechas
    fecha_parto_desde = filters.DateTimeFilter(
        field_name="fecha_parto", lookup_expr="gte",
    )
    fecha_parto_hasta = filters.DateTimeFilter(
        field_name="fecha_parto", lookup_expr="lte",
    )
    fecha_ingreso_desde = filters.DateTimeFilter(
        field_name="fecha_ingreso", lookup_expr="gte",
    )
    fecha_ingreso_hasta = filters.DateTimeFilter(
        field_name="fecha_ingreso", lookup_expr="lte",
    )

    #  FILTROS POR FOREIGNKEY
    paciente = filters.NumberFilter(field_name="paciente__id")
    paciente_nombre = filters.CharFilter(
        field_name="paciente__nombre", lookup_expr="icontains",
    )
    paciente_apellido = filters.CharFilter(
        field_name="paciente__apellido_paterno", lookup_expr="icontains",
    )
    paciente_id_clinico = filters.CharFilter(
        field_name="paciente__id_clinico", lookup_expr="icontains",
    )

    embarazo = filters.NumberFilter(field_name="embarazo__id")

    medico_responsable = filters.NumberFilter(field_name="medico_responsable__id")
    medico_nombre = filters.CharFilter(
        field_name="medico_responsable__nombre", lookup_expr="icontains",
    )

    # Filtros por edad gestacional
    edad_gestacional_min = filters.NumberFilter(method="filter_edad_gestacional_min")
    edad_gestacional_max = filters.NumberFilter(method="filter_edad_gestacional_max")

    # Filtros por pérdida sanguínea
    perdida_sanguinea_min = filters.NumberFilter(
        field_name="perdida_sanguinea_estimada", lookup_expr="gte",
    )
    perdida_sanguinea_max = filters.NumberFilter(
        field_name="perdida_sanguinea_estimada", lookup_expr="lte",
    )

    # Filtros por duración
    duracion_min = filters.NumberFilter(
        field_name="duracion_trabajo_parto_horas", lookup_expr="gte",
    )
    duracion_max = filters.NumberFilter(
        field_name="duracion_trabajo_parto_horas", lookup_expr="lte",
    )

    # Filtros booleanos
    con_complicaciones = filters.BooleanFilter(method="filter_con_complicaciones")
    solo_cesareas = filters.BooleanFilter(method="filter_solo_cesareas")
    solo_vaginales = filters.BooleanFilter(method="filter_solo_vaginales")

    # Filtros de auditoría
    created_by = filters.NumberFilter(field_name="created_by__id")
    modified_by = filters.NumberFilter(field_name="modified_by__id")

    class Meta:
        """Meta"""
        model = Parto
        fields = {
            "tipo_parto": ["exact", "icontains"],
            "presentacion_fetal": ["exact"],
            "parto_finalizado": ["exact"],
            "hemorragia_postparto": ["exact"],
            "episiotomia": ["exact"],
            "desgarros": ["exact"],
            "analgesia_utilizada": ["exact"],
            "oxitocina_utilizada": ["exact"],
            "induccion_parto": ["exact"],
            "trabajo_parto_espontaneo": ["exact"],
        }

    def filter_edad_gestacional_min(self, queryset, _name, value):
        """Filtrar por edad gestacional mínima (en semanas)"""
        return queryset.filter(
            edad_gestacional_parto__regex=r"^("
            + "|".join([str(i) for i in range(int(value), 46)])
            + r")(\+\d)$",
        )

    def filter_edad_gestacional_max(self, queryset, _name, value):
        """Filtrar por edad gestacional máxima (en semanas)"""
        return queryset.filter(
            edad_gestacional_parto__regex=r"^("
            + "|".join([str(i) for i in range(20, int(value) + 1)])
            + r")(\+\d)$",
        )

    def filter_con_complicaciones(self, queryset, _name, value):
        """Filtrar partos con complicaciones"""
        if value:
            return queryset.filter(
                Q(hemorragia_postparto=True)
                | Q(desgarros=True)
                | Q(perdida_sanguinea_estimada__gt=500)
                | Q(complicaciones_maternas__isnull=False),
            ).exclude(complicaciones_maternas="")
        return queryset

    def filter_solo_cesareas(self, queryset, _name, value):
        """Filtrar solo cesáreas"""
        if value:
            return queryset.filter(tipo_parto__icontains="cesarea")
        return queryset

    def filter_solo_vaginales(self, queryset, _name, value):
        """Filtrar solo partos vaginales"""
        if value:
            return queryset.filter(tipo_parto__icontains="vaginal")
        return queryset


class RecienNacidoFilter(filters.FilterSet):
    """Filtro avanzado para recién nacidos"""

    # Filtros por rango de fechas
    fecha_nacimiento_desde = filters.DateTimeFilter(
        field_name="fecha_nacimiento", lookup_expr="gte",
    )
    fecha_nacimiento_hasta = filters.DateTimeFilter(
        field_name="fecha_nacimiento", lookup_expr="lte",
    )

    # Filtros por peso
    peso_min = filters.NumberFilter(field_name="peso_nacimiento", lookup_expr="gte")
    peso_max = filters.NumberFilter(field_name="peso_nacimiento", lookup_expr="lte")

    # Filtros por talla
    talla_min = filters.NumberFilter(field_name="talla_nacimiento", lookup_expr="gte")
    talla_max = filters.NumberFilter(field_name="talla_nacimiento", lookup_expr="lte")

    # Filtros por Apgar
    apgar_1_min = filters.NumberFilter(field_name="apgar_1_minuto", lookup_expr="gte")
    apgar_1_max = filters.NumberFilter(field_name="apgar_1_minuto", lookup_expr="lte")
    apgar_5_min = filters.NumberFilter(field_name="apgar_5_minutos", lookup_expr="gte")
    apgar_5_max = filters.NumberFilter(field_name="apgar_5_minutos", lookup_expr="lte")

    # Filtros por clasificación
    bajo_peso = filters.BooleanFilter(method="filter_bajo_peso")
    macrosomia = filters.BooleanFilter(method="filter_macrosomia")
    apgar_bajo = filters.BooleanFilter(method="filter_apgar_bajo")
    con_complicaciones = filters.BooleanFilter(method="filter_con_complicaciones")

    class Meta:
        """Meta"""
        model = RecienNacido
        fields = {
            "sexo": ["exact"],
            "estado_nacimiento": ["exact"],
            "requirio_reanimacion": ["exact"],
            "malformaciones_congenitas": ["exact"],
            "destino_rn": ["exact"],
            "llanto_inmediato": ["exact"],
            "respiracion_espontanea": ["exact"],
            "tono_muscular_normal": ["exact"],
            "parto": ["exact"],
            "numero_gemelo": ["exact"],
        }

    def filter_bajo_peso(self, queryset, _name, value):
        """Filtrar recién nacidos con bajo peso (<2500g)"""
        if value:
            return queryset.filter(peso_nacimiento__lt=2500)
        return queryset

    def filter_macrosomia(self, queryset, _name, value):
        """Filtrar recién nacidos con macrosomía (>4000g)"""
        if value:
            return queryset.filter(peso_nacimiento__gt=4000)
        return queryset

    def filter_apgar_bajo(self, queryset, _name, value):
        """Filtrar recién nacidos con Apgar bajo (<7 a los 5 min)"""
        if value:
            return queryset.filter(apgar_5_minutos__lt=7)
        return queryset

    def filter_con_complicaciones(self, queryset, _name, value):
        """Filtrar recién nacidos con complicaciones"""
        if value:
            return queryset.filter(
                Q(requirio_reanimacion=True)
                | Q(malformaciones_congenitas=True)
                | Q(apgar_5_minutos__lt=7)
                | Q(llanto_inmediato=False)
                | Q(respiracion_espontanea=False),
            )
        return queryset


class PartogramaFilter(filters.FilterSet):
    """Filtro avanzado para registros de partograma"""

    # Filtros por rango de fechas
    hora_registro_desde = filters.DateTimeFilter(
        field_name="hora_registro", lookup_expr="gte",
    )
    hora_registro_hasta = filters.DateTimeFilter(
        field_name="hora_registro", lookup_expr="lte",
    )

    # Filtros por dilatación
    dilatacion_min = filters.NumberFilter(
        field_name="dilatacion_cervical", lookup_expr="gte",
    )
    dilatacion_max = filters.NumberFilter(
        field_name="dilatacion_cervical", lookup_expr="lte",
    )

    # Filtros por FCF
    fcf_min = filters.NumberFilter(field_name="fcf_baseline", lookup_expr="gte")
    fcf_max = filters.NumberFilter(field_name="fcf_baseline", lookup_expr="lte")

    # Filtros por contracciones
    contracciones_min = filters.NumberFilter(
        field_name="contracciones_10min", lookup_expr="gte",
    )
    contracciones_max = filters.NumberFilter(
        field_name="contracciones_10min", lookup_expr="lte",
    )

    # Filtros booleanos
    solo_alertas = filters.BooleanFilter(method="filter_solo_alertas")
    fcf_anormal = filters.BooleanFilter(field_name="alerta_fcf_anormal")
    progreso_lento = filters.BooleanFilter(field_name="alerta_progreso_lento")
    signos_vitales_alterados = filters.BooleanFilter(field_name="alerta_signos_vitales")

    class Meta:
        """Meta"""
        model = PartogramaRegistro
        fields = {
            "parto": ["exact"],
            "intensidad_contracciones": ["exact"],
            "variabilidad_fc": ["exact"],
            "registrado_por_id": ["exact"],
        }

    def filter_solo_alertas(self, queryset, _name, value):
        """Filtrar solo registros con alertas activas"""
        if value:
            return queryset.filter(
                Q(alerta_fcf_anormal=True)
                | Q(alerta_progreso_lento=True)
                | Q(alerta_signos_vitales=True),
            )
        return queryset
