"""Copia las redes de biometría entrenadas a modelos-ia/redes/, con sus métricas al lado.

    python entrenamiento/biometria/exportar.py
"""
import shutil
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DESTINO = AQUI.parents[2] / "modelos-ia" / "redes"

if __name__ == "__main__":
    for tarea in ("femur", "abdomen"):
        carpeta = AQUI / "salidas" / tarea
        if not (carpeta / f"biometria_{tarea}.pth").exists():
            print(f"FALTA biometria_{tarea}.pth (entrénela primero)")
            continue
        shutil.copy2(carpeta / f"biometria_{tarea}.pth", DESTINO / f"biometria_{tarea}.pth")
        shutil.copy2(carpeta / "metricas.json", DESTINO / f"biometria_{tarea}.json")
        print(f"copiado biometria_{tarea}")
