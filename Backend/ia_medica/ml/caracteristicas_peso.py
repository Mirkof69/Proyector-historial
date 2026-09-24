"""Qué variables entran al modelo, en qué orden y con qué significado.

Por qué este archivo existe aparte
----------------------------------
Es la **única** definición de las columnas. Lo importan las tres piezas del
sistema: el que construye el dataset, el que entrena y el que sirve las
predicciones.

Si cada una tuviera su propia lista, aparecería el fallo más caro que puede dar
un modelo en producción: recibir las columnas en otro orden y **predecir
números plausibles y equivocados, sin lanzar ninguna excepción**. Un modelo que
devuelve 3.200 g cuando debería decir 2.100 g no se distingue de uno correcto
mirando la respuesta.

Por eso, además, al guardar el modelo se guarda un `columnas.json` con esta
misma lista, y el cargador se niega a servir si no coincide.
"""
from __future__ import annotations

#: Medidas de la ecografía, en milímetros. Son OBLIGATORIAS: si falta alguna,
#: la fila se descarta en vez de imputarse. No se rellena a ojo el predictor
#: principal de un modelo clínico.
BIOMETRIA_OBLIGATORIA: tuple[str, ...] = (
    "dbp_mm",   # diámetro biparietal
    "cc_mm",    # circunferencia cefálica
    "ca_mm",    # circunferencia abdominal
    "lf_mm",    # longitud del fémur
)

#: Derivadas de las anteriores. Se recalculan en el ETL en vez de leerlas de la
#: base, porque `relacion_cc_ca` y `relacion_lf_ca` vienen nulas en los
#: registros antiguos, anteriores a que `calcular_relaciones()` existiera.
BIOMETRIA_DERIVADA: tuple[str, ...] = (
    "relacion_cc_ca",
    "relacion_lf_ca",
    "peso_hadlock_g",   # la fórmula clásica: es el número que hay que batir
)

#: Cuándo se tomó la medida y para cuándo se predice.
TEMPORALES: tuple[str, ...] = (
    "eg_eco_semanas",       # edad gestacional el día de la ecografía
    "eg_al_nacer_semanas",  # OJO: ver la nota sobre fuga de información
)

#: De la madre. Explican parte del peso que la biometría no captura.
MATERNAS: tuple[str, ...] = (
    "edad_materna",          # calculada A LA FECHA DE LA ECO, no a hoy
    "imc_pregestacional",
    "numero_para",           # partos previos
    "numero_abortos",
    "numero_cesareas",
)

#: Antecedentes patológicos personales. Booleanas, 0 o 1.
ANTECEDENTES: tuple[str, ...] = (
    "diabetes",
    "hipertension",
    "preeclampsia_previa",
    "diabetes_gestacional_previa",
)

#: El orden de esta tupla ES el contrato. No reordenar sin reentrenar.
CARACTERISTICAS: tuple[str, ...] = (
    *BIOMETRIA_OBLIGATORIA,
    *BIOMETRIA_DERIVADA,
    *TEMPORALES,
    *MATERNAS,
    *ANTECEDENTES,
)

#: Columnas que identifican la fila pero NO entran al modelo.
#: `grupo` es la clave del split: todas las filas de la misma paciente tienen
#: que caer del mismo lado, o la métrica sale inflada.
COLUMNAS_CLAVE: tuple[str, ...] = (
    "tenant",
    "grupo",
    "recien_nacido_id",
    "paciente_id",
    "ecografia_id",
    "es_sintetico",
    "fecha_parto",
)

#: Lo que el modelo predice.
OBJETIVO_REGRESION = "peso_nacimiento_g"
OBJETIVO_CLASIFICACION = "clase_peso"

#: Contra qué se mide el modelo. NO entra como variable: si entrara, el modelo
#: podría limitarse a copiarla y la comparación dejaría de significar nada.
#:
#: Es Hadlock PROYECTADO a la edad gestacional del parto, no el Hadlock crudo
#: del día de la ecografía. El crudo responde otra pregunta —cuánto pesa hoy—
#: y usarlo como rival daba un MAE de 1.473 g: un adversario de paja.
COMPARADOR = "peso_hadlock_proyectado_g"

COLUMNAS_DATASET: tuple[str, ...] = (
    *COLUMNAS_CLAVE,
    *CARACTERISTICAS,
    COMPARADOR,
    OBJETIVO_REGRESION,
    OBJETIVO_CLASIFICACION,
)

