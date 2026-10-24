"""Genera el guion de la demostración (HTML → PDF con Chromium de Playwright).

    python docs/entregables/demostracion/generar_guion.py

Lee los resultados en vivo de Desktop/MUESTRAS_IA_Fetal_Medical (los deja
Backend/scripts/muestras_ia.py) y escribe GUION_DEMOSTRACION.pdf en esa carpeta.
"""
from __future__ import annotations

import html
import os
import re
import subprocess
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MUESTRAS = Path(os.environ["USERPROFILE"]) / "Desktop" / "MUESTRAS_IA_Fetal_Medical"
E2E = AQUI.parents[2] / "Backend" / "e2e"
e = html.escape

# ── Flujo de negocio: carriles por rol ────────────────────────────────────────
CARRILES = ["Recepción", "Enfermería", "Médica / médico", "Sistema e IA"]
# (fila, carril, título, detalle)
PASOS = [
    (0, 0, "1 · Registra o busca a la paciente", "datos personales cifrados"),
    (1, 0, "2 · Agenda la cita", "Agenda de Citas"),
    (2, 1, "3 · Triaje", "signos vitales y prioridad"),
    (3, 2, "4 · Historia clínica", "antecedentes y embarazos previos"),
    (4, 2, "5 · Abre el embarazo", "FUM → edad gestacional, FPP, riesgo"),
    (5, 2, "6 · Control prenatal", "PA, altura uterina, FCF, peso"),
    (5, 3, "Alertas automáticas", "PA alta, valores fuera de rango"),
    (6, 2, "7 · Ecografía", "sube la imagen"),
    (6, 3, "13 redes CNN", "plano → red del plano → medidas → EG"),
    (7, 2, "8 · Laboratorio", "resultados de exámenes"),
    (7, 3, "Valor crítico → alerta", "llega a Alertas Médicas"),
    (8, 2, "9 · Trabajo de parto", "partograma y tactos"),
    (8, 3, "IA intraparto y CTG", "ángulo de progresión · gradient boosting"),
    (9, 2, "10 · Parto y recién nacido", "registro del parto, RN, epicrisis"),
    (10, 3, "11 · Reportes y auditoría", "PDF, registro de quién hizo qué"),
]
FLECHAS = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (5, 7), (7, 8), (7, 9), (9, 10), (9, 11), (11, 12),
           (11, 13), (13, 14)]
COLOR = ["#7c5c1e", "#1f6f5c", "#1d4e89", "#6b3fa0"]


