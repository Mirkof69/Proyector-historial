"""Auditoría de los datasets ginecológicos antes de entrenar.

Por cada dataset: cuántas imágenes, copias exactas (md5), casi copias (dHash a
distancia <= 4 bits) y, si las hay, casi copias entre entrenamiento y prueba.
La lección de la B4: una métrica alta con copias entre particiones no mide nada.

Uso: python auditar.py  ->  salidas/auditoria.json
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parents[2] / "datos" / "extraidos" / "ginecologia"
SALIDA = Path(__file__).resolve().parent / "salidas"


def dhash(ruta: Path, lado: int = 16) -> int:
    img = Image.open(ruta).convert("L").resize((lado + 1, lado), Image.BILINEAR)
    a = np.asarray(img, dtype=np.int16)
    bits = (a[:, 1:] > a[:, :-1]).flatten()
    return int("".join("1" if b else "0" for b in bits), 2)


def casi_copias(hashes: dict[str, int], umbral: int = 4) -> list[tuple[str, str, int]]:
    claves = list(hashes)
    valores = np.array([hashes[k] for k in claves], dtype=object)
    pares = []
    for i in range(len(claves)):
        for j in range(i + 1, len(claves)):
            d = bin(valores[i] ^ valores[j]).count("1")
            if d <= umbral:
                pares.append((claves[i], claves[j], d))
    return pares


def auditar(nombre: str, rutas: list[Path], particion: dict[str, str] | None = None) -> dict:
    md5 = defaultdict(list)
    hashes = {}
    tamanos = Counter()
    for r in rutas:
        md5[hashlib.md5(r.read_bytes()).hexdigest()].append(r.name)
        hashes[r.name] = dhash(r)
        with Image.open(r) as im:
            tamanos[im.size] += 1
    exactas = [v for v in md5.values() if len(v) > 1]
    pares = casi_copias(hashes)
    resultado = {
        "imagenes": len(rutas),
        "copias_exactas_grupos": len(exactas),
        "copias_exactas_ejemplos": exactas[:5],
        "casi_copias_pares": len(pares),
        "casi_copias_ejemplos": pares[:8],
        "tamanos_mas_comunes": [[f"{w}x{h}", n] for (w, h), n in tamanos.most_common(5)],
    }
    if particion:
        cruzadas = [(a, b, d) for a, b, d in pares
                    if particion.get(a) and particion.get(b) and particion[a] != particion[b]]
        resultado["casi_copias_entre_particiones"] = len(cruzadas)
        resultado["casi_copias_entre_particiones_ejemplos"] = cruzadas[:8]
    print(nombre, json.dumps({k: v for k, v in resultado.items() if not k.endswith("ejemplos")}, ensure_ascii=False))
    return resultado


def main() -> None:
    SALIDA.mkdir(exist_ok=True)
    informe = {}

    # MMOTU: partición oficial por paciente (train.txt / val.txt)
    m = RAIZ / "mmotu"
    part = {f"{n}.JPG": "entrenamiento" for n in (m / "train.txt").read_text().split()}
    part |= {f"{n}.JPG": "prueba" for n in (m / "val.txt").read_text().split()}
    informe["mmotu"] = auditar("mmotu", sorted((m / "MMOTU" / "images").glob("*.JPG")), part)

    # Ovario normal / folículo dominante / poliquístico: una imagen por paciente
    p = RAIZ / "ovario_pco"
    informe["ovario_pco"] = auditar("ovario_pco", sorted(p.glob("*/*.jpg")))
    informe["ovario_pco"]["por_clase"] = {d.name: len(list(d.glob("*.jpg"))) for d in p.iterdir() if d.is_dir()}

    # Miomas: el campo <folder> del XML identifica a la paciente (se anonimiza: nunca se guarda el texto)
    mi = RAIZ / "miomas"
    pacientes, objetos = {}, Counter()
    for x in (mi / "Annotations").glob("*.xml"):
        t = x.read_text(encoding="utf-8", errors="replace")
        carpeta = re.search(r"<folder>(.*?)</folder>", t)
        pacientes[x.stem + ".jpg"] = hashlib.sha256((carpeta.group(1) if carpeta else x.stem).encode()).hexdigest()[:10]
        objetos[len(re.findall(r"<object>", t))] += 1
    informe["miomas"] = auditar("miomas", sorted((mi / "JPEGImages").glob("*.jpg")), pacientes)
    informe["miomas"]["pacientes_distintas"] = len(set(pacientes.values()))
    informe["miomas"]["miomas_por_imagen"] = dict(sorted(objetos.items()))
    informe["miomas"]["nota"] = ("casi_copias_entre_particiones aquí = casi copias entre pacientes distintas "
                                 "(posible error de agrupación o imagen repetida)")
    (SALIDA / "auditoria.json").write_text(json.dumps(informe, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