#: Etiquetas legibles, para la pantalla y para el análisis de importancia.
ETIQUETAS: dict[str, str] = {
    "dbp_mm": "Diámetro biparietal",
    "cc_mm": "Circunferencia cefálica",
    "ca_mm": "Circunferencia abdominal",
    "lf_mm": "Longitud del fémur",
    "relacion_cc_ca": "Relación cabeza/abdomen",
    "relacion_lf_ca": "Relación fémur/abdomen",
    "peso_hadlock_g": "Peso por fórmula de Hadlock",
    "eg_eco_semanas": "Semanas en la ecografía",
    "eg_al_nacer_semanas": "Semanas previstas al nacer",
    "edad_materna": "Edad de la madre",
    "imc_pregestacional": "IMC antes del embarazo",
    "numero_para": "Partos previos",
    "numero_abortos": "Abortos previos",
    "numero_cesareas": "Cesáreas previas",
    "diabetes": "Diabetes",
    "hipertension": "Hipertensión",
    "preeclampsia_previa": "Preeclampsia previa",
    "diabetes_gestacional_previa": "Diabetes gestacional previa",
}


# ---------------------------------------------------------------------------
# Lo que NO entra, y por qué. Cada exclusión es una decisión que hay que poder
# defender, así que se documenta aquí y no en un comentario perdido.
# ---------------------------------------------------------------------------

#: `numero_gesta` — EXCLUIDA por colinealidad exacta.
#: `Embarazo.clean()` (`embarazos/models.py:127`) obliga a que
#: G = P + A + 1. Es una combinación lineal de dos columnas que ya están:
#: no aporta información, hace singular la matriz de los modelos lineales y
#: reparte la importancia entre columnas redundantes, volviendo ilegible el
#: análisis de qué variables pesan.

#: `sexo` del feto — EXCLUIDA porque en producción no se conoce.
#: Aporta unos 120 g, pero en el parto sí se sabe (`RecienNacido.sexo`) y en la
#: ecografía muchas veces no. Entrenar con una variable que al servir va a
#: faltar hace que el modelo real rinda peor que el de validación, sin que se
#: vea por qué. Va a las limitaciones del trabajo.

#: `peso_fetal_estimado` y `percentil_peso` de la base — EXCLUIDAS por fuga.
#: Son la salida de Hadlock sobre las mismas cuatro medidas que ya entran. El
#: modelo "acertaría" copiando la fórmula. Lo que sí entra es
#: `peso_hadlock_g`, recalculado en el ETL — pero entra COMO COMPARADOR
#: declarado, no como si fuera un dato independiente.

#: `dias_eco_a_parto` — EXCLUIDA por fuga temporal.
#: Solo se conoce después del parto. El día de la ecografía nadie sabe cuántos
#: días faltan. Su lugar lo ocupa `eg_al_nacer_semanas`, que es otra cosa: ver
#: abajo.


#: AVISO SOBRE `eg_al_nacer_semanas` — el punto más delicado del modelo.
#:
#: Es el predictor más fuerte del peso al nacer y **no se conoce el día de la
#: ecografía**. Si se entrenara con la edad gestacional real del parto y en
#: producción no se tuviera, el modelo rendiría mucho peor de lo que dice su
#: validación y nadie entendería por qué.
#:
#: Quitarla tampoco sirve: sin ella el modelo no puede distinguir «3.200 g a
#: las 39 semanas» de «2.100 g a las 34».
#:
#: La solución es cambiarle el significado. **Es la edad gestacional
#: OBJETIVO**, no la observada:
#:   - al entrenar se llena con el valor real del parto,
#:   - al predecir la aporta la médica: «¿cuánto pesaría si nace a las 39?».
#:
#: Es exactamente como se usa hoy una proyección de Hadlock. Pero hay que
#: decirlo —en el docstring, en la ficha del modelo y en la respuesta de la
#: API—, o es una fuga disfrazada de variable.
SEMANTICA_EG_OBJETIVO = (
    "Edad gestacional para la que se pide la estimación. En producción la "
    "aporta el profesional; no es un dato que el sistema conozca."
)

#: Rango aceptado para esa edad gestacional. Fuera de aquí el modelo estaría
#: extrapolando, porque no vio casos.
EG_OBJETIVO_MINIMA = 24.0
EG_OBJETIVO_MAXIMA = 42.0


def construir_vector(datos: dict) -> list[float]:
    """Una fila de características, en el orden exacto de `CARACTERISTICAS`.

    Lo usa el endpoint de predicción. Es la contrapartida del ETL: garantiza
    que lo que se sirve tiene la misma forma que lo que se entrenó.

    Lanza `KeyError` si falta una característica obligatoria. Es deliberado:
    es preferible un error claro a una predicción silenciosamente equivocada.
    """
    faltan = [c for c in BIOMETRIA_OBLIGATORIA if datos.get(c) is None]
    if faltan:
        raise KeyError(
            f"Faltan medidas obligatorias: {', '.join(faltan)}. "
            f"Sin ellas no se puede estimar el peso.",
        )

    fila = []
    for caracteristica in CARACTERISTICAS:
        valor = datos.get(caracteristica)
        if valor is None:
            # Las opcionales van como NaN: el modelo las maneja de forma
            # nativa, sin imputarlas a la media (que inventaría un dato).
            fila.append(float("nan"))
        elif isinstance(valor, bool):
            fila.append(1.0 if valor else 0.0)
        else:
            fila.append(float(valor))
    return fila
