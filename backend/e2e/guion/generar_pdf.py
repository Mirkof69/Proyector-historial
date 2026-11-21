"""Arma el PDF del guion paso a paso con las capturas de capturar_guion.js.

    python guion/generar_pdf.py        (cwd = backend/e2e; antes: node guion/capturar_guion.js)

Una página por paso: la captura con los recuadros rojos numerados, qué tocar
(los números coinciden con los recuadros), qué escribir y qué decir. Deja
GUION_PASO_A_PASO.pdf en Escritorio/MUESTRAS_IA_Fetal_Medical.
"""
from __future__ import annotations

import html
import importlib.util
import json
import os
import subprocess
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / "salida"
RAIZ = AQUI.parents[2]
MUESTRAS = Path(os.environ["USERPROFILE"]) / "Desktop" / "MUESTRAS_IA_Fetal_Medical"
e = html.escape

CUENTAS = {"dra.garcia": ("Médica", "dra.garcia@fetalmedical.bo"),
           "enf.mamani": ("Enfermera", "enf.mamani@fetalmedical.bo"),
           "admin.demo": ("Administrador", "admin.demo@fetalmedical.bo")}

EVITAR = [
    ("Presión 139/89", "no avisa de prehipertensión (BUG-003)"),
    ("IMC exactamente 25 o 30", "lo clasifica mal (BUG-005)"),
    ("Bishop 5 en la calculadora rápida", "lo muestra como «intermedio» (BUG-006)"),
    ("Escribir a mano un resultado de laboratorio o abrir el detalle del examen",
     "no se guarda o la pantalla falla (BUG-007/008); usa la importación del paso del laboratorio"),
    ("Peso del recién nacido menor de 400 g", "se recorta sin avisar (BUG-009/010)"),
    ("Tamaño de píxel 0 o vacío al medir", "se reemplaza sin avisar (BUG-011)"),
]

PREGUNTAS = [
    ("¿Qué es una red neuronal convolucional?",
     "Una red que aprende filtros sobre la imagen: las primeras capas detectan bordes, las siguientes formas y las "
     "últimas estructuras como el cráneo. Aprende de miles de ecografías etiquetadas por especialistas."),
    ("¿Qué diferencia hay entre clasificación, segmentación y regresión?",
     "Clasificación dice qué es (plano, tipo de lesión). Segmentación (U-Net) pinta pixel a pixel dónde está y sobre "
     "esa silueta se mide. Regresión devuelve directamente un número (la circunferencia en mm)."),
    ("¿Y el machine learning que no es red neuronal?",
     "La cardiotocografía usa gradient boosting y el peso al nacer usa regresión Ridge: aprendizaje supervisado sobre "
     "tablas de números con la respuesta correcta, no sobre imágenes."),
    ("¿Cómo sabe que funciona?",
     "Cada modelo se midió en pacientes que no vio al entrenar, separando por paciente. Las cifras viajan en cada "
     "respuesta y se muestran en la Guía de IA."),
    ("¿Qué pasa si la IA se equivoca?",
     "Siempre muestra su margen de error y avisos; es apoyo, no diagnóstico. La carpeta de muestras deja a la vista "
     "también los casos en que no concuerda con el experto."),
    ("¿Qué pasa si escribo un dato imposible?",
     "El sistema lo rechaza y explica por qué, como la altura uterina de 33 cm a las 39 semanas del paso del control."),
]


def flujo_svg() -> str:
    """El diagrama del flujo de negocio es el mismo del guion resumido (docs/entregables/demostracion)."""
    ruta = RAIZ / "docs" / "entregables" / "demostracion" / "generar_guion.py"
    spec = importlib.util.spec_from_file_location("generar_guion", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo.svg_flujo()


def pagina_paso(p: dict, total: int) -> str:
    rol, correo = CUENTAS.get(p.get("cuenta", ""), ("", ""))
    clics = "".join(f"<li><span class='num'>{i}</span>{e(c)}</li>" for i, c in enumerate(p.get("clics", []), 1))
    escribir = "".join(f"<tr><th>{e(c)}</th><td>{e(str(v))}</td></tr>" for c, v in p.get("escribir", []) if v)
    nota = f"<div class='nota'><b>Cuidado:</b> {e(p['nota'])}</div>" if p.get("nota") else ""
    return f"""
<section class="paso">
  <header><span class="n">Paso {int(p['n'])} de {total}</span><span class="sec">{e(p['seccion'])}</span>
    <span class="cuenta" title="{e(correo)}">{e(rol)} · {e(p.get('cuenta', ''))}</span></header>
  <h2>{e(p['titulo'])}</h2>
  <div class="captura"><img src="capturas/{p['n']}.png" alt="Captura del paso {int(p['n'])}"></div>
  <div class="cols">
    <div class="hacer"><h3>Qué hacer</h3><ol>{clics}</ol>
      {f"<h3>Qué escribir</h3><table>{escribir}</table>" if escribir else ""}</div>
    <div class="decir"><h3>Qué decir</h3><p>«{e(p['decir'])}»</p>{nota}</div>
  </div>
</section>"""


def construir() -> str:
    datos = json.loads((SALIDA / "pasos.json").read_text(encoding="utf-8"))
    pasos, pac = datos["pasos"], datos["paciente"]
    indice, actual = [], None
    for p in pasos:
        if p["seccion"] != actual:
            actual = p["seccion"]
            indice.append(f"<li><b>{e(actual)}</b> <span>desde el paso {int(p['n'])}</span></li>")
    evitar = "".join(f"<tr><td>{e(a)}</td><td>{e(b)}</td></tr>" for a, b in EVITAR)
    preguntas = "".join(f"<dt>{e(a)}</dt><dd>{e(b)}</dd>" for a, b in PREGUNTAS)
    plantilla = (AQUI / "plantilla_pdf.html").read_text(encoding="utf-8")
    return (plantilla
            .replace("{{PACIENTE}}", e(f"{pac['nombre']} {pac['apellido_paterno']} {pac['apellido_materno']}"))
            .replace("{{CI}}", e(pac["ci"])).replace("{{NACIMIENTO}}", e(pac["fecha_nacimiento"]))
            .replace("{{TELEFONO}}", e(pac["telefono"])).replace("{{CIUDAD}}", e(pac["ciudad"]))
            .replace("{{FLUJO}}", flujo_svg()).replace("{{INDICE}}", "".join(indice))
            .replace("{{PASOS}}", "".join(pagina_paso(p, len(pasos)) for p in pasos))
            .replace("{{TOTAL}}", str(len(pasos))).replace("{{EVITAR}}", evitar).replace("{{PREGUNTAS}}", preguntas))


def main():
    destino = SALIDA / "guion_paso_a_paso.html"
    destino.write_text(construir(), encoding="utf-8")
    pdf = MUESTRAS / "GUION_PASO_A_PASO.pdf"
    a_pdf = RAIZ / "docs" / "entregables" / "demostracion" / "a_pdf.js"
    subprocess.run(["node", str(a_pdf), str(destino), str(pdf)], check=True, cwd=AQUI.parent)
    print("Listo:", pdf)


if __name__ == "__main__":
    main()
