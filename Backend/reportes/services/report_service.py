"""=============================================================================
MÓDULO: REPORTES - REPORT SERVICE
=============================================================================
Servicio de generación de estadísticas y reportes
Adaptado de ReportService de cocineros-sistema (Laravel)
=============================================================================
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from django.utils import timezone

logger = logging.getLogger(__name__)


class ReportService:
    """Servicio centralizado para generación de reportes y estadísticas

    Adaptado del ReportService de cocineros-sistema (Laravel) a Django
    """

    @staticmethod
    def get_stats_overview(
        start_date: datetime | None = None, end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Obtiene estadísticas generales del sistema

        Args:
            start_date: Fecha inicial del rango
            end_date: Fecha final del rango

        Returns:
            Diccionario con estadísticas generales

        """
        from django.utils import timezone

        from citas.models import Cita
        from controles.models import ControlPrenatal
        from embarazos.models import Embarazo
        from laboratorio.models import ExamenLaboratorio
        from pacientes.models import Paciente
        from partos.models import Parto

        # Filtros de fecha
        date_filter = {}
        if start_date and end_date:
            date_filter["fecha_registro__range"] = (start_date, end_date)

        # Pacientes totales
        total_pacientes = Paciente.objects.filter(**date_filter).count()

        # Embarazos activos
        embarazos_activos = Embarazo.objects.filter(estado="activo").count()

        # Citas del día
        citas_hoy = Cita.objects.filter(fecha_cita=timezone.now().date()).count()

        # Partos del mes
        partos_mes = Parto.objects.filter(
            fecha_parto__year=timezone.now().year,
            fecha_parto__month=timezone.now().month,
        ).count()

        # Controles realizados
        controles_filter = {}
        if start_date and end_date:
            controles_filter["fecha_control__range"] = (start_date, end_date)
        total_controles = ControlPrenatal.objects.filter(**controles_filter).count()

        # Exámenes realizados
        examenes_filter = {}
        if start_date and end_date:
            examenes_filter["fecha_solicitud__range"] = (start_date, end_date)

        total_examenes = ExamenLaboratorio.objects.filter(**examenes_filter).count()

        # Tasa de asistencia a citas
        citas_filter = {}
        if start_date and end_date:
            citas_filter["fecha_cita__range"] = (start_date, end_date)

        total_citas = Cita.objects.filter(**citas_filter).count()
        citas_asistidas = Cita.objects.filter(
            **citas_filter, estado="completada",
        ).count()
        tasa_asistencia = (
            (citas_asistidas / total_citas * 100) if total_citas > 0 else 0
        )

        # Cálculo de crecimiento (comparación con período anterior)
        if start_date and end_date:
            dias_rango = (end_date - start_date).days
            fecha_inicio_anterior = start_date - timedelta(days=dias_rango)
            fecha_fin_anterior = start_date - timedelta(days=1)

            pacientes_anterior = Paciente.objects.filter(
                fecha_registro__range=(fecha_inicio_anterior, fecha_fin_anterior),
            ).count()

            crecimiento = (
                ((total_pacientes - pacientes_anterior) / pacientes_anterior * 100)
                if pacientes_anterior > 0
                else 0
            )
        else:
            crecimiento = 0

        return {
            "total_pacientes": total_pacientes,
            "embarazos_activos": embarazos_activos,
            "citas_hoy": citas_hoy,
            "partos_mes": partos_mes,
            "total_controles": total_controles,
            "total_examenes": total_examenes,
            "tasa_asistencia": round(tasa_asistencia, 2),
            "crecimiento_porcentaje": round(crecimiento, 2),
        }

    @staticmethod
    def get_monthly_comparison(months: int = 6) -> dict[str, list]:
        """Obtiene comparación mensual de actividad

        Args:
            months: Número de meses a comparar

        Returns:
            Diccionario con datos de comparación mensual

        """
        from django.db.models import Count
        from django.utils import timezone

        from controles.models import ControlPrenatal
        from pacientes.models import Paciente

        start_date = timezone.now() - timedelta(days=months * 30)

        # Obtener pacientes por mes
        pacientes_por_mes = (
            Paciente.objects.filter(fecha_registro__gte=start_date)
            .extra(select={"mes": "to_char(fecha_registro, 'YYYY-MM')"})
            .values("mes")
            .annotate(total=Count("id"))
            .order_by("mes")
        )

        # Obtener controles por mes
        controles_por_mes = (
            ControlPrenatal.objects.filter(fecha_control__gte=start_date)
            .extra(select={"mes": "to_char(fecha_control, 'YYYY-MM')"})
            .values("mes")
            .annotate(total=Count("id"))
            .order_by("mes")
        )

        # Formatear datos
        labels = []
        pacientes = []
        controles = []

        # Crear diccionarios para búsqueda rápida
        pacientes_dict = {item["mes"]: item["total"] for item in pacientes_por_mes}
        controles_dict = {item["mes"]: item["total"] for item in controles_por_mes}

        # Generar todos los meses en el rango
        current = start_date
        while current <= timezone.now():
            mes_str = current.strftime("%Y-%m")
            labels.append(current.strftime("%b %Y"))
            pacientes.append(pacientes_dict.get(mes_str, 0))
            controles.append(controles_dict.get(mes_str, 0))
            current += timedelta(days=30)

        return {"labels": labels, "pacientes": pacientes, "controles": controles}

    @staticmethod
    def get_risk_analysis() -> dict[str, int]:
        """Obtiene análisis de riesgo de pacientes
        """
        from embarazos.models import Embarazo

        return {
            "bajo": Embarazo.objects.filter(riesgo_embarazo="bajo").count(),
            "moderado": Embarazo.objects.filter(riesgo_embarazo="medio").count(),
            "alto": Embarazo.objects.filter(riesgo_embarazo="alto").count(),
        }

    @staticmethod
    def get_dashboard_stats(
        start_date: datetime | None = None, end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Obtiene estadísticas para el dashboard principal
        """
        from django.utils import timezone

        from citas.models import Cita
        from controles.models import ControlPrenatal
        from embarazos.models import Embarazo
        from pacientes.models import Paciente
        from partos.models import Parto

        date_filter: dict[str, Any] = {}
        if start_date and end_date:
            date_filter["fecha_registro__range"] = (start_date, end_date)

        # Pacientes
        total_pacientes = Paciente.objects.count()
        nuevos_pacientes = Paciente.objects.filter(**date_filter).count()

        # Embarazos
        embarazos_activos = Embarazo.objects.filter(estado="activo").count()
        embarazos_alto_riesgo = Embarazo.objects.filter(
            estado="activo", riesgo_embarazo__in=["alto"],
        ).count()

        # Controles (del mes actual o rango)
        controles_filter: dict[str, Any] = {}
        if start_date and end_date:
            controles_filter["fecha_control__range"] = (start_date, end_date)
        else:
            now = timezone.now()
            controles_filter["fecha_control__month"] = now.month
            controles_filter["fecha_control__year"] = now.year

        controles_mes = ControlPrenatal.objects.filter(**controles_filter).count()

        # Citas
        now_date = timezone.now().date()
        citas_pendientes = Cita.objects.filter(estado="agendada").count()
        citas_hoy = Cita.objects.filter(fecha_cita=now_date).count()

        # Partos (del mes actual o rango)
        partos_filter: dict[str, Any] = {}
        if start_date and end_date:
            partos_filter["fecha_parto__range"] = (start_date, end_date)
        else:
            now = timezone.now()
            partos_filter["fecha_parto__month"] = now.month
            partos_filter["fecha_parto__year"] = now.year
        partos_mes = Parto.objects.filter(**partos_filter).count()

        return {
            "total_pacientes": total_pacientes,
            "nuevos_pacientes": nuevos_pacientes,
            "embarazos_activos": embarazos_activos,
            "embarazos_alto_riesgo": embarazos_alto_riesgo,
            "controles_mes": controles_mes,
            "citas_pendientes": citas_pendientes,
            "citas_hoy": citas_hoy,
            "partos_mes": partos_mes,
        }

    @staticmethod
    def get_embarazos_stats(
        start_date: datetime | None = None, end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Obtiene estadísticas detalladas de embarazos
        """
        from django.db.models import Count

        from embarazos.models import Embarazo
        from pacientes.models import Paciente

        # Filtro base
        filter_kwargs = {}
        if start_date and end_date:
            filter_kwargs["fecha_registro__range"] = (start_date, end_date)

        total_embarazos = Embarazo.objects.filter(**filter_kwargs).count()

        # Por riesgo
        por_riesgo = list(
            Embarazo.objects.filter(**filter_kwargs)
            .values("riesgo_embarazo")
            .annotate(total=Count("id")),
        )
        # Mapear nombres de riesgo para consistencia
        riesgo_map = []
        for item in por_riesgo:
            riesgo_map.append(
                {
                    "clasificacion_riesgo": item["riesgo_embarazo"],
                    "total": item["total"],
                },
            )

        # Por trimestre - calcular basándose en FUR
        primer_tri = 0
        segundo_tri = 0
        tercer_tri = 0

        embarazos_activos = Embarazo.objects.filter(**filter_kwargs, estado="activo")
        for emb in embarazos_activos:
            if emb.fecha_ultima_menstruacion:
                hoy = timezone.localdate()
                dias = (hoy - emb.fecha_ultima_menstruacion).days
                semanas = dias // 7
                if semanas <= 13:
                    primer_tri += 1
                elif semanas <= 27:
                    segundo_tri += 1
                else:
                    tercer_tri += 1

        por_trimestre = {
            "primer_trimestre": primer_tri,
            "segundo_trimestre": segundo_tri,
            "tercer_trimestre": tercer_tri,
        }

        # Edad promedio
        if filter_kwargs:
            embarazo_filter = {f"embarazos__{k}": v for k, v in filter_kwargs.items()}
            pacientes_embarazadas = (
                Paciente.objects.filter(embarazos__isnull=False)
                .filter(**embarazo_filter)
                .distinct()
            )
        else:
            pacientes_embarazadas = Paciente.objects.filter(
                embarazos__isnull=False,
            ).distinct()

        # Calcular edad promedio manualmente ya que es una propiedad del modelo
        if pacientes_embarazadas.exists():
            edades = [p.edad for p in pacientes_embarazadas if p.fecha_nacimiento]
            edad_promedio = sum(edades) / len(edades) if edades else 0
        else:
            edad_promedio = 0

        return {
            "total_embarazos": total_embarazos,
            "por_riesgo": riesgo_map,
            "por_trimestre": por_trimestre,
            "edad_promedio": round(edad_promedio, 1),
            "semanas_promedio": 0,  # Placeholder
        }

    @staticmethod
    def get_controles_stats(
        start_date: datetime | None = None, end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Obtiene estadísticas de controles prenatales
        """
        from django.db.models import Avg, Count

        from controles.models import ControlPrenatal

        filter_kwargs = {}
        if start_date and end_date:
            filter_kwargs["fecha_control__range"] = (start_date, end_date)

        total_controles = ControlPrenatal.objects.filter(**filter_kwargs).count()

        # Por médico - incluir TODOS los controles (con y sin médico asignado)
        por_medico = list(
            ControlPrenatal.objects.filter(**filter_kwargs)
            .values("medico__nombre", "medico__apellido_paterno")
            .annotate(total=Count("id")),
        )

        # Promedios
        promedios = ControlPrenatal.objects.filter(**filter_kwargs).aggregate(
            peso_promedio=Avg("peso_actual"),
            presion_sistolica_promedio=Avg("presion_arterial_sistolica"),
            presion_diastolica_promedio=Avg("presion_arterial_diastolica"),
        )

        # Controles diarios (para gráfico)
        controles_diarios = list(
            ControlPrenatal.objects.filter(**filter_kwargs)
            .extra(select={"fecha": "to_char(fecha_control, 'YYYY-MM-DD')"})
            .values("fecha")
            .annotate(total=Count("id"))
            .order_by("fecha"),
        )

        return {
            "total_controles": total_controles,
            "por_medico": por_medico,
            "promedios": promedios,
            "controles_diarios": controles_diarios,
        }

    @staticmethod
    def get_citas_stats(
        start_date: datetime | None = None, end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Obtiene estadísticas de citas
        """
        from django.db.models import Count

        from citas.models import Cita

        filter_kwargs = {}
        if start_date and end_date:
            filter_kwargs["fecha_cita__range"] = (start_date, end_date)

        total_citas = Cita.objects.filter(**filter_kwargs).count()

        # Por estado
        por_estado = list(
            Cita.objects.filter(**filter_kwargs)
            .values("estado")
            .annotate(total=Count("id")),
        )

        # Por tipo
        por_tipo = list(
            Cita.objects.filter(**filter_kwargs)
            .values("tipo_cita")
            .annotate(total=Count("id")),
        )

        # Contadores específicos
        completadas = Cita.objects.filter(**filter_kwargs, estado="completada").count()
        canceladas = Cita.objects.filter(**filter_kwargs, estado="cancelada").count()
        no_asistidas = Cita.objects.filter(**filter_kwargs, estado="no_asistio").count()

        # Tasas
        tasa_asistencia = (completadas / total_citas * 100) if total_citas > 0 else 0
        tasa_cancelacion = (canceladas / total_citas * 100) if total_citas > 0 else 0

        return {
            "total_citas": total_citas,
            "por_estado": por_estado,
            "por_tipo": por_tipo,
            "completadas": completadas,
            "canceladas": canceladas,
            "no_asistidas": no_asistidas,
            "tasa_asistencia": round(tasa_asistencia, 1),
            "tasa_cancelacion": round(tasa_cancelacion, 1),
        }

    @staticmethod
    def get_partos_stats(
        start_date: datetime | None = None, end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Obtiene estadísticas de partos
        """
        from django.db.models import Count

        from partos.models import Parto

        filter_kwargs = {}
        if start_date and end_date:
            # Ajustar end_date al final del día para incluir todos los partos de ese día
            end_date_adjusted = end_date.replace(
                hour=23, minute=59, second=59, microsecond=999999,
            )
            filter_kwargs["fecha_parto__gte"] = start_date
            filter_kwargs["fecha_parto__lte"] = end_date_adjusted

        total_partos = Parto.objects.filter(**filter_kwargs).count()

        # Por tipo de parto
        por_tipo = list(
            Parto.objects.filter(**filter_kwargs)
            .values("tipo_parto")
            .annotate(total=Count("id")),
        )

        por_atencion: list[Any] = []

        con_complicaciones = 0
        sin_complicaciones = total_partos

        promedios = {
            "peso_promedio": 0,
            "talla_promedio": 0,
            "apgar_1_promedio": 0,
            "apgar_5_promedio": 0,
        }

        # Partos mensuales
        partos_mensuales = list(
            Parto.objects.filter(**filter_kwargs)
            .extra(select={"mes": "to_char(fecha_parto, 'YYYY-MM')"})
            .values("mes")
            .annotate(total=Count("id"))
            .order_by("mes"),
        )

        return {
            "total_partos": total_partos,
            "por_tipo": por_tipo,
            "por_atencion": por_atencion,
            "con_complicaciones": con_complicaciones,
            "sin_complicaciones": sin_complicaciones,
            "promedios": promedios,
            "partos_mensuales": partos_mensuales,
        }

    @staticmethod
    def get_all_statistics(
        start_date: datetime | None = None, end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Obtiene TODAS las estadísticas del sistema en una sola llamada
        Con manejo de errores defensivo para cada sección
        """
        import traceback

        result = {}

        # Dashboard stats
        try:
            result["dashboard"] = ReportService.get_dashboard_stats(
                start_date, end_date,
            )
        except Exception as e:
            logger.exception("Error en dashboard_stats: %s", e)
            traceback.print_exc()
            result["dashboard"] = {"error": str(e)}

        # Embarazos stats
        try:
            result["embarazos"] = ReportService.get_embarazos_stats(
                start_date, end_date,
            )
        except Exception as e:
            logger.exception("Error en embarazos_stats: %s", e)
            traceback.print_exc()
            result["embarazos"] = {"error": str(e)}

        # Controles stats
        try:
            result["controles"] = ReportService.get_controles_stats(
                start_date, end_date,
            )
        except Exception as e:
            logger.exception("Error en controles_stats: %s", e)
            traceback.print_exc()
            result["controles"] = {"error": str(e)}

        # Citas stats
        try:
            result["citas"] = ReportService.get_citas_stats(start_date, end_date)
        except Exception as e:
            logger.exception("Error en citas_stats: %s", e)
            traceback.print_exc()
            result["citas"] = {"error": str(e)}

        # Partos stats
        try:
            result["partos"] = ReportService.get_partos_stats(start_date, end_date)
        except Exception as e:
            logger.exception("Error en partos_stats: %s", e)
            traceback.print_exc()
            result["partos"] = {"error": str(e)}

        return result

    @staticmethod
    def get_composition_chart_data(_start_date=None, _end_date=None):
        """Gráfico de dona - Composición porcentual"""
        from controles.models import ControlPrenatal
        from embarazos.models import Embarazo
        from pacientes.models import Paciente
        from partos.models import Parto

        try:
            total_pacientes = Paciente.objects.count()
            total_embarazos = Embarazo.objects.count()
            total_controles = ControlPrenatal.objects.count()
            total_partos = Parto.objects.count()

            total = total_pacientes + total_embarazos + total_controles + total_partos
            if total == 0:
                return []

            return [
                {
                    "name": "Pacientes",
                    "value": total_pacientes,
                    "percentage": round((total_pacientes / total) * 100, 1),
                },
                {
                    "name": "Embarazos",
                    "value": total_embarazos,
                    "percentage": round((total_embarazos / total) * 100, 1),
                },
                {
                    "name": "Controles",
                    "value": total_controles,
                    "percentage": round((total_controles / total) * 100, 1),
                },
                {
                    "name": "Partos",
                    "value": total_partos,
                    "percentage": round((total_partos / total) * 100, 1),
                },
            ]
        except Exception as e:
            logger.exception("Error en get_composition_chart_data: %s", e)
            return []

    @staticmethod
    def get_stacked_bar_chart_data(months=12):
        """Gráfico de barras apiladas - Comparativa mensual"""
        from django.utils import timezone

        from citas.models import Cita
        from controles.models import ControlPrenatal
        from embarazos.models import Embarazo
        from partos.models import Parto

        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=30 * months)
            data = []

            for i in range(months):
                month_start = start_date + timedelta(days=30 * i)
                month_end = month_start + timedelta(days=30)

                data.append(
                    {
                        "month": month_start.strftime("%b %Y"),
                        "embarazos": Embarazo.objects.filter(
                            fecha_registro__gte=month_start,
                            fecha_registro__lt=month_end,
                        ).count(),
                        "controles": ControlPrenatal.objects.filter(
                            fecha_control__gte=month_start, fecha_control__lt=month_end,
                        ).count(),
                        "partos": Parto.objects.filter(
                            fecha_parto__gte=month_start, fecha_parto__lt=month_end,
                        ).count(),
                        "citas": Cita.objects.filter(
                            fecha_cita__gte=month_start, fecha_cita__lt=month_end,
                        ).count(),
                    },
                )

            return data
        except Exception as e:
            logger.exception("Error en get_stacked_bar_chart_data: %s", e)
            return []

    @staticmethod
    def get_distribution_chart_data():
        """Gráfico de distribución - Edades de pacientes"""
        from pacientes.models import Paciente

        try:
            pacientes = Paciente.objects.all()
            edades = []

            for p in pacientes:
                if p.fecha_nacimiento:
                    edad = (datetime.now().date() - p.fecha_nacimiento).days // 365
                    if 0 <= edad <= 100:
                        edades.append(edad)

            if not edades:
                return {"data": [], "stats": {}}

            distribution = {}
            for edad in edades:
                rango = (edad // 5) * 5
                distribution[rango] = distribution.get(rango, 0) + 1

            data = [{"age": k, "count": v} for k, v in sorted(distribution.items())]
            mean = sum(edades) / len(edades)
            sorted_edades = sorted(edades)

            return {
                "data": data,
                "stats": {
                    "mean": round(mean, 1),
                    "median": sorted_edades[len(sorted_edades) // 2],
                    "min": min(edades),
                    "max": max(edades),
                    "count": len(edades),
                },
            }
        except Exception as e:
            logger.exception("Error en get_distribution_chart_data: %s", e)
            return {"data": [], "stats": {}}