def svg_flujo() -> str:
    ancho, col, x0, y0, alto_fila, caja_w, caja_h = 760, 190, 0, 46, 62, 172, 46
    filas = max(p[0] for p in PASOS) + 1
    alto = y0 + filas * alto_fila + 70
    out = [f'<svg viewBox="0 0 {ancho} {alto}" class="flujo" role="img" aria-label="Flujo de negocio por rol">',
           '<defs><marker id="pt" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
           'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#5b6470"/></marker></defs>']
    for i, nombre in enumerate(CARRILES):
        x = x0 + i * col
        out.append(f'<rect x="{x + 2}" y="0" width="{col - 4}" height="{alto - 64}" rx="6" fill="{COLOR[i]}" '
                   f'fill-opacity="0.06" stroke="{COLOR[i]}" stroke-opacity="0.35"/>')
        out.append(f'<text x="{x + col / 2}" y="26" text-anchor="middle" class="carril" fill="{COLOR[i]}">{e(nombre)}</text>')
    pos = []
    for fila, carril, titulo, detalle in PASOS:
        cx = x0 + carril * col + (col - caja_w) / 2
        cy = y0 + fila * alto_fila
        pos.append((cx, cy))
        out.append(f'<rect x="{cx}" y="{cy}" width="{caja_w}" height="{caja_h}" rx="5" fill="#fff" '
                   f'stroke="{COLOR[carril]}" stroke-width="1.4"/>')
        out.append(f'<text x="{cx + 8}" y="{cy + 19}" class="t">{e(titulo)}</text>')
        out.append(f'<text x="{cx + 8}" y="{cy + 35}" class="d">{e(detalle)}</text>')
    for a, b in FLECHAS:
        (ax, ay), (bx, by) = pos[a], pos[b]
        if ay == by:  # misma fila: horizontal
            out.append(f'<line x1="{ax + caja_w}" y1="{ay + caja_h / 2}" x2="{bx - 3}" y2="{by + caja_h / 2}" '
                       'class="fl" marker-end="url(#pt)"/>')
        else:  # baja: sale por abajo y entra por arriba (codo si cambia de carril)
            x1, y1, x2, y2 = ax + caja_w / 2, ay + caja_h, bx + caja_w / 2, by - 3
            ym = y1 + (y2 - y1) / 2
            out.append(f'<path d="M{x1},{y1} L{x1},{ym} L{x2},{ym} L{x2},{y2}" class="fl" marker-end="url(#pt)"/>')
    ya = alto - 54
    out.append(f'<rect x="2" y="{ya}" width="{ancho - 4}" height="48" rx="6" fill="#3a3f47" fill-opacity="0.07" '
               'stroke="#3a3f47" stroke-opacity="0.4" stroke-dasharray="4 3"/>')
    out.append(f'<text x="14" y="{ya + 20}" class="t">Administrador (transversal a todo el flujo)</text>')
    out.append(f'<text x="14" y="{ya + 37}" class="d">usuarios · cargos y permisos por rol · verificación en dos pasos '
               '(MFA) · logs de acceso · configuración · respaldo</text>')
    out.append("</svg>")
    return "".join(out)


