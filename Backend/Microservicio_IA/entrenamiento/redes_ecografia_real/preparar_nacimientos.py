"""Descarga los nacimientos reales y los deja en un Excel en español.

    python preparar_nacimientos.py

Escribe `datos/nacimientos_reales_2014.xlsx` con tres hojas:

    Nacimientos   1.000 nacimientos reales, columnas en español y en gramos
    Diccionario   qué significa cada columna y si entra al modelo
    Fuente        de dónde vienen los datos y cómo citarlos

DE DÓNDE SALEN LOS DATOS
------------------------
Son 1.000 nacimientos REALES elegidos al azar de los registros de natalidad de
Estados Unidos de 2014 (Centros para el Control y la Prevención de
Enfermedades, CDC). La muestra la publica OpenIntro como conjunto de datos
`births14`, de uso libre para docencia:

    Çetinkaya-Rundel M, Diez D, Bray A, Kim AY, et al.
    openintro: Data Sets and Supplemental Functions from 'OpenIntro'
    Textbooks and Labs. Conjunto de datos `births14`.
    https://www.openintro.org/data/index.php?data=births14

Qué NO tienen: medidas de ecografía. Por eso sobre estos datos no se puede
aplicar la fórmula de Hadlock de cuatro medidas; se usa su curva de peso por
semana (Hadlock 1991) como referencia clínica.
"""
from pathlib import Path

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

AQUI = Path(__file__).resolve().parent
URL = "https://vincentarelbundock.github.io/Rdatasets/csv/openintro/births14.csv"
CSV = AQUI / "datos" / "births14.csv"
SALIDA = AQUI / "datos" / "nacimientos_reales_2014.xlsx"

LIBRAS_A_GRAMOS = 453.592
LIBRAS_A_KG = 0.453592

DICCIONARIO = [
    # columna, descripción, unidad, ¿entra al modelo?
    ("id", "Número de registro", "—", "no: identificador"),
    ("semanas_gestacion", "Semanas de embarazo al nacer", "semanas", "SÍ"),
    ("edad_madre", "Edad de la madre", "años", "SÍ"),
    ("edad_padre", "Edad del padre (vacío si no se registró)", "años", "SÍ"),
    ("controles_prenatales", "Visitas médicas durante el embarazo", "n.º", "SÍ"),
    ("aumento_peso_madre_kg", "Kilos que ganó la madre en el embarazo", "kg", "SÍ"),
    ("fumadora", "La madre fumaba durante el embarazo", "0/1", "SÍ"),
    ("sexo_bebe", "Sexo del bebé", "texto", "SÍ (como 1 = masculino)"),
    ("prematuro", "Nació antes de las 37 semanas", "0/1", "no: se deduce de las semanas"),
    ("casada", "Estado civil de la madre", "0/1", "no: variable social, no clínica"),
    ("madre_blanca", "Origen étnico declarado", "0/1", "no: no se traslada a Bolivia"),
    ("peso_nacimiento_g", "Peso real al nacer", "g", "OBJETIVO (regresión)"),
    ("bajo_peso", "Nació con menos de 2.500 g", "0/1", "OBJETIVO (clasificación)"),
]


def descargar() -> pd.DataFrame:
    if not CSV.exists():
        CSV.parent.mkdir(parents=True, exist_ok=True)
        pd.read_csv(URL).to_csv(CSV, index=False)
    return pd.read_csv(CSV)


def a_espanol(crudo: pd.DataFrame) -> pd.DataFrame:
    """Traduce columnas y valores, y pasa las libras a gramos y kilos."""
    d = pd.DataFrame({
        "id": crudo["rownames"],
        "semanas_gestacion": crudo["weeks"],
        "edad_madre": crudo["mage"],
        "edad_padre": crudo["fage"],
        "controles_prenatales": crudo["visits"],
        "aumento_peso_madre_kg": (crudo["gained"] * LIBRAS_A_KG).round(1),
        "fumadora": crudo["habit"].map({"smoker": 1, "nonsmoker": 0}),
        "sexo_bebe": crudo["sex"].map({"male": "masculino", "female": "femenino"}),
        "prematuro": (crudo["premie"] == "premie").astype(int),
        "casada": (crudo["marital"] == "married").astype(int),
        "madre_blanca": (crudo["whitemom"] == "white").astype(int),
        "peso_nacimiento_g": (crudo["weight"] * LIBRAS_A_GRAMOS).round(0).astype(int),
    })
    # El corte clínico estándar. Se recalcula en vez de copiar la columna
    # original para que coincida exactamente con el del sistema (2.500 g).
    d["bajo_peso"] = (d["peso_nacimiento_g"] < 2500).astype(int)
    return d


def dar_formato(hoja, anchos=None):
    for celda in hoja[1]:
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = PatternFill("solid", fgColor="2E5B86")
        celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    hoja.row_dimensions[1].height = 32
    hoja.freeze_panes = "A2"
    hoja.auto_filter.ref = hoja.dimensions
    for i, col in enumerate(hoja.iter_cols(min_row=1, max_row=1), start=1):
        nombre = str(col[0].value)
        hoja.column_dimensions[get_column_letter(i)].width = (anchos or {}).get(
            nombre, max(12, min(30, len(nombre) + 3)))


def main():
    datos = a_espanol(descargar())
    diccionario = pd.DataFrame(DICCIONARIO, columns=["columna", "descripcion", "unidad", "entra_al_modelo"])
    fuente = pd.DataFrame({"campo": [
        "Qué son", "Origen", "Publicado por", "Dirección", "Tamaño",
        "Qué NO tienen", "Aviso",
    ], "detalle": [
        "Nacimientos reales, elegidos al azar",
        "Registros de natalidad de Estados Unidos, año 2014 (CDC)",
        "OpenIntro, conjunto de datos «births14», de uso libre para docencia",
        "https://www.openintro.org/data/index.php?data=births14",
        f"{len(datos)} nacimientos",
        "Medidas de ecografía (no se puede aplicar Hadlock de 4 medidas)",
        "Población de EE. UU.: los resultados no se trasladan tal cual a Bolivia",
    ]})

    with pd.ExcelWriter(SALIDA, engine="openpyxl") as escritor:
        datos.to_excel(escritor, sheet_name="Nacimientos", index=False)
        diccionario.to_excel(escritor, sheet_name="Diccionario", index=False)
        fuente.to_excel(escritor, sheet_name="Fuente", index=False)
        dar_formato(escritor.sheets["Nacimientos"])
        dar_formato(escritor.sheets["Diccionario"],
                    {"columna": 26, "descripcion": 52, "unidad": 11, "entra_al_modelo": 32})
        dar_formato(escritor.sheets["Fuente"], {"campo": 18, "detalle": 80})

    print(f"Escrito {SALIDA}: {len(datos)} nacimientos reales")
    print(f"  bajo peso: {datos['bajo_peso'].sum()} ({datos['bajo_peso'].mean():.1%})")


if __name__ == "__main__":
    main()
