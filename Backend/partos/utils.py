"""=============================================================================
MÓDULO: PARTOS - UTILIDADES
=============================================================================
Funciones auxiliares para el módulo de partos
=============================================================================
"""

import re
from datetime import timedelta

from django.db.models import Avg, Count
from django.utils import timezone

from .models import Parto


def calcular_edad_gestacional_dias(edad_gestacional_str):
    """Convierte formato "39+2" a días totales

    Args:
        edad_gestacional_str: String en formato "39+2" o "39"

    Returns:
        int: Total de días de gestación

    """
    if not edad_gestacional_str:
        return None

    try:
        if "+" in edad_gestacional_str:
            semanas, dias = edad_gestacional_str.split("+")
            return int(semanas) * 7 + int(dias)
        return int(edad_gestacional_str) * 7
    except (ValueError, AttributeError):
        return None


def validar_formato_edad_gestacional(valor):
    """Valida el formato de edad gestacional

    Args:
        valor: String a validar

    Returns:
        tuple: (bool, str) - (es_valido, mensaje_error)

    """
    if not valor:
        return False, "Edad gestacional es requerida"

    if not re.match(r"^\d{1,2}(\+\d)$", valor):
        return False, "Formato inválido. Use: 39 o 39+2"

    try:
        semanas = int(valor.split("+", 1)[0])
        if semanas < 20 or semanas > 45:
            return False, f"Semanas deben estar entre 20 y 45. Valor: {semanas}"

        if "+" in valor:
            dias = int(valor.split("+")[1])
            if dias < 0 or dias > 6:
                return False, f"Días deben estar entre 0 y 6. Valor: {dias}"

        return True, "Válido"
    except (ValueError, IndexError):
        return False, "Error al procesar el valor"


def calcular_tendencias_partos(queryset, periodo_dias=30):
    """Calcula tendencias de partos en un período

    Args:
        queryset: QuerySet de partos
        periodo_dias: Días a analizar

    Returns:
        dict: Estadísticas de tendencias

    """
    fecha_inicio = timezone.now() - timedelta(days=periodo_dias)

    partos_periodo = queryset.filter(fecha_parto__gte=fecha_inicio)

    # Calcular promedios
    total = partos_periodo.count()

    if total == 0:
        return {"total_partos": 0, "promedio_diario": 0, "tendencia": "sin_datos"}

    promedio_diario = total / periodo_dias

    # Calcular tendencia (comparar primera mitad vs segunda mitad)
    mitad_periodo = periodo_dias // 2
    fecha_mitad = timezone.now() - timedelta(days=mitad_periodo)

    primera_mitad = partos_periodo.filter(fecha_parto__lt=fecha_mitad).count()
    segunda_mitad = partos_periodo.filter(fecha_parto__gte=fecha_mitad).count()

    if primera_mitad == 0:
        tendencia = "creciente"
    else:
        cambio_porcentual = ((segunda_mitad - primera_mitad) / primera_mitad) * 100
        if cambio_porcentual > 10:
            tendencia = "creciente"
        elif cambio_porcentual < -10:
            tendencia = "decreciente"
        else:
            tendencia = "estable"

    return {
        "total_partos": total,
        "promedio_diario": round(promedio_diario, 2),
        "primera_mitad": primera_mitad,
        "segunda_mitad": segunda_mitad,
        "tendencia": tendencia,
        "cambio_porcentual": round(cambio_porcentual, 2) if primera_mitad > 0 else 0,
    }