# ── Guion paso a paso ──────────────────────────────────────────────────────────
# (cuenta, pantalla / ruta del menú, qué hacer, qué decir)
GUION = [
    ("dra.garcia", "Inicio de sesión", "Entrar con la cuenta de la médica.",
     "«Cada usuario tiene un rol; el sistema solo le muestra lo que ese rol puede usar. Hay verificación en dos pasos y "
     "bloqueo tras 5 intentos fallidos.»"),
    ("dra.garcia", "Panel Principal", "Mostrar indicadores del día y las alertas pendientes.",
     "«Es lo primero que ve el personal: cuántas pacientes, controles y alertas tiene hoy.»"),
    ("dra.garcia", "Herramientas → Agenda de Citas", "Mostrar las citas del día (paso 1-2 del flujo).",
     "«Recepción registra a la paciente y le agenda la cita. Recepción no ve datos clínicos: solo citas y el listado.»"),
    ("dra.garcia", "Gestión Clínica → Pacientes", "Buscar una paciente y abrir su ficha.",
     "«El nombre y el documento se guardan cifrados en la base; la búsqueda funciona sin descifrarlos.»"),
    ("dra.garcia", "Gestión Clínica → Triaje", "Mostrar un triaje registrado (paso 3).",
     "«Enfermería toma signos vitales y asigna prioridad antes de que la paciente pase con la médica.»"),
    ("dra.garcia", "Historial Clínico", "Abrir la historia completa de la paciente (paso 4).",
     "«Todo en una sola vista: antecedentes, embarazos, controles, ecografías, laboratorio y partos.»"),
    ("dra.garcia", "Gestión Clínica → Embarazos", "Abrir un embarazo (paso 5).",
     "«Con la fecha de última menstruación el sistema calcula la edad gestacional, la fecha probable de parto y el riesgo.»"),
    ("dra.garcia", "Gestión Clínica → Controles Prenatales → Nuevo", "Registrar un control: PA 120/80, altura uterina "
     "30 cm. Para mostrar una alerta: PA 160/110 (paso 6).",
     "«Si un valor sale de rango, el sistema genera una alerta médica automáticamente.»"),
    ("dra.garcia", "Estudios Auxiliares → Análisis CNN (IA) → Ecografía", "Subir las muestras de 01 a 08 (ver la tabla de "
     "IA en vivo). Para medir, escribir el tamaño de píxel que trae RESULTADO.txt (paso 7).",
     "«Primero una red reconoce el plano; luego la red de ese plano mide; el sistema pasa de píxeles a milímetros y "
     "calcula la edad gestacional con Hadlock. Siempre muestra el margen de error.»"),
    ("dra.garcia", "Análisis CNN (IA) → Ecografía ginecológica", "Masa ovárica, Mioma y Ovario poliquístico con las "
     "carpetas 10, 11 y 12.",
     "«En ginecología la IA orienta; la masa ovárica no sirve como tamizaje de cáncer y el sistema lo dice en pantalla.»"),
    ("dra.garcia", "Análisis CNN (IA) → Cardiotocografía", "Copiar los 21 valores de 13_cardiotocografia/"
     "ctg_patológica.txt y pulsar Clasificar.",
     "«Este no es una red neuronal: es aprendizaje supervisado sobre una tabla de 21 variables del monitoreo fetal.»"),
    ("dra.garcia", "Estudios Auxiliares → Guía de IA", "Recorrer la guía: cada modelo con su cifra y sus límites; abajo, "
     "los descartados.",
     "«No subimos ningún modelo que no alcanzara un rendimiento aceptable en pacientes que no vio al entrenar.»"),
    ("dra.garcia", "Estudios Auxiliares → Laboratorio", "Mostrar el listado y resultados ya cargados (paso 8).",
     "«Un valor crítico de laboratorio genera una alerta para la médica tratante.»"),
    ("dra.garcia", "Gestión Clínica → Partos → abrir un parto → Trabajo de parto", "Mostrar el partograma; Registrar "
     "tacto → subir 09_unet_intraparto/intraparto_1.png (paso 9).",
     "«La U-Net encuentra la sínfisis del pubis y la cabeza fetal y mide el ángulo de progresión: cuanto mayor, más "
     "descendida está la cabeza.»"),
    ("dra.garcia", "Partos → recién nacido y epicrisis", "Mostrar el registro del recién nacido y la epicrisis (paso 10).",
     "«El parto cierra el ciclo: recién nacido, APGAR y el resumen de alta.»"),
    ("dra.garcia", "Herramientas → Calculadoras · Centro de reportes · Alertas Médicas",
     "Una calculadora (IMC 23 o 27; Bishop 3 u 8) y generar un PDF (paso 11).",
     "«Los reportes salen en PDF y cada acción queda registrada para auditoría.»"),
    ("enf.mamani", "Cerrar sesión y entrar como enfermera", "Mostrar que el menú es más corto: no ve Partos ni Reportes.",
     "«Mínimo privilegio: enfermería hace triaje, controles y vacunas; no puede abrir partos.»"),
    ("admin.demo", "Cargos y permisos · Gestión de Usuarios · Logs de Acceso · Configuración",
     "Mostrar los cargos, un usuario, los registros de acceso y el perfil con MFA y los 4 temas.",
     "«El administrador crea cargos sobre los roles, ve quién entró y cuándo, y exige verificación en dos pasos.»"),
]

EVITAR = [
    ("Entrar como recepción delante del público", "salen 4 avisos de «Acceso Denegado» en el Panel (BUG-001)"),
    ("Equivocarse de contraseña varias veces", "el mensaje de bloqueo es confuso (BUG-002)"),
    ("Presión 139/89", "no avisa de prehipertensión (BUG-003)"),
    ("Altura uterina 34 cm", "error 500 (BUG-004)"),
    ("IMC exactamente 25 o 30", "lo clasifica mal (BUG-005)"),
    ("Bishop 5 en la calculadora rápida", "lo muestra como «intermedio» (BUG-006)"),
    ("Escribir a mano un resultado de laboratorio o abrir el detalle del examen", "no se guarda / la pantalla falla "
     "(BUG-007/008)"),
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
     "Siempre muestra su margen de error y avisos; es apoyo, no diagnóstico. En la carpeta de muestras se ven también "
     "los casos donde no concuerda con el experto."),
    ("¿Por qué descartaron modelos?",
     "Acidemia (AUC 0,73), prematuro por TPEHG (sin señal), translucencia nucal (68,6 % en otra sede) y otros no "
     "alcanzaron un rendimiento clínico aceptable: mejor no darlos que dar un número falso."),
]


