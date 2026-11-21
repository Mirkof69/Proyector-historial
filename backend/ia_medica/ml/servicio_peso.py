"""Servir el modelo de peso al nacer: cargarlo una vez y predecir desde una ecografía.

Hasta ahora el modelo se entrenaba y se guardaba en `modelos-ia/tabulares/`, pero nada
del sistema lo cargaba: existía solo para la línea de comandos. Este módulo lo
conecta.

Tres reglas que no se negocian:

1. **Mismas variables que al entrenar.** Se construyen con
   `dataset_peso.caracteristicas_de`, la misma función que usa el dataset, y
   el cargador se niega a servir si `columnas.json` no coincide con
   `CARACTERISTICAS`.
2. **No inventar.** Si no hay modelo, si falta una medida, si el embarazo es
   gemelar o la ecografía es de menos de 20 semanas, se dice por qué y no se da
   ningún número.
3. **Hadlock siempre al lado.** La respuesta lleva la fórmula clínica proyectada
   a la misma semana, y una advertencia mientras el modelo esté entrenado con
   datos simulados.
"""
from __future__ import annotations

import json
import logging
import threading
from functools import lru_cache
from pathlib import Path

from ia_medica.ml.caracteristicas_peso import CARACTERISTICAS, COMPARADOR, construir_vector

logger = logging.getLogger(__name__)

NOMBRE_MODELO = "peso_nacimiento"
#: Hadlock está validado desde las 20 semanas (ver dataset_peso.EG_ECO_MINIMA).
EG_ECO_MINIMA = 20
SEMANAS_OBJETIVO_MIN, SEMANAS_OBJETIVO_MAX = 24.0, 42.0

_cerrojo = threading.Lock()


class PrediccionNoDisponible(Exception):
    """No se puede predecir. El mensaje dice por qué, para mostrarlo tal cual."""


def directorio_modelos() -> Path:
    from django.conf import settings

    return Path(settings.ML_MODELOS_DIR) / NOMBRE_MODELO


def _clave_version(nombre: str) -> tuple:
    try:
        return tuple(int(p) for p in nombre.split("."))
    except ValueError:
        return (-1,)


@lru_cache(maxsize=1)
def cargar() -> tuple[object, dict]:
    """(modelo, ficha) de la versión más alta guardada. Se carga una sola vez.

    `modelo.joblib` es un pickle: cargarlo ejecuta código. Por eso solo se lee
    de `ML_MODELOS_DIR`, que no cuelga de `MEDIA_ROOT` ni lo sirve nginx.
    """
    with _cerrojo:
        base = directorio_modelos()
        versiones = sorted((d for d in base.glob("*") if (d / "modelo.joblib").exists()),
                           key=lambda d: _clave_version(d.name)) if base.exists() else []
        if not versiones:
            raise PrediccionNoDisponible(
                "No hay un modelo de peso al nacer entrenado. Se entrena con "
                "`python manage.py entrenar_modelo_peso`.",
            )
        carpeta = versiones[-1]
        columnas = json.loads((carpeta / "columnas.json").read_text(encoding="utf-8"))
        if list(columnas) != list(CARACTERISTICAS):
            raise PrediccionNoDisponible(
                f"El modelo {carpeta.name} se entrenó con otras variables que las que "
                "calcula hoy el sistema. Hay que volver a entrenarlo antes de usarlo.",
            )
        import joblib

        modelo = joblib.load(carpeta / "modelo.joblib")
        ficha = json.loads((carpeta / "ficha.json").read_text(encoding="utf-8"))
        logger.info("Modelo de peso al nacer %s cargado", carpeta.name)
        return modelo, ficha


def _antecedentes(paciente_id) -> dict[str, int]:
    from antecedentes.models import AntecedentePatologico

    resultado = {"diabetes": 0, "hipertension": 0,
                 "preeclampsia_previa": 0, "diabetes_gestacional_previa": 0}
    for a in AntecedentePatologico.objects.filter(paciente_id=paciente_id, tipo="personal"):
        for campo in resultado:
            if getattr(a, campo, False):
                resultado[campo] = 1
    return resultado