def calcular_estadisticas_avanzadas(queryset):
    """Calcula estadísticas avanzadas de partos

    Args:
        queryset: QuerySet de partos

    Returns:
        dict: Estadísticas detalladas

    """
    total = queryset.count()

    if total == 0:
        return {"error": "No hay datos para calcular estadísticas"}

    # Estadísticas por tipo de parto
    tipos = queryset.values("tipo_parto").annotate(count=Count("id")).order_by("-count")

    # Tasas de complicaciones
    con_hemorragia = queryset.filter(hemorragia_postparto=True).count()
    con_desgarros = queryset.filter(desgarros=True).count()
    con_episiotomia = queryset.filter(episiotomia=True).count()

    # Promedios
    promedios = queryset.aggregate(
        duracion_promedio=Avg("duracion_trabajo_parto_horas"),
        perdida_promedio=Avg("perdida_sanguinea_estimada"),
        peso_placenta_promedio=Avg("peso_placenta"),
    )

    # Intervenciones
    con_analgesia = queryset.filter(analgesia_utilizada=True).count()
    con_oxitocina = queryset.filter(oxitocina_utilizada=True).count()
    con_induccion = queryset.filter(induccion_parto=True).count()

    return {
        "total_partos": total,
        "tipos_parto": list(tipos),
        "tasas_complicaciones": {
            "hemorragia": {
                "count": con_hemorragia,
                "porcentaje": round((con_hemorragia / total) * 100, 2),
            },
            "desgarros": {
                "count": con_desgarros,
                "porcentaje": round((con_desgarros / total) * 100, 2),
            },
            "episiotomia": {
                "count": con_episiotomia,
                "porcentaje": round((con_episiotomia / total) * 100, 2),
            },
        },
        "promedios": {
            "duracion_horas": round(float(promedios["duracion_promedio"] or 0), 2),
            "perdida_sanguinea_ml": round(float(promedios["perdida_promedio"] or 0), 2),
            "peso_placenta_g": round(
                float(promedios["peso_placenta_promedio"] or 0), 2,
            ),
        },
        "intervenciones": {
            "analgesia": {
                "count": con_analgesia,
                "porcentaje": round((con_analgesia / total) * 100, 2),
            },
            "oxitocina": {
                "count": con_oxitocina,
                "porcentaje": round((con_oxitocina / total) * 100, 2),
            },
            "induccion": {
                "count": con_induccion,
                "porcentaje": round((con_induccion / total) * 100, 2),
            },
        },
    }


def generar_numero_parto_manual(year=None):
    """Genera un número de parto manualmente (backup si falla el automático)

    Args:
        year: Año para el número (default: año actual)

    Returns:
        str: Número de parto en formato PARTO-YYYY-NNNN

    """
    if year is None:
        year = timezone.now().year

    # Obtener el último número del año
    last_parto = (
        Parto.objects.filter(numero_parto__startswith=f"PARTO-{year}")
        .order_by("-numero_parto")
        .first()
    )

    if last_parto and last_parto.numero_parto:
        try:
            last_number = int(last_parto.numero_parto.split("-", 1)[-1])
            new_number = last_number + 1
        except (ValueError, IndexError):
            new_number = 1
    else:
        new_number = 1

    return f"PARTO-{year}-{new_number:04d}"


def verificar_duplicados_parto(paciente_id, fecha_parto, tolerancia_horas=24):
    """Verifica si existe un parto duplicado para el mismo paciente

    Args:
        paciente_id: ID del paciente
        fecha_parto: Fecha del parto
        tolerancia_horas: Horas de tolerancia para considerar duplicado

    Returns:
        tuple: (bool, list) - (hay_duplicados, lista_de_partos_similares)

    """
    if not fecha_parto:
        return False, []

    # Buscar partos del mismo paciente en el rango de fechas
    fecha_inicio = fecha_parto - timedelta(hours=tolerancia_horas)
    fecha_fin = fecha_parto + timedelta(hours=tolerancia_horas)

    partos_similares = Parto.objects.filter(
        paciente_id=paciente_id,
        fecha_parto__gte=fecha_inicio,
        fecha_parto__lte=fecha_fin,
    )

    if partos_similares.exists():
        return True, list(partos_similares.values("id", "numero_parto", "fecha_parto"))

    return False, []


