"""La prueba que decide si la red mira cerebros o mira el origen de la imagen.

En Fetal Brain Abnormalities, TODAS las imágenes normales son cortes de
FETAL_PLANES_DB (Barcelona; se llaman «Patient00738_Plane3_…») y TODAS las
anomalías vienen de otras fuentes. Una red puede acertar al 100 % aprendiendo
«aspecto de Barcelona = normal» sin mirar el cerebro.

Aquí se le pasan las 999 cabezas de HC18: embarazos del Radboud UMC
(Países Bajos), otros ecógrafos y otros ecografistas, sin anomalías cerebrales
anotadas. Si la red ha aprendido anatomía, casi todas deben salir «normal». Si
ha aprendido el origen, dará falsas alarmas en masa.

    python prueba_otro_hospital.py   → salidas/predicciones_hc18.csv
"""
import sys
from pathlib import Path

import pandas as pd
import torch

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from entrenar import FAMILIAS, IA, SALIDAS, UMBRAL, nueva_red, predecir  # noqa: E402

REDES = IA / "entrenamiento" / "redes_ecografia_real"


def main():
    cat = pd.read_excel(REDES / "catalogo_imagenes.xlsx", sheet_name="HC18")
    df = pd.DataFrame({"ruta": [(REDES / r).relative_to(IA).as_posix() for r in cat["ruta"]],
                       "familia": "normal"})
    red = nueva_red()
    red.load_state_dict(torch.load(SALIDAS / "anomalias_cerebrales_b0.pth", weights_only=True))
    p = predecir(red, df)
    salida = cat[["archivo", "paciente", "trimestre", "circunferencia_cefalica_mm"]].copy()
    for i, f in enumerate(FAMILIAS):
        salida["p_" + f] = p[:, i]
    salida["p_anomalia"] = 1 - salida["p_normal"]
    salida.to_csv(SALIDAS / "predicciones_hc18.csv", index=False, encoding="utf-8")
    alarma = salida["p_anomalia"] >= UMBRAL
    print(f"Falsas alarmas en cabezas normales de otro hospital: {alarma.sum()} de {len(salida)} "
          f"({alarma.mean():.1%})")
    print(salida.assign(alarma=alarma).groupby("trimestre")["alarma"].agg(["sum", "size", "mean"]))


if __name__ == "__main__":
    main()
