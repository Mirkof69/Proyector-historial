r"""Figuras del Capítulo 6: diagramas, gráficos con los datos reales de la corrida y capturas.

    .venv\Scripts\python -m capitulo6.figuras --run 20261114-105512 [--retest ID]

Todo sale de archivos generados por ejecuciones reales (results.json, cobertura.json, resúmenes de Locust,
registro de ejecución). Las capturas del panel y de los reportes se toman con Selenium.
"""
from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from reporting.modelo import cargar  # noqa: E402
from utils import config  # noqa: E402

RAIZ = config.RAIZ
SALIDA = RAIZ / "capitulo6" / "imagenes"
AZUL, VERDE, ROJO, AMBAR, GRIS, TINTA = "#1F3864", "#1E7F4F", "#B3261E", "#C77700", "#6B7280", "#1B2A2C"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 200, "savefig.bbox": "tight"})


# ---------------------------------------------------------------------- texto como imagen (consola, código, árbol)
def texto_a_imagen(lineas: list[str], destino: Path, ancho_car: int = 118, oscuro: bool = True, tam: int = 17):
    try:
        fuente = ImageFont.truetype("consola.ttf", tam)
    except OSError:
        fuente = ImageFont.load_default()
    filas = []
    for linea in lineas:
        linea = linea.rstrip("\n").replace("\t", "    ")
        filas += textwrap.wrap(linea, ancho_car, subsequent_indent="    ", replace_whitespace=False,
                               drop_whitespace=False) or [""]
    alto_linea = tam + 6
    ancho = int(fuente.getlength("M" * ancho_car)) + 40
    img = Image.new("RGB", (ancho, alto_linea * len(filas) + 36), "#0F1718" if oscuro else "#FFFFFF")
    d = ImageDraw.Draw(img)
    for i, fila in enumerate(filas):
        color = "#D6E4E4" if oscuro else "#1B2A2C"
        if "PASSED" in fila or " passed" in fila or "PASS" in fila.split():
            color = "#5FD39A" if oscuro else VERDE
        if "FAILED" in fila or " failed" in fila or "FAIL" in fila.split():
            color = "#FF8A80" if oscuro else ROJO
        if fila.startswith("==") or fila.lstrip().startswith(("#", '"""')):
            color = "#5CC2C8" if oscuro else AZUL
        d.text((20, 18 + i * alto_linea), fila, font=fuente, fill=color)
    destino.parent.mkdir(parents=True, exist_ok=True)
    img.save(destino, dpi=(200, 200))
    return destino


# ---------------------------------------------------------------------- diagramas
def _caja(ax, x, y, w, h, texto, color=AZUL, tam=8.5, relleno=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", linewidth=1.4,
                                edgecolor=color, facecolor=relleno or "#EEF5FC"))
    ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center", fontsize=tam, color=TINTA, linespacing=1.35)