def calcular_riesgo_parto(parto):
    """Calcula el nivel de riesgo de un parto basado en varios factores

    Args:
        parto: Instancia del modelo Parto

    Returns:
        dict: Nivel de riesgo y factores

    """
    factores_riesgo = []
    puntos_riesgo = 0

    # Evaluar edad gestacional
    if parto.edad_gestacional_parto:
        dias = calcular_edad_gestacional_dias(parto.edad_gestacional_parto)
        if dias and dias < 259:  # < 37 semanas
            factores_riesgo.append("Parto prematuro")
            puntos_riesgo += 3
        elif dias and dias > 294:  # > 42 semanas
            factores_riesgo.append("Embarazo prolongado")
            puntos_riesgo += 2

    # Evaluar pérdida sanguínea
    if parto.perdida_sanguinea_estimada:
        if parto.perdida_sanguinea_estimada > 1000:
            factores_riesgo.append("Hemorragia severa")
            puntos_riesgo += 3
        elif parto.perdida_sanguinea_estimada > 500:
            factores_riesgo.append("Hemorragia moderada")
            puntos_riesgo += 2

    # Evaluar complicaciones
    if parto.hemorragia_postparto:
        factores_riesgo.append("Hemorragia postparto")
        puntos_riesgo += 2

    if parto.desgarros:
        factores_riesgo.append("Desgarros")
        puntos_riesgo += 1

    # Evaluar duración del trabajo de parto
    if parto.duracion_trabajo_parto_horas:
        if parto.duracion_trabajo_parto_horas > 24:
            factores_riesgo.append("Trabajo de parto prolongado")
            puntos_riesgo += 2

    # Determinar nivel de riesgo
    if puntos_riesgo == 0:
        nivel = "bajo"
    elif puntos_riesgo <= 3:
        nivel = "moderado"
    elif puntos_riesgo <= 6:
        nivel = "alto"
    else:
        nivel = "muy_alto"

    return {
        "nivel_riesgo": nivel,
        "puntos_riesgo": puntos_riesgo,
        "factores": factores_riesgo,
        "total_factores": len(factores_riesgo),
    }


def formatear_duracion(horas):
    """Formatea duración en horas a formato legible

    Args:
        horas: Número de horas (puede ser decimal)

    Returns:
        str: Duración formateada (ej: "5h 30min")

    """
    if not horas:
        return "No registrado"

    horas_enteras = int(horas)
    minutos = int((horas - horas_enteras) * 60)

    if horas_enteras == 0:
        return f"{minutos}min"
    if minutos == 0:
        return f"{horas_enteras}h"
    return f"{horas_enteras}h {minutos}min"


def obtener_resumen_periodo(queryset, fecha_inicio, fecha_fin):
    """Obtiene un resumen completo de partos en un período

    Args:
        queryset: QuerySet de partos
        fecha_inicio: Fecha de inicio del período
        fecha_fin: Fecha de fin del período

    Returns:
        dict: Resumen completo del período

    """
    partos_periodo = queryset.filter(
        fecha_parto__gte=fecha_inicio, fecha_parto__lte=fecha_fin,
    )

    total = partos_periodo.count()

    if total == 0:
        return {
            "periodo": {
                "inicio": str(fecha_inicio),
                "fin": str(fecha_fin),
                "dias": (fecha_fin - fecha_inicio).days,
            },
            "total_partos": 0,
            "mensaje": "No hay partos en este período",
        }

    # Calcular estadísticas
    stats = calcular_estadisticas_avanzadas(partos_periodo)

    # Agregar información del período
    dias_periodo = (fecha_fin - fecha_inicio).days + 1
    promedio_diario = total / dias_periodo if dias_periodo > 0 else 0

    return {
        "periodo": {
            "inicio": str(fecha_inicio),
            "fin": str(fecha_fin),
            "dias": dias_periodo,
        },
        "total_partos": total,
        "promedio_diario": round(promedio_diario, 2),
        "estadisticas": stats,
    }
