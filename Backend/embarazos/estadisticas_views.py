"""=============================================================================
VIEWS: ESTADÍSTICAS DE CLASIFICACIÓN DE RIESGOS
=============================================================================
Endpoints para dashboard de clasificación de riesgos de embarazos
=============================================================================
"""

from datetime import timedelta

from django.db.models import Avg, Count
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from core.permissions import FetalMedicalPermission
from rest_framework.response import Response

from controles.models import ControlPrenatal

from .models import Embarazo


class ClasificacionRiesgosViewSet(viewsets.ViewSet):
    """ViewSet para estadísticas y dashboard de clasificación de riesgos
    """

    permission_classes = [FetalMedicalPermission]

    @action(detail=False, methods=["get"], url_path="distribucion")
    def distribucion_riesgos(self, _request):
        """Retorna la distribución de embarazos por nivel de riesgo

        GET /api/clasificacion-riesgos/distribucion/
        """
        # Total de embarazos activos
        embarazos_activos = Embarazo.objects.filter(estado="activo")

        # Contar por nivel de riesgo
        distribucion = (
            embarazos_activos.values("riesgo_embarazo")
            .annotate(total=Count("id"))
            .order_by("riesgo_embarazo")
        )

        # Calcular porcentajes
        total_embarazos = embarazos_activos.count()

        resultado = []
        for item in distribucion:
            riesgo = item["riesgo_embarazo"]
            total = item["total"]
            porcentaje = (total / total_embarazos * 100) if total_embarazos > 0 else 0

            resultado.append(
                {
                    "nivel": riesgo,
                    "total": total,
                    "porcentaje": round(porcentaje, 2),
                    "label": dict(Embarazo.RIESGOS).get(riesgo, riesgo),
                },
            )

        return Response(
            {
                "distribucion": resultado,
                "total_embarazos": total_embarazos,
                "fecha_actualizacion": timezone.now().isoformat(),
            },
        )

    @action(detail=False, methods=["get"], url_path="alto-riesgo")
    def pacientes_alto_riesgo(self, _request):
        """Retorna lista de pacientes con embarazos de alto riesgo

        GET /api/clasificacion-riesgos/alto-riesgo/
        """
        embarazos_alto_riesgo = (
            Embarazo.objects.filter(estado="activo", riesgo_embarazo="alto")
            .select_related("paciente", "medico_responsable")
            .order_by("-fecha_ultima_menstruacion")
        )

        resultado = []
        for embarazo in embarazos_alto_riesgo:
            # Obtener último control
            ultimo_control = (
                ControlPrenatal.objects.filter(embarazo=embarazo)
                .order_by("-fecha_control")
                .first()
            )

            resultado.append(
                {
                    "embarazo_id": embarazo.id,
                    "paciente": {
                        "id": embarazo.paciente.id,
                        "nombre_completo": embarazo.paciente.nombre_completo,
                        "ci": embarazo.paciente.ci,
                        "edad": embarazo.paciente.edad,
                    },
                    "semanas_gestacion": embarazo.semanas_gestacion,
                    "fecha_ultimo_control": ultimo_control.fecha_control.isoformat()
                    if ultimo_control
                    else None,
                    "medico_responsable": {
                        "id": embarazo.medico_responsable.id,
                        "nombre_completo": embarazo.medico_responsable.nombre_completo,
                    }
                    if embarazo.medico_responsable
                    else None,
                    "fecha_probable_parto": embarazo.fecha_probable_parto.isoformat()
                    if embarazo.fecha_probable_parto
                    else None,
                },
            )

        return Response({"pacientes_alto_riesgo": resultado, "total": len(resultado)})

    @action(detail=False, methods=["get"], url_path="tendencias")
    def tendencias_riesgos(self, _request):
        """Retorna tendencias de clasificación de riesgos en los últimos meses

        GET /api/clasificacion-riesgos/tendencias/
        """
        # Últimos 6 meses
        hace_6_meses = timezone.now() - timedelta(days=180)

        embarazos_recientes = Embarazo.objects.filter(
            fecha_creacion__gte=hace_6_meses,
        ).order_by("fecha_creacion")

        # Agrupar por mes y riesgo
        from django.db.models.functions import TruncMonth

        tendencias = (
            embarazos_recientes.annotate(mes=TruncMonth("fecha_creacion"))
            .values("mes", "riesgo_embarazo")
            .annotate(total=Count("id"))
            .order_by("mes", "riesgo_embarazo")
        )

        # Formatear resultado
        resultado_por_mes = {}
        for item in tendencias:
            mes_str = item["mes"].strftime("%Y-%m")
            if mes_str not in resultado_por_mes:
                resultado_por_mes[mes_str] = {
                    "mes": mes_str,
                    "bajo": 0,
                    "medio": 0,
                    "alto": 0,
                }
            resultado_por_mes[mes_str][item["riesgo_embarazo"]] = item["total"]

        return Response(
            {"tendencias": list(resultado_por_mes.values()), "periodo": "6 meses"},
        )

    @action(detail=False, methods=["get"], url_path="estadisticas-generales")
    def estadisticas_generales(self, _request):
        """Retorna estadísticas generales de clasificación de riesgos

        GET /api/clasificacion-riesgos/estadisticas-generales/
        """
        embarazos_activos = Embarazo.objects.filter(estado="activo")

        # Contadores generales
        total_activos = embarazos_activos.count()
        total_bajo = embarazos_activos.filter(riesgo_embarazo="bajo").count()
        total_medio = embarazos_activos.filter(riesgo_embarazo="medio").count()
        total_alto = embarazos_activos.filter(riesgo_embarazo="alto").count()

        # Embarazos de alto riesgo sin control reciente (últimos 30 días)
        hace_30_dias = timezone.now() - timedelta(days=30)

        alto_riesgo_sin_control = []
        for embarazo in embarazos_activos.filter(riesgo_embarazo="alto"):
            ultimo_control = (
                ControlPrenatal.objects.filter(embarazo=embarazo)
                .order_by("-fecha_control")
                .first()
            )

            if not ultimo_control or ultimo_control.fecha_control < hace_30_dias.date():
                alto_riesgo_sin_control.append(embarazo.id)

        # Promedio de semanas de gestación por nivel de riesgo
        promedios = embarazos_activos.values("riesgo_embarazo").annotate(
            promedio_semanas=Avg("semanas_gestacion"),
        )

        promedios_dict = {
            item["riesgo_embarazo"]: round(item["promedio_semanas"] or 0, 1)
            for item in promedios
        }

        return Response(
            {
                "total_activos": total_activos,
                "distribucion": {
                    "bajo": total_bajo,
                    "medio": total_medio,
                    "alto": total_alto,
                },
                "porcentajes": {
                    "bajo": round(
                        (total_bajo / total_activos * 100) if total_activos > 0 else 0,
                        2,
                    ),
                    "medio": round(
                        (total_medio / total_activos * 100) if total_activos > 0 else 0,
                        2,
                    ),
                    "alto": round(
                        (total_alto / total_activos * 100) if total_activos > 0 else 0,
                        2,
                    ),
                },
                "alertas": {
                    "alto_riesgo_sin_control_30d": len(alto_riesgo_sin_control),
                },
                "promedios_semanas_gestacion": promedios_dict,
                "fecha_actualizacion": timezone.now().isoformat(),
            },
        )

    @action(detail=False, methods=["get"], url_path="factores-riesgo")
    def factores_riesgo_comunes(self, _request):
        """Retorna los factores de riesgo más comunes en embarazos de alto riesgo

        GET /api/clasificacion-riesgos/factores-riesgo/
        """
        embarazos_alto_riesgo = Embarazo.objects.filter(
            estado="activo", riesgo_embarazo="alto",
        ).select_related("paciente")

        # Analizar factores comunes
        factores = {
            "edad_avanzada": 0,  # > 35 años
            "edad_temprana": 0,  # < 18 años
            "multiparidad": 0,  # >= 4 partos
            "cesareas_previas": 0,  # >= 1 cesárea
            "abortos_previos": 0,  # >= 2 abortos
            "obesidad": 0,  # IMC >= 30
            "bajo_peso": 0,  # IMC < 18.5
        }

        for embarazo in embarazos_alto_riesgo:
            edad = embarazo.paciente.edad

            if edad > 35:
                factores["edad_avanzada"] += 1
            elif edad < 18:
                factores["edad_temprana"] += 1

            if embarazo.numero_para >= 4:
                factores["multiparidad"] += 1

            if embarazo.numero_cesareas >= 1:
                factores["cesareas_previas"] += 1

            if embarazo.numero_abortos >= 2:
                factores["abortos_previos"] += 1

            # Calcular IMC si hay datos
            if embarazo.peso_pregestacional and embarazo.talla_materna:
                talla_m = float(embarazo.talla_materna) / 100
                imc = float(embarazo.peso_pregestacional) / (talla_m * talla_m)

                if imc >= 30:
                    factores["obesidad"] += 1
                elif imc < 18.5:
                    factores["bajo_peso"] += 1

        # Convertir a lista ordenada por frecuencia
        factores_lista = [
            {"factor": key, "total": value, "nombre": self._get_factor_nombre(key)}
            for key, value in factores.items()
        ]
        factores_lista.sort(key=lambda x: x["total"], reverse=True)

        return Response(
            {
                "factores_riesgo": factores_lista,
                "total_embarazos_alto_riesgo": embarazos_alto_riesgo.count(),
            },
        )

    def _get_factor_nombre(self, key):
        """Helper para obtener nombres legibles de factores"""
        nombres = {
            "edad_avanzada": "Edad Avanzada (>35 años)",
            "edad_temprana": "Edad Temprana (<18 años)",
            "multiparidad": "Multiparidad (≥4 partos)",
            "cesareas_previas": "Cesáreas Previas",
            "abortos_previos": "Abortos Previos (≥2)",
            "obesidad": "Obesidad (IMC ≥30)",
            "bajo_peso": "Bajo Peso (IMC <18.5)",
        }
        return nombres.get(key, key)