def _flecha(ax, a, b, texto="", color=GRIS, curva=0.0):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=13, linewidth=1.2, color=color,
                                 connectionstyle=f"arc3,rad={curva}"))
    if texto:
        ax.text((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 0.13, texto, ha="center", va="bottom", fontsize=7.2, color=GRIS)


def arquitectura():
    fig, ax = plt.subplots(figsize=(11.5, 7.2))
    ax.set_xlim(0, 12), ax.set_ylim(0, 7.6), ax.axis("off")
    _caja(ax, 0.2, 5.9, 2.0, 1.1, "Analista QA", GRIS, relleno="#F3F4F6")
    _caja(ax, 3.0, 5.9, 2.6, 1.1, "Panel web de ejecución\nrunner_web (FastAPI :8090)\nsuite · navegador · registro en vivo", AZUL)
    _caja(ax, 6.4, 5.9, 2.5, 1.1, "pytest 9.2 + conftest.py\nfixtures por rol · resultados\nevidencias EV", AZUL)
    _caja(ax, 9.6, 5.9, 2.2, 1.1, "data/\ncatálogo de casos\nfábrica de datos QA", GRIS, relleno="#F3F4F6")
    _flecha(ax, (2.2, 6.45), (3.0, 6.45), "elige suite")
    _flecha(ax, (5.6, 6.45), (6.4, 6.45), "lanza")
    _flecha(ax, (9.6, 6.45), (8.9, 6.45), "datos")
    y = 3.9
    cajas = [("tests/ui\nSelenium WebDriver 4.52\nPage Object Model", 0.2), ("tests/api\npytest + requests\npermisos · clínica · IA", 3.15),
             ("tests/ide\nSelenium IDE (.side)\nselenium-side-runner", 6.1), ("tests/rendimiento\nLocust 2.47\ncarga · estrés · pico", 9.05)]
    for texto, x in cajas:
        _caja(ax, x, y, 2.75, 1.15, texto, VERDE, relleno="#EAF6EF")
        _flecha(ax, (7.65, 5.9), (x + 1.37, y + 1.15))
    _caja(ax, 0.2, 2.25, 2.75, 0.9, "pages/ · components/\nPage Objects y menú", VERDE, relleno="#EAF6EF")
    _flecha(ax, (1.57, 3.9), (1.57, 3.15))
    _caja(ax, 3.4, 0.35, 5.2, 1.25, "SISTEMA BAJO PRUEBA · Fetal Medical Bolivia\nReact :3000 · API Django REST :8000 · IA FastAPI :8001\n"
                                    "PostgreSQL · Redis · 5 roles", ROJO, 9, "#FCEDED")
    for x in (1.57, 4.52, 7.47, 10.42):
        _flecha(ax, (x, 2.25 if x == 1.57 else 3.9), (6.0 + (x - 6.0) * 0.35, 1.6), color=ROJO)
    _caja(ax, 9.35, 2.0, 2.45, 1.25, "reports/<corrida>/\nresults.json\ncapturas EV · Locust", AMBAR, relleno="#FFF4E0")
    _flecha(ax, (8.9, 5.95), (10.6, 3.25), "resultados", AMBAR, -0.25)
    _caja(ax, 9.35, 0.25, 2.45, 1.25, "reporting/ + ai/\nHTML · Word · PDF · ZIP\nresumen IA · correo", AMBAR, relleno="#FFF4E0")
    _flecha(ax, (10.57, 2.0), (10.57, 1.5), color=AMBAR)
    fig.savefig(SALIDA / "arquitectura.png")
    plt.close(fig)


def flujo():
    pasos = ["Selección de\nsuite y navegador", "Preparación:\nsesión por rol y\ndatos sintéticos QA", "Ejecución del\nscript (UI, API,\nIDE o Locust)",
             "Aserciones:\nPASS / FAIL", "Evidencias EV\n(captura, consola,\nHTML al fallar)", "results.json\ny reportes HTML,\nWord, PDF, ZIP",
             "IA: resumen y\nanálisis (opcional)\ny correo", "Limpieza de\nlos datos QA"]
    fig, ax = plt.subplots(figsize=(11.5, 3.6))
    ax.set_xlim(0, 12), ax.set_ylim(0, 3.6), ax.axis("off")
    for i, texto in enumerate(pasos):
        fila, col = divmod(i, 4)
        x = 0.2 + col * 2.95 if fila == 0 else 0.2 + (3 - col) * 2.95
        y = 2.05 if fila == 0 else 0.3
        _caja(ax, x, y, 2.5, 1.15, f"{i + 1}. {texto}", AZUL if i not in (3, 7) else VERDE, 8.4,
              "#EEF5FC" if i not in (3, 7) else "#EAF6EF")
        if i in (0, 1, 2):
            _flecha(ax, (x + 2.5, y + 0.57), (x + 2.95, y + 0.57))
        if i == 3:
            _flecha(ax, (x + 1.25, y), (x + 1.25, 1.45))
        if i in (4, 5, 6):
            _flecha(ax, (x, y + 0.57), (x - 0.45, y + 0.57))
    fig.savefig(SALIDA / "flujo_ejecucion.png")
    plt.close(fig)


def arbol():
    lineas = """automatizacion/
├── config/config.yaml          configuración no secreta (URL, navegador, esperas)
├── .env.example                variables con valores ficticios (el .env real no se versiona)
├── conftest.py                 fixtures por rol, resultados y evidencias
├── pytest.ini                  marcadores: smoke, regression, roles, pacientes, ...
├── pages/                      base_page, login_page, pacientes_page, formularios_clinicos, pantalla_page
├── components/                 menu_lateral
├── tests/
│   ├── ui/                     autenticación, pacientes, flujo clínico, roles y pantallas, barrido, regresión
│   ├── api/                    auth, permisos, pacientes, historia clínica, ecografía e IA, clínica, citas, robustez
│   ├── ide/                    reproduce las grabaciones de Selenium IDE
│   └── rendimiento/            Locust: carga, estrés, pico, resistencia
├── selenium_ide/               TC-109, TC-110, TC-111 (.side)
├── locust/locustfile.py        usuarios virtuales por rol
├── data/                       catalogo_tc, fabrica, defectos, imagenes_ia/
├── utils/                      config, driver_factory, api_client, totp, evidencias
├── reporting/                  modelo, generar (HTML, Word, PDF, ZIP), correo, plantillas/
├── ai/                         anonimizador, proveedor_ollama, proveedor_claude, servicio, tareas
├── runner_web/                 app (FastAPI), plantillas/panel.html, historial.sqlite3
├── tools/                      inventario, explorer, sonda_dom, generar_side, ejecutar_side, exportar_casos
├── docs/                       inventario/, defectos/, casos_prueba.xlsx, matriz_trazabilidad.md, decisiones.md
├── capitulo6/                  fuente, figuras y generador de este capítulo
└── reports/<corrida>/          results.json, evidencias/, locust/, reporte.html, .docx, .pdf, .zip""".splitlines()
    texto_a_imagen(lineas, SALIDA / "arbol.png", 112, oscuro=False, tam=16)


# ---------------------------------------------------------------------- gráficos
def graficos(run_id: str):
    r = cargar(run_id)
    cob = json.loads((RAIZ / "docs" / "cobertura.json").read_text(encoding="utf-8"))

    mods = sorted(r.por_modulo, key=lambda m: m["total"])
    fig, ax = plt.subplots(figsize=(8.6, 0.36 * len(mods) + 1.4))
    izq = [0] * len(mods)
    for estado, color in (("PASS", VERDE), ("FAIL", ROJO), ("BLOCKED", AMBAR), ("NOT RUN", GRIS)):
        vals = [m[estado] for m in mods]
        ax.barh([m["modulo"] for m in mods], vals, left=izq, color=color, label=estado, height=0.62)
        izq = [a + b for a, b in zip(izq, vals)]
    for i, m in enumerate(mods):
        ax.text(izq[i] + max(izq) * 0.01, i, str(m["total"]), va="center", fontsize=8.5, color=TINTA)
    ax.set_xlabel("Pruebas ejecutadas")
    ax.legend(ncol=4, frameon=False, loc="lower right", fontsize=8.5)
    fig.savefig(SALIDA / "g_modulos.png")
    plt.close(fig)

    est = cob["estados_tc"]
    orden = [("PASS", VERDE), ("FAIL", ROJO), ("BLOCKED", AMBAR), ("NOT RUN", GRIS), ("MANUAL", AZUL)]
    fig, ax = plt.subplots(figsize=(6.6, 3.3))
    barras = ax.bar([e for e, _ in orden], [est.get(e, 0) for e, _ in orden], color=[c for _, c in orden], width=0.6)
    ax.bar_label(barras, fontsize=10)
    ax.set_ylabel("Casos de prueba")
    fig.savefig(SALIDA / "g_estados_tc.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.6, 3.2))
    datos = [("Diseñados", cob["casos_diseñados"], AZUL), ("Seleccionados\npara automatizar", cob["seleccionados_automatizar"], "#2F5597"),
             ("Automatizados", cob["automatizados"], VERDE), ("Manuales", cob["manuales"], GRIS)]
    barras = ax.bar([d[0] for d in datos], [d[1] for d in datos], color=[d[2] for d in datos], width=0.6)
    ax.bar_label(barras, fontsize=10)
    ax.set_ylabel("Casos de prueba")
    fig.savefig(SALIDA / "g_cobertura.png")
    plt.close(fig)

    sev = {}
    for d in r.defectos:
        sev.setdefault(d["severidad"], []).append(d)
    orden_sev = [s for s in ("Crítica", "Alta", "Media", "Baja") if s in sev]
    fig, ax = plt.subplots(figsize=(6.6, 3.2))
    cerrados = [sum(d["estado"] in ("Verificado", "Cerrado", "Corregido") for d in sev[s]) for s in orden_sev]
    abiertos = [len(sev[s]) - c for s, c in zip(orden_sev, cerrados)]
    b1 = ax.bar(orden_sev, cerrados, color=VERDE, label="Corregidos y verificados", width=0.55)
    b2 = ax.bar(orden_sev, abiertos, bottom=cerrados, color=AMBAR, label="Abiertos o parciales", width=0.55)
    ax.bar_label(b1, labels=[str(v) if v else "" for v in cerrados], label_type="center", color="white", fontsize=10)
    ax.bar_label(b2, labels=[str(v) if v else "" for v in abiertos], label_type="center", fontsize=10)
    ax.set_ylabel("Defectos"), ax.legend(frameon=False, fontsize=8.5)
    ax.yaxis.get_major_locator().set_params(integer=True)
    fig.savefig(SALIDA / "g_defectos.png")
    plt.close(fig)

    carga = next((x for x in r.rendimiento if x["escenario"] == "carga"), None)
    if carga:
        eps = sorted(carga["por_endpoint"], key=lambda e: e["p95_ms"])
        fig, ax = plt.subplots(figsize=(8.6, 0.34 * len(eps) + 1.3))
        barras = ax.barh([e["nombre"].replace("/api", "") for e in eps], [e["p95_ms"] for e in eps], color=AZUL, height=0.6)
        ax.bar_label(barras, labels=[f"{e['p95_ms']:.0f} ms" for e in eps], padding=3, fontsize=8.5)
        ax.axvline(2000, color=ROJO, linestyle="--", linewidth=1)
        ax.text(2000, len(eps) - 0.4, " criterio: 2 000 ms", color=ROJO, fontsize=8.5, va="bottom", ha="right")
        ax.set_xlabel("Percentil 95 del tiempo de respuesta (ms)")
        ax.set_xlim(0, 2150)
        fig.savefig(SALIDA / "g_p95.png")
        plt.close(fig)
        hist = r.dir_run / "locust" / "carga_stats_history.csv"
        if hist.exists():
            import csv
            filas = [f for f in csv.DictReader(open(hist, encoding="utf-8")) if f["Name"] == "Aggregated"]
            t0 = int(filas[0]["Timestamp"])
            t = [int(f["Timestamp"]) - t0 for f in filas]
            fig, ax = plt.subplots(figsize=(8.6, 3.3))
            ax.plot(t, [float(f["95%"] or 0) if f["95%"] != "N/A" else 0 for f in filas], color=AZUL, label="p95 (ms)")
            ax.plot(t, [float(f["50%"] or 0) if f["50%"] != "N/A" else 0 for f in filas], color=VERDE, label="mediana (ms)")
            ax.set_xlabel("Segundos desde el inicio"), ax.set_ylabel("Tiempo de respuesta (ms)")
            ax2 = ax.twinx()
            ax2.spines["right"].set_visible(True)
            ax2.plot(t, [int(f["User Count"]) for f in filas], color=AMBAR, linestyle="--", label="usuarios")
            ax2.set_ylabel("Usuarios concurrentes")
            lineas = ax.get_lines() + ax2.get_lines()
            ax.legend(lineas, [x.get_label() for x in lineas], frameon=False, fontsize=8.5, loc="upper center", ncol=3)
            fig.savefig(SALIDA / "g_carga_tiempo.png")
            plt.close(fig)


# ---------------------------------------------------------------------- capturas
def capturas(run_id: str):
    from selenium.webdriver.support.ui import WebDriverWait

    from utils.driver_factory import crear_driver
    d = crear_driver()
    try:
        d.set_window_size(1440, 1000)
        usuario, clave = config.env("RUNNER_USER"), config.env("RUNNER_PASSWORD")
        d.get(f"http://{usuario}:{clave}@127.0.0.1:8090/")
        WebDriverWait(d, 15).until(lambda x: "Panel de pruebas" in x.title)
        d.save_screenshot(str(SALIDA / "panel_web.png"))
        d.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        d.save_screenshot(str(SALIDA / "panel_historial.png"))
        d.get(f"http://127.0.0.1:8090/corrida/{run_id}/reporte.html")
        WebDriverWait(d, 15).until(lambda x: "Ejecución" in x.title)
        d.save_screenshot(str(SALIDA / "reporte_html.png"))
        d.execute_script("document.querySelector('#casos').scrollIntoView()")
        d.save_screenshot(str(SALIDA / "reporte_html_casos.png"))
        locust = RAIZ / "reports" / run_id / "locust" / "carga.html"
        if locust.exists():
            d.get(locust.as_uri())
            WebDriverWait(d, 20).until(lambda x: x.execute_script("return document.readyState") == "complete"
                                       and len(x.find_element("tag name", "body").text) > 200)
            d.save_screenshot(str(SALIDA / "locust_html.png"))
    finally:
        d.quit()
    pdf = RAIZ / "reports" / run_id / "reporte.pdf"
    if pdf.exists():
        import fitz
        fitz.open(pdf)[0].get_pixmap(dpi=110).save(SALIDA / "reporte_pdf.png")


def consolas(run_id: str, retest: str | None):
    registro = (RAIZ / "reports" / run_id / "ejecucion.log").read_text(encoding="utf-8").splitlines()
    cabeza = [x for x in registro[:60] if x.strip()][:26]
    cola = [x for x in registro if x.strip()][-22:]
    texto_a_imagen(cabeza, SALIDA / "consola_inicio.png", 128, tam=15)
    texto_a_imagen(cola, SALIDA / "consola_fin.png", 128, tam=15)
    side = RAIZ / "reports" / run_id / "evidencias" / "EV-TC-109-side-runner.txt"
    if side.exists():
        lineas = [x for x in side.read_text(encoding="utf-8").splitlines() if x.strip() and "Deprecation" not in x
                  and "trace-deprecation" not in x and not x.strip().startswith("at ")][:24]
        texto_a_imagen(lineas, SALIDA / "consola_side.png", 130, tam=15)
    if retest and (RAIZ / "reports" / retest / "ejecucion.log").exists():
        lineas = [x for x in (RAIZ / "reports" / retest / "ejecucion.log").read_text(encoding="utf-8").splitlines() if x.strip()]
        texto_a_imagen(lineas[:8] + ["   ..."] + lineas[-16:], SALIDA / "consola_retest.png", 128, tam=15)
    codigo = (RAIZ / "pages" / "login_page.py").read_text(encoding="utf-8").splitlines()[12:60]
    texto_a_imagen(codigo, SALIDA / "codigo_pom.png", 104, oscuro=False, tam=15)
    prueba = (RAIZ / "tests" / "ui" / "test_flujo_clinico_ui.py").read_text(encoding="utf-8").splitlines()
    ini = next(i for i, x in enumerate(prueba) if "TC-040" in x) - 1
    texto_a_imagen(prueba[ini:ini + 20], SALIDA / "codigo_prueba.png", 104, oscuro=False, tam=15)
    busc = (RAIZ / "tests" / "ui" / "test_buscadores_ui.py").read_text(encoding="utf-8").splitlines()
    ini = next(i for i, x in enumerate(busc) if "def test_tc171" in x)
    fin = next(i for i, x in enumerate(busc) if "    finally:" in x and i > ini)
    texto_a_imagen(busc[ini:fin], SALIDA / "codigo_localizadores.png", 118, oscuro=False, tam=14)
    loc = (RAIZ / "locust" / "locustfile.py").read_text(encoding="utf-8").splitlines()
    ini = next(i for i, x in enumerate(loc) if x.startswith("class UsuarioClinica"))
    fin = next(i for i, x in enumerate(loc) if x.startswith("class Medico"))
    texto_a_imagen(loc[ini:fin], SALIDA / "codigo_locust.png", 104, oscuro=False, tam=15)


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--retest")
    ap.add_argument("--sin-capturas", action="store_true")
    a = ap.parse_args()
    SALIDA.mkdir(parents=True, exist_ok=True)
    arquitectura(), flujo(), arbol()
    graficos(a.run)
    consolas(a.run, a.retest)
    if not a.sin_capturas:
        capturas(a.run)
    print("figuras en", SALIDA, len(list(SALIDA.glob("*.png"))))


if __name__ == "__main__":
    principal()
