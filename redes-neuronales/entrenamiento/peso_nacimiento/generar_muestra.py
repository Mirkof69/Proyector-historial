"""Genera la muestra grande en Excel que usa el notebook del modelo de peso.

    cd Backend
    .venv/Scripts/python.exe notebooks/generar_muestra.py

Escribe `notebooks/datos/muestra_peso_nacimiento.xlsx` con cuatro hojas:

    Muestra          5.000 embarazos simulados, una fila por bebé
    Diccionario      qué significa cada columna, su unidad y su papel
    Resumen          conteos y medias por clase, para mirar sin programar
    Dataset_sistema  las 277 filas reales que construye el sistema desde la base

Por qué se genera con el simulador del proyecto
-----------------------------------------------
La muestra sale de `core/simulacion/curvas_obstetricas.py`, el mismo generador
que alimenta la base de datos de demostración. Así el notebook enseña el modelo
sobre datos con la misma estructura que los del sistema, pero con muchos más
casos: 5.000 en vez de 277, suficientes para que las gráficas se vean bien y
las métricas no bailen según qué casos toquen.

LOS DATOS SON SIMULADOS. Se generan a partir de curvas de crecimiento
publicadas; no son pacientes reales. Un modelo entrenado sobre ellos recupera
la relación con la que se generaron. Eso sirve para enseñar cómo funciona el
modelo, no para afirmar nada sobre la población boliviana.
"""
from __future__ import annotations

import os
import random
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2] / "backend"
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

import django  # noqa: E402

django.setup()

import pandas as pd  # noqa: E402
from openpyxl.styles import Alignment, Font, PatternFill  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402

from core.simulacion.curvas_obstetricas import (  # noqa: E402
    clasificar_peso_nacimiento,
    simular_biometria,
    simular_peso_nacimiento,
    sortear_semanas_al_parto,
    sortear_z_tamano,
)
from ecografias.peso_fetal import hadlock_1985_4p, proyectar_peso  # noqa: E402

SEMILLA = 2026
N_CASOS = 5000
SALIDA = AQUI / "datos" / "muestra_peso_nacimiento.xlsx"

#: Qué es cada columna. Se escribe en la hoja «Diccionario» y el notebook la
#: lee para rotular las gráficas.
DICCIONARIO = [
    # (columna, descripción, unidad, papel)
    ("id_paciente", "Identificador de la paciente simulada", "—", "identificador"),
    ("dbp_mm", "Diámetro biparietal: ancho de la cabeza", "mm", "entrada"),
    ("cc_mm", "Circunferencia cefálica: contorno de la cabeza", "mm", "entrada"),
    ("ca_mm", "Circunferencia abdominal: contorno del abdomen", "mm", "entrada"),
    ("lf_mm", "Longitud del fémur", "mm", "entrada"),
    ("relacion_cc_ca", "Cabeza / abdomen. Alta en fetos delgados", "cociente", "entrada"),
    ("relacion_lf_ca", "Fémur / abdomen", "cociente", "entrada"),
    ("peso_hadlock_g", "Peso por la fórmula de Hadlock EL DÍA DE LA ECO", "g", "entrada"),
    ("eg_eco_semanas", "Semanas de embarazo el día de la ecografía", "semanas", "entrada"),
    ("eg_al_nacer_semanas", "Semanas de embarazo al nacer (en consulta: la que pregunta la médica)", "semanas", "entrada"),
    ("edad_materna", "Edad de la madre el día de la ecografía", "años", "entrada"),
    ("imc_pregestacional", "Índice de masa corporal antes del embarazo (vacío si no se registró)", "kg/m²", "entrada"),
    ("numero_para", "Partos anteriores", "n.º", "entrada"),
    ("numero_abortos", "Abortos anteriores", "n.º", "entrada"),
    ("numero_cesareas", "Cesáreas anteriores", "n.º", "entrada"),
    ("diabetes", "Diabetes previa al embarazo", "0/1", "entrada"),
    ("hipertension", "Hipertensión crónica", "0/1", "entrada"),
    ("preeclampsia_previa", "Preeclampsia en un embarazo anterior", "0/1", "entrada"),
    ("diabetes_gestacional_previa", "Diabetes gestacional en un embarazo anterior", "0/1", "entrada"),
    ("peso_hadlock_proyectado_g", "Hadlock llevado a la semana del parto: lo que calcularía una médica", "g", "comparador"),
    ("peso_nacimiento_g", "Peso real al nacer: lo que el modelo aprende a predecir", "g", "objetivo"),
    ("clase_peso", "bajo_peso (<2500) · normal · macrosomia (>4000)", "clase", "objetivo"),
]


