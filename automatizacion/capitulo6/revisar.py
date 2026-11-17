r"""Revisión del PDF del capítulo: hojas de contacto para mirarlo y búsqueda de marcas sospechosas en el texto.

    .venv\Scripts\python -m capitulo6.revisar CARPETA_SALIDA
"""
import sys

import pymupdf
from PIL import Image

PDF = "capitulo6/entregables/Capitulo_6_Estrategia_y_Ejecucion_de_Pruebas.pdf"


def principal(salida: str):
    doc = pymupdf.open(PDF)
    pags = [p.get_pixmap(dpi=50) for p in doc]
    for k in range(0, len(pags), 8):
        grupo = pags[k:k + 8]
        w, h = max(p.width for p in grupo), max(p.height for p in grupo)
        hoja = Image.new("RGB", (w * 4, h * 2), "white")
        for i, p in enumerate(grupo):
            hoja.paste(Image.frombytes("RGB", (p.width, p.height), p.samples), ((i % 4) * w, (i // 4) * h))
        hoja.save(f"{salida}/contacto_{k // 8 + 1:02d}.png")
    print("hojas:", len(pags))
    for i, p in enumerate(doc):
        t = p.get_text()
        if len(t.strip()) < 150 and not p.get_images():
            print("casi vacía:", i + 1, repr(t.strip()[:60]))
        for marca in ("¿REF?", " 000", "None", "[[", "@fin", "@tabla", "@figura", "PENDIENTE", "×", "**"):
            if marca in t:
                print(f"marca «{marca}» en hoja {i + 1}:", [x for x in t.splitlines() if marca in x][:2])


if __name__ == "__main__":
    principal(sys.argv[1])
