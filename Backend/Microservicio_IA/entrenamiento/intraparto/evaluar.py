"""Vuelve a medir la red intraparto ya entrenada (sin reentrenar).

    python entrenamiento/intraparto/evaluar.py

Útil cuando cambia el cálculo del ángulo de progresión (app/angulo_progresion.py)
pero no la red: actualiza `salidas/intraparto/metricas.json` y la ficha .pth.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import torch

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from app.unet import UNet  # noqa: E402
from entrenamiento.segmentacion import entrenar as e  # noqa: E402

SALIDA = RAIZ / "entrenamiento" / "segmentacion" / "salidas" / "intraparto"


def main() -> None:
    paquete = torch.load(SALIDA / "segmentacion_intraparto.pth", map_location=e.DISPOSITIVO, weights_only=True)
    meta = paquete["meta"]
    red = UNet(meta["codificador"], len(meta["clases"]), preentrenado=False)
    red.load_state_dict(paquete["estado"])
    red.to(e.DISPOSITIVO).eval()
    cat = pd.read_csv(e.CATALOGO["intraparto"])
    prueba = cat[cat["particion"] == "prueba"].reset_index(drop=True)
    X, Y = e.cargar(prueba, meta["lado"])
    pred = e.predecir(red, X)
    cfg = e.CONFIG["intraparto"]
    nuevas = e.medir_intraparto(red, prueba, pred, Y, cfg, print)
    meta["metricas"] |= nuevas
    torch.save({"estado": paquete["estado"], "meta": meta}, SALIDA / "segmentacion_intraparto.pth")
    (SALIDA / "metricas.json").write_text(json.dumps(meta["metricas"], ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