def predecir_desde_ecografia(ecografia, semanas_objetivo: float = 39.0) -> dict:
    """Peso al nacer previsto si el bebé nace en `semanas_objetivo`.

    Las semanas del parto no se conocen el día de la ecografía: las pregunta
    la médica («¿cuánto pesaría si nace a las 39?»), igual que se proyecta
    Hadlock en la práctica.
    """
    import pandas as pd

    from controles.models import ControlPrenatal
    from core.simulacion.curvas_obstetricas import clasificar_peso_nacimiento
    from ia_medica.ml.dataset_peso import caracteristicas_de

    biometria = getattr(ecografia, "biometria", None)
    if biometria is None or None in (biometria.diametro_biparietal, biometria.circunferencia_cefalica,
                                      biometria.circunferencia_abdominal, biometria.longitud_femur):
        raise PrediccionNoDisponible(
            "La ecografía no tiene las cuatro medidas (DBP, CC, CA y LF): sin ellas no se puede estimar el peso.",
        )
    embarazo = ecografia.embarazo
    if embarazo is None:
        raise PrediccionNoDisponible("La ecografía no está vinculada a un embarazo.")
    if embarazo.tipo_embarazo != "simple":
        raise PrediccionNoDisponible(
            "En un embarazo múltiple no se sabe a qué feto corresponde la biometría; "
            "el modelo solo se entrenó con embarazos simples.",
        )
    eg_eco = float(ecografia.edad_gestacional_semanas or 0) + float(ecografia.edad_gestacional_dias or 0) / 7
    if eg_eco < EG_ECO_MINIMA:
        raise PrediccionNoDisponible(
            f"La ecografía es de {eg_eco:.1f} semanas; el modelo necesita 20 o más.",
        )
    if not (SEMANAS_OBJETIVO_MIN <= semanas_objetivo <= SEMANAS_OBJETIVO_MAX):
        raise PrediccionNoDisponible("La semana del parto tiene que estar entre 24 y 42.")
    if semanas_objetivo < eg_eco:
        raise PrediccionNoDisponible(
            f"La semana del parto ({semanas_objetivo}) no puede ser anterior a la de la ecografía ({eg_eco:.1f}).",
        )

    modelo, ficha = cargar()
    datos = caracteristicas_de(
        ecografia, embarazo=embarazo, paciente=ecografia.paciente,
        antecedentes=_antecedentes(ecografia.paciente_id),
        controles=list(ControlPrenatal.objects.filter(embarazo=embarazo)),
        eg_al_nacer=semanas_objetivo,
    )
    fila = pd.DataFrame([construir_vector(datos)], columns=list(CARACTERISTICAS))
    peso = int(round(float(modelo.predict(fila)[0])))

    elegido = ficha.get("comparativa", {}).get(ficha.get("algoritmo"), {})
    mae = elegido.get("mae_g", {}).get("media")
    r2 = elegido.get("r2", {}).get("media")
    hadlock = datos.get(COMPARADOR)

    advertencias = []
    if ficha.get("entrenado_con_datos_sinteticos"):
        advertencias.append(
            "Modelo entrenado con partos SIMULADOS del sistema: úselo como demostración "
            "y compárelo con Hadlock. Para uso clínico hay que reentrenarlo con partos reales.",
        )
    if semanas_objetivo - eg_eco > 1:
        advertencias.append(
            f"La ecografía es de {semanas_objetivo - eg_eco:.0f} semanas antes del parto previsto. "
            "El modelo se validó con ecografías de la última semana; con más distancia el error crece.",
        )

    return {
        "peso_previsto_g": peso,
        "clase": clasificar_peso_nacimiento(peso),
        "margen_g": round(mae) if mae is not None else None,
        "peso_hadlock_proyectado_g": round(hadlock) if hadlock else None,
        "semanas_objetivo": semanas_objetivo,
        "semanas_ecografia": round(eg_eco, 1),
        "modelo": {"version": ficha.get("version"), "algoritmo": ficha.get("descripcion"),
                   "r2_validacion": round(r2, 3) if r2 is not None else None,
                   "entrenado_con_datos_sinteticos": bool(ficha.get("entrenado_con_datos_sinteticos"))},
        "advertencias": advertencias,
    }