def generar(n: int, semilla: int) -> pd.DataFrame:
    """Una fila por embarazo: ecografía del tercer trimestre + desenlace."""
    rng = random.Random(semilla)
    filas = []

    for i in range(n):
        # Un solo factor de tamaño por feto: liga la biometría con el peso.
        z = sortear_z_tamano(rng)

        eg_parto = sortear_semanas_al_parto(rng)
        # La ecografía se hace entre medio y diez semanas antes del parto, y
        # nunca antes de la semana 20 (Hadlock no está validado por debajo).
        eg_eco = max(20.0, eg_parto - rng.uniform(0.5, 10.0))

        b = simular_biometria(eg_eco, z_tamano=z, rng=rng)
        dbp, cc, ca, lf = (float(b[k]) for k in ("dbp", "cc", "ca", "lf"))

        edad = int(min(45, max(15, round(rng.gauss(27, 6)))))
        # Un 8% sin IMC registrado: es lo que pasa en una clínica, y el
        # notebook tiene que enseñar cómo se maneja un dato que falta.
        imc = None if rng.random() < 0.08 else round(
            min(42.0, max(16.0, rng.gauss(24.5, 4.0))), 1)

        para = rng.choices([0, 1, 2, 3, 4], weights=[38, 30, 18, 9, 5])[0]
        abortos = rng.choices([0, 1, 2], weights=[80, 16, 4])[0]
        cesareas = rng.randint(0, para) if para and rng.random() < 0.3 else 0

        diabetes = int(rng.random() < 0.04)
        hipertension = int(rng.random() < 0.06)
        # Solo puede haber antecedente de un embarazo anterior si lo hubo.
        preeclampsia_previa = int(para > 0 and rng.random() < 0.06)
        dm_gestacional_previa = int(para > 0 and rng.random() < 0.07)

        sexo = rng.choice(["masculino", "femenino"])
        peso = simular_peso_nacimiento(
            semanas_parto=eg_parto,
            z_tamano=z,
            imc_materno=imc if imc is not None else 24.5,
            paridad=para,
            diabetes=bool(diabetes or dm_gestacional_previa),
            hipertension=bool(hipertension or preeclampsia_previa),
            sexo=sexo,  # influye en el peso pero NO es entrada: en la eco no se sabe
            rng=rng,
        )

        hadlock = hadlock_1985_4p(dbp, cc, ca, lf)
        filas.append({
            "id_paciente": f"P{i + 1:05d}",
            "dbp_mm": dbp,
            "cc_mm": cc,
            "ca_mm": ca,
            "lf_mm": lf,
            "relacion_cc_ca": round(cc / ca, 4),
            "relacion_lf_ca": round(lf / ca, 4),
            "peso_hadlock_g": hadlock,
            "eg_eco_semanas": round(eg_eco, 2),
            "eg_al_nacer_semanas": float(eg_parto),
            "edad_materna": edad,
            "imc_pregestacional": imc,
            "numero_para": para,
            "numero_abortos": abortos,
            "numero_cesareas": cesareas,
            "diabetes": diabetes,
            "hipertension": hipertension,
            "preeclampsia_previa": preeclampsia_previa,
            "diabetes_gestacional_previa": dm_gestacional_previa,
            "peso_hadlock_proyectado_g": proyectar_peso(hadlock, eg_eco, eg_parto),
            "peso_nacimiento_g": peso,
            "clase_peso": clasificar_peso_nacimiento(peso),
        })

    return pd.DataFrame(filas)


def resumen(marco: pd.DataFrame) -> pd.DataFrame:
    """Medias por clase: lo que se mira primero sin abrir el notebook."""
    orden = ["bajo_peso", "normal", "macrosomia"]
    g = marco.groupby("clase_peso")
    tabla = pd.DataFrame({
        "casos": g.size(),
        "porcentaje": (g.size() / len(marco) * 100).round(1),
        "peso_medio_g": g["peso_nacimiento_g"].mean().round(0),
        "semanas_al_nacer_media": g["eg_al_nacer_semanas"].mean().round(1),
        "circ_abdominal_media_mm": g["ca_mm"].mean().round(1),
        "hadlock_proyectado_medio_g": g["peso_hadlock_proyectado_g"].mean().round(0),
        "con_diabetes_pct": (g["diabetes"].mean() * 100).round(1),
    }).reindex(orden)
    tabla.index.name = "clase"
    return tabla.reset_index()


def dar_formato(hoja, anchos: dict[str, int] | None = None) -> None:
    """Cabecera marcada, fila congelada, filtros y anchos legibles."""
    cabecera = PatternFill("solid", fgColor="2E5B86")
    for celda in hoja[1]:
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = cabecera
        celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    hoja.row_dimensions[1].height = 32
    hoja.freeze_panes = "A2"
    hoja.auto_filter.ref = hoja.dimensions

    for i, columna in enumerate(hoja.iter_cols(min_row=1, max_row=1), start=1):
        nombre = str(columna[0].value)
        ancho = (anchos or {}).get(nombre, max(12, min(34, len(nombre) + 3)))
        hoja.column_dimensions[get_column_letter(i)].width = ancho


def main() -> None:
    marco = generar(N_CASOS, SEMILLA)
    diccionario = pd.DataFrame(DICCIONARIO, columns=["columna", "descripcion", "unidad", "papel"])

    ruta_sistema = AQUI.parents[1] / "datos" / "tabulares" / "peso_nacimiento.csv"
    sistema = pd.read_csv(ruta_sistema) if ruta_sistema.exists() else None

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(SALIDA, engine="openpyxl") as escritor:
        marco.to_excel(escritor, sheet_name="Muestra", index=False)
        diccionario.to_excel(escritor, sheet_name="Diccionario", index=False)
        resumen(marco).to_excel(escritor, sheet_name="Resumen", index=False)
        if sistema is not None:
            sistema.to_excel(escritor, sheet_name="Dataset_sistema", index=False)

        dar_formato(escritor.sheets["Muestra"])
        dar_formato(escritor.sheets["Diccionario"],
                    {"columna": 30, "descripcion": 72, "unidad": 12, "papel": 15})
        dar_formato(escritor.sheets["Resumen"])
        if sistema is not None:
            dar_formato(escritor.sheets["Dataset_sistema"])

    print(f"Escrito {SALIDA}")
    print(f"  Muestra: {len(marco)} filas x {len(marco.columns)} columnas")
    print(marco["clase_peso"].value_counts().to_string())
    if sistema is not None:
        print(f"  Dataset_sistema: {len(sistema)} filas")


if __name__ == "__main__":
    main()
