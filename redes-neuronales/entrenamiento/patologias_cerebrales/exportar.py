"""Empaqueta la red final para el microservicio.

    python exportar.py   → ../../../modelos-ia/redes/anomalias_cerebrales_fetales.pth (+ .json)

El paquete lleva los pesos, el preprocesado exacto del entrenamiento y las
métricas medidas (salidas/metricas.json): el microservicio las devuelve tal
cual con cada predicción, sin copiarlas a mano.
"""
import json
import sys
from pathlib import Path

import torch

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from entrenar import FAMILIAS, LADO, UMBRAL  # noqa: E402

DESTINO = AQUI.parents[2] / "modelos-ia" / "redes" / "anomalias_cerebrales_fetales.pth"


def main():
    metricas = json.loads((AQUI / "salidas" / "metricas.json").read_text(encoding="utf-8"))
    estado = torch.load(AQUI / "salidas" / "anomalias_cerebrales_b0.pth", map_location="cpu", weights_only=True)
    meta = {
        "arquitectura": "efficientnet_b0",
        "lado": LADO + 32,        # relleno a cuadrado y reducido a 352…
        "recorte": LADO,          # …y recorte central de 320, como en la prueba
        "media": 0.45,
        "desv": 0.225,
        "volteo_prueba": True,
        "clases": FAMILIAS,
        "umbral": UMBRAL,
        "dataset": ("Fetal Brain Abnormalities (Roboflow, CC BY 4.0; 212 imágenes originales) + "
                    "cortes cerebrales normales de FETAL_PLANES_DB (Zenodo 3904280, CC BY 4.0)"),
        "metricas": metricas,
    }
    DESTINO.parent.mkdir(exist_ok=True)
    torch.save({"meta": meta, "estado": estado}, DESTINO)
    # Ficha legible (y la que lee /health sin cargar la red)
    DESTINO.with_suffix(".json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Guardado {DESTINO} ({DESTINO.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
