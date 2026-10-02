"""Copia las redes ginecológicas entrenadas al microservicio (trained_models/).

    python entrenamiento/ginecologia/exportar.py

Junto a cada .pth deja un .json con sus métricas de prueba: es lo que el
servicio muestra en /api/modelos sin cargar la red.
"""
import shutil
from pathlib import Path

AQUI = Path(__file__).resolve().parent
IA = AQUI.parents[1]
DESTINO = IA / "trained_models"

ORIGENES = {
    "segmentacion_ovario": IA / "entrenamiento" / "segmentacion" / "salidas" / "ovario",
    "segmentacion_mioma": IA / "entrenamiento" / "segmentacion" / "salidas" / "mioma",
    "clasificador_ovario": AQUI / "salidas" / "ovario",
    "clasificador_ovario_pco": AQUI / "salidas" / "ovario_pco",
}

if __name__ == "__main__":
    DESTINO.mkdir(exist_ok=True)
    for nombre, carpeta in ORIGENES.items():
        pesos, metricas = carpeta / f"{nombre}.pth", carpeta / "metricas.json"
        if not pesos.exists():
            print(f"FALTA {pesos} (entrénela primero)")
            continue
        shutil.copy2(pesos, DESTINO / f"{nombre}.pth")
        shutil.copy2(metricas, DESTINO / f"{nombre}.json")
        print(f"copiado {nombre}")
