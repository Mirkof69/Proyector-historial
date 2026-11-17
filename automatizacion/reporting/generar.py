"""Genera los reportes de una corrida: HTML, Word con evidencias, PDF (Word) y un ZIP con todo.

    .venv\\Scripts\\python -m reporting.generar [--run 20261114-001500] [--sin-pdf] [--correo]

Salida en reports/<run_id>/: reporte.html, reporte.docx, reporte.pdf y fetal_medical_<run_id>.zip.
"""
from __future__ import annotations

import argparse
import json
import zipfile
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from jinja2 import Environment, FileSystemLoader, select_autoescape

from reporting.modelo import Reporte, cargar

PLANTILLAS = Path(__file__).resolve().parent / "plantillas"
COLOR = {"PASS": "1E7F4F", "FAIL": "B3261E", "BLOCKED": "A15C00", "NOT RUN": "6B7280"}


def _extras(r: Reporte) -> tuple[dict, dict]:
    """Resumen ejecutivo y análisis de fallos hechos por la IA en esta corrida (si se pidieron)."""
    ia, analisis = {}, {}
    f = r.dir_run / "ia_resumen.json"
    if f.exists():
        ia = json.loads(f.read_text(encoding="utf-8"))
    f = r.dir_run / "ia_fallos.json"
    if f.exists():
        analisis = {x["nodeid"]: x for x in json.loads(f.read_text(encoding="utf-8"))}
    return ia, analisis


# ---------------------------------------------------------------------- HTML
def html(r: Reporte) -> Path:
    env = Environment(loader=FileSystemLoader(PLANTILLAS), autoescape=select_autoescape(["html", "j2"]))
    ia, analisis = _extras(r)
    texto = env.get_template("reporte.html.j2").render(r=r, ia=ia, analisis=analisis,
                                                        generado=datetime.now().strftime("%d/%m/%Y %H:%M"))
    destino = r.dir_run / "reporte.html"
    destino.write_text(texto, encoding="utf-8")
    return destino


# ---------------------------------------------------------------------- Word
def _sombrear(celda, color_hex: str):
    tc = celda._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:color"), "auto")
    sh.set(qn("w:fill"), color_hex)
    tc.append(sh)


def _no_partir_filas(tabla):
    for fila in tabla.rows:
        tr = fila._tr.get_or_add_trPr()
        cant = OxmlElement("w:cantSplit")
        tr.append(cant)
    encabezado = tabla.rows[0]._tr.get_or_add_trPr()
    rep = OxmlElement("w:tblHeader")
    encabezado.append(rep)


def _tabla(doc, encabezados: list[str], filas: list[list], anchos: list[float] | None = None):
    t = doc.add_table(rows=1, cols=len(encabezados))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(encabezados):
        c = t.rows[0].cells[i]
        c.text = ""
        run = c.paragraphs[0].add_run(h)
        run.bold = True
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        _sombrear(c, "1F5F63")
    for fila in filas:
        celdas = t.add_row().cells
        for i, v in enumerate(fila):
            celdas[i].text = ""
            run = celdas[i].paragraphs[0].add_run(str(v))
            run.font.size = Pt(8.5)
            if str(v) in COLOR:
                run.bold = True
                run.font.color.rgb = RGBColor.from_string(COLOR[str(v)])
    if anchos:
        for fila in t.rows:
            for i, w in enumerate(anchos):
                fila.cells[i].width = Cm(w)
    _no_partir_filas(t)
    doc.add_paragraph()
    return t


