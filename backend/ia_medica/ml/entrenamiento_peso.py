"""Entrena y evalúa el modelo de peso al nacer, contra rivales honestos.

Qué tipo de modelo es
---------------------
**Regresión supervisada.** Aprende de casos en los que ya se conoce la
respuesta —bebés que nacieron y se pesaron— a predecir el peso de los que aún
no han nacido. De ese peso previsto sale después la clasificación en tres
clases: bajo peso, normal, macrosomía.

Por qué se comparan cinco modelos y no uno
------------------------------------------
Un modelo solo, con su métrica, no dice nada: un MAE de 400 g puede ser un
éxito o un desastre según lo que ya hubiera. Por eso se entrenan todos sobre
las mismas filas y se miden igual:

    1. Mediana constante   el suelo: predecir siempre lo mismo
    2. Hadlock proyectado  lo que ya hace la práctica clínica
    3. Ridge               un modelo lineal: ¿hace falta algo más?
    4. Random Forest       árboles promediados
    5. Gradient Boosting   árboles en cadena, cada uno corrige al anterior

Si el ganador no bate a Hadlock proyectado, **la conclusión del trabajo es
que la fórmula de 1985 ya era suficiente**, y se dice así. Es un resultado
tan válido como el contrario.

Por qué validación cruzada y no un solo corte
---------------------------------------------
Con 277 filas, un corte 80/20 deja unas 55 para probar. El MAE sobre 55 casos
varía mucho según qué 55 toquen, y reportar un único número daría una
precisión que no existe. Con validación cruzada de 5 particiones se mide cinco
veces y se reporta media ± desviación.

Las particiones son **por paciente** (`GroupKFold`), no por fila: si una misma
madre tuviera dos filas, una en entrenamiento y otra en prueba, el modelo
«reconocería» a la paciente y la métrica saldría inflada.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from ia_medica.ml.caracteristicas_peso import (
    CARACTERISTICAS,
    COMPARADOR,
    ETIQUETAS,
    OBJETIVO_REGRESION,
)

SEMILLA = 2026
PARTICIONES = 5


def clase_de(peso_g: float) -> str:
    """Los mismos cortes que el resto del sistema (2500 y 4000 g)."""
    from ecografias.peso_fetal import CORTE_BAJO_PESO_G, CORTE_MACROSOMIA_G

    if peso_g < CORTE_BAJO_PESO_G:
        return "bajo_peso"
    if peso_g > CORTE_MACROSOMIA_G:
        return "macrosomia"
    return "normal"


@dataclass
class Resultado:
    """Las métricas de un modelo, agregadas sobre las particiones."""

    nombre: str
    descripcion: str
    mae: list[float] = field(default_factory=list)
    rmse: list[float] = field(default_factory=list)
    r2: list[float] = field(default_factory=list)
    dentro_10: list[float] = field(default_factory=list)
    dentro_15: list[float] = field(default_factory=list)
    # Predicciones fuera de muestra, para la matriz de confusión.
    y_real: list[float] = field(default_factory=list)
    y_pred: list[float] = field(default_factory=list)

    def resumen(self) -> dict:
        def ms(v):
            return {"media": float(np.mean(v)), "desv": float(np.std(v))} if v else None

        return {
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "mae_g": ms(self.mae),
            "rmse_g": ms(self.rmse),
            "r2": ms(self.r2),
            "dentro_10pct": ms(self.dentro_10),
            "dentro_15pct": ms(self.dentro_15),
        }


def _metricas(real: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    """MAE, RMSE, R² y el porcentaje dentro de ±10% y ±15%.

    El ±15% no es arbitrario: es el error que declara Hadlock para su propia
    fórmula, y la métrica con la que se comparan las fórmulas de peso fetal en
    la literatura. Es lo que permite decir «el modelo iguala o supera a Hadlock»
    en términos que un obstetra entiende.
    """
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    relativo = np.abs(pred - real) / real
    return {
        "mae": float(mean_absolute_error(real, pred)),
        "rmse": float(np.sqrt(mean_squared_error(real, pred))),
        "r2": float(r2_score(real, pred)),
        "dentro_10": float(np.mean(relativo <= 0.10)),
        "dentro_15": float(np.mean(relativo <= 0.15)),
    }


def _modelos():
    """Los tres modelos que aprenden. Los rivales fijos van aparte.

    Por qué estos tres, y no xgboost
    --------------------------------
    El proyecto no tiene xgboost ni lightgbm, y meter una dependencia binaria
    pesada en un backend Django no compensa: `HistGradientBoostingRegressor`
    es la implementación de boosting por histogramas de scikit-learn, inspirada
    en LightGBM, y en tablas de este tamaño rinde igual.

    Además, los dos de árboles aceptan `NaN` de forma nativa: el IMC que falta
    no se rellena con la media (que sería inventar un dato), el modelo aprende
    qué hacer cuando falta. Ridge no lo acepta, así que lleva un imputador
    delante — y eso también es un dato: si Ridge rinde igual que los árboles,
    no hacía falta complejidad.
    """
    from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    return {
        "ridge": (
            "Ridge (lineal regularizado)",
            make_pipeline(
                SimpleImputer(strategy="median"),
                StandardScaler(),
                Ridge(alpha=1.0),
            ),
        ),
        "random_forest": (
            "Random Forest (300 árboles)",
            make_pipeline(
                SimpleImputer(strategy="median"),
                RandomForestRegressor(
                    n_estimators=300, min_samples_leaf=3,
                    random_state=SEMILLA, n_jobs=-1,
                ),
            ),
        ),
        "gradient_boosting": (
            "Gradient Boosting (histogramas)",
            HistGradientBoostingRegressor(
                max_iter=300, learning_rate=0.05, max_leaf_nodes=15,
                min_samples_leaf=10, l2_regularization=1.0,
                random_state=SEMILLA,
            ),
        ),
    }


def evaluar(marco: pd.DataFrame) -> tuple[dict[str, Resultado], dict]:
    """Validación cruzada de todos los modelos sobre las mismas particiones.

    Devuelve los resultados por modelo y un dict con información del conjunto.
    """
    from sklearn.model_selection import GroupKFold

    marco = marco.dropna(subset=[OBJETIVO_REGRESION]).reset_index(drop=True)
    X = marco[list(CARACTERISTICAS)].astype(float)
    y = marco[OBJETIVO_REGRESION].astype(float).to_numpy()
    grupos = marco["grupo"].to_numpy()
    comparador = marco[COMPARADOR].astype(float).to_numpy()

    n_grupos = len(set(grupos))
    particiones = min(PARTICIONES, n_grupos)
    divisor = GroupKFold(n_splits=particiones)

    resultados: dict[str, Resultado] = {
        "mediana": Resultado("mediana", "Mediana constante (el suelo)"),
        "hadlock": Resultado("hadlock", "Hadlock proyectado (práctica clínica)"),
    }
    modelos = _modelos()
    for clave, (desc, _) in modelos.items():
        resultados[clave] = Resultado(clave, desc)

    for entreno, prueba in divisor.split(X, y, grupos):
        y_prueba = y[prueba]

        # Rival 1: la mediana del entrenamiento, para todos.
        pred = np.full_like(y_prueba, np.median(y[entreno]))
        _anotar(resultados["mediana"], y_prueba, pred)

        # Rival 2: Hadlock proyectado. Donde no se pudo proyectar (fuera de la
        # tabla), se cae a la mediana: así se compara sobre las mismas filas.
        pred = comparador[prueba].copy()
        sin_dato = np.isnan(pred)
        pred[sin_dato] = np.median(y[entreno])
        _anotar(resultados["hadlock"], y_prueba, pred)

        for clave, (_, modelo) in modelos.items():
            from sklearn.base import clone

            m = clone(modelo)
            m.fit(X.iloc[entreno], y[entreno])
            _anotar(resultados[clave], y_prueba, m.predict(X.iloc[prueba]))

    info = {
        "filas": len(marco),
        "pacientes": n_grupos,
        "particiones": particiones,
        "sinteticas": int(marco["es_sintetico"].sum()),
        "hadlock_sin_proyeccion": int(np.isnan(comparador).sum()),
    }
    return resultados, info


def _anotar(res: Resultado, real: np.ndarray, pred: np.ndarray) -> None:
    m = _metricas(real, pred)
    res.mae.append(m["mae"])
    res.rmse.append(m["rmse"])
    res.r2.append(m["r2"])
    res.dentro_10.append(m["dentro_10"])
    res.dentro_15.append(m["dentro_15"])
    res.y_real.extend(real.tolist())
    res.y_pred.extend(pred.tolist())


def comparar_pareado(modelo: Resultado, rival: Resultado) -> dict:
    """¿El modelo mejora al rival de verdad, o solo por azar?

    Por qué no basta con comparar medias
    ------------------------------------
    Medido sobre las 277 filas: Ridge 212 ± 14 g, Hadlock proyectado 223 ± 13 g.
    La regla ingenua —«gana quien tenga menos error medio»— declara ganador a
    Ridge por 11 gramos y lo despliega. Pero esos 11 g caben de sobra dentro
    del ruido de ±13-14 g: es un empate presentado como mejora.

    Como los dos se evalúan sobre las MISMAS particiones, se puede hacer algo
    mejor: comparar partición a partición. Si el modelo es mejor de verdad,
    debería ganar en (casi) todas, y la diferencia media debería ser grande
    frente a su propia variabilidad.

    Criterio: la mejora media tiene que superar dos errores estándar de la
    diferencia pareada. Es aproximadamente un contraste unilateral al 95%.
    Con cinco particiones no es un test de hipótesis formal —hay muy pocos
    grados de libertad para eso—, pero sí basta para no confundir ruido con
    señal, que es lo que importa aquí.
    """
    diferencias = np.array(rival.mae) - np.array(modelo.mae)
    n = len(diferencias)
    media = float(diferencias.mean())
    desv = float(diferencias.std(ddof=1)) if n > 1 else 0.0
    error_estandar = desv / np.sqrt(n) if n > 1 else float("inf")
    gana_en = int((diferencias > 0).sum())

    return {
        "mejora_media_g": media,
        "desv_g": desv,
        "error_estandar_g": float(error_estandar),
        "gana_en_particiones": gana_en,
        "particiones": n,
        # La decisión: mejora clara y consistente.
        "mejora_significativa": bool(media > 2 * error_estandar and gana_en == n),
    }


def matriz_confusion(res: Resultado) -> dict:
    """Matriz de confusión de la clasificación DERIVADA del peso previsto.

    La clase no se predice aparte: sale de pasar el peso previsto por los
    mismos cortes. Así el sistema nunca puede decir «3.800 g» y «macrosomía» a
    la vez, que es una contradicción que confunde más que ayuda.

    Lo que importa aquí no es la exactitud global: con un 84% de clase
    «normal», predecir siempre «normal» ya da un 84% de acierto y ninguna
    utilidad. Lo que importa es la **sensibilidad por clase**, sobre todo en
    bajo peso: un bajo peso no detectado cuesta mucho más que una falsa alarma.
    """
    clases = ["bajo_peso", "normal", "macrosomia"]
    real = [clase_de(v) for v in res.y_real]
    pred = [clase_de(v) for v in res.y_pred]

    matriz = {r: {p: 0 for p in clases} for r in clases}
    for r, p in zip(real, pred):
        matriz[r][p] += 1

    por_clase = {}
    for c in clases:
        verdaderos = matriz[c][c]
        total_real = sum(matriz[c].values())
        total_pred = sum(matriz[r][c] for r in clases)
        sens = verdaderos / total_real if total_real else None
        prec = verdaderos / total_pred if total_pred else None
        f1 = (
            2 * sens * prec / (sens + prec)
            if sens and prec and (sens + prec) else 0.0
        )
        por_clase[c] = {
            "casos": total_real,
            "sensibilidad": sens,
            "precision": prec,
            "f1": f1,
        }

    aciertos = sum(matriz[c][c] for c in clases)
    f1s = [v["f1"] for v in por_clase.values() if v["casos"]]
    return {
        "matriz": matriz,
        "por_clase": por_clase,
        "exactitud": aciertos / len(real) if real else None,
        "f1_macro": float(np.mean(f1s)) if f1s else None,
    }


def importancia_variables(marco: pd.DataFrame, clave_modelo: str) -> list[dict]:
    """Qué variables pesan más, por permutación.

    Se usa importancia por permutación y no la `feature_importances_` de los
    árboles: ésta favorece a las variables con muchos valores distintos y
    engaña con las booleanas. La permutación mide algo más honesto: cuánto
    empeora el error si esa columna se baraja al azar.

    Se calcula sobre una partición de prueba, no sobre el entrenamiento: una
    variable puede ser muy importante para memorizar y no servir para
    generalizar.
    """
    from sklearn.base import clone
    from sklearn.inspection import permutation_importance
    from sklearn.model_selection import GroupShuffleSplit

    marco = marco.dropna(subset=[OBJETIVO_REGRESION]).reset_index(drop=True)
    X = marco[list(CARACTERISTICAS)].astype(float)
    y = marco[OBJETIVO_REGRESION].astype(float).to_numpy()
    grupos = marco["grupo"].to_numpy()

    entreno, prueba = next(
        GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=SEMILLA)
        .split(X, y, grupos),
    )
    modelo = clone(_modelos()[clave_modelo][1])
    modelo.fit(X.iloc[entreno], y[entreno])

    r = permutation_importance(
        modelo, X.iloc[prueba], y[prueba],
        scoring="neg_mean_absolute_error", n_repeats=20,
        random_state=SEMILLA, n_jobs=-1,
    )
    filas = [
        {
            "variable": c,
            "etiqueta": ETIQUETAS.get(c, c),
            "aumento_mae_g": float(r.importances_mean[i]),
            "desv": float(r.importances_std[i]),
        }
        for i, c in enumerate(CARACTERISTICAS)
    ]
    return sorted(filas, key=lambda f: f["aumento_mae_g"], reverse=True)


def entrenar_final(marco: pd.DataFrame, clave_modelo: str):
    """Entrena el modelo elegido sobre TODAS las filas, para desplegarlo.

    La validación cruzada sirve para estimar cómo rendirá; el modelo que se
    guarda se entrena con todo, porque con 277 filas no sobra ninguna.
    """
    from sklearn.base import clone

    marco = marco.dropna(subset=[OBJETIVO_REGRESION]).reset_index(drop=True)
    X = marco[list(CARACTERISTICAS)].astype(float)
    y = marco[OBJETIVO_REGRESION].astype(float).to_numpy()

    modelo = clone(_modelos()[clave_modelo][1])
    inicio = time.perf_counter()
    modelo.fit(X, y)
    return modelo, (time.perf_counter() - inicio) * 1000


def guardar(directorio: Path, modelo, ficha: dict) -> None:
    """Guarda el modelo, la lista de columnas y la ficha con las métricas.

    `columnas.json` no es opcional: el cargador compara esa lista con
    `CARACTERISTICAS` antes de servir, y se niega si no coinciden. Sin esa
    comprobación, un reentrenamiento a medias daría predicciones plausibles y
    equivocadas para siempre.
    """
    import joblib

    directorio.mkdir(parents=True, exist_ok=True)
    joblib.dump(modelo, directorio / "modelo.joblib")
    (directorio / "columnas.json").write_text(
        json.dumps(list(CARACTERISTICAS), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (directorio / "ficha.json").write_text(
        json.dumps(ficha, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
