"""Catálogo REAL de los modelos de IA del sistema, con su métrica medida.

Reemplaza a la tabla fija de `cnn_service.MODELOS_CONFIG`, que mostraba
exactitudes inventadas («EfficientNet-B4 94,1 %», «U-Net 88,7 %») para redes
que no existían o no tenían ninguna métrica válida.

Cada entrada sale de la ficha que dejó el entrenamiento:
- redes de imagen: `GET /api/modelos` del microservicio (los .json junto a cada .pth);
- modelos supervisados tabulares: `ml_modelos/<nombre>/<versión>/ficha.json`.

Si el microservicio no responde, sus redes figuran como «no disponible»: nunca
se rellena con números de referencia.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

#: archivo del microservicio → (nombre, tipo, cómo leer su métrica principal)
REDES_IMAGEN = {
    "plano_anatomico_fetal_planes": ("Plano anatómico (EfficientNet-B0)", "clasificación de imagen",
                                     lambda m: f"Exactitud {m['exactitud']:.1%} en {m['imagenes_prueba']} imágenes no vistas"),
    "segmentacion_cabeza": ("Segmentación de cabeza (U-Net)", "segmentación y medida",
                            lambda m: f"Circunferencia cefálica en otro hospital: error {m['prueba_externa_hc18']['hc_error_medio_mm']} mm, "
                                      f"{m['prueba_externa_hc18']['dentro_de_5_por_ciento']:.0%} dentro del 5 %"),
    "segmentacion_torax": ("Segmentación de tórax y corazón (U-Net)", "segmentación y medida",
                           lambda m: f"Dice {m['dice_prueba_medio']:.3f}; índice cardiotorácico ±{m['indice_cardiotoracico_prueba']['ict_areas_error_medio']}"),
    "segmentacion_abdomen": ("Segmentación abdominal (U-Net)", "segmentación",
                             lambda m: f"Dice {m['dice_prueba_medio']:.3f}; estómago visto en el "
                                       f"{m['marcadores_plano_abdominal']['estomago']['sensibilidad']:.0%}"),
    "anomalias_cerebrales_fetales": ("Cribado de anomalías cerebrales (EfficientNet-B0)", "cribado",
                                     lambda m: f"Falsas alarmas en otro hospital: {m['externa_falsos_positivos']['fp']} de "
                                               f"{m['externa_falsos_positivos']['n']}. Sensibilidad real no medible con datos públicos"),
    "circunferencia_cefalica_hc18": ("Circunferencia cefálica por regresión (EfficientNet-B0)", "regresión",
                                     lambda m: f"R² {m['r2']}; error medio {m['error_medio_mm']} mm"),
}


def _redes_del_microservicio() -> list[dict]:
    import requests

    from ecografias.ai_views import obtener_url_ia

    try:
        estado = requests.get(f"{obtener_url_ia()}/api/modelos", timeout=3).json()
    except Exception:
        logger.info("Microservicio de IA no disponible para el catálogo de modelos")
        estado = {}
    salida = []
    for archivo, (nombre, tipo, resumen) in REDES_IMAGEN.items():
        info = estado.get(archivo) or {}
        metricas = info.get("metricas_prueba")
        try:
            metrica = resumen(metricas) if metricas else None
        except (KeyError, TypeError):
            metrica = None
        salida.append({"codigo": archivo, "nombre": nombre, "tipo": tipo, "origen": "microservicio",
                       "disponible": bool(info.get("disponible")), "metrica_principal": metrica,
                       "datos_reales": True, "huella": (info.get("sha256") or "")[:12] or None})
    return salida


def _modelos_tabulares() -> list[dict]:
    from django.conf import settings

    base = Path(getattr(settings, "ML_MODELOS_DIR", settings.BASE_DIR / "ml_modelos"))
    salida = []

    def ultima(nombre: str) -> tuple[str, dict] | None:
        carpeta = base / nombre
        fichas = sorted(carpeta.glob("*/ficha.json"), key=lambda p: p.stat().st_mtime) if carpeta.exists() else []
        return (fichas[-1].parent.name, json.loads(fichas[-1].read_text(encoding="utf-8"))) if fichas else None

    if (ctg := ultima("cardiotocografia")):
        version, f = ctg
        p = f["prueba"]
        salida.append({"codigo": "cardiotocografia", "nombre": "Cardiotocografía (Gradient Boosting)",
                       "tipo": "clasificación supervisada", "origen": "backend", "disponible": True, "version": version,
                       "metrica_principal": f"Exactitud {p['exactitud']:.1%} (IC95 {p['exactitud_ic95'][0]:.1%}–"
                                            f"{p['exactitud_ic95'][1]:.1%}) en {f['registros_prueba']} registros no vistos",
                       "datos_reales": True})
    if (peso := ultima("peso_nacimiento")):
        version, f = peso
        mae = f.get("comparativa", {}).get(f.get("algoritmo"), {}).get("mae_g", {}).get("media")
        metrica = f"Error medio {mae:.0f} g en partos simulados" if mae else None
        reales = _desempeno_peso_real()
        if reales:
            metrica = f"{metrica} · con {reales[0]} nacimientos reales: {reales[1]:.0f} g"
        salida.append({"codigo": "peso_nacimiento", "nombre": "Peso al nacer (regresión supervisada)",
                       "tipo": "regresión supervisada", "origen": "backend", "disponible": True, "version": version,
                       "metrica_principal": metrica,
                       "datos_reales": not f.get("entrenado_con_datos_sinteticos", True)})
    return salida


def _desempeno_peso_real() -> tuple[int, float] | None:
    """(n, error medio) del modelo de peso sobre predicciones ya cerradas con el bebé real."""
    from ia_medica.models import PrediccionPesoNacimiento

    errores = list(PrediccionPesoNacimiento.objects.filter(error_modelo_g__isnull=False)
                   .values_list("error_modelo_g", flat=True))
    return (len(errores), sum(map(abs, errores)) / len(errores)) if errores else None


def catalogo() -> list[dict]:
    """Todos los modelos, cada uno con la métrica que se midió de verdad."""
    return _redes_del_microservicio() + _modelos_tabulares()