def leer_resultados() -> list[tuple[str, str, list[tuple[str, str, str, str]]]]:
    """(título, carpeta, [(archivo, referencia, respuesta, resultado)]) desde cada RESULTADO.txt."""
    salida = []
    for carpeta in sorted(p for p in MUESTRAS.iterdir() if p.is_dir()):
        texto = (carpeta / "RESULTADO.txt").read_text(encoding="utf-8-sig")
        titulo = texto.splitlines()[0]
        casos = []
        for bloque in texto.split("■ ")[1:]:
            lineas = bloque.strip().splitlines()
            campo = dict(linea.strip().split(": ", 1) for linea in lineas[1:] if ": " in linea)
            casos.append((lineas[0], campo.get("Referencia", ""), campo.get("La red respondió", ""),
                          campo.get("Resultado", "")))
        salida.append((titulo, carpeta.name, casos))
    return salida


def chip(resultado: str) -> str:
    clase = "ok" if resultado.startswith("CONCUERDA") else "no" if resultado.startswith("NO") else "ref"
    texto = re.sub(r" · \d+ ms", "", resultado)
    ms = re.search(r"(\d+) ms", resultado)
    return f'<span class="chip {clase}">{e(texto)}</span>' + (f'<span class="ms">{ms.group(1)} ms</span>' if ms else "")


def construir() -> str:
    filas_guion = "".join(
        f"<tr><td class='n'>{i}</td><td><span class='cuenta'>{e(c)}</span><b>{e(p)}</b><br>{e(h)}</td>"
        f"<td class='decir'>{e(d)}</td></tr>" for i, (c, p, h, d) in enumerate(GUION, 1))
    bloques_ia = []
    for titulo, carpeta, casos in leer_resultados():
        filas = "".join(f"<tr><td class='arch'>{e(a)}</td><td>{e(r)}</td><td>{e(o)}</td><td class='res'>{chip(x)}</td></tr>"
                        for a, r, o, x in casos)
        bloques_ia.append(f"<h3>{e(titulo)} <small>{e(carpeta)}</small></h3><table class='ia'><thead><tr><th>Archivo</th>"
                          f"<th>Referencia del experto</th><th>Respuesta en vivo</th><th>Resultado</th></tr></thead>"
                          f"<tbody>{filas}</tbody></table>")
    evitar = "".join(f"<tr><td>{e(a)}</td><td>{e(b)}</td></tr>" for a, b in EVITAR)
    preguntas = "".join(f"<dt>{e(p)}</dt><dd>{e(r)}</dd>" for p, r in PREGUNTAS)
    plantilla = (AQUI / "plantilla_guion.html").read_text(encoding="utf-8")
    return (plantilla.replace("{{FLUJO}}", svg_flujo()).replace("{{GUION}}", filas_guion)
            .replace("{{IA}}", "".join(bloques_ia)).replace("{{EVITAR}}", evitar).replace("{{PREGUNTAS}}", preguntas))


def main():
    destino_html = AQUI / "guion_demostracion.html"
    destino_html.write_text(construir(), encoding="utf-8")
    pdf = MUESTRAS / "GUION_DEMOSTRACION.pdf"
    subprocess.run(["node", str(AQUI / "a_pdf.js"), str(destino_html), str(pdf)], check=True, cwd=E2E)
    print("Listo:", pdf)


if __name__ == "__main__":
    main()
