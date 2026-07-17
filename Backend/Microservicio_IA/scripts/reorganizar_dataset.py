# -*- coding: utf-8 -*-
"""Reorganiza datasets_pathology/ en un arbol limpio datasets_pathology_v2/.

CRITERIO (aprobado por el responsable del proyecto, 2026-07-17):

1. El dataset ORIGINAL nunca se modifica: solo se lee. v2 se construye copiando.
2. El HASH DE CONTENIDO manda; la carpeta actual es solo una pista de etiqueta.
3. Deduplicacion: una imagen (un md5) = un archivo en v2.
4. Etiquetas contradictorias (mismo md5 en 2+ clases): NO se resuelven por
   heuristica. Van a _conflictos/ con un CSV que documenta en que clases
   aparecian, y quedan FUERA del entrenamiento hasta que un criterio medico
   las resuelva.
5. Estructura aplanada: la clase es la carpeta de primer nivel; los sub-splits
   del dataset original (train/valid/test/images/...) se descartan.
6. Re-split estratificado 70/15/15 AGRUPANDO POR HASH: como cada md5 unico se
   asigna a exactamente un split, la fuga entre splits es imposible por
   construccion.
7. Verificacion: la invariante
       imagenes_v2 + conflictos == hashes_distintos
       hashes_distintos + duplicados_eliminados == archivos_originales
   se comprueba al final; si no cierra, el script falla en voz alta.

Uso:
    python scripts/reorganizar_dataset.py            # ejecuta
    python scripts/reorganizar_dataset.py --dry-run  # solo inventario/reporte
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import random
import shutil
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ORIGEN = BASE / "datasets_pathology"
DESTINO = BASE / "datasets_pathology_v2"
SPLITS_ORIGEN = ["train", "validation", "val"]
PROPORCIONES = {"train": 0.70, "valid": 0.15, "test": 0.15}
SEMILLA = 42  # reproducible: la defensa tiene que poder re-correr esto


def md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def inventariar() -> tuple[dict[str, list[Path]], dict[str, set[str]], int]:
    """Devuelve (hash -> rutas originales, hash -> clases, total archivos)."""
    por_hash: dict[str, list[Path]] = defaultdict(list)
    clases_por_hash: dict[str, set[str]] = defaultdict(set)
    total = 0

    for split in SPLITS_ORIGEN:
        raiz = ORIGEN / split
        if not raiz.is_dir():
            continue
        for ruta in raiz.rglob("*"):
            if not ruta.is_file():
                continue
            # La clase es la carpeta de PRIMER nivel dentro del split:
            # train/anencefalia/train/img.png -> clase "anencefalia"
            rel = ruta.relative_to(raiz)
            if len(rel.parts) < 2:
                continue  # archivo suelto en la raiz del split: se ignora
            clase = rel.parts[0]
            h = md5(ruta)
            por_hash[h].append(ruta)
            clases_por_hash[h].add(clase)
            total += 1
            if total % 5000 == 0:
                print(f"  ... {total} archivos inventariados", flush=True)

    return por_hash, clases_por_hash, total


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not ORIGEN.is_dir():
        print(f"ERROR: no existe {ORIGEN}")
        return 1

    print("== PASO 1: inventario por hash de contenido ==", flush=True)
    por_hash, clases_por_hash, total_original = inventariar()
    hashes_distintos = len(por_hash)
    duplicados = total_original - hashes_distintos
    print(f"  archivos originales : {total_original}")
    print(f"  hashes distintos    : {hashes_distintos}")
    print(f"  duplicados exactos  : {duplicados}")

    limpios = {h: next(iter(c)) for h, c in clases_por_hash.items() if len(c) == 1}
    conflictos = {h: sorted(c) for h, c in clases_por_hash.items() if len(c) > 1}
    print(f"  imagenes con etiqueta unica    : {len(limpios)}")
    print(f"  imagenes con etiqueta EN CONFLICTO: {len(conflictos)}")

    # ── Inventario auditable (evidencia) ──
    DESTINO.mkdir(parents=True, exist_ok=True)
    inv_path = DESTINO / "_inventario.csv"
    with open(inv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["md5", "clases_detectadas", "estado", "copias_originales", "ruta_original_1"])
        for h, rutas in por_hash.items():
            clases = sorted(clases_por_hash[h])
            estado = "conflicto" if len(clases) > 1 else "ok"
            w.writerow([h, "|".join(clases), estado, len(rutas), str(rutas[0].relative_to(ORIGEN))])
    print(f"  inventario -> {inv_path}")

    # ── Distribucion por clase (post-dedup) ──
    por_clase: dict[str, list[str]] = defaultdict(list)
    for h, clase in limpios.items():
        por_clase[clase].append(h)
    print("\n== PASO 2: distribucion por clase (deduplicada) ==")
    for clase in sorted(por_clase):
        print(f"  {clase:26s} {len(por_clase[clase]):6d}")

    if args.dry_run:
        print("\n--dry-run: no se copio nada.")
        return 0

    # ── Re-split estratificado agrupado por hash ──
    print("\n== PASO 3: re-split 70/15/15 estratificado por clase ==", flush=True)
    rng = random.Random(SEMILLA)
    asignacion: dict[str, str] = {}  # hash -> split
    resumen: dict[str, dict[str, int]] = {}
    for clase, hashes in por_clase.items():
        hs = sorted(hashes)  # orden determinista antes de barajar
        rng.shuffle(hs)
        n = len(hs)
        n_train = int(n * PROPORCIONES["train"])
        n_valid = int(n * PROPORCIONES["valid"])
        cortes = {
            "train": hs[:n_train],
            "valid": hs[n_train:n_train + n_valid],
            "test": hs[n_train + n_valid:],
        }
        for split, lote in cortes.items():
            for h in lote:
                asignacion[h] = split
        resumen[clase] = {s: len(l) for s, l in cortes.items()}

    # ── Copia por lotes, con conteo antes/despues ──
    print("\n== PASO 4: copiando (el original NO se toca) ==", flush=True)
    copiados = 0
    for clase in sorted(por_clase):
        antes = copiados
        for h in por_clase[clase]:
            origen = por_hash[h][0]
            split = asignacion[h]
            destino_dir = DESTINO / split / clase
            destino_dir.mkdir(parents=True, exist_ok=True)
            # Nombre = hash + extension original: elimina colisiones de nombre
            shutil.copy2(origen, destino_dir / f"{h}{origen.suffix.lower()}")
            copiados += 1
        r = resumen[clase]
        print(f"  {clase:26s} origen={len(por_clase[clase]):5d} -> copiadas={copiados - antes:5d} "
              f"(train={r['train']}, valid={r['valid']}, test={r['test']})", flush=True)

    # ── Conflictos: se preservan, se documentan, NO se entrenan ──
    print("\n== PASO 5: conflictos de etiqueta (excluidos del entrenamiento) ==", flush=True)
    dir_conf = DESTINO / "_conflictos"
    dir_conf.mkdir(parents=True, exist_ok=True)
    with open(dir_conf / "_conflictos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["archivo_en_conflictos", "md5", "clases_en_conflicto", "rutas_originales"])
        for h, clases in conflictos.items():
            origen = por_hash[h][0]
            nombre = f"{h}{origen.suffix.lower()}"
            shutil.copy2(origen, dir_conf / nombre)
            w.writerow([nombre, h, "|".join(clases),
                        " | ".join(str(p.relative_to(ORIGEN)) for p in por_hash[h])])
    print(f"  {len(conflictos)} imagenes -> {dir_conf} (con _conflictos.csv)")

    # ── Verificacion de la invariante ──
    print("\n== PASO 6: verificacion de conteos ==")
    n_v2 = sum(1 for p in DESTINO.rglob("*") if p.is_file() and p.suffix.lower() not in {".csv"} and "_conflictos" not in p.parts)
    n_conf = sum(1 for p in (DESTINO / "_conflictos").iterdir() if p.is_file() and p.suffix.lower() != ".csv")
    ok1 = (n_v2 + n_conf) == hashes_distintos
    ok2 = (hashes_distintos + duplicados) == total_original
    print(f"  imagenes en v2 (splits) : {n_v2}")
    print(f"  imagenes en _conflictos : {n_conf}")
    print(f"  suma                    : {n_v2 + n_conf} == hashes distintos {hashes_distintos} ? {'OK' if ok1 else 'FALLA'}")
    print(f"  hashes {hashes_distintos} + duplicados {duplicados} == originales {total_original} ? {'OK' if ok2 else 'FALLA'}")

    # Fuga entre splits: imposible por construccion, pero se comprueba igual.
    vistos: dict[str, str] = {}
    fugas = 0
    for split in ("train", "valid", "test"):
        for p in (DESTINO / split).rglob("*"):
            if p.is_file():
                h = p.stem
                if h in vistos and vistos[h] != split:
                    fugas += 1
                vistos[h] = split
    print(f"  fuga entre splits       : {fugas} {'OK' if fugas == 0 else 'FALLA'}")

    total_original_intacto = sum(1 for s in SPLITS_ORIGEN for p in (ORIGEN / s).rglob("*") if p.is_file())
    ok3 = total_original_intacto == total_original
    print(f"  dataset ORIGINAL intacto: {total_original_intacto} archivos {'OK' if ok3 else 'FALLA'}")

    if not (ok1 and ok2 and ok3 and fugas == 0):
        print("\nRESULTADO: FALLO la verificacion. Revisar antes de usar v2.")
        return 1
    print("\nRESULTADO: OK — v2 listo y verificado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
