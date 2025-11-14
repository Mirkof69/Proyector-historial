# =============================================================================
# FILTROS PERSONALIZADOS DE PACIENTES
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: pacientes
# Descripción: Filtros avanzados para búsqueda y filtrado de pacientes.
# Versión: 1.0.0
# Última actualización: 2025-11-14
# =============================================================================

from django_filters import rest_framework as filters
from django.db.models import Q
from .models import Paciente


class PacienteFilter(filters.FilterSet):
    """
    Filtros personalizados para pacientes.

    Permite filtrar por:
    - Datos básicos (nombre, cédula, edad)
    - Factores de riesgo médico
    - Antecedentes obstétricos
    - Hábitos
    - Rangos de fechas
    - Estado activo/inactivo
    """

    # Filtros de texto (parcial, case-insensitive)
    nombres = filters.CharFilter(field_name='nombres', lookup_expr='icontains')
    apellidos = filters.CharFilter(field_name='apellidos', lookup_expr='icontains')
    nombre_completo = filters.CharFilter(method='filter_nombre_completo')
    cedula = filters.CharFilter(field_name='cedula_identidad', lookup_expr='icontains')
    id_clinico = filters.CharFilter(field_name='id_clinico', lookup_expr='icontains')
    telefono = filters.CharFilter(field_name='telefono', lookup_expr='icontains')
    email = filters.CharFilter(field_name='email', lookup_expr='icontains')

    # Filtros de edad
    edad_min = filters.NumberFilter(method='filter_edad_min')
    edad_max = filters.NumberFilter(method='filter_edad_max')
    edad_exacta = filters.NumberFilter(method='filter_edad_exacta')

    # Filtros de fecha de nacimiento
    fecha_nacimiento = filters.DateFilter(field_name='fecha_nacimiento')
    fecha_nacimiento_desde = filters.DateFilter(field_name='fecha_nacimiento', lookup_expr='gte')
    fecha_nacimiento_hasta = filters.DateFilter(field_name='fecha_nacimiento', lookup_expr='lte')

    # Filtros de género y estado civil
    genero = filters.ChoiceFilter(field_name='genero', choices=Paciente.GENEROS)
    estado_civil = filters.ChoiceFilter(field_name='estado_civil', choices=Paciente.ESTADOS_CIVILES)

    # Filtros de antecedentes obstétricos
    gestas = filters.NumberFilter(field_name='gestas')
    gestas_min = filters.NumberFilter(field_name='gestas', lookup_expr='gte')
    gestas_max = filters.NumberFilter(field_name='gestas', lookup_expr='lte')

    partos = filters.NumberFilter(field_name='partos')
    partos_min = filters.NumberFilter(field_name='partos', lookup_expr='gte')
    partos_max = filters.NumberFilter(field_name='partos', lookup_expr='lte')

    abortos = filters.NumberFilter(field_name='abortos')
    abortos_min = filters.NumberFilter(field_name='abortos', lookup_expr='gte')
    abortos_max = filters.NumberFilter(field_name='abortos', lookup_expr='lte')

    cesareas = filters.NumberFilter(field_name='cesareas')
    cesareas_min = filters.NumberFilter(field_name='cesareas', lookup_expr='gte')
    cesareas_max = filters.NumberFilter(field_name='cesareas', lookup_expr='lte')

    # Clasificación obstétrica
    es_primigesta = filters.BooleanFilter(method='filter_primigesta')
    es_multigesta = filters.BooleanFilter(method='filter_multigesta')
    es_gran_multigesta = filters.BooleanFilter(method='filter_gran_multigesta')

    # Filtros de factores de riesgo
    diabetes_previa = filters.BooleanFilter(field_name='diabetes_previa')
    hipertension_previa = filters.BooleanFilter(field_name='hipertension_previa')
    preeclampsia_previa = filters.BooleanFilter(field_name='preeclampsia_previa')
    eclampsia_previa = filters.BooleanFilter(field_name='eclampsia_previa')
    hemorragia_postparto_previa = filters.BooleanFilter(field_name='hemorragia_postparto_previa')
    cirugia_uterina_previa = filters.BooleanFilter(field_name='cirugia_uterina_previa')
    incompetencia_cervical = filters.BooleanFilter(field_name='incompetencia_cervical')
    malformaciones_uterinas = filters.BooleanFilter(field_name='malformaciones_uterinas')

    # Filtros de hábitos
    fuma = filters.BooleanFilter(field_name='fuma')
    consume_alcohol = filters.BooleanFilter(field_name='consume_alcohol')
    consume_drogas = filters.BooleanFilter(field_name='consume_drogas')

    # Filtros de seguro
    tiene_seguro = filters.BooleanFilter(field_name='tiene_seguro')
    tipo_seguro = filters.CharFilter(field_name='tipo_seguro', lookup_expr='icontains')

    # Filtros de nivel socioeconómico
    nivel_educativo = filters.ChoiceFilter(field_name='nivel_educativo', choices=Paciente.NIVELES_EDUCATIVOS)
    acceso_agua_potable = filters.BooleanFilter(field_name='acceso_agua_potable')
    acceso_alcantarillado = filters.BooleanFilter(field_name='acceso_alcantarillado')

    # Filtros de estado
    activo = filters.BooleanFilter(field_name='activo')
    eliminado = filters.BooleanFilter(field_name='eliminado')

    # Filtros de fechas de auditoría
    fecha_creacion = filters.DateFilter(field_name='fecha_creacion')
    fecha_creacion_desde = filters.DateFilter(field_name='fecha_creacion', lookup_expr='gte')
    fecha_creacion_hasta = filters.DateFilter(field_name='fecha_creacion', lookup_expr='lte')

    fecha_modificacion = filters.DateFilter(field_name='fecha_modificacion')
    fecha_modificacion_desde = filters.DateFilter(field_name='fecha_modificacion', lookup_expr='gte')
    fecha_modificacion_hasta = filters.DateFilter(field_name='fecha_modificacion', lookup_expr='lte')

    # Filtros compuestos
    con_factores_riesgo = filters.BooleanFilter(method='filter_con_factores_riesgo')
    alto_riesgo = filters.BooleanFilter(method='filter_alto_riesgo')
    sin_antecedentes = filters.BooleanFilter(method='filter_sin_antecedentes')

    class Meta:
        model = Paciente
        fields = []  # Los campos se definen arriba

    # =========================================================================
    # MÉTODOS DE FILTRADO PERSONALIZADOS
    # =========================================================================

    def filter_nombre_completo(self, queryset, name, value):
        """
        Busca en nombres y apellidos simultáneamente.
        """
        return queryset.filter(
            Q(nombres__icontains=value) | Q(apellidos__icontains=value)
        )

    def filter_edad_min(self, queryset, name, value):
        """
        Filtra pacientes con edad >= valor especificado.
        """
        from django.utils import timezone
        from datetime import timedelta

        fecha_max = timezone.now().date() - timedelta(days=int(value)*365.25)
        return queryset.filter(fecha_nacimiento__lte=fecha_max)

    def filter_edad_max(self, queryset, name, value):
        """
        Filtra pacientes con edad <= valor especificado.
        """
        from django.utils import timezone
        from datetime import timedelta

        fecha_min = timezone.now().date() - timedelta(days=int(value)*365.25)
        return queryset.filter(fecha_nacimiento__gte=fecha_min)

    def filter_edad_exacta(self, queryset, name, value):
        """
        Filtra pacientes con edad exacta (±6 meses).
        """
        from django.utils import timezone
        from datetime import timedelta

        hoy = timezone.now().date()
        fecha_min = hoy - timedelta(days=int(value)*365.25 + 182)
        fecha_max = hoy - timedelta(days=int(value)*365.25 - 182)
        return queryset.filter(fecha_nacimiento__range=[fecha_min, fecha_max])

    def filter_primigesta(self, queryset, name, value):
        """
        Filtra primigestas (gestas = 0 o 1).
        """
        if value:
            return queryset.filter(gestas__lte=1)
        else:
            return queryset.filter(gestas__gte=2)

    def filter_multigesta(self, queryset, name, value):
        """
        Filtra multigestas (gestas >= 2 y < 5).
        """
        if value:
            return queryset.filter(gestas__gte=2, gestas__lt=5)
        else:
            return queryset.exclude(gestas__gte=2, gestas__lt=5)

    def filter_gran_multigesta(self, queryset, name, value):
        """
        Filtra gran multigestas (gestas >= 5).
        """
        if value:
            return queryset.filter(gestas__gte=5)
        else:
            return queryset.filter(gestas__lt=5)

    def filter_con_factores_riesgo(self, queryset, name, value):
        """
        Filtra pacientes que tienen al menos un factor de riesgo.
        """
        if value:
            return queryset.filter(
                Q(diabetes_previa=True) |
                Q(hipertension_previa=True) |
                Q(preeclampsia_previa=True) |
                Q(eclampsia_previa=True) |
                Q(hemorragia_postparto_previa=True) |
                Q(cirugia_uterina_previa=True) |
                Q(incompetencia_cervical=True) |
                Q(malformaciones_uterinas=True) |
                Q(fuma=True) |
                Q(consume_drogas=True)
            )
        else:
            return queryset.filter(
                diabetes_previa=False,
                hipertension_previa=False,
                preeclampsia_previa=False,
                eclampsia_previa=False,
                hemorragia_postparto_previa=False,
                cirugia_uterina_previa=False,
                incompetencia_cervical=False,
                malformaciones_uterinas=False,
                fuma=False,
                consume_drogas=False
            )

    def filter_alto_riesgo(self, queryset, name, value):
        """
        Filtra pacientes de alto riesgo (índice >= 50).
        Este filtro puede ser lento en bases de datos grandes.
        """
        if value:
            # Filtrar por criterios que indican alto riesgo
            pacientes_riesgo = []
            for paciente in queryset:
                if paciente.get_indice_riesgo() >= 50:
                    pacientes_riesgo.append(paciente.id)
            return queryset.filter(id__in=pacientes_riesgo)
        else:
            pacientes_bajo_riesgo = []
            for paciente in queryset:
                if paciente.get_indice_riesgo() < 50:
                    pacientes_bajo_riesgo.append(paciente.id)
            return queryset.filter(id__in=pacientes_bajo_riesgo)

    def filter_sin_antecedentes(self, queryset, name, value):
        """
        Filtra pacientes sin antecedentes médicos relevantes.
        """
        if value:
            return queryset.filter(
                diabetes_previa=False,
                hipertension_previa=False,
                preeclampsia_previa=False,
                eclampsia_previa=False,
                hemorragia_postparto_previa=False,
                cirugia_uterina_previa=False,
                incompetencia_cervical=False,
                malformaciones_uterinas=False,
                fuma=False,
                consume_alcohol=False,
                consume_drogas=False,
                gestas=0
            )
        else:
            return queryset.exclude(
                diabetes_previa=False,
                hipertension_previa=False,
                preeclampsia_previa=False,
                eclampsia_previa=False,
                hemorragia_postparto_previa=False,
                cirugia_uterina_previa=False,
                incompetencia_cervical=False,
                malformaciones_uterinas=False,
                fuma=False,
                consume_alcohol=False,
                consume_drogas=False,
                gestas=0
            )