def word(r: Reporte, max_ev_aprobados: int = 1) -> Path:
    doc = Document()
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21)
    sec.orientation = WD_ORIENT.PORTRAIT
    for lado in ("left_margin", "right_margin"):
        setattr(sec, lado, Cm(2.2))
    sec.top_margin = sec.bottom_margin = Cm(2)
    estilo = doc.styles["Normal"]
    estilo.font.name = "Calibri"
    estilo.font.size = Pt(10.5)

    ia, analisis = _extras(r)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("Reporte de ejecución de pruebas automatizadas")
    run.bold, run.font.size = True, Pt(20)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run("Fetal Medical Bolivia · Sistema de historia clínica obstétrica").font.size = Pt(12)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run(f"Corrida {r.run_id} · {r.datos['inicio'].replace('T', ' ')} · duración {r.duracion_legible}").italic = True

    doc.add_heading("1. Resumen", level=1)
    tot = r.totales
    _tabla(doc, ["Pruebas", "PASS", "FAIL", "BLOCKED", "NOT RUN", "Éxito sobre ejecutadas", "Casos (TC)"],
           [[tot["total"], tot["PASS"], tot["FAIL"], tot["BLOCKED"], tot["NOT RUN"], f"{r.tasa_exito} %",
             len(r.por_tc)]])
    cob = r.cobertura_catalogo
    doc.add_paragraph(f"Cobertura del catálogo: {cob['ejecutados']} de {cob['automatizables']} casos automatizables "
                      f"ejecutados ({cob['pct']} %); el catálogo tiene {cob['catalogo']} casos en total.")
    if ia:
        doc.add_paragraph(ia["resumen"])
        nota = doc.add_paragraph(f"Resumen redactado por IA ({ia['proveedor']}, {ia['modelo']}) a partir de los "
                                 "resultados; el estado de cada prueba lo decide su aserción, nunca la IA.")
        nota.runs[0].italic = True

    doc.add_heading("2. Ambiente", level=1)
    a = r.datos["ambiente"]
    _tabla(doc, ["Elemento", "Valor"], [["Sistema bajo prueba", a["sut_url"]], ["API", a["sut_api"]],
                                         ["Navegador", f"{a['navegador']}{' (headless)' if a['headless'] else ''}"],
                                         ["Equipo", a["so"]], ["Python", a["python"]],
                                         ["Suite", r.datos.get("suite") or "completa"]], [5, 11])

    doc.add_heading("3. Resultados por módulo", level=1)
    _tabla(doc, ["Módulo", "Pruebas", "PASS", "FAIL", "BLOCKED", "NOT RUN", "Éxito"],
           [[m["modulo"], m["total"], m["PASS"], m["FAIL"], m["BLOCKED"], m["NOT RUN"], f"{m['tasa']} %"]
            for m in r.por_modulo], [5.2, 1.6, 1.4, 1.4, 1.8, 1.8, 1.6])

    doc.add_heading("4. Casos de prueba", level=1)
    _tabla(doc, ["Caso", "Título", "Módulo", "Pruebas", "Tiempo", "Estado"],
           [[t["tc"], t["titulo"], t["modulo"], len(t["pruebas"]), f"{t['duracion_s']} s", t["estado"]]
            for t in sorted(r.por_tc.values(), key=lambda x: x["tc"])], [1.6, 7.0, 3.2, 1.4, 1.6, 1.8])

    doc.add_heading(f"5. Fallos ({len(r.fallos)})", level=1)
    if not r.fallos:
        doc.add_paragraph("No hubo fallos en esta corrida.")
    for c in r.fallos:
        doc.add_heading(f"{c['tc']} · {c['nombre']}", level=2)
        doc.add_paragraph(f"Módulo: {c['modulo']} · Clasificación: {c['clasificacion']}"
                          + (f" · Defectos: {', '.join(c['defectos'])}" if c["defectos"] else ""))
        err = doc.add_paragraph(c["error"][:1200])
        err.runs[0].font.size = Pt(8.5)
        if c["nodeid"] in analisis:
            doc.add_paragraph(f"Análisis IA: {analisis[c['nodeid']]['texto']}").runs[0].italic = True
        for ev in c["evidencias"]:
            ruta = r.dir_run / ev["archivo"]
            if ruta.exists() and ruta.suffix == ".png":
                doc.add_picture(str(ruta), width=Cm(15.5))
                cap = doc.add_paragraph(f"{ev['codigo']} — {ev.get('descripcion', '')}")
                cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                cap.runs[0].font.size = Pt(8)

    if r.rendimiento:
        doc.add_heading("6. Rendimiento (Locust)", level=1)
        _tabla(doc, ["Escenario", "Peticiones", "Errores", "p50", "p95", "p99", "Pet./s"],
               [[x["escenario"], x["peticiones"], f"{x['error_pct']} %", f"{x['p50_ms']:.0f} ms",
                 f"{x['p95_ms']:.0f} ms", f"{x['p99_ms']:.0f} ms", x["rps"]] for x in r.rendimiento])

    doc.add_heading("7. Defectos registrados", level=1)
    _tabla(doc, ["Defecto", "Título", "Severidad", "Estado", "Commit"],
           [[d["id"], d["titulo"], d["severidad"], d["estado"], d.get("commit") or "—"] for d in r.defectos],
           [1.8, 9.0, 1.8, 2.2, 2.0])

    doc.add_heading("8. Evidencias de casos aprobados", level=1)
    doc.add_paragraph(f"Una captura por caso aprobado (hasta {max_ev_aprobados}); el resto está en la carpeta "
                      "evidencias/ de la corrida con su código EV.")
    for t in sorted(r.por_tc.values(), key=lambda x: x["tc"]):
        if t["estado"] != "PASS":
            continue
        evs = [ev for p in t["pruebas"] for ev in p["evidencias"] if ev["archivo"].endswith(".png")][:max_ev_aprobados]
        for ev in evs:
            ruta = r.dir_run / ev["archivo"]
            if ruta.exists():
                doc.add_picture(str(ruta), width=Cm(13))
                cap = doc.add_paragraph(f"{ev['codigo']} — {t['tc']} {t['titulo']}")
                cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                cap.runs[0].font.size = Pt(8)

    destino = r.dir_run / "reporte.docx"
    doc.save(destino)
    return destino


