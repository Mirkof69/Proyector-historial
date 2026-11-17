r"""Arma el Capítulo 6 en Word y PDF con el mismo motor y formato del informe del proyecto.

    .venv\Scripts\python -m capitulo6.construir_cap6

Reutiliza, sin modificarlo, documento/generador/construir.py (letra, márgenes, tablas con paleta, pies de figura,
índices) y la conversión a PDF de paginar.py. Dos pasadas: la primera mide en qué página cae cada título, figura,
tabla y gráfico; la segunda escribe los índices con esas páginas.
Fuente: capitulo6/fuente/capitulo6.txt (la genera capitulo6/generar_fuente.py). Datos de la portada:
capitulo6/portada.json. Salida: capitulo6/entregables/Capitulo_6_Estrategia_y_Ejecucion_de_Pruebas.docx y .pdf.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
GENERADOR = RAIZ.parent / "documento" / "generador"
sys.path.insert(0, str(GENERADOR))

import construir as C  # noqa: E402
import paginar as PG  # noqa: E402
from docx.enum.section import WD_SECTION  # noqa: E402
from docx.shared import Cm  # noqa: E402

C.RAIZ = RAIZ                 # las figuras se resuelven dentro de automatizacion/
C.TABLAS_SALTO = set()
C.TABLAS_LARGAS = set()
# Un solo formato para todas las tablas del capítulo (casos de prueba, ejecución, defectos, métricas): la paleta
# azul del informe. Sin esto, las fichas de casos salían en negro y las de defectos en rojo.
C.paleta_de = lambda id_tabla, ficha: C.PALETAS["azul"]  # noqa: E731
FUENTE = RAIZ / "capitulo6" / "fuente" / "capitulo6.txt"
SALIDA = RAIZ / "capitulo6" / "entregables"
NOMBRE = "Capitulo_6_Estrategia_y_Ejecucion_de_Pruebas"
TITULO_1 = "CAPÍTULO 6. ESTRATEGIA Y EJECUCIÓN DE PRUEBAS"


def caratula_oficial(doc) -> bool:
    """Carátula oficial del autor (documento/caratula.docx), la misma del informe, con los datos del capítulo."""
    p = json.loads((RAIZ / "capitulo6" / "portada.json").read_text(encoding="utf-8"))
    C.CAMPOS_CARATULA = {
        "tema": f"CAPÍTULO 6: ESTRATEGIA Y EJECUCIÓN DE PRUEBAS. {p['proyecto'].upper()}",
        "Docente: ": f"Docente: {p.get('docente', '')}",
        "Materia: ": f"Materia: {p['materia_linea']}",
        "Fecha ": f"Fecha: {p.get('fecha', 'noviembre de 2026')}",
    }
    return C.insertar_caratula(doc)


def portada() -> list[str]:
    p = json.loads((RAIZ / "capitulo6" / "portada.json").read_text(encoding="utf-8"))
    L = [f"@portada_mediana {p['universidad']}", f"@portada_linea {p['facultad']}", f"@portada_linea {p['carrera']}",
         "@espacio 2", f"@portada_mediana {p['materia']}", "@espacio 2",
         "@portada_grande CAPÍTULO 6: ESTRATEGIA Y EJECUCIÓN DE PRUEBAS", "@espacio 1",
         f"@portada_linea {p['proyecto']}", "@espacio 2", f"@izquierda **Integrante:** {p['integrante']} | 3.0"]
    if p.get("docente"):
        L.append(f"@izquierda **Docente:** {p['docente']} | 3.0")
    L += [f"@izquierda **Materia:** {p['materia_linea']} | 3.0", "@espacio 2", f"@portada_linea {p['ciudad']}",
          f"@portada_linea {p['anio']}"]
    return L


INDICES = ["@titulo_indice ÍNDICE DE CONTENIDO", "@indice contenido", "@salto", "@titulo_indice ÍNDICE DE FIGURAS",
           "@indice figuras", "@salto", "@titulo_indice ÍNDICE DE TABLAS", "@indice tablas", "@salto",
           "@titulo_indice ÍNDICE DE GRÁFICOS", "@indice graficos"]


def armar(cuerpo: list[str], reg, indices: dict):
    doc = C.documento_base()
    esc = C.Escritor(doc, reg)
    sec = doc.sections[0]
    C.encabezado_vacio(sec)
    con_plantilla = caratula_oficial(doc)
    if con_plantilla:
        sec.left_margin = sec.right_margin = Cm(3.0)
    else:
        esc.ejecutar(portada(), indices)
    s2 = doc.add_section(WD_SECTION.NEW_PAGE)
    s2.left_margin, s2.right_margin = Cm(3.0), Cm(2.5)
    if con_plantilla:   # el párrafo que lleva el salto de sección de la carátula no ocupa espacio (igual que el informe)
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        for par in doc.element.body.iter(qn("w:p")):
            ppr = par.find(qn("w:pPr"))
            if ppr is not None and ppr.find(qn("w:sectPr")) is not None:
                sp = OxmlElement("w:spacing")
                sp.set(qn("w:after"), "0"), sp.set(qn("w:before"), "0"), sp.set(qn("w:line"), "20"), sp.set(qn("w:lineRule"), "exact")
                ppr.insert(0, sp)
                rpr = OxmlElement("w:rPr")
                sz = OxmlElement("w:sz")
                sz.set(qn("w:val"), "2")
                rpr.append(sz)
                ppr.find(qn("w:sectPr")).addprevious(rpr)
                break
    C.encabezado_con_numero(s2)
    C.formato_numeracion(s2, "lowerRoman", 1)
    esc.ejecutar(INDICES, indices)
    s3 = doc.add_section(WD_SECTION.NEW_PAGE)
    C.encabezado_con_numero(s3)
    C.formato_numeracion(s3, "decimal", 1)
    esc.ejecutar(cuerpo, indices)
    SALIDA.mkdir(parents=True, exist_ok=True)
    ruta = SALIDA / f"{NOMBRE}.docx"
    doc.save(ruta)
    return ruta


def medir(reg, pdf: Path) -> dict:
    pags = PG.paginas_texto(pdf)
    cuerpo = next(i for i, ls in enumerate(pags) if any(x == TITULO_1 for x in ls) and not any("ÍNDICE" in x for x in ls))
    impresa = lambda i: str(i - cuerpo + 1) if i >= cuerpo else PG.romano(i)  # noqa: E731

    def buscar(prefijo, desde):
        pre = PG.norm(prefijo)[:60]
        for i in range(desde, len(pags)):
            for x in pags[i]:
                if x.startswith(pre) or (len(pre) > 40 and pre.startswith(x) and len(x) > 25):
                    return i
        return None

    contenido, pos = [], cuerpo
    for nivel, txt in reg.titulos:
        i = buscar(txt, pos)
        if i is None:
            raise SystemExit(f"No encontré en el PDF el título: {txt}")
        pos = i
        contenido.append(((max(nivel, 1) - 1) * 0.6, txt, impresa(i), nivel == 1))
    indices = {"contenido": contenido}
    for clave, lista, nombre in (("figuras", reg.figuras, "Figura"), ("tablas", reg.tablas, "Tabla"),
                                 ("graficos", reg.graficos, "Gráfico")):
        ent, pos = [], cuerpo
        for n, titulo, _ in lista:
            i = buscar(f"{nombre} {n}. ", pos)
            if i is None:
                raise SystemExit(f"No encontré «{nombre} {n}.» en el PDF")
            pos = i
            ent.append((0.0, f"{nombre} {n}. " + re.sub(r"\*\*|\*|\^\{|\}|_\{", "", titulo), impresa(i), False))
        indices[clave] = ent
    return indices


def tablas_partidas(docx: Path) -> list[str]:
    """Títulos de las tablas que empiezan en una hoja y terminan en otra sin empezar arriba de la hoja (Word)."""
    import shutil
    import tempfile

    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    copia = Path(tempfile.mkdtemp(prefix="cap6_tablas_")) / "revision.docx"
    shutil.copy2(docx, copia)
    titulos = []
    try:
        d = word.Documents.Open(str(copia), ReadOnly=True, AddToRecentFiles=False)
        d.Repaginate()
        for i in range(1, d.Tables.Count + 1):
            t = d.Tables(i)
            p0 = t.Range.Characters(1).Information(3)
            p1 = t.Range.Characters(t.Range.Characters.Count).Information(3)
            # una tabla que ya empieza en el tercio superior de la hoja y aun así sigue es una tabla larga: se deja
            arriba = t.Range.Characters(1).Information(6) < 260   # posición vertical en puntos desde el borde
            if p1 > p0 and not arriba:
                r = t.Range
                r.Collapse(0)
                r.MoveEnd(4, 1)
                titulos.append(re.sub(r"^Tabla \d+\.\s*", "", r.Text.strip()))
        d.Close(False)
    finally:
        word.Quit()
    return titulos


def principal():
    cuerpo = FUENTE.read_text(encoding="utf-8").splitlines()
    reg = C.numerar(cuerpo)
    prov = {"contenido": [((max(n, 1) - 1) * 0.6, t, "000", n <= 1) for n, t in reg.titulos],
            "figuras": [(0.0, f"Figura {n}. {t}", "000", False) for n, t, _ in reg.figuras],
            "tablas": [(0.0, f"Tabla {n}. {t}", "000", False) for n, t, _ in reg.tablas],
            "graficos": [(0.0, f"Gráfico {n}. {t}", "000", False) for n, t, _ in reg.graficos]}
    docx = armar(cuerpo, reg, prov)
    # Ninguna tabla empieza en una hoja y termina en otra: la que no cabe en lo que queda de la hoja baja entera a
    # la siguiente (salto antes). Las que miden más de una hoja siguen, con su encabezado repetido.
    for _ in range(4):
        partidas = [x for x in tablas_partidas(docx) if x not in C.TABLAS_SALTO]
        if not partidas:
            break
        C.TABLAS_SALTO |= set(partidas)
        print("tablas que bajan a hoja nueva:", len(partidas))
        docx = armar(cuerpo, reg, prov)
    pdf = PG.a_pdf([docx])[0]
    indices = medir(reg, pdf)
    docx = armar(cuerpo, reg, indices)
    pdf = PG.a_pdf([docx])[0]
    indices2 = medir(reg, pdf)
    movidas = [(a[1], a[2], b[2]) for k in indices for a, b in zip(indices[k], indices2[k]) if a[2] != b[2]]
    if movidas:   # una tercera pasada con las páginas definitivas
        docx = armar(cuerpo, reg, indices2)
        pdf = PG.a_pdf([docx])[0]
        indices3 = medir(reg, pdf)
        movidas = [(a[1], a[2], b[2]) for k in indices2 for a, b in zip(indices2[k], indices3[k]) if a[2] != b[2]]
    import fitz
    print(f"PDF: {pdf} · {fitz.open(pdf).page_count} hojas · figuras {len(reg.figuras)}, tablas {len(reg.tablas)}, "
          f"gráficos {len(reg.graficos)} · páginas movidas: {movidas[:5] or 'ninguna'}")


if __name__ == "__main__":
    principal()
