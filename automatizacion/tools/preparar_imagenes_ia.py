"""Copia una muestra fija (semilla 13) de imágenes de la PARTICIÓN DE PRUEBA a data/imagenes_ia/, con su etiqueta.

Fuentes (CC BY 4.0, sin datos personales): FETAL_PLANES_DB (Burgos-Artizzu et al., 2020) y HC18 (van den Heuvel et
al., 2018), tal como las catalogó el sistema en catalogo_imagenes.xlsx. Las redes no vieron estas imágenes al entrenar.

    python tools/preparar_imagenes_ia.py --sistema "<repo del sistema>"
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
from collections import defaultdict
from pathlib import Path

import openpyxl

DESTINO = Path(__file__).resolve().parents[1] / "data" / "imagenes_ia"


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sistema", required=True)
    a = ap.parse_args()
    base = Path(a.sistema) / "Backend" / "Microservicio_IA" / "entrenamiento" / "redes_ecografia_real"
    wb = openpyxl.load_workbook(base / "catalogo_imagenes.xlsx", read_only=True)
    rnd = random.Random(13)
    DESTINO.mkdir(parents=True, exist_ok=True)
    manifiesto = {"planos": [], "hc18": [], "fuente": "catalogo_imagenes.xlsx (partición «prueba»)"}

    filas = list(wb["Planos"].iter_rows(min_row=2, values_only=True))
    por_plano = defaultdict(list)
    for archivo, ruta, paciente, plano, *_resto, particion in filas:
        if particion == "prueba":
            por_plano[plano].append((archivo, ruta, paciente))
    for plano, lista in sorted(por_plano.items()):
        vistos = set()
        rnd.shuffle(lista)
        for archivo, ruta, paciente in lista:
            if paciente in vistos:   # una imagen por paciente para no sobrerrepresentar a nadie
                continue
            vistos.add(paciente)
            shutil.copy2(base / ruta, DESTINO / archivo)
            manifiesto["planos"].append({"archivo": archivo, "plano": plano})
            if len(vistos) == 5:
                break

    filas = [f for f in wb["HC18"].iter_rows(min_row=2, values_only=True) if f[-1] == "prueba"]
    rnd.shuffle(filas)
    for archivo, ruta, paciente, _n, px_mm, hc_mm, *_r in filas[:8]:
        shutil.copy2(base / ruta, DESTINO / archivo)
        manifiesto["hc18"].append({"archivo": archivo, "pixel_mm": px_mm, "hc_mm": hc_mm})

    (DESTINO / "manifiesto.json").write_text(json.dumps(manifiesto, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"planos: {len(manifiesto['planos'])} ({len(por_plano)} clases) | hc18: {len(manifiesto['hc18'])}")


if __name__ == "__main__":
    principal()