def pdf(docx: Path) -> Path | None:
    """Convierte con Microsoft Word (COM). Devuelve None si Word no está disponible."""
    try:
        import pythoncom
        import win32com.client
    except ImportError:
        return None
    destino = docx.with_suffix(".pdf")
    pythoncom.CoInitialize()
    word_app = None
    try:
        word_app = win32com.client.DispatchEx("Word.Application")
        word_app.Visible = False
        word_app.DisplayAlerts = 0
        documento = word_app.Documents.Open(str(docx.resolve()), ReadOnly=True, AddToRecentFiles=False)
        documento.SaveAs2(str(destino.resolve()), FileFormat=17)
        documento.Close(False)
        return destino
    except Exception:
        return None
    finally:
        if word_app is not None:
            try:
                word_app.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()


def paquete(r: Reporte) -> Path:
    destino = r.dir_run / f"fetal_medical_{r.run_id}.zip"
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for f in r.dir_run.rglob("*"):
            if f.is_file() and f != destino and f.suffix != ".zip":
                z.write(f, f.relative_to(r.dir_run))
    return destino


def generar(run_id: str | None = None, con_pdf: bool = True) -> dict:
    r = cargar(run_id)
    salida = {"run_id": r.run_id, "html": html(r)}
    salida["docx"] = word(r)
    salida["pdf"] = pdf(salida["docx"]) if con_pdf else None
    salida["zip"] = paquete(r)
    return salida


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run")
    ap.add_argument("--sin-pdf", action="store_true")
    ap.add_argument("--correo", action="store_true", help="envía el reporte por correo (SMTP de .env)")
    a = ap.parse_args()
    s = generar(a.run, not a.sin_pdf)
    for k, v in s.items():
        print(f"{k}: {v}")
    if a.correo:
        from reporting.correo import enviar
        print(enviar(s["run_id"]))


if __name__ == "__main__":
    principal()
