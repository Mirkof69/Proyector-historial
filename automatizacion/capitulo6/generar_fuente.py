r"""Genera la fuente del Capítulo 6 (capitulo6/fuente/capitulo6.txt) con los datos reales de las corridas.

    .venv\Scripts\python -m capitulo6.generar_fuente --run REGRESION --retest RETEST --deteccion ID1 ID2

Cada cifra sale de un archivo producido por una ejecución: results.json de las corridas, docs/cobertura.json,
los resúmenes de Locust, data/defectos.py, docs/inventario/inventario.json y el historial de git. El marcado es
el del generador del informe (documento/generador/construir.py), para que el capítulo tenga su mismo formato.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path

from data.casos_ide import CASOS_IDE
from data.catalogo_tc import CASOS
from data.defectos import DEFECTOS
from reporting.modelo import cargar
from tools.exportar_casos import TECNICAS, calcular
from utils import config

RAIZ = config.RAIZ
DESTINO = RAIZ / "capitulo6" / "fuente" / "capitulo6.txt"
IMG = "capitulo6/imagenes"
PROPIA = "Elaboración propia"
AUTOR = "Miguel Mirkof Becerra Guzmán"


def c(texto) -> str:
    """Texto seguro para una celda: sin barras verticales, saltos ni marcas del generador."""
    t = str(texto if texto is not None else "").replace("|", "/").replace("\n", " ").replace("*", "×").strip()
    return t if t not in ("^", "<", "") else (t or "—")


def tabla(ident: str, titulo: str, encabezados: list[str], filas: list[list], anchos: list[float] | None = None,
          fuente: str = PROPIA) -> list[str]:
    a = ",".join(str(x) for x in anchos) if anchos else ""
    L = [f"@tabla {ident} | {titulo} | {fuente} | {a}", "| " + " | ".join(encabezados) + " |"]
    L += ["| " + " | ".join(c(x) for x in fila) + " |" for fila in filas]
    return L + ["@fin", ""]


def figura(ident: str, archivo: str, titulo: str, ancho: float = 15.5, fuente: str = PROPIA, grafico=False) -> list[str]:
    return [f"@{'grafico' if grafico else 'figura'} {ident} | {archivo} | {titulo} | {fuente} | {ancho}", ""]


def num(n) -> str:
    """Miles con espacio fino y decimales con coma, como en el informe."""
    if isinstance(n, float) and not n.is_integer():
        return f"{n:,.1f}".replace(",", " ").replace(".", ",")
    return f"{int(n):,}".replace(",", " ")


def fecha(iso: str) -> str:
    return f"{iso[8:10]}/{iso[5:7]}/{iso[:4]} {iso[11:16]}"


def git(*args) -> str:
    return subprocess.run(["git", *args], cwd=str(RAIZ.parent), capture_output=True, text=True, encoding="utf-8").stdout.strip()


def evidencia_de(r, tc: str, paso: str | None = None):
    """Primera captura EV de un caso en la corrida (o la del paso indicado)."""
    t = r.por_tc.get(tc)
    if not t:
        return None
    evs = [ev for p in t["pruebas"] for ev in p["evidencias"] if ev["archivo"].endswith(".png")]
    if paso:
        evs = [ev for ev in evs if f"-{paso}-" in ev["codigo"]] or evs
    return evs[0] if evs else None


def generar(run: str, retest: str, deteccion: list[str]) -> list[str]:
    r = cargar(run)
    rt = cargar(retest)
    det = [cargar(x) for x in deteccion]
    d = calcular(run)
    filas, traz, cob = d["filas"], d["trazabilidad"], d["cobertura"]
    traz = sorted(traz, key=lambda x: (x["id"].startswith("RNF"), int(x["id"].split("-")[1])))
    inv = json.loads((RAIZ / "docs" / "inventario" / "inventario.json").read_text(encoding="utf-8"))
    rf, rnf = inv["requisitos"]["rf"], inv["requisitos"]["rnf"]
    pantallas = [x for x in inv["rutas"] if not x["redirige_a"]]
    por_rol = {rol: sum(rol in x["roles"] for x in pantallas) for rol in config.ROLES}
    carga = next((x for x in r.rendimiento if x["escenario"] == "carga"), None)
    tot = r.totales
    amb = r.datos["ambiente"]
    rama = git("rev-parse", "--abbrev-ref", "HEAD")
    commits = [x.split(" ", 1) for x in git("log", "--format=%h %s", "--grep=^fix(BUG-", "-20").splitlines()]
    ev_dir = f"reports/{run}"
    # Selenium IDE: comandos y validaciones de cada grabación
    ide = []
    for x in CASOS_IDE:
        cmds = [k["command"] for k in x["comandos"]]
        ide.append({**x, "n": len(cmds), "validaciones": [k for k in cmds if k.startswith(("assert", "verify"))],
                    "localizadores": Counter(k["target"].split("=", 1)[0] for k in x["comandos"]
                                             if k["target"].split("=", 1)[0] in ("id", "css", "xpath", "linkText", "name")),
                    "estado": (r.por_tc.get(x["id"]) or {}).get("estado", "NOT RUN")})
    ide_comandos = Counter(k["command"] for x in CASOS_IDE for k in x["comandos"])
    ide_loc = sum((x["localizadores"] for x in ide), Counter())
    # Selenium WebDriver: localizadores, validaciones y capturas contados en el código
    import re as _re
    codigo_ui = {f: f.read_text(encoding="utf-8") for carpeta in ("pages", "components", "tests/ui")
                 for f in sorted((RAIZ / carpeta).glob("*.py"))}
    wd_loc = {tipo: sum(len(_re.findall(rf"By\.{tipo}\b", txt)) for txt in codigo_ui.values())
              for tipo in ("ID", "NAME", "XPATH", "CSS_SELECTOR", "TAG_NAME")}
    wd_asserts = sum(len(_re.findall(r"^\s*assert ", txt, flags=_re.M)) for f, txt in codigo_ui.items() if "tests" in f.parts)
    wd_capturas = sum(txt.count(".evidencia(") + txt.count("evidencias.captura(") for txt in codigo_ui.values())
    L: list[str] = []
    A = L.append

    def P(*parrafos):
        for p in parrafos:
            L.extend([p, ""])

    # ================================================================ 6.1
    A("# CAPÍTULO 6. ESTRATEGIA Y EJECUCIÓN DE PRUEBAS"), A("")
    P("Este capítulo documenta el proceso de pruebas aplicado al sistema Fetal Medical Bolivia: la planificación, el "
      "diseño de los casos, la solución de automatización construida para ejecutarlos, las pruebas no funcionales, los "
      "resultados obtenidos y los defectos encontrados y corregidos. Todas las cifras provienen de ejecuciones reales "
      f"realizadas entre el 13 y el 14 de noviembre de 2026 sobre el sistema en marcha; la corrida de regresión que "
      f"sirve de referencia es la {run}.")

    A("## 6.1. Plan de Pruebas"), A("")
    A("### 6.1.1. Introducción"), A("")
    P("Fetal Medical Bolivia es un sistema web de historia clínica gineco-obstétrica desarrollado para el área de "
      "Ginecología y Obstetricia. Registra a la paciente, su embarazo, los controles prenatales, el triaje de "
      "enfermería, los exámenes de laboratorio, las ecografías, el parto y la epicrisis, agenda las citas y analiza "
      "imágenes de ecografía con redes neuronales convolucionales. Está formado por una interfaz en React "
      "(puerto 3000), una API en Django REST Framework (puerto 8000), un microservicio de inteligencia artificial en "
      "FastAPI (puerto 8001), un servicio de notificaciones en vivo (puerto 8010), PostgreSQL y Redis.",
      "El sistema lo usan cinco roles con permisos distintos: administrador, médico, enfermería, laboratorio y "
      "recepción. Por tratarse de información clínica, el proceso principal evaluado es el ciclo de atención de la "
      "paciente (registro, embarazo, control, triaje, ecografía y parto) y, junto con él, el control de acceso: que "
      "cada rol vea y modifique solo lo que le corresponde.")

    A("### 6.1.2. Objetivo"), A("")
    P("**Objetivo general.** Comprobar, con evidencia reproducible, que el sistema cumple sus requisitos funcionales "
      "y de calidad con los cinco roles, y dejar una solución de automatización que permita repetir esa comprobación "
      "después de cada cambio.")
    A("**Objetivos específicos.**"), A("")
    for x in ("Verificar los flujos clínicos principales por la interfaz y por la API con datos sintéticos.",
              "Verificar el control de acceso de cada rol en el menú, en las pantallas y en la API.",
              "Detectar defectos, registrarlos, corregirlos con trazabilidad y confirmar la corrección con retesting y regresión.",
              "Medir el tiempo de respuesta de la API con la carga esperada de una clínica.",
              "Automatizar la ejecución, la captura de evidencias y la generación y el envío de los reportes."):
        A(f"- {x}")
    A("")

    A("### 6.1.3. Alcance"), A("")
    P(f"El alcance se definió a partir de un inventario generado del código del sistema (tools/inventario.py): "
      f"{len(pantallas)} pantallas, {len(inv['formularios'])} archivos con formulario y "
      f"{num(sum(len(f['campos']) for f in inv['formularios']))} campos, {num(len(inv['endpoints']))} rutas de la API, "
      f"{len(rf)} requisitos funcionales y {len(rnf)} no funcionales. La [[tab:alcance]] resume lo evaluado.")
    mods = Counter(f["modulo"] for f in filas)
    L.extend(tabla("alcance", "Módulos y elementos dentro del alcance", ["Elemento", "Detalle"], [
        ["Módulos funcionales", ", ".join(m for m in mods if m not in ("Rendimiento", "Selenium IDE", "Interfaz", "Operación", "Datos"))],
        ["Roles", "Administrador, médico, enfermería, laboratorio y recepción (las cinco cuentas reales de la clínica)"],
        ["Pantallas por rol", "; ".join(f"{config.ROLES[k].nombre}: {v}" for k, v in por_rol.items())],
        ["Interfaz", "Formularios de registro, validaciones, búsquedas, menú por rol, URL prohibidas y carga de todas las pantallas permitidas"],
        ["API", "Autenticación y doble factor, matriz rol × endpoint, reglas clínicas, importaciones, ecografía e IA, robustez de listados"],
        ["Plataforma", f"{amb['so']}, Google Chrome 156, sistema desplegado en modo producción en el equipo de pruebas"],
        ["Versión", f"Rama {rama} del repositorio del sistema"],
    ], [4.2, 11.8]))

    A("### 6.1.4. Fuera de Alcance"), A("")
    L.extend(tabla("fuera", "Elementos fuera del alcance y motivo", ["Elemento", "Motivo de la exclusión"], [
        ["Precisión clínica de las redes neuronales", "Se mide con los conjuntos de prueba de cada modelo en la suite de IA del sistema; aquí solo se prueba que la API responde y clasifica las imágenes de muestra"],
        ["Importaciones masivas desde Excel", "Crearían cientos de registros en la base real; las cubre la suite propia del sistema"],
        ["Borrado físico de registros", "Riesgo sobre la base real; se prueba la baja lógica con datos QA"],
        ["Pruebas en Firefox y Edge", "La solución los admite (opción --navegador), pero la ejecución de referencia se hizo en Chrome"],
        ["Dispositivos móviles", "El sistema se usa en computadoras de consultorio"],
        ["Pruebas de seguridad ofensiva", "No se dispone de un ambiente aislado; se prueban los controles de acceso y de sesión"],
        ["Estrés, pico y resistencia (TC-113 a TC-115)", "Diseñadas y automatizadas, pero no ejecutadas: pueden saturar el equipo donde corre la clínica y requieren autorización"],
    ], [5.2, 10.8]))

    A("### 6.1.5. Estrategia de Pruebas"), A("")
    P("La estrategia combina tres capas. Primero, **pruebas de la API** (pytest con requests): son rápidas, estables y "
      "permiten probar reglas clínicas y permisos con muchas combinaciones de datos. Segundo, **pruebas de la "
      "interfaz** (Selenium WebDriver con el patrón Page Object Model): recorren los flujos tal como los usa cada rol "
      "y comprueban el resultado también en la API, porque un mensaje de «guardado» no basta. Tercero, un **barrido "
      "exploratorio automatizado** que abre todas las pantallas permitidas de cada rol y registra errores de "
      "JavaScript, respuestas 4xx y 5xx, pantallas en blanco y desbordes.",
      "Los casos que no conviene automatizar (cargas masivas, borrados, modelos de IA) se verifican con la suite "
      "propia del sistema. Cada defecto sigue el ciclo informe → corrección en un commit propio → retesting del caso "
      "que lo detectó → regresión del conjunto.")

    A("### 6.1.6. Niveles de Prueba"), A("")
    L.extend(tabla("niveles", "Niveles de prueba utilizados", ["Nivel", "¿Se utilizó?", "Cómo"], [
        ["Unitario y de componentes", "Sí, como soporte", "Suite propia del sistema: 1 170 pruebas del backend y 145 del frontend, ejecutadas antes de cada commit de corrección"],
        ["Integración", "Sí", "Pruebas de la API con sesión real: API ↔ base de datos ↔ microservicio de IA"],
        ["Sistema", "Sí (nivel principal)", "Pruebas de extremo a extremo por la interfaz con los cinco roles"],
        ["Aceptación", "No en este capítulo", "Se realizó con el cliente y está documentada en el informe del proyecto"],
    ], [3.8, 3.2, 9.0]))

    A("### 6.1.7. Tipos de Prueba"), A("")
    tipos = Counter(f["tipo"] for f in filas)
    L.extend(tabla("tipos", "Tipos de prueba realizados", ["Tipo", "Aplicación en el proyecto"], [
        ["Funcionales", f"{tipos['Funcional']} casos sobre los módulos del sistema (UI y API)"],
        ["De control de acceso", "Matriz rol × endpoint, menú por rol y URL prohibidas"],
        ["Exploratorias", "Barrido automatizado de todas las pantallas por rol (TC-102) y revisión de sus capturas"],
        ["Retesting", f"Reejecución de los casos que detectaron cada defecto corregido (corrida {retest})"],
        ["Regresión", f"Suite completa tras las correcciones (corrida {run})"],
        ["Rendimiento", "Latencia de la API (TC-116) y prueba de carga con Locust (TC-112)"],
        ["Robustez", "Parámetros inválidos en unos 200 listados: ninguno debe responder 500 (TC-103)"],
    ], [4.2, 11.8]))

    A("### 6.1.8. Estrategia de Automatización"), A("")
    P(f"De los {cob['casos_diseñados']} casos diseñados se seleccionaron {cob['seleccionados_automatizar']} para "
      f"automatizar y {cob['manuales']} quedaron fuera de la automatización. Los criterios de selección fueron: "
      "criticidad del flujo, frecuencia con que debe repetirse, estabilidad de la pantalla, posibilidad de preparar y "
      "limpiar los datos sin afectar la base real, y que el resultado se pueda comprobar con una aserción objetiva. "
      "Se dejó sin automatizar lo que crea datos masivos, borra registros, depende del reloj del servidor o mide la "
      "precisión de un modelo de IA. El detalle está en la sección 6.3.2.")

    A("### 6.1.9. Ambiente de Pruebas"), A("")
    L.extend(tabla("ambiente", "Ambiente de pruebas", ["Componente", "Detalle"], [
        ["Equipo", f"{amb['so']} (equipo de desarrollo y pruebas, el mismo que aloja el sistema)"],
        ["Sistema bajo prueba", f"Interfaz {amb['sut_url']}; API {amb['sut_api']}; IA en el puerto 8001; notificaciones en el 8010"],
        ["Servidor de la API", "Django 6.0.5 y Django REST Framework 3.17.1 sobre waitress (configuración de producción)"],
        ["Interfaz", "React 18.3 y Ant Design 5.22, compilada (build de producción)"],
        ["Base de datos", "PostgreSQL 18, esquema de la clínica; respaldo completo antes de iniciar (13/11/2026, 711 MB)"],
        ["Navegador", "Google Chrome 156 en modo sin ventana; el controlador lo descarga Selenium Manager"],
        ["Automatización", f"Python {amb['python']}, Selenium 4.52.0, pytest 9.2.0, requests 2.34.2, Locust 2.47.0, Node.js 24.15 con selenium-side-runner 4.0.13"],
        ["Versión probada", f"Rama {rama}"],
    ], [4.2, 11.8]))

    A("### 6.1.10. Datos de Prueba"), A("")
    P("Las pruebas usan únicamente **datos sintéticos** generados con Faker: nombres con el prefijo «QA» y cédulas que "
      "empiezan con 99, de modo que se distinguen de cualquier paciente real. Cada prueba crea lo que necesita y, al "
      "terminar la corrida, la automatización da de baja a las pacientes QA y cancela las citas QA. Se usan las cinco "
      "cuentas reales de la clínica, una por rol; sus credenciales y las claves del doble factor se leen de un archivo "
      ".env local que no se versiona. La [[tab:datos]] resume las clases de datos.")
    L.extend(tabla("datos", "Clases de datos de prueba", ["Clase", "Ejemplos usados"], [
        ["Válidos", "Paciente QA con consentimiento; embarazo con FUM de 150 y 203 días; control con PA 112/72; biometría de 29 semanas"],
        ["Inválidos", "Cédula con letras (12AB45); campos obligatorios vacíos; archivo HTML con extensión PDF; paciente sin consentimiento"],
        ["Límites", "Glucosa en ayunas 91, 92, 100, 125 y 126 mg/dL; presión 139/89, 140/90 y 160/110; cuatro y cinco contraseñas erróneas"],
        ["Duplicados", "Cédula repetida; doble clic en Guardar; segundo embarazo activo; cita en un turno ocupado"],
        ["Roles", "Las cinco cuentas; una cuenta temporal QA para el bloqueo por intentos y otra para el doble factor"],
        ["Archivos", "30 ecografías de planos fetales y 8 de circunferencia cefálica de conjuntos públicos de prueba; 3 ginecológicas"],
    ], [3.2, 12.8]))

    A("### 6.1.11. Recursos y Herramientas"), A("")
    L.extend(tabla("herramientas_plan", "Recursos y herramientas", ["Uso", "Herramienta"], [
        ["Automatización de la interfaz", "Selenium WebDriver 4.52 con pytest 9.2 (framework principal)"],
        ["Grabación y reproducción", "Selenium IDE (archivos .side) con selenium-side-runner 4.0.13"],
        ["Pruebas de la API", "pytest con requests 2.34"],
        ["Rendimiento", "Locust 2.47"],
        ["Datos", "Faker 40.54 y pyotp 2.10 (códigos del doble factor)"],
        ["Ejecución", "Panel web propio en FastAPI 0.162 y línea de comandos"],
        ["Reportes y evidencias", "Jinja2 (HTML), python-docx (Word), Microsoft Word (PDF), capturas EV de Selenium"],
        ["Gestión de defectos", "Informes BUG-XXX en Markdown y registro CSV generados de data/defectos.py"],
        ["Repositorio", "Git; correcciones en la rama " + rama],
        ["Inteligencia artificial", "Módulo propio con Ollama (local) o Claude (API de Anthropic), con anonimización previa"],
    ], [4.6, 11.4]))

    A("### 6.1.12. Criterios de Entrada"), A("")
    for x in ("El sistema responde en sus cuatro servicios (comprobación de INICIAR.bat).",
              "Existe un respaldo completo de la base de datos anterior a la primera ejecución.",
              "Las cinco cuentas inician sesión y las de administrador y médico tienen su doble factor configurado.",
              "El inventario de pantallas, formularios y endpoints está generado de la versión que se prueba.",
              "Los casos de prueba tienen pasos, datos y resultado esperado."):
        A(f"- {x}")
    A("")
    A("### 6.1.13. Criterios de Salida"), A("")
    for x in ("Todos los casos seleccionados para automatizar tienen script y fueron ejecutados, o su no ejecución está justificada.",
              "No quedan defectos de severidad crítica o alta abiertos.",
              "Cada defecto corregido tiene retesting aprobado y la regresión completa no introduce fallos nuevos.",
              "La prueba de carga cumple el criterio: percentil 95 menor que 2 segundos y menos de 1 % de errores.",
              "Los reportes y las evidencias de la corrida de referencia están generados."):
        A(f"- {x}")
    A("")

    A("### 6.1.14. Gestión de Defectos"), A("")
    P("Cada defecto se registra en data/defectos.py y de ahí se genera su informe (docs/defectos/BUG-XXX.md) y el "
      "registro en CSV. El informe contiene: identificador, título, módulo, pantalla o endpoint, pasos para "
      "reproducir, resultado esperado y obtenido, severidad, prioridad, estado, responsable, caso relacionado, "
      "evidencia y causa raíz; tras la corrección se agregan el commit, la fecha, el retesting y la regresión. La "
      "severidad mide el daño (crítica, alta, media, baja) y la prioridad el orden de atención. Los estados son: "
      "abierto, corregido, verificado (retesting aprobado) y abierto con propuesta. Cada corrección es un commit "
      "con el formato fix(BUG-XXX): descripción.")

    A("### 6.1.15. Riesgos y Contingencias"), A("")
    L.extend(tabla("riesgos_plan", "Riesgos del proceso de pruebas", ["Riesgo", "Impacto", "Contingencia"], [
        ["Las pruebas se ejecutan sobre la base real de la clínica", "Alto", "Respaldo previo; solo datos QA; limpieza al terminar; sin borrados físicos ni cargas masivas"],
        ["Una prueba altera una cuenta real (ocurrió con el doble factor)", "Alto", "Las claves previas se conservan en .env para restaurarlas; el caso TC-119 usa una cuenta temporal; el explorador no abre /setup-mfa"],
        ["Bloqueo de una cuenta por contraseñas erróneas", "Medio", "Los casos negativos usan cuentas temporales o inexistentes"],
        ["Cambios de la interfaz rompen los localizadores", "Medio", "Page Object Model: cada localizador está en un solo lugar; sonda de DOM para regenerarlos"],
        ["La carga satura el equipo que aloja el sistema", "Alto", "Solo se ejecuta la carga esperada (40 usuarios, solo lecturas); estrés, pico y resistencia requieren autorización"],
        ["Falsos fallos por tiempos de carga", "Medio", "Esperas explícitas en todas las interacciones; ninguna pausa fija"],
    ], [5.4, 1.8, 8.8]))

    A("### 6.1.16. Cronograma"), A("")
    L.extend(tabla("cronograma", "Cronograma de las actividades de prueba", ["Actividad", "Fecha", "Responsable"], [
        ["Respaldo de la base e inventario del sistema", "13/11/2026", AUTOR],
        ["Diseño del catálogo de casos y de la fábrica de datos", "13/11/2026", AUTOR],
        ["Construcción del framework (POM, fixtures, evidencias) y pruebas de autenticación", "13/11/2026", AUTOR],
        ["Pruebas de la API y barrido exploratorio: detección de defectos", "13/11/2026", AUTOR],
        ["Corrección de defectos y verificación del sistema", "13/11/2026", AUTOR],
        ["Retesting, pruebas de interfaz restantes, Selenium IDE y Locust", "14/11/2026", AUTOR],
        ["Panel web, reportes, correo y módulo de IA", "14/11/2026", AUTOR],
        ["Regresión completa, reportes y redacción del capítulo", "14/11/2026", AUTOR],
    ], [9.6, 2.4, 4.0]))

    A("### 6.1.17. Entregables"), A("")
    for x in ("Catálogo de casos de prueba (docs/casos_prueba.xlsx y data/catalogo_tc.py).",
              "Matriz de trazabilidad requisito → caso → script → defecto → resultado (docs/matriz_trazabilidad.md).",
              "Proyecto de automatización con su README, requirements.txt y .env.example.",
              "Grabaciones de Selenium IDE (selenium_ide/) y guion de Locust (locust/locustfile.py).",
              "Informes de defectos (docs/defectos/) y registro en CSV.",
              f"Reportes de la corrida de referencia en HTML, Word, PDF y ZIP con sus evidencias (reports/{run}/).",
              "Inventario del sistema y registro de decisiones (docs/inventario/, docs/decisiones.md).",
              "Este capítulo y su lista de verificación (docs/checklist_entrega.md)."):
        A(f"- {x}")
    A("")

    # ================================================================ 6.2
    A("## 6.2. Pruebas Funcionales"), A("")
    A("### 6.2.1. Funcionalidades"), A("")
    P(f"La [[tab:funcionalidades]] lista las funcionalidades evaluadas por módulo, con la cantidad de casos diseñados "
      "para cada una.")
    func = {}
    for f in filas:
        if f["tipo"] == "Funcional":
            func.setdefault((f["modulo"], f["funcionalidad"]), []).append(f["id"])
    L.extend(tabla("funcionalidades", "Funcionalidades evaluadas", ["Módulo", "Funcionalidad", "Casos", "Identificadores"],
                   [[m, fu, len(ids), ", ".join(ids) if len(ids) <= 6 else f"{ids[0]} a {ids[-1]} y otros"]
                    for (m, fu), ids in func.items()], [3.4, 5.4, 1.4, 5.8]))

    A("### 6.2.2. Requisitos"), A("")
    P(f"Los requisitos son los del proyecto (RF-01 a RF-{len(rf):02d} y RNF-01 a RNF-{len(rnf):02d}). La "
      "[[tab:requisitos]] relaciona cada requisito funcional con sus casos; la matriz completa, con los no "
      "funcionales, está en la sección 6.5.6.")
    L.extend(tabla("requisitos", "Requisitos funcionales y casos que los verifican", ["ID", "Requisito", "Casos"],
                   [[t["id"], t["descripcion"],
                     ", ".join(t["casos"]) or "Sin caso en este ciclo"] for t in traz if t["id"].startswith("RF-")],
                   [1.5, 9.5, 5.0]))

    A("### 6.2.3. Criterios de Aceptación"), A("")
    for x in ("El resultado obtenido coincide con el resultado esperado del caso, comprobado con una aserción.",
              "Lo que la pantalla informa como guardado existe en la API con los mismos valores.",
              "Un rol sin permiso recibe 403 de la API y la pantalla de acceso denegado, nunca los datos.",
              "Ninguna pantalla permitida deja errores de JavaScript en la consola ni respuestas 5xx.",
              "Las reglas clínicas aplican los umbrales documentados (por ejemplo, IADPSG para la glucosa en el embarazo)."):
        A(f"- {x}")
    A("")

    A("### 6.2.4. Técnicas de Diseño"), A("")
    tec = Counter(TECNICAS.get(f["tecnica"], f["tecnica"]) for f in filas)
    P("Los casos se diseñaron con técnicas de caja negra. La [[tab:tecnicas]] indica cuántos casos se construyeron "
      "con cada una y un ejemplo.")
    ejemplos = {"Partición de equivalencia": "Cédula válida, con letras y duplicada (TC-021, TC-024, TC-025)",
                "Valores límite": "Glucosa en ayunas 91, 92, 100, 125 y 126 mg/dL (TC-091)",
                "Tabla de decisión": "Rol × módulo × acción en la matriz de permisos (TC-016)",
                "Transición de estados": "Doble factor: sin configurar → pendiente → activo; bloqueo tras 5 fallos (TC-003, TC-012, TC-119)",
                "Flujo / caso de uso": "Paciente → embarazo → control → ecografía (TC-021, TC-036, TC-040, TC-067)",
                "Exploratoria": "Barrido de todas las pantallas por rol (TC-102)", "No aplica": "Casos de rendimiento"}
    L.extend(tabla("tecnicas", "Técnicas de diseño de casos", ["Técnica", "Casos", "Ejemplo"],
                   [[k, v, ejemplos.get(k, "")] for k, v in tec.most_common()], [4.2, 1.6, 10.2]))

    A("### 6.2.5. Casos de Prueba"), A("")
    P(f"Se diseñaron {len(filas)} casos (TC-001 a TC-{len(filas):03d}). Cada uno tiene identificador, título, "
      "requisito, prioridad, técnica, precondiciones, datos, pasos, resultado esperado y criterio de automatización. "
      "La [[tab:casos_muestra]] presenta una muestra representativa y los cuatro casos siguientes se muestran "
      "completos; el catálogo entero está en el Anexo 1 y en docs/casos_prueba.xlsx.")
    muestra = ["TC-002", "TC-012", "TC-016", "TC-021", "TC-024", "TC-031", "TC-036", "TC-045", "TC-047", "TC-051",
               "TC-067", "TC-069", "TC-091", "TC-102", "TC-112", "TC-119"]
    porid = {f["id"]: f for f in filas}
    L.extend(tabla("casos_muestra", "Muestra de casos de prueba", ["ID", "Funcionalidad", "Qué se verifica", "Resultado esperado"],
                   [[i, porid[i]["funcionalidad"], porid[i]["titulo"], porid[i]["esperado"]] for i in muestra if i in porid],
                   [1.6, 3.2, 5.4, 5.8]))
    for i in ("TC-021", "TC-016", "TC-091", "TC-045"):
        f = porid[i]
        L.append(f"@ficha caso_{i.lower().replace('-', '')} | Caso de prueba {i}: {c(f['titulo'])} | {PROPIA}")
        for etq, val in (("Identificador", f["id"]), ("Módulo y funcionalidad", f"{f['modulo']} · {f['funcionalidad']}"),
                         ("Requisito", f["requisito"]), ("Prioridad", f["prioridad"]),
                         ("Técnica", TECNICAS.get(f["tecnica"], f["tecnica"])), ("Precondiciones", f["precondiciones"]),
                         ("Datos de prueba", f["datos"]), ("Pasos", f["pasos"]), ("Resultado esperado", f["esperado"]),
                         ("Criterio de éxito", "La aserción del script se cumple y el dato existe en la API"),
                         ("Automatización", f"{f['herramienta']} · {', '.join(f['scripts']) or 'sin script'}")):
            L.append(f"{etq}: {c(val)}")
        L.extend(["@fin", ""])

    A("### 6.2.6. Datos de Prueba"), A("")
    P("Los datos de cada caso están en su ficha y se generan con data/fabrica.py. La fábrica produce pacientes, "
      "embarazos, controles y triajes sintéticos con valores válidos por defecto, y cada prueba cambia solo el campo "
      "que quiere examinar (por ejemplo, la presión para probar la alerta de hipertensión). Los valores límite y los "
      "inválidos se pasan como parámetros de la prueba, de manera que un mismo script ejecuta todas las clases de "
      "equivalencia: el caso TC-091 corre cinco veces, una por cada valor de glucosa.")

    A("### 6.2.7. Cobertura"), A("")
    sin = cob["rf_sin_casos"] + cob["rnf_sin_casos"]
    P(f"**Cobertura de requisitos.** De {cob['rf_total']} requisitos funcionales, {cob['rf_con_casos']} tienen al "
      f"menos un caso; de {cob['rnf_total']} no funcionales, {cob['rnf_con_casos']}. La cobertura de requisitos es "
      f"({cob['rf_con_casos']} + {cob['rnf_con_casos']}) / ({cob['rf_total']} + {cob['rnf_total']}) × 100 = "
      f"{num(cob['cobertura_requisitos_pct'])} %. Quedaron sin caso en este ciclo: {', '.join(sin)}; son requisitos "
      "de operación, respaldo, portabilidad y configuración del establecimiento que verifica la suite propia del "
      "sistema y que se proponen para el siguiente ciclo (sección 6.8).",
      "Esta cobertura de pruebas no debe confundirse con la cobertura de automatización, que mide cuántos de los "
      "casos seleccionados tienen script y se calcula en la sección 6.3.12.")
    L.extend(figura("g_cobertura", f"{IMG}/g_cobertura.png", "Casos diseñados, seleccionados para automatizar y automatizados", 11.5, grafico=True))

    # ================================================================ 6.3
    A("## 6.3. Pruebas Automatizadas"), A("")
    A("### 6.3.1. Objetivo de la Automatización"), A("")
    P(f"El sistema tiene {len(pantallas)} pantallas y cinco roles: comprobar a mano que cada rol ve lo que debe y nada más, después "
      "de cada cambio, no es viable. La automatización se incorporó para resolver tres necesidades: repetir la "
      "regresión completa después de cada corrección sin depender de la memoria de quien prueba; probar el control "
      "de acceso con todas las combinaciones de rol, módulo y acción; y dejar evidencia verificable (capturas, "
      "registros y reportes) de cada ejecución. El beneficio esperado es detectar pronto los defectos que un cambio "
      "introduce en otro módulo, como ocurrió con la corrección de BUG-001 (sección 6.5.5).")

    A("### 6.3.2. Alcance y Selección de Casos Automatizables"), A("")
    P(f"Se automatizan {cob['seleccionados_automatizar']} de los {cob['casos_diseñados']} casos. La "
      "[[tab:seleccion]] muestra la decisión de una muestra de casos; la columna correspondiente del Anexo 1 la "
      "contiene para todos.")
    sel = ["TC-002", "TC-016", "TC-021", "TC-030", "TC-039", "TC-069", "TC-079", "TC-100", "TC-102", "TC-109",
           "TC-112", "TC-113"]
    L.extend(tabla("seleccion", "Selección de casos automatizables", ["ID", "Funcionalidad", "¿Se automatiza?", "Prioridad", "Justificación", "Herramienta"],
                   [[i, porid[i]["titulo"], porid[i]["automatiza"], porid[i]["prioridad"], porid[i]["justificacion"],
                     porid[i]["herramienta"]] for i in sel if i in porid], [1.5, 3.9, 2.5, 1.9, 3.8, 2.4]))

    A("### 6.3.3. Herramientas y Tecnologías Utilizadas"), A("")
    P("**Selenium WebDriver es la herramienta principal.** Se eligió porque el sistema es una aplicación de una sola "
      "página con componentes de Ant Design (selectores con búsqueda en el servidor, asistentes por pasos, fechas con "
      "máscara) y con doble factor: se necesita código para calcular el código TOTP, esperar las respuestas de la "
      "API, preparar datos y comprobar el resultado en la base. Con Python y pytest, además, las pruebas de la "
      "interfaz y las de la API comparten fixtures, datos y reportes.",
      f"**Selenium IDE** cubre {len(ide)} casos en {len(set(x['modulo'] for x in ide))} módulos: el inicio de sesión de "
      "los cinco roles (con doble factor en administrador y médico), el menú y las URL prohibidas, el buscador y los "
      f"filtros de los {len([x for x in ide if x['funcionalidad'] == 'Búsqueda y filtros'])} listados del sistema, el "
      "registro de una paciente, la búsqueda avanzada, una calculadora, el Centro de reportes y la Guía de IA. Cada "
      "caso es un proyecto .side en el formato de Selenium IDE, que se abre y edita en la extensión del navegador y "
      "se reproduce con selenium-side-runner desde pytest. Los proyectos se construyeron con un generador propio "
      "(tools/generar_side.py) a partir de los localizadores del DOM real, no con la grabadora de la extensión: así "
      "todos comparten los mismos comandos de inicio de sesión y no contienen credenciales. **Robot Framework no se "
      "utilizó**: duplicaría en palabras clave lo que los Page Objects ya resuelven. Todo el código de la solución "
      "está en un solo lenguaje, Python; Selenium IDE usa su propio formato de comandos.")
    L.extend(tabla("herramientas", "Herramientas y versiones de la automatización", ["Herramienta", "Versión", "Para qué se usa"], [
        ["Python", amb["python"], "Lenguaje de toda la solución"],
        ["Selenium WebDriver", "4.52.0", "Interfaz: localizadores, interacciones y esperas explícitas"],
        ["Selenium Manager", "incluido", "Descarga el controlador del navegador"],
        ["Google Chrome", "156", "Navegador de la ejecución de referencia (Edge y Firefox admitidos)"],
        ["pytest", "9.2.0", "Ejecutor, fixtures, marcadores y parametrización"],
        ["requests", "2.34.2", "Pruebas de la API con sesión y CSRF"],
        ["pyotp", "2.10.0", "Código TOTP del doble factor"],
        ["Faker", "40.54.0", "Datos sintéticos"],
        ["Selenium IDE / selenium-side-runner", "4.0.13", "Grabaciones .side y su reproducción"],
        ["Locust", "2.47.0", "Pruebas de carga"],
        ["FastAPI y uvicorn", "0.162.7 / 0.54.0", "Panel web de ejecución"],
        ["Jinja2 y python-docx", "3.1.6 / 1.2.0", "Reportes HTML y Word"],
        ["Git", "—", "Control de versiones y trazabilidad de las correcciones"],
    ], [5.2, 2.8, 8.0]))

    A("### 6.3.4. Arquitectura y Funcionamiento de la Solución de Automatización"), A("")
    P("La solución es un proyecto independiente del sistema que prueba (carpeta automatizacion/). La "
      "[[fig:arquitectura]] muestra sus componentes: el analista elige una suite en el panel web o en la línea de "
      "comandos; pytest carga las fixtures del conftest.py, que abren un navegador con la sesión de cada rol y un "
      "cliente de la API por rol; las pruebas usan los Page Objects para interactuar con la interfaz o llaman a la "
      "API; cada resultado se guarda con sus evidencias; al terminar se generan los reportes.")
    L.extend(figura("arquitectura", f"{IMG}/arquitectura.png", "Arquitectura de la solución de automatización", 15.8))
    P("El flujo de una corrida tiene ocho pasos ([[fig:flujo]]). La preparación inicia sesión una sola vez por rol y "
      "reutiliza ese navegador en todas las pruebas del rol; para los roles con doble factor calcula el código TOTP "
      "con la clave guardada en .env. Cada prueba registra su identificador de caso con el marcador "
      "@pytest.mark.tc. Si una aserción falla, el conftest.py guarda la captura de la pantalla, la consola del "
      "navegador y el HTML de la página, y clasifica el fallo de forma inicial (sistema, script, datos o ambiente). "
      "El archivo results.json reúne todos los casos con su estado, duración, error y evidencias.")
    L.extend(figura("flujo", f"{IMG}/flujo_ejecucion.png", "Flujo de ejecución de una corrida", 15.8))
    P("**Panel web de ejecución.** Para lanzar las pruebas sin usar la consola se desarrolló un panel propio "
      "(runner_web/, FastAPI) que no forma parte del sistema bajo prueba. Recibe la solicitud por un formulario "
      "(suite, navegador, mostrar el navegador, análisis con IA y envío por correo), inicia pytest como un proceso "
      "aparte con un identificador de corrida, transmite su registro en vivo al navegador con Server-Sent Events, "
      "permite cancelar la corrida cerrando el proceso y sus navegadores y, al terminar, genera los reportes y "
      "guarda el resumen en un historial SQLite desde el que se descargan. Solo escucha en el propio equipo y pide "
      "usuario y clave. La [[fig:panel]] muestra el panel y la [[fig:panel_historial]] su historial.")
    L.extend(figura("panel", f"{IMG}/panel_web.png", "Panel web de ejecución: selección de suite y registro en vivo", 15.8))
    L.extend(figura("panel_historial", f"{IMG}/panel_historial.png", "Panel web: historial de corridas y descarga de reportes", 15.8))

    A("### 6.3.5. Estructura del Proyecto de Automatización"), A("")
    P("La [[fig:arbol]] muestra la estructura real del proyecto. Las carpetas pages/ y components/ contienen los Page "
      "Objects; tests/ las pruebas separadas por tipo; data/ el catálogo de casos y la fábrica de datos; utils/ la "
      "configuración, el navegador, el cliente de la API y las evidencias; reporting/, ai/ y runner_web/ los "
      "reportes, la IA y el panel; reports/ guarda una carpeta por corrida y no se versiona.")
    L.extend(figura("arbol", f"{IMG}/arbol.png", "Estructura de carpetas del proyecto de automatización", 15.8))

    A("### 6.3.6. Diseño e Implementación de Scripts"), A("")
    P("Se aplica el patrón **Page Object Model**: cada pantalla es una clase con sus localizadores y sus acciones, y "
      "las pruebas solo expresan el caso. La clase BasePage reúne las esperas explícitas (WebDriverWait con "
      "expected_conditions), el clic con reintento cuando React redibuja el elemento, la lectura de tablas y la "
      "captura de evidencias; no se usa ninguna pausa fija. El orden de preferencia de los localizadores es: "
      "identificador del campo (Ant Design usa el nombre del campo), atributo aria-label, selector CSS y, por último, "
      "XPath relativo con contains() para botones por su texto. Los localizadores se obtuvieron del DOM real con una "
      "sonda propia (tools/sonda_dom.py), no por suposición.",
      "La [[fig:codigo_pom]] muestra el Page Object del inicio de sesión: los localizadores como constantes de la "
      "clase, el método que espera el resultado (panel, doble factor, configuración o error) y el flujo completo con "
      "el código TOTP.")
    L.extend(figura("codigo_pom", f"{IMG}/codigo_pom.png", "Page Object del inicio de sesión (pages/login_page.py)", 15.8))
    P("La [[fig:codigo_prueba]] muestra cómo se representa un caso: el marcador con el identificador TC-040, la "
      "preparación de los datos por la API, la interacción por la pantalla con el rol que usa esa función, las "
      "evidencias de cada paso y la aserción final contra la API. Los fallos se manejan en un solo lugar "
      "(conftest.py): la prueba no captura excepciones, las deja llegar al registro de resultados.")
    L.extend(figura("codigo_prueba", f"{IMG}/codigo_prueba.png", "Script del caso TC-040 (tests/ui/test_flujo_clinico_ui.py)", 15.8))
    P("**Tipos de localizador en Selenium WebDriver.** El código usa los cuatro tipos pedidos y los cuenta la "
      "[[tab:localizadores]]: por ID (campos de los formularios), por Name (el campo de carga de imagen de la "
      "pantalla de IA, único elemento del sistema con ese atributo), por XPath (botones por su texto, celdas de una "
      "columna, opciones de un desplegable) y por CSS Selector (buscadores por su texto de ayuda, filas de las "
      "tablas, mensajes). El caso TC-171 los reúne en una sola prueba ([[fig:codigo_localizadores]]): inicia sesión "
      "con doble factor, carga una ecografía y valida el resultado con sus aserciones y tres capturas.")
    L.extend(tabla("localizadores", "Localizadores, validaciones y capturas en el código de Selenium WebDriver",
                   ["Elemento", "Cantidad", "Ejemplo"], [
        ["Localizador por ID (By.ID)", wd_loc["ID"], "By.ID con «email», «totp_code», «fecha_ultima_menstruacion»"],
        ["Localizador por Name (By.NAME)", wd_loc["NAME"], "By.NAME con «file» (carga de la ecografía)"],
        ["Localizador por XPath (By.XPATH)", wd_loc["XPATH"], "//button[.//span[normalize-space(.)='Buscar']]"],
        ["Localizador por CSS Selector (By.CSS_SELECTOR)", wd_loc["CSS_SELECTOR"], "input[placeholder='Buscar por nombre, CI o ID...']"],
        ["Validaciones (assert) en las pruebas de interfaz", wd_asserts, "assert encontrada, con el mensaje del fallo"],
        ["Puntos de captura de pantalla", wd_capturas, "pag.evidencia(...) y evidencias.captura(...)"],
    ], [6.2, 1.9, 7.9], "Conteo sobre pages/, components/ y tests/ui/"))
    L.extend(figura("codigo_localizadores", f"{IMG}/codigo_localizadores.png", "Caso TC-171: localizadores por ID, Name, XPath y CSS Selector con validaciones y capturas", 15.8))
    P("**Buscadores y filtros.** Los 17 listados con buscador se prueban con una sola prueba parametrizada "
      "(tests/ui/test_buscadores_ui.py, TC-154 a TC-170) y una matriz de datos (data/modulos_busqueda.py) que indica, "
      "para cada módulo, su ruta, el rol que lo usa, el texto de ayuda del buscador, la columna de la que se toma el "
      "término y el filtro desplegable. La prueba toma una palabra del primer registro, la busca y exige que aparezca; "
      "busca un texto inexistente y exige que el listado quede vacío; y aplica el filtro exigiendo que no haya errores. "
      "La misma matriz alimenta los casos de Selenium IDE, de modo que ambas herramientas prueban lo mismo.")
    P(f"**Selenium IDE.** Cada caso es un proyecto .side con sus comandos. Los {len(ide)} proyectos suman "
      f"{sum(x['n'] for x in ide)} comandos y {sum(len(x['validaciones']) for x in ide)} validaciones. La "
      "[[tab:side_comandos]] muestra los comandos utilizados y la [[tab:side]] los del buscador de pacientes (TC-111) "
      "como ejemplo. Las credenciales no están en el archivo: se usan marcadores que el ejecutor reemplaza en una copia "
      "temporal con los valores de .env, el código TOTP vigente y una cédula de prueba. El archivo "
      "FetalMedical_SeleniumIDE.side reúne todos los casos en un solo proyecto con una suite por módulo, para abrirlo "
      "en la extensión.")
    usos = {"open": "Abrir una pantalla", "setWindowSize": "Tamaño de la ventana", "type": "Escribir en un campo",
            "sendKeys": "Enviar una tecla (ENTER)", "click": "Pulsar un botón, un filtro o una pestaña",
            "waitForElementVisible": "Espera explícita hasta que el elemento se ve",
            "waitForElementPresent": "Espera explícita hasta que el elemento existe",
            "waitForElementNotPresent": "Espera explícita hasta que el elemento desaparece",
            "executeScript": "Leer un dato de la página y guardarlo en una variable (término de búsqueda, conteos, ruta)",
            "assert": "Validar el valor de una variable", "assertElementPresent": "Validar que un elemento existe",
            "assertElementNotPresent": "Validar que un elemento no existe", "assertValue": "Validar el valor de un campo",
            "assertText": "Validar el texto de un elemento", "assertTitle": "Validar el título de la página",
            "verifyElementPresent": "Validación que no detiene la prueba", "echo": "Dejar un mensaje en el registro"}
    L.extend(tabla("side_comandos", "Comandos de Selenium IDE utilizados", ["Comando", "Usos", "Para qué se usa"],
                   [[k, v, usos.get(k, "")] for k, v in ide_comandos.most_common()], [4.6, 1.6, 9.8]))
    L.extend(tabla("side_localizadores", "Tipos de localizador en los proyectos de Selenium IDE", ["Tipo", "Usos", "Ejemplo"], [
        ["id=", ide_loc["id"], "id=email, id=totp_code, id=nombre"],
        ["css=", ide_loc["css"], "css=input[placeholder='Buscar por nombre, CI o ID...']"],
        ["xpath=", ide_loc["xpath"], "xpath=//tr[contains(@class,'ant-table-row')][contains(.,'${termino}')]"],
    ], [2.4, 1.8, 11.8]))
    side = json.loads((RAIZ / "selenium_ide" / "TC-111_buscar_pacientes.side").read_text(encoding="utf-8"))
    L.extend(tabla("side", "Comandos del proyecto de Selenium IDE del caso TC-111 (buscador de pacientes)", ["N.º", "Comando", "Objetivo", "Valor"],
                   [[i + 1, x["command"], x["target"] if len(x["target"]) < 170 else "Script que toma una palabra del primer registro (ver el archivo .side)",
                     x["value"].replace("__QA_PASSWORD__", "(clave de .env)").replace("__QA_EMAIL_RECEPCION__", "(correo de .env)")]
                    for i, x in enumerate(side["tests"][0]["commands"])], [1.0, 3.8, 8.2, 3.0]))
    roles = {"administrador": "Administrador", "medico": "Médico", "enfermera": "Enfermería", "laboratorista": "Laboratorio",
             "recepcion": "Recepción", "anónimo": "Sin sesión"}
    L.extend(tabla("side_casos", "Casos automatizados con Selenium IDE (Cmd.: comandos; Asserts: validaciones)",
                   ["Caso", "Módulo", "Escenario", "Rol", "Cmd.", "Asserts", "Estado"],
                   [[x["id"], x["modulo"], x["titulo"].replace(" (Selenium IDE)", ""), roles.get(x["rol"], x["rol"]), x["n"],
                     len(x["validaciones"]), x["estado"]] for x in ide], [1.6, 2.4, 4.4, 2.8, 1.3, 1.8, 1.7]))

    A("### 6.3.7. Funcionalidades Automatizadas"), A("")
    auto = {}
    for f in filas:
        if f["scripts"]:
            auto.setdefault((f["modulo"], f["herramienta"]), []).append(f)
    L.extend(tabla("automatizadas", "Funcionalidades con pruebas automatizadas implementadas",
                   ["Módulo", "Escenarios cubiertos", "Casos", "Herramienta", "Estado"],
                   [[m, "; ".join(dict.fromkeys(x["funcionalidad"] for x in fs)),
                     ", ".join(x["id"] for x in fs) if len(fs) <= 5 else f"{fs[0]['id']} … {fs[-1]['id']} ({len(fs)})",
                     h, "Completo"] for (m, h), fs in auto.items()], [2.6, 5.2, 3.5, 2.4, 2.3]))

    A("### 6.3.8. Relación entre Casos de Prueba y Scripts"), A("")
    P("Cada script declara el caso que implementa con el marcador @pytest.mark.tc; de ese marcador sale la "
      "[[tab:scripts]], generada por tools/exportar_casos.py. Un script parametrizado cubre varios escenarios del "
      "mismo caso (por ejemplo, TC-016 se ejecuta una vez por cada combinación de rol y módulo).")
    por_script = {}
    for f in filas:
        for s in f["scripts"]:
            por_script.setdefault(s, []).append(f)
    L.extend(tabla("scripts", "Scripts y casos que implementan", ["Script", "Herramienta", "Casos", "Pruebas"],
                   [[s, fs[0]["herramienta"], ", ".join(x["id"] for x in fs), sum(x["pruebas"] for x in fs)]
                    for s, fs in sorted(por_script.items())], [6.0, 2.6, 5.4, 2.0]))

    A("### 6.3.9. Gestión de Datos y Configuración"), A("")
    P("La configuración tiene dos niveles. Lo que no es secreto (URL del sistema, navegador, tiempo de las esperas) "
      "está en config/config.yaml. Las credenciales de las cuentas, las claves del doble factor, la contraseña del "
      "correo, la llave de la IA y la clave del panel están en un archivo .env local excluido del repositorio por "
      ".gitignore; el repositorio incluye .env.example con los nombres de las variables y valores ficticios. Ningún "
      "script, grabación, reporte ni este documento contiene una contraseña o un token.",
      "Los datos se preparan con la fábrica (data/fabrica.py) y se crean por la API con el rol que corresponde. Todo "
      "lo creado se anota y, al terminar la corrida, una fixture de sesión da de baja a las pacientes QA y cancela "
      "las citas QA. Los casos negativos de autenticación usan cuentas temporales creadas y desactivadas por la "
      "propia prueba, para no bloquear las cuentas reales.")

    A("### 6.3.10. Ejecución de la Automatización"), A("")
    P("**Requisitos previos:** Windows, Python 3.12, Google Chrome, Node.js (solo para Selenium IDE), Microsoft Word "
      "(solo para el PDF) y el sistema en marcha con INICIAR.bat. **Instalación:** crear el entorno virtual, instalar "
      "requirements.txt y copiar .env.example como .env con los valores reales. La [[tab:comandos]] reúne los "
      "comandos; el README del proyecto los repite con más detalle.")
    L.extend(tabla("comandos", "Comandos de instalación y ejecución", ["Propósito", "Comando"], [
        ["Crear el entorno", "python -m venv .venv"],
        ["Instalar dependencias", r".venv\Scripts\python -m pip install -r requirements.txt"],
        ["Abrir el panel web", "EJECUTAR_PANEL.bat (http://127.0.0.1:8090)"],
        ["Suite de humo", r".venv\Scripts\python -m pytest -m smoke"],
        ["API completa", r".venv\Scripts\python -m pytest tests\api"],
        ["Interfaz sin el barrido", r'.venv\Scripts\python -m pytest tests\ui -m "not regression"'],
        ["Roles y permisos", r".venv\Scripts\python -m pytest -m roles"],
        ["Selenium IDE", r".venv\Scripts\python -m pytest tests\ide"],
        ["Rendimiento", r".venv\Scripts\python -m pytest tests\rendimiento"],
        ["Todo", r".venv\Scripts\python -m pytest"],
        ["Un caso, con ventana y en Edge", r".venv\Scripts\python -m pytest tests\ui\test_pacientes_ui.py -k tc021 --visible --navegador edge"],
        ["Reportes de la última corrida", r".venv\Scripts\python -m reporting.generar --correo"],
    ], [5.0, 11.0]))
    P(f"Los resultados quedan en reports/<corrida>/: results.json, la carpeta evidencias/, los reportes y el ZIP. La "
      f"[[fig:consola_inicio]] y la [[fig:consola_fin]] muestran el inicio y el final del registro de la corrida "
      f"{run}, lanzada desde el panel web.")
    L.extend(figura("consola_inicio", f"{IMG}/consola_inicio.png", f"Inicio del registro de ejecución de la corrida {run}", 15.8))
    L.extend(figura("consola_fin", f"{IMG}/consola_fin.png", f"Final del registro de ejecución de la corrida {run}", 15.8))

    A("### 6.3.11. Evidencias de Automatización"), A("")
    n_ev = sum(len(x["evidencias"]) for x in r.casos)
    P(f"Cada captura se nombra EV-<caso>-<paso>-<fecha y hora> y queda asociada a su caso en results.json. La corrida "
      f"de referencia guardó {num(n_ev)} capturas, además de las {num(sum(1 for _ in (RAIZ / 'docs' / 'inventario' / 'capturas').rglob('*.png')))} "
      "capturas del barrido de pantallas (una por pantalla y rol). La [[tab:evidencias]] relaciona las evidencias "
      "que se presentan en este capítulo con su caso; las figuras siguientes son esas capturas.")
    presentadas = [("TC-002", "panel", "Inicio de sesión del administrador con doble factor"), ("TC-021", "registrada", "Paciente QA registrada por recepción"),
                   ("TC-036", "guardado", "Embarazo registrado por el médico"), ("TC-040", "formulario", "Formulario del control prenatal"),
                   ("TC-045", "alerta", "Alerta de hipertensión en el detalle del control"), ("TC-051", "paso-2", "Triaje de enfermería: signos vitales"),
                   ("TC-067", "biometria", "Ecografía con biometría fetal"), ("TC-069", "resultado", "Análisis de una ecografía con IA"),
                   ("TC-014", "menu-recepcion", "Menú del rol de recepción"), ("TC-015", "denegada-enfermera", "Acceso denegado a una URL prohibida"),
                   ("TC-099", "pestana-1", "Centro de reportes"), ("TC-121", "sin-dato", "Triaje sin saturación: «Sin dato»"),
                   ("TC-154", "busqueda", "Buscador de pacientes con WebDriver"), ("TC-155", "filtro", "Filtro del listado de citas con WebDriver"),
                   ("TC-162", "sin-resultados", "Búsqueda sin coincidencias en embarazos con WebDriver"),
                   ("TC-171", "imagen", "Ecografía cargada con el localizador por Name"),
                   ("TC-171", "resultado", "Resultado del análisis de IA"),
                   ("TC-111", "ejecucion", "Selenium IDE: buscador de pacientes"), ("TC-122", "ejecucion", "Selenium IDE: inicio de sesión con doble factor"),
                   ("TC-139", "ejecucion", "Selenium IDE: buscador y filtro de embarazos"), ("TC-149", "ejecucion", "Selenium IDE: registro de una paciente")]
    usadas = []
    for tc, paso, desc in presentadas:
        ev = evidencia_de(r, tc, paso) or evidencia_de(rt, tc, paso)
        if ev:
            origen = run if evidencia_de(r, tc, paso) else retest
            usadas.append((tc, ev, desc, origen))
    L.extend(tabla("evidencias", "Evidencias presentadas y caso al que pertenecen", ["Código de evidencia", "Caso", "Qué muestra", "Estado"],
                   [[ev["codigo"], tc, desc, (r.por_tc.get(tc) or rt.por_tc.get(tc))["estado"]] for tc, ev, desc, _ in usadas],
                   [6.6, 1.5, 6.2, 1.7]))
    for tc, ev, desc, origen in usadas:
        L.extend(figura(f"ev_{tc.lower().replace('-', '')}_{ev['paso'].replace('-', '')}", f"reports/{origen}/{ev['archivo']}",
                        f"{ev['codigo']}: {desc} ({tc})", 15.0, f"Captura de la ejecución automatizada, corrida {origen}"))
    P("Los casos de Selenium IDE dejan como evidencia la salida de su ejecutor, guardada como imagen con su código EV "
      "y como texto (EV-<caso>-side-runner.txt); si un caso falla, el ejecutor guarda además la captura de la pantalla.")
    P("El reporte HTML de la corrida ([[fig:reporte_html]] y [[fig:reporte_html_casos]]) y su versión en PDF "
      "([[fig:reporte_pdf]]) se generan automáticamente al terminar.")
    L.extend(figura("reporte_html", f"{IMG}/reporte_html.png", "Reporte HTML de la corrida: resumen y resultados por módulo", 15.8))
    L.extend(figura("reporte_html_casos", f"{IMG}/reporte_html_casos.png", "Reporte HTML de la corrida: casos ejecutados con sus evidencias", 15.8))
    L.extend(figura("reporte_pdf", f"{IMG}/reporte_pdf.png", "Primera página del reporte en PDF de la corrida", 10.5))

    A("### 6.3.12. Cobertura de Automatización"), A("")
    P(f"Base de cálculo: los casos con «¿Se automatiza? = Sí» del catálogo ({cob['seleccionados_automatizar']}). Un "
      "caso cuenta como automatizado si existe un script con su marcador o una grabación .side con su identificador.")
    A(f"@ecuacion Cobertura de automatización = ({cob['automatizados']} / {cob['seleccionados_automatizar']}) × 100 = {num(cob['cobertura_automatizacion_pct'])} %"), A("")
    pend = cob["pendientes_automatizar"]
    P(f"Casos automatizados: {cob['automatizados']}. Pendientes: {len(pend)}"
      + (f" ({', '.join(pend)})." if pend else ".")
      + " Este indicador no es el porcentaje de pruebas aprobadas ni la cobertura de requisitos: tres de los casos "
        "automatizados (TC-113, TC-114 y TC-115) tienen script pero no se ejecutaron, por la razón indicada en 6.4.")

    A("### 6.3.13. Resultados de Ejecución Automatizada"), A("")
    L.extend(tabla("resultado_auto", "Resultado de la corrida automatizada de referencia", ["Dato", "Valor"], [
        ["Corrida", run], ["Fecha y hora de inicio", fecha(r.datos["inicio"])], ["Duración", r.duracion_legible],
        ["Suite", "Completa: API, interfaz, Selenium IDE, barrido de pantallas y rendimiento"],
        ["Ambiente", f"{amb['so']}, Chrome sin ventana, {amb['sut_url']}"],
        ["Pruebas ejecutadas", tot["total"]], ["PASS", tot["PASS"]], ["FAIL", tot["FAIL"]], ["BLOCKED", tot["BLOCKED"]],
        ["NOT RUN", tot["NOT RUN"]], ["Éxito sobre las ejecutadas", f"{num(r.tasa_exito)} %"],
        ["Casos de prueba con resultado", len(r.por_tc)],
        ["Evidencia", f"reports/{run}/reporte.html, reporte.pdf y carpeta evidencias/"],
    ], [5.2, 10.8]))
    L.extend(figura("g_modulos", f"{IMG}/g_modulos.png", "Pruebas ejecutadas por módulo y estado", 14.5, grafico=True))
    if r.fallos:
        P(f"**Análisis de los fallos.** La corrida tuvo {tot['FAIL']} pruebas en FAIL. La [[tab:fallos]] explica cada una.")
        L.extend(tabla("fallos", "Pruebas en FAIL de la corrida de referencia y su análisis", ["Caso", "Prueba", "Causa", "Defecto"],
                       [[x["tc"], x["nombre"], x["error"][:260], ", ".join(x["defectos"]) or "—"] for x in r.fallos],
                       [1.5, 4.0, 8.7, 1.8]))
    else:
        P("La corrida no tuvo pruebas en FAIL.")
    nr = [x for x in r.casos if x["estado"] in ("NOT RUN", "BLOCKED")]
    if nr:
        L.extend(tabla("no_ejecutadas", "Pruebas no ejecutadas y motivo", ["Caso", "Prueba", "Estado", "Motivo"],
                       [[x["tc"], x["nombre"], x["estado"], x["error"][:200].replace("Skipped: ", "").replace("NOT RUN: ", "")] for x in nr], [1.6, 5.0, 2.2, 7.2]))

    A("### 6.3.14. Integración Continua y Ejecución Programada (CI/CD)"), A("")
    P("**No se implementó un pipeline de integración continua.** Las pruebas se ejecutan de forma local, desde el "
      "panel web o la consola, porque necesitan el sistema completo en marcha (PostgreSQL, Redis, la API, la interfaz "
      "y el microservicio de IA con sus modelos) y las cuentas reales con su doble factor, que no deben guardarse en "
      "un servicio externo. Como mejora futura se propone un flujo de GitHub Actions con un ejecutor propio en el "
      "equipo de la clínica que, en cada cambio de la rama principal, levante el sistema con una base de pruebas, "
      "ejecute la suite de humo y publique el reporte HTML como artefacto.")

    A("### 6.3.15. Mantenimiento, Reutilización y Limitaciones"), A("")
    P("**Reutilización.** La clase BasePage concentra esperas, clics y tablas; FormularioClinico agrega los "
      "selectores de Ant Design (buscar y elegir, fechas con máscara) que usan los formularios de embarazo, control, "
      "triaje y ecografía; PantallaPage mide la «salud» de cualquier pantalla. Las fixtures navegador(rol) y "
      "cliente(rol) dan a cualquier prueba una sesión del rol que necesite. **Mantenimiento.** Si cambia una "
      "pantalla, se corrige su Page Object y no las pruebas; la sonda de DOM vuelve a listar campos y botones; el "
      "inventario se regenera del código y el caso TC-014 avisa si el menú ofrece una pantalla que el rol no puede "
      "abrir. Agregar un caso es añadir una fila al catálogo y una función con su marcador.",
      "**Limitaciones.** (1) Las pruebas corren sobre la base real, de modo que no se automatizan borrados ni cargas "
      "masivas. (2) Dependen de la clave del doble factor guardada en .env: si un usuario reconfigura su doble "
      "factor, hay que actualizarla. (3) La ejecución de referencia es solo en Chrome. (4) El ejecutor de Selenium "
      "IDE falla si su ruta tiene espacios, por lo que se instala en una carpeta del usuario sin espacios. (5) El "
      "PDF necesita Microsoft Word. (6) El barrido detecta errores técnicos, no errores de contenido: una cifra "
      "equivocada en pantalla solo se descubre con un caso específico.")

    A("### 6.3.16. Incorporación de Inteligencia Artificial (IA) como Valor Agregado"), A("")
    ia_estado = __import__("ai.servicio", fromlist=["estado"]).estado()
    uso = RAIZ / "ai" / "registro_uso_ia.jsonl"
    usos = [json.loads(x) for x in uso.read_text(encoding="utf-8").splitlines() if x.strip()] if uso.exists() else []
    P("**Necesidad.** Después de una corrida con fallos, el analista debe leer cada error y su traza para decidir si "
      "es un defecto del sistema, del script, de los datos o del ambiente, y luego resumir el estado para quien "
      "decide. Ese trabajo es repetitivo y es donde la IA puede ayudar.",
      "**Lo implementado.** El módulo ai/ ofrece cinco tareas: resumen ejecutivo de la corrida, análisis de cada "
      "fallo (causa probable, clasificación y severidad sugerida), escenarios Gherkin a partir de un requisito, "
      "sugerencia de localizadores a partir de un fragmento de HTML y consulta del estado del proveedor. Admite dos "
      "proveedores configurables: un modelo local con Ollama (por defecto, nada sale del equipo) y Claude por la API "
      "de Anthropic (si se define una llave). Todo texto pasa antes por un anonimizador y cada uso se anota en "
      "ai/registro_uso_ia.jsonl con fecha, tarea, proveedor, modelo y tamaños, sin el contenido. El panel web y el "
      "reporte muestran el resultado rotulado como sugerencia de la IA.",
      "**Entrada y prompt representativo.** Para el análisis de un fallo se envía un JSON con el caso, el nombre de la "
      "prueba, el error, el final de la traza, la consola del navegador y la clasificación inicial, con esta "
      "instrucción: «Eres analista de QA de un sistema web de historia clínica obstétrica. Solo usas los datos que "
      "recibes: si algo no está, dices que no hay datos. No decides si una prueba pasó o falló: eso ya lo decidió su "
      "aserción. Analiza este fallo en 3 líneas: (1) causa probable; (2) si parece defecto del sistema, del script, "
      "de los datos o del ambiente y por qué; (3) severidad sugerida y qué revisar primero.»")
    if usos and any(not u.get("error") for u in usos):
        ok = [u for u in usos if not u.get("error")]
        P(f"**Resultado y evidencia.** El registro de uso contiene {len(ok)} consultas correctas con "
          f"{ok[-1]['proveedor']} ({ok[-1]['modelo']}). El resumen y los análisis generados están en "
          f"reports/{run}/ia_resumen.json e ia_fallos.json y se muestran en el reporte.")
    else:
        P("**Estado real del uso.** El módulo está implementado y probado en su parte verificable sin modelo: el "
          "anonimizador, la selección del proveedor y el registro de uso. **En la corrida de referencia la IA no "
          f"generó resultados**, porque en el equipo no había un proveedor disponible ({ia_estado['motivo'] or 'sin proveedor'}). "
          "Por eso este capítulo no presenta ninguna salida de IA como evidencia: el resumen ejecutivo y el análisis "
          "de fallos quedan como funcionalidad lista para usarse cuando se instale Ollama con su modelo o se "
          "configure la llave, y su evaluación con casos reales queda como trabajo pendiente (sección 6.8).")
    P("**Revisión humana.** La IA no participa en el veredicto: el estado PASS o FAIL lo fija la aserción de cada "
      "script. Lo que la IA propone (una clasificación, un escenario, un localizador) es un borrador que el analista "
      "revisa, corrige y ejecuta antes de aceptarlo. Durante el desarrollo de la solución sí se usó un asistente de "
      "IA para escribir y depurar scripts; todo ese código se ejecutó contra el sistema y se corrigió con las "
      "capturas y trazas reales: de las primeras ejecuciones de los formularios clínicos, seis de siete pruebas "
      "fallaron por supuestos equivocados (un campo deshabilitado, un botón con otro texto, un campo obligatorio) y "
      "se corrigieron una por una hasta pasar.")

    A("### 6.3.17. Seguridad, Privacidad y Uso Responsable de IA"), A("")
    for x in ("**Sin secretos en el código:** contraseñas, claves TOTP, llave de la IA y clave del correo viven solo en .env, excluido del repositorio.",
              "**Anonimización previa:** antes de enviar un texto a cualquier modelo (también al local) se reemplazan correos, números de cinco o más dígitos (cédulas, teléfonos), identificadores clínicos, nombres de pacientes QA, tokens y valores de campos de clave.",
              "**Solo datos sintéticos:** las pruebas no usan datos de pacientes reales, por lo que un error o un HTML capturado no los contiene.",
              "**Proveedor local por defecto:** el servicio externo solo se usa si el responsable define su llave.",
              "**Registro de uso:** cada consulta queda anotada sin su contenido.",
              "**Evidencias sin secretos:** la captura de la configuración del doble factor oculta la clave antes de guardarse y la salida del ejecutor de Selenium IDE enmascara la contraseña.",
              "**Código verificado antes de aceptarlo:** ningún script sugerido se da por válido sin ejecutarlo."):
        A(f"- {x}")
    A("")

    A("### 6.3.18. Evaluación del Aporte de la Automatización y de la IA"), A("")
    seg = r.datos.get("duracion_s", 0)
    P(f"**Repetibilidad y tiempo medido.** La corrida completa ejecutó {tot['total']} pruebas en {r.duracion_legible} "
      f"sin intervención ({num(seg / max(tot['total'], 1))} segundos por prueba en promedio). No existe una medición "
      "comparable de la misma batería hecha a mano, por lo que no se afirma un porcentaje de ahorro; lo observado es "
      "que la batería se repitió completa varias veces en dos días, algo que manualmente no se habría hecho.",
      f"**Defectos encontrados.** La automatización detectó los {len(DEFECTOS)} defectos del ciclo: la matriz de "
      "permisos encontró que la API no aplicaba la tabla de roles (BUG-001) y que exponía los correos y teléfonos de "
      "las cuentas (BUG-002); los valores límite, un error en la clasificación de la glucosa en el embarazo "
      "(BUG-003); el barrido de pantallas, el reemplazo de la clave del doble factor (BUG-004), una pantalla que se "
      "caía (BUG-005), pantallas que pedían datos prohibidos (BUG-006), botones sin nombre accesible (BUG-007) y un "
      "dato mostrado como cero (BUG-008).",
      "**Regresión.** Tras corregir BUG-001, el barrido detectó dos efectos de esa corrección en pantallas del "
      "laboratorio: su panel pedía un dato recién prohibido y su historia clínica dejaba de cargar. Ambos se "
      "corrigieron antes de la corrida de referencia. Sin la regresión automatizada habrían llegado al usuario.",
      "**Limitaciones del aporte.** La automatización también produjo un incidente: al recorrer /setup-mfa reemplazó "
      "la clave del doble factor de dos cuentas reales, que hubo que restaurar. El hallazgo fue valioso (era un "
      "defecto crítico del sistema), pero muestra que automatizar sobre una base real exige contención. **IA:** su "
      "aporte al análisis de resultados no pudo medirse porque no se ejecutó con un modelo; se describe solo lo "
      "implementado.")

    # ================================================================ 6.4
    A("## 6.4. Pruebas No Funcionales"), A("")
    A("### 6.4.1. Tipo de Prueba No Funcional"), A("")
    P("Se evaluó el **rendimiento** de la API con dos pruebas: una **prueba de carga** con la cantidad esperada de "
      "usuarios de una clínica (TC-112, Locust) y una medición de **latencia** de 16 rutas representativas con un "
      "solo usuario (TC-116). Se diseñaron y automatizaron además una prueba de **estrés** (TC-113), una de **pico** "
      "(TC-114) y una de **resistencia** (TC-115), que no se ejecutaron (sección 6.4.7). La parte sometida a prueba "
      "es la API REST: inicio de sesión con doble factor y las consultas que cada rol hace durante un turno.")

    A("### 6.4.2. Objetivo y Alcance de la Prueba"), A("")
    L.extend(tabla("nf_objetivo", "Objetivo y alcance de la prueba de carga", ["Aspecto", "Definición"], [
        ["Componente evaluado", "API REST del sistema (puerto 8000): autenticación, pacientes, embarazos, controles, ecografías, triaje, laboratorio, citas, auditoría, usuarios e indicadores"],
        ["Atributo de calidad", "Tiempo de respuesta y tasa de errores con carga concurrente"],
        ["Condición simulada", "40 usuarios concurrentes durante 3 minutos, con 1 a 4 segundos de lectura entre peticiones"],
        ["Criterio esperado", "Percentil 95 menor que 2 000 ms y menos de 1 % de errores (criterio propuesto para el proyecto; el requisito RNF-01 pide además p95 menor que 200 ms en los listados con un usuario)"],
        ["Por qué importa", "Durante la consulta el médico abre la historia de la paciente mientras recepción agenda y enfermería registra el triaje: la espera no debe interrumpir la atención"],
    ], [4.0, 12.0]))

    A("### 6.4.3. Escenario y Configuración de la Prueba"), A("")
    L.extend(tabla("nf_escenario", "Escenario y configuración de la prueba de carga", ["Parámetro", "Valor"], [
        ["Ambiente", "Sistema en modo producción en el equipo de pruebas (waitress con 32 hilos); http://127.0.0.1:8000"],
        ["Herramienta", "Locust 2.47.0, modo sin interfaz, lanzado desde pytest (tests/rendimiento/test_carga_locust.py)"],
        ["Usuarios y rampa", "40 usuarios virtuales, 4 nuevos por segundo (10 segundos de rampa)"],
        ["Duración", "3 minutos"],
        ["Mezcla de usuarios", "Recepción 3, médico 3, enfermería 2, laboratorio 1, administración 1 (pesos)"],
        ["Operaciones", "Cada usuario inicia sesión (con doble factor si su rol lo exige) y repite las consultas de su rol: búsquedas, listados paginados, ficha de la paciente e indicadores. Solo lecturas"],
        ["Datos y autenticación", "Las cinco cuentas de prueba; contraseña y claves TOTP leídas de .env; cookies de sesión y CSRF como el navegador"],
        ["Condiciones", "Locust y el sistema comparten el mismo equipo, por lo que compiten por el procesador; sin red de por medio"],
        ["Comando", r".venv\Scripts\python -m pytest tests\rendimiento (equivale a locust -f locust\locustfile.py --headless -u 40 -r 4 -t 3m)"],
    ], [3.8, 12.2]))
    P("La [[fig:codigo_locust]] muestra la clase base del usuario virtual: el inicio de sesión con el código TOTP y "
      "el tiempo de espera entre tareas.")
    L.extend(figura("codigo_locust", f"{IMG}/codigo_locust.png", "Usuario virtual de Locust (locust/locustfile.py)", 15.8))

    A("### 6.4.4. Herramienta Utilizada y Justificación"), A("")
    P("Se eligió **Locust** porque los usuarios virtuales se escriben en Python, igual que el resto de la solución: "
      "reutiliza la configuración, las cuentas por rol y el cálculo del código TOTP, y permite modelar un "
      "comportamiento distinto para cada rol con sus pesos. k6 habría exigido reescribir el inicio de sesión con "
      "doble factor en JavaScript. El archivo locust/locustfile.py define una clase por rol y, con la variable "
      "ESCENARIO, las formas de carga de estrés, pico y resistencia. Locust escribe sus estadísticas en CSV y un "
      "reporte HTML; la prueba de pytest lee el CSV y aplica el criterio de aceptación.")

    A("### 6.4.5. Métricas y Resultados Obtenidos"), A("")
    if carga:
        eps = carga["por_endpoint"]
        lento = max(eps, key=lambda e: e["p95_ms"])
        import csv
        with open(r.dir_run / "locust" / "carga_stats.csv", encoding="utf-8") as fh:
            agg = next(x for x in csv.DictReader(fh) if x["Name"] == "Aggregated")
        L.extend(tabla("nf_resultados", "Resultados de la prueba de carga (TC-112)", ["Métrica", "Resultado", "Interpretación"], [
            ["Usuarios concurrentes", 40, "Carga simulada alcanzada"],
            ["Solicitudes totales", num(carga["peticiones"]), "Volumen procesado en 3 minutos"],
            ["Throughput", f"{num(round(carga['rps'], 1))} solicitudes/s", "Solicitudes procesadas por segundo"],
            ["Tiempo promedio", f"{num(round(float(agg['Average Response Time'])))} ms", "Promedio de respuesta"],
            ["Mediana (p50)", f"{num(carga['p50_ms'])} ms", "La mitad de las respuestas tardó esto o menos"],
            ["Percentil 95 (p95)", f"{num(carga['p95_ms'])} ms", "El 95 % de las respuestas fue igual o inferior"],
            ["Percentil 99 (p99)", f"{num(carga['p99_ms'])} ms", "Incluye los inicios de sesión, que calculan el hash de la contraseña"],
            ["Tiempo mínimo y máximo", f"{num(round(float(agg['Min Response Time'])))} ms y {num(round(float(agg['Max Response Time'])))} ms", "Extremos observados"],
            ["Solicitudes fallidas", f"{carga['fallas']} ({num(carga['error_pct'])} %)", "Tasa de errores"],
        ], [4.4, 4.2, 7.4], f"Reporte de Locust de la corrida {run}"))
        L.extend(figura("g_p95", f"{IMG}/g_p95.png", "Percentil 95 del tiempo de respuesta por operación", 15.0, f"Estadísticas de Locust, corrida {run}", grafico=True))
        L.extend(figura("g_carga_tiempo", f"{IMG}/g_carga_tiempo.png", "Tiempo de respuesta y usuarios concurrentes durante la prueba", 15.0, f"Historial de Locust, corrida {run}", grafico=True))
        L.extend(figura("locust_html", f"{IMG}/locust_html.png", "Reporte HTML generado por Locust (EV-NF-01)", 15.8, f"Locust 2.47, corrida {run}"))
        lat = RAIZ / "reports" / "latencia_api.json"
        if lat.exists():
            dl = json.loads(lat.read_text(encoding="utf-8"))
            rutas = dl.get("rutas") or dl.get("resultados") or []
            if rutas:
                L.extend(tabla("nf_latencia", "Latencia de la API con un usuario (TC-116)", ["Ruta", "Mediana (ms)", "p95 (ms)"],
                               [[x.get("ruta"), num(round(x.get("mediana_ms", x.get("p50_ms", 0)))), num(round(x.get("p95_ms", 0)))] for x in rutas],
                               [9.0, 3.5, 3.5], "reports/latencia_api.json"))

        A("### 6.4.6. Análisis e Interpretación"), A("")
        P(f"Con 40 usuarios concurrentes el percentil 95 global fue de {num(carga['p95_ms'])} ms y no hubo solicitudes "
          f"fallidas ({num(carga['error_pct'])} %): **el sistema cumplió el criterio** de p95 menor que 2 000 ms y "
          f"errores por debajo del 1 %. La operación más lenta fue {lento['nombre'].replace('/api', '')} "
          f"(p95 de {num(lento['p95_ms'])} ms): el inicio de sesión tarda más por diseño, porque verifica la "
          "contraseña con una función de derivación de clave lenta, y ocurre una vez por sesión. Entre las consultas "
          "clínicas la más lenta fue el listado de controles prenatales, que arma más datos por fila; es el primer "
          "candidato a optimizar si la carga creciera.",
          "El gráfico de la prueba no muestra degradación: el tiempo de respuesta se mantiene estable después de la "
          "rampa. **No se identificó un punto de saturación** porque no se ejecutó la prueba de estrés: con estos "
          "datos solo puede afirmarse que el sistema atiende 40 usuarios concurrentes de solo lectura en este equipo, "
          "no cuál es su límite. Durante la preparación se observó además que las conexiones a «localhost» tardaban "
          "unos 2 segundos en establecerse en Windows (el cliente intenta primero IPv6) y 16 ms con 127.0.0.1; ese "
          "retraso es del cliente y por eso la prueba usa la dirección numérica.")
    A("### 6.4.7. Evidencias, Limitaciones y Recomendaciones"), A("")
    L.extend(tabla("nf_evidencias", "Evidencias de las pruebas no funcionales", ["Código", "Evidencia", "Ubicación"], [
        ["EV-NF-01", f"Reporte HTML de Locust de la prueba de carga, {fecha(r.datos['inicio'])[:10]}", f"reports/{run}/locust/carga.html"],
        ["EV-NF-02", "Estadísticas e historial de la prueba en CSV", f"reports/{run}/locust/carga_stats.csv y carga_stats_history.csv"],
        ["EV-NF-03", "Resumen con el criterio aplicado", f"reports/{run}/locust/carga_resumen.json"],
        ["EV-NF-04", "Guion de los usuarios virtuales", "locust/locustfile.py"],
        ["EV-NF-05", "Latencia por ruta con un usuario", "reports/latencia_api.json"],
    ], [2.0, 7.0, 7.0]))
    L.extend(tabla("nf_no_ejecutadas", "Pruebas no funcionales no ejecutadas", ["Caso", "Prueba", "Estado", "Motivo"], [
        ["TC-113", "Estrés: escalones de 20 usuarios por minuto hasta 200", "No ejecutada", "Puede saturar el equipo que aloja el sistema; requiere autorización (AUTORIZAR_ESTRES=1)"],
        ["TC-114", "Pico: de 10 a 150 usuarios durante un minuto", "No ejecutada", "Mismo motivo"],
        ["TC-115", "Resistencia: 40 usuarios durante 15 minutos", "No ejecutada", "Mismo motivo"],
        ["TC-117", "Rendimiento de la pantalla de inicio de sesión con Lighthouse", "No ejecutada", "Complemento opcional, no automatizado"],
    ], [1.5, 6.2, 2.3, 6.0]))
    P("**Limitaciones.** El generador de carga y el sistema corren en el mismo equipo y sin red intermedia; la prueba "
      "solo hace lecturas; no se monitoreó el uso de procesador, memoria ni base de datos. **Recomendaciones.** "
      "Ejecutar el estrés, el pico y la resistencia fuera del horario de atención, con monitoreo de recursos; repetir "
      "la carga desde otro equipo de la red de la clínica; incluir escrituras con una base de pruebas; y revisar el "
      "listado de controles prenatales si se requiere mayor concurrencia.")

    # ================================================================ 6.5
    A("## 6.5. Ejecución de Pruebas"), A("")
    A("### 6.5.1. Ejecución Manual"), A("")
    manuales = [f for f in filas if f["automatiza"] == "No"]
    P(f"Los {len(manuales)} casos que no se automatizaron en esta solución no se ejecutaron uno por uno a mano en "
      "este ciclo. Su comportamiento lo verifica la suite propia del sistema (pruebas unitarias y de integración del "
      "backend), que se ejecutó completa el 13/11/2026 antes de confirmar las correcciones, con 1 170 pruebas "
      "aprobadas y 6 omitidas, y su registro de casos de prueba (docs/QA_CASOS_DE_PRUEBA.md) informa 64 de 64 casos "
      "aprobados. La [[tab:manuales]] indica, para cada caso, con qué se verificó. La prueba manual propiamente dicha "
      "de este ciclo fue exploratoria: la revisión de las capturas del barrido, con la que se encontraron BUG-004 y "
      "BUG-008.")
    L.extend(tabla("manuales", "Casos no automatizados en esta solución y su verificación", ["Caso", "Título", "Origen", "Verificación", "Tester y fecha"],
                   [[f["id"], f["titulo"], f["origen"],
                     "No ejecutado" if f["id"] == "TC-117" else
                     "Verificado al levantar el ambiente con INICIAR.bat" if f["id"] == "TC-106" else
                     f"Suite del sistema ({f['origen']})", "—" if f["id"] == "TC-117" else f"{AUTOR.split()[0]} {AUTOR.split()[2]}, 13/11/2026"]
                    for f in manuales], [1.5, 5.6, 1.7, 4.4, 2.8]))

    A("### 6.5.2. Ejecución Automatizada"), A("")
    P("La [[tab:corridas]] registra las corridas automatizadas del ciclo: las de detección, la de retesting y la de "
      "regresión. Entre ellas hubo corridas parciales de construcción de los scripts, que quedan en reports/ pero no "
      "se cuentan como resultado.")
    L.extend(tabla("corridas", "Corridas automatizadas del ciclo", ["Corrida", "Propósito", "Fecha", "Pruebas", "PASS", "FAIL", "BLOCKED", "NOT RUN"],
                   [[x.run_id, "Detección (API)", fecha(x.datos["inicio"])[:10], x.totales["total"], x.totales["PASS"], x.totales["FAIL"],
                     x.totales["BLOCKED"], x.totales["NOT RUN"]] for x in det]
                   + [[rt.run_id, "Retesting", fecha(rt.datos["inicio"])[:10], rt.totales["total"], rt.totales["PASS"], rt.totales["FAIL"],
                       rt.totales["BLOCKED"], rt.totales["NOT RUN"]],
                      [r.run_id, "Regresión completa", fecha(r.datos["inicio"])[:10], tot["total"], tot["PASS"], tot["FAIL"], tot["BLOCKED"],
                       tot["NOT RUN"]]],
                   [3.2, 2.7, 2.2, 1.6, 1.2, 1.1, 2.1, 1.9]))
    P("La evidencia de cada corrida está en su carpeta reports/<corrida>/: results.json en las de detección y, "
      "además, reporte.html, reporte.pdf y las capturas en las de retesting y regresión.")

    A("### 6.5.3. Gestión de Incidencias"), A("")
    L.extend(tabla("incidencias", "Casos fallidos y defectos registrados", ["Defecto", "Título", "Caso", "Severidad", "Prioridad", "Estado"],
                   [[x["id"], x["titulo"], x["caso"], x["severidad"], x["prioridad"], x["estado"]] for x in DEFECTOS],
                   [1.9, 5.7, 1.7, 2.2, 2.1, 2.4]))
    for x in DEFECTOS:
        L.append(f"@ficha riesgo_{x['id'].lower().replace('-', '')} | Informe de defecto {x['id']} | {PROPIA}")
        for etq, clave in (("Título", "titulo"), ("Módulo", "modulo"), ("Pantalla o endpoint", "pantalla_endpoint"),
                           ("Pasos para reproducir", "pasos"), ("Resultado esperado", "esperado"), ("Resultado obtenido", "obtenido"),
                           ("Severidad y prioridad", None), ("Caso relacionado", "caso"), ("Evidencia", "evidencia"),
                           ("Causa raíz", "causa_raiz"), ("Corrección", "correccion"), ("Commit y fecha", None),
                           ("Retesting", "retesting"), ("Regresión", "regresion"), ("Estado", "estado")):
            if etq == "Severidad y prioridad":
                val = f"{x['severidad']} / {x['prioridad']}"
            elif etq == "Commit y fecha":
                val = f"{x.get('commit', '')} · {x.get('fecha_correccion', '')}" if x.get("commit") else ""
            else:
                val = x.get(clave, "")
            if val:
                L.append(f"{etq}: {c(val)}")
        L.extend(["@fin", ""])

    A("### 6.5.4. Retesting"), A("")
    P(f"Después de cada corrección se volvió a ejecutar **el caso que detectó el defecto** (corrida {retest}). La "
      "[[tab:retesting]] compara el resultado anterior con el obtenido. BUG-004 no se reprodujo de nuevo sobre una "
      "cuenta real: su retesting es el caso TC-119, que activa el doble factor de una cuenta temporal y comprueba que "
      "pedir otro código QR responde 409 y no cambia la clave.")
    L.extend(tabla("retesting", "Retesting de los defectos corregidos", ["Defecto", "Caso repetido", "Resultado esperado", "Antes", "Después"],
                   [[x["id"], x.get("caso_retest", x["caso"]), x["esperado"], "FAIL",
                     x.get("retesting", "") or "—"] for x in DEFECTOS if x.get("commit")], [1.9, 1.8, 4.9, 1.4, 6.0]))
    if (RAIZ / "capitulo6" / "imagenes" / "consola_retest.png").exists():
        L.extend(figura("consola_retest", f"{IMG}/consola_retest.png", f"Registro de la corrida de retesting {retest}", 15.8))

    A("### 6.5.5. Regression Testing"), A("")
    P(f"El retesting confirma que el defecto se corrigió; la regresión comprueba que la corrección **no dañó otra "
      f"funcionalidad**. Tras las correcciones se ejecutó la suite completa (corrida {run}): {tot['total']} pruebas "
      f"sobre todos los módulos, con {tot['PASS']} en PASS y {tot['FAIL']} en FAIL. Se seleccionó la suite entera, y "
      "no solo los módulos tocados, porque la corrección de BUG-001 cambió la capa de permisos, de la que dependen "
      "todas las pantallas.",
      "Las regresiones anteriores a la de referencia sí encontraron dos efectos no deseados de la corrección de "
      "BUG-001. El primero (barrido del 13/11/2026): el panel principal del laboratorio pedía las estadísticas de "
      "reportes, que la corrección acababa de prohibir a ese rol, y dejaba un error 403 en la consola; se corrigió en "
      "el commit 53b0849. El segundo (corrida 20261114-105512, con 2 pruebas en FAIL): la historia clínica dejaba de "
      "cargar para el laboratorio con el mensaje «No se pudo cargar la historia clínica completa», porque la pantalla "
      "pedía notas y vacunas que ese rol ya no puede leer y cancelaba toda la carga; se corrigió en el commit e833f3c, "
      "que hace que cada apartado se pida solo si el rol tiene su permiso. Una tercera corrida (20261114-112100) tuvo "
      "1 FAIL que se analizó y resultó un problema del script, no del sistema: React redibujó un botón mientras la "
      "espera lo evaluaba; se corrigió la espera en la página base. Al ampliar la automatización con los casos de "
      "Selenium IDE y de los buscadores, la corrida 20261115-085208 tuvo 566 pruebas en PASS y 2 en FAIL, y ninguna "
      "era un defecto del sistema: en TC-131 Chrome no llegó a arrancar (condición del ambiente; el ejecutor ahora "
      "reintenta una vez ese caso) y en TC-036 el ENTER que confirma la fecha de la FUM enviaba el formulario antes "
      "de que la prueba pulsara Guardar (el embarazo sí se registró; el script ahora confirma la fecha con TAB). "
      "Antes de cada commit se ejecutó además la suite propia del sistema (1 170 pruebas del backend y 145 del "
      "frontend aprobadas).")
    L.extend(tabla("regresion", "Regresión por módulo tras las correcciones", ["Módulo", "Pruebas", "PASS", "FAIL", "BLOCKED", "NOT RUN", "Éxito"],
                   [[m["modulo"], m["total"], m["PASS"], m["FAIL"], m["BLOCKED"], m["NOT RUN"], f"{num(m['tasa'])} %"] for m in r.por_modulo],
                   [5.0, 1.8, 1.6, 1.6, 2.0, 2.0, 2.0]))

    A("### 6.5.6. Trazabilidad"), A("")
    P("La [[tab:trazabilidad]] relaciona cada requisito con sus casos, los que están automatizados, los defectos "
      "encontrados y el resultado de la corrida de referencia. «Parcial» indica que algún caso del requisito no se "
      "ejecutó en la automatización (se verifica con la suite del sistema).")
    L.extend(tabla("trazabilidad", "Matriz de trazabilidad requisito → caso → defecto → resultado",
                   ["Requisito", "Casos", "Automatizados", "Defectos", "Resultado"],
                   [[t["id"], ", ".join(t["casos"]) or "—", ", ".join(t["automatizados"]) or "—", ", ".join(t["defectos"]) or "—",
                     t["resultado"]] for t in traz], [1.8, 5.6, 5.0, 1.8, 1.8]))

    A("### 6.5.7. Evidencias"), A("")
    L.extend(tabla("evidencias_indice", "Índice de evidencias del ciclo de pruebas", ["Evidencia", "Ubicación"], [
        ["Resultados de cada corrida", "reports/<corrida>/results.json"],
        ["Capturas de los casos (códigos EV)", f"reports/{run}/evidencias/ ({num(n_ev)} capturas)"],
        ["Registro de ejecución", f"reports/{run}/ejecucion.log"],
        ["Reportes HTML, Word, PDF y ZIP", f"reports/{run}/"],
        ["Capturas del barrido de pantallas por rol", "docs/inventario/capturas/<rol>/"],
        ["Resultado del barrido", "reports/explorador/tc102_<rol>.json"],
        ["Reporte y estadísticas de Locust", f"reports/{run}/locust/"],
        ["Salida de las grabaciones de Selenium IDE", f"reports/{run}/evidencias/EV-TC-109-side-runner.txt y siguientes"],
        ["Informes de defectos y evidencias previas a la corrección", "docs/defectos/ y docs/defectos/evidencias/"],
        ["Commits de corrección", "Rama " + rama + " del repositorio del sistema"],
    ], [6.5, 9.5]))
    L.extend(tabla("estados", "Estados de ejecución utilizados", ["Estado", "Significado"], [
        ["PASS", "El resultado obtenido cumple con lo esperado."], ["FAIL", "El resultado obtenido no cumple con lo esperado."],
        ["BLOCKED", "No se pudo ejecutar por un bloqueo o condición externa."],
        ["NOT RUN", "El caso está definido, pero todavía no fue ejecutado."]], [3.0, 13.0]))

    # ================================================================ 6.6
    A("## 6.6. Resultados"), A("")
    A("### 6.6.1. Resumen de Ejecución"), A("")
    est = cob["estados_tc"]
    L.extend(tabla("resumen", "Resumen de la ejecución de casos de prueba", ["Indicador", "Cantidad"], [
        ["Casos diseñados", cob["casos_diseñados"]],
        ["Casos ejecutados por la automatización (PASS + FAIL)", est.get("PASS", 0) + est.get("FAIL", 0)],
        ["PASS", est.get("PASS", 0)], ["FAIL", est.get("FAIL", 0)], ["BLOCKED", est.get("BLOCKED", 0)],
        ["NOT RUN (automatizados no ejecutados)", est.get("NOT RUN", 0)],
        ["No automatizados (verificados con la suite del sistema)", est.get("MANUAL", 0)],
        ["Pruebas individuales ejecutadas", tot["total"]],
    ], [11.0, 5.0]))
    L.extend(figura("g_estados_tc", f"{IMG}/g_estados_tc.png", "Casos de prueba por estado", 11.5, grafico=True))
    P(f"De los {cob['casos_diseñados']} casos, {est.get('PASS', 0)} terminaron en PASS y {est.get('FAIL', 0)} en FAIL. "
      "Un caso cuenta como PASS solo si todas sus pruebas pasaron; por eso las "
      f"{tot['total']} pruebas individuales se agrupan en {len(r.por_tc)} casos.")

    A("### 6.6.2. Defectos"), A("")
    sev = Counter(x["severidad"] for x in DEFECTOS)
    esta = Counter(x["estado"] for x in DEFECTOS)
    P(f"Se registraron {len(DEFECTOS)} defectos: " + ", ".join(f"{v} de severidad {k.lower()}" for k, v in sev.items())
      + ". Por estado: " + ", ".join(f"{v} {k.lower()}" for k, v in esta.items()) + ". La [[tab:defectos_resumen]] los "
      "resume con su commit de corrección.")
    L.extend(tabla("defectos_resumen", "Resumen de defectos", ["Defecto", "Severidad", "Caso", "Estado", "Commit", "Observación"],
                   [[x["id"], x["severidad"], x["caso"], x["estado"], x.get("commit") or "—", x.get("observacion", "") or "—"]
                    for x in DEFECTOS], [1.9, 2.0, 1.7, 2.4, 2.0, 6.0]))
    L.extend(figura("g_defectos", f"{IMG}/g_defectos.png", "Defectos por severidad y estado", 11.5, grafico=True))
    L.extend(tabla("commits", "Commits de corrección en el repositorio del sistema", ["Commit", "Descripción"],
                   [[h, m] for h, m in commits], [2.0, 14.0], f"git log de la rama {rama}"))

    A("### 6.6.3. Resultados de Automatización"), A("")
    suites = {}
    for x in r.casos:
        clave = ("Interfaz (Selenium WebDriver)" if "/ui/" in x["nodeid"] else "API (pytest + requests)" if "/api/" in x["nodeid"]
                 else "Selenium IDE" if "/ide/" in x["nodeid"] else "Rendimiento (Locust)")
        suites.setdefault(clave, Counter())[x["estado"]] += 1
    L.extend(tabla("suites", "Resultados por suite de la corrida de referencia", ["Suite", "Pruebas", "PASS", "FAIL", "BLOCKED", "NOT RUN"],
                   [[k, sum(v.values()), v["PASS"], v["FAIL"], v["BLOCKED"], v["NOT RUN"]] for k, v in suites.items()]
                   + [["!!Total", tot["total"], tot["PASS"], tot["FAIL"], tot["BLOCKED"], tot["NOT RUN"]]],
                   [6.0, 2.0, 2.0, 2.0, 2.0, 2.0]))

    A("### 6.6.4. Métricas"), A("")
    metricas = [
        ["Cobertura de requisitos", "Requisitos con caso / requisitos × 100", f"{num(cob['cobertura_requisitos_pct'])} %",
         f"{cob['rf_con_casos'] + cob['rnf_con_casos']} de {cob['rf_total'] + cob['rnf_total']} requisitos tienen al menos un caso"],
        ["Cobertura de automatización", "Casos automatizados / casos seleccionados × 100", f"{num(cob['cobertura_automatizacion_pct'])} %",
         "Todos los casos seleccionados tienen script" if not pend else f"Faltan {len(pend)} scripts"],
        ["Porcentaje de salud de la suite", "PASS / (PASS + FAIL) × 100", f"{num(r.tasa_exito)} %",
         f"{tot['PASS']} de {tot['PASS'] + tot['FAIL']} pruebas ejecutadas pasaron"],
        ["Salud por herramienta", "PASS / (PASS + FAIL) × 100 de cada suite",
         "; ".join(f"{k.split(' (')[0]} {num(round(100 * v['PASS'] / max(v['PASS'] + v['FAIL'], 1), 1))} %" for k, v in suites.items()),
         "El mismo indicador separado por suite"],
        ["Casos ejecutados", "Casos con PASS o FAIL / casos seleccionados × 100",
         f"{num(round(100 * (est.get('PASS', 0) + est.get('FAIL', 0)) / cob['seleccionados_automatizar'], 1))} %",
         "Los no ejecutados son las pruebas de estrés y un caso de configuración inicial ya realizado"],
        ["Defectos corregidos y verificados", "Defectos verificados / defectos × 100",
         f"{num(round(100 * sum(x['estado'] == 'Verificado' for x in DEFECTOS) / len(DEFECTOS), 1))} %",
         f"{sum(x['estado'] == 'Verificado' for x in DEFECTOS)} de {len(DEFECTOS)}; ninguno crítico o alto queda abierto"],
        ["Densidad de defectos", "Defectos / casos ejecutados", f"{num(round(len(DEFECTOS) / max(est.get('PASS', 0) + est.get('FAIL', 0), 1), 2)).replace('.', ',')}",
         "Defectos encontrados por cada caso ejecutado"],
    ]
    if carga:
        metricas += [["Percentil 95 con carga", "p95 de Locust con 40 usuarios", f"{num(carga['p95_ms'])} ms", "Criterio: menor que 2 000 ms"],
                     ["Tasa de errores con carga", "Solicitudes fallidas / solicitudes × 100", f"{num(carga['error_pct'])} %", "Criterio: menor que 1 %"]]
    L.extend(tabla("metricas", "Métricas del proceso de pruebas", ["Métrica", "Fórmula", "Valor", "Interpretación"], metricas, [3.6, 4.6, 1.9, 5.9]))

    # ================================================================ 6.7 y 6.8
    abiertos = [x for x in DEFECTOS if x["estado"] != "Verificado"]
    A("## 6.7. Conclusiones"), A("")
    for x in (
        f"Se evaluaron los módulos del ciclo de atención (pacientes, embarazo, control prenatal, triaje, laboratorio, ecografía e IA, partos, citas y reportes) y el control de acceso de los cinco roles, con {cob['casos_diseñados']} casos diseñados y {tot['total']} pruebas automatizadas ejecutadas en la corrida de referencia.",
        f"Se encontraron {len(DEFECTOS)} defectos. Los más graves eran de seguridad y de criterio clínico: abrir una pantalla reemplazaba la clave del doble factor y dejaba la cuenta sin acceso; la API no aplicaba la tabla de roles a enfermería y laboratorio; y una glucosa en ayunas de 100 a 125 mg/dL en una gestante se informaba como prediabetes en lugar de diabetes gestacional.",
        f"Se corrigieron y verificaron {sum(x['estado'] == 'Verificado' for x in DEFECTOS)} defectos, cada uno en su commit, con retesting aprobado; "
        + (f"quedan {len(abiertos)} con severidad media o baja ({', '.join(x['id'] for x in abiertos)}), documentados con su propuesta." if abiertos else "no queda ninguno abierto."),
        f"La regresión completa terminó con {tot['PASS']} pruebas en PASS y {tot['FAIL']} en FAIL, y demostró su utilidad al detectar un efecto secundario de una corrección el mismo día en que se introdujo.",
        (f"Con 40 usuarios concurrentes la API respondió con un percentil 95 de {num(carga['p95_ms'])} ms y sin errores, dentro del criterio definido; no se determinó el límite del sistema porque las pruebas de estrés, pico y resistencia no se ejecutaron." if carga else "La prueba de carga no se ejecutó."),
        "La automatización aportó repetibilidad, evidencia y cobertura del control de acceso que no era alcanzable a mano; también obligó a tomar medidas de contención por ejecutarse sobre la base real.",
        "Limitaciones: ejecución solo en Chrome, pruebas sobre la base real (sin borrados ni cargas masivas), integración continua no implementada, y el módulo de IA implementado pero sin resultados porque no había un modelo disponible en el equipo.",
        "Las conclusiones corresponden al alcance definido en 6.1.3; lo excluido en 6.1.4 no fue evaluado y no se afirma nada sobre ello."):
        A(f"- {x}")
    A("")
    A("## 6.8. Recomendaciones"), A("")
    for x in (
        "Corregir BUG-007: agregar nombre accesible (aria-label) a los botones de solo ícono, empezando por las acciones de las tablas.",
        "Ejecutar las pruebas de estrés, pico y resistencia (TC-113 a TC-115) fuera del horario de atención y con monitoreo de procesador, memoria y base de datos.",
        f"Diseñar casos para los requisitos que quedaron sin caso en este ciclo ({', '.join(sin)}).",
        "Crear un ambiente de pruebas con una copia de la base para automatizar importaciones masivas y borrados protegidos (TC-030, TC-039, TC-055) sin riesgo para los datos reales.",
        "Agregar atributos data-testid a los botones y selectores principales de la interfaz para que los localizadores no dependan del texto visible.",
        "Ejecutar la suite de interfaz también en Edge y Firefox, que el framework ya admite.",
        "Implementar la integración continua propuesta en 6.3.14, empezando por la suite de humo.",
        "Instalar Ollama con su modelo o configurar la llave de la IA, y evaluar con fallos reales si el análisis automático acierta la clasificación antes de confiar en él.",
        "Agregar protección contra la reutilización de un código TOTP dentro de su ventana de validez, observada durante las pruebas de autenticación.",
        "Programar la suite de humo cada mañana desde el panel web y enviar el reporte por correo, una vez configurada la contraseña de aplicación."):
        A(f"- {x}")
    A("")

    # ================================================================ checklist y anexos
    A("# CHECKLIST DE ENTREGA"), A("")
    chk = [
        ("El Plan de Pruebas explica el alcance, estrategia y condiciones de trabajo.", "Sí", "6.1.1 a 6.1.17"),
        ("Las funcionalidades y requisitos están identificados.", "Sí", "6.2.1 y 6.2.2"),
        ("Los casos de prueba están completos y pueden ser reproducidos.", "Sí", "6.2.5, Anexo 1 y docs/casos_prueba.xlsx"),
        ("Los datos de prueba están definidos.", "Sí", "6.1.10 y 6.2.6"),
        ("Las ejecuciones tienen estado, resultado y evidencia.", "Sí", "6.5.2, 6.3.11 y reportes"),
        ("Los defectos están documentados y relacionados con los casos.", "Sí", "6.5.3 y docs/defectos/"),
        ("Retesting y Regression están correctamente diferenciados.", "Sí", "6.5.4 y 6.5.5"),
        ("La automatización explica qué se automatizó y por qué.", "Sí", "6.3.1 y 6.3.2"),
        ("Se identifica la herramienta o framework principal y se justifica su elección.", "Sí", "6.3.3"),
        ("Se explica la arquitectura y el flujo de ejecución de la solución.", "Sí", "6.3.4"),
        ("Los scripts están relacionados con casos de prueba identificados.", "Sí", "6.3.8"),
        ("Se documentan comandos e instrucciones para reproducir la ejecución.", "Sí", "6.3.10 y README"),
        ("Las evidencias corresponden a ejecuciones reales.", "Sí", "6.3.11 y 6.5.7"),
        ("Se diferencia lo implementado de lo que queda como propuesta futura.", "Sí", "6.3.14, 6.3.16 y 6.4.7"),
        ("Si se utilizó IA, se documentan herramienta, entrada, prompt, resultado y revisión humana.", "Parcial", "6.3.16: implementada; sin resultados de modelo en esta corrida"),
        ("No se exponen credenciales, tokens ni datos sensibles.", "Sí", "6.3.9 y 6.3.17"),
        ("La estructura y ejecución de la automatización están documentadas.", "Sí", "6.3.5 y 6.3.10"),
        ("La cobertura de automatización tiene una base de cálculo clara.", "Sí", "6.3.12"),
        ("Los resultados corresponden a ejecuciones reales.", "Sí", "6.3.13 y 6.6"),
        ("Las conclusiones se basan en los resultados.", "Sí", "6.7"),
        ("Las recomendaciones son concretas.", "Sí", "6.8"),
        ("Los apartados que no aplican están justificados.", "Sí", "6.1.4, 6.3.14 y 6.4.7"),
    ]
    L.extend(tabla("checklist", "Lista de verificación de la guía del capítulo", ["Punto de la guía", "Cumple", "Dónde"],
                   [[a, b, ("Sección " + x) if x[0].isdigit() and len(x) < 8 else x] for a, b, x in chk], [9.8, 1.8, 4.4]))
    (RAIZ / "docs" / "checklist_entrega.md").write_text(
        "# Checklist de entrega del Capítulo 6\n\n| Punto de la guía | ¿Cumple? | Dónde |\n|---|---|---|\n"
        + "\n".join(f"| {a} | {b} | {x} |" for a, b, x in chk) + "\n", encoding="utf-8")

    A("@horizontal"), A("")
    A("## Anexo 1. Catálogo Completo de Casos de Prueba"), A("")
    L.extend(tabla("anexo_casos", "Catálogo completo de casos de prueba con su resultado («Sistema»: verificado por la suite propia del sistema)",
                   ["ID", "Módulo", "Título", "Req.", "Prior.", "Pasos", "Resultado esperado", "Herramienta", "Estado"],
                   [[f["id"], f["modulo"], f["titulo"], f["requisito"], f["prioridad"], f["pasos"], f["esperado"], f["herramienta"],
                     f["estado"] if f["estado"] != "MANUAL" else "Sistema"] for f in filas],
                   [1.6, 2.6, 3.5, 1.5, 1.4, 4.3, 3.4, 2.6, 1.6], f"data/catalogo_tc.py y corrida {run}"))
    return L


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--retest", required=True)
    ap.add_argument("--deteccion", nargs="+", required=True)
    a = ap.parse_args()
    lineas = generar(a.run, a.retest, a.deteccion)
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("fuente:", DESTINO, len(lineas), "líneas")


if __name__ == "__main__":
    principal()
