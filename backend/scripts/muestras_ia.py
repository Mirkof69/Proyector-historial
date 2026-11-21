"""Arma en el Escritorio una carpeta con muestras REALES para cada modelo de IA,
las pasa por el sistema en marcha y guarda lo que respondió cada uno.

    python scripts/muestras_ia.py

Por cada modelo deja una subcarpeta con las imágenes de entrada, la imagen que
dibujó la red (``*__resultado.png``) y ``RESULTADO.txt`` con el valor de
referencia del experto, lo que respondió la red y cuánto tardó. Al final escribe
``LEEME.txt`` con el resumen de todas.

Necesita el microservicio de IA (8001). La cardiotocografía y el peso al nacer
pasan por el backend (8000) con la cuenta de la médica de demostración: su
contraseña se lee de E2E_PASSWORD (la misma variable que las pruebas E2E).
"""
from __future__ import annotations

import base64
import csv
import os
import shutil
import sys
import time
import unicodedata
from pathlib import Path

import openpyxl
import requests

BACKEND = Path(__file__).resolve().parents[1]
IA = BACKEND.parent / "redes-neuronales"
ENT = IA / "entrenamiento"
MULTI = IA / "datos/extraidos/obstetricia/FetalBiometry-Multicentre-Landmarks-2026/images/MULTICENTRE"
CEREBRO = IA / "datos/extraidos/fetal_brain_abnormalities/test"
DESTINO = Path(os.environ["USERPROFILE"]) / "Desktop" / "MUESTRAS_IA_Fetal_Medical"
API_IA = os.environ.get("API_IA", "http://127.0.0.1:8001/api")
# localhost y no 127.0.0.1: las cookies de sesión y la clínica se resuelven por el nombre.
API = os.environ.get("E2E_API", "http://localhost:8000/api")
EMAIL = os.environ.get("E2E_EMAIL", "dra.garcia@fetalmedical.bo")

resumen: list[dict] = []


def filas(ruta: Path) -> list[dict]:
    with open(ruta, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def hoja(nombre: str) -> list[dict]:
    libro = openpyxl.load_workbook(ENT / "redes_ecografia_real" / "catalogo_imagenes.xlsx", read_only=True)
    datos = libro[nombre].iter_rows(values_only=True)
    cab = next(datos)
    return [dict(zip(cab, f)) for f in datos]


def sin_tildes(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


def mm(valor) -> str:
    return f"{float(valor):.1f}".replace(".", ",")


class Modelo:
    """Una subcarpeta: copia las entradas, llama a la red y anota cada respuesta."""

    def __init__(self, carpeta: str, titulo: str, tipo: str, pantalla: str, cifra: str, nota: str = ""):
        self.dir = DESTINO / carpeta
        self.dir.mkdir(parents=True, exist_ok=True)
        self.titulo, self.lineas, self.casos = titulo, [], []
        self.lineas += [titulo, "=" * len(titulo), f"Tipo de modelo: {tipo}",
                        f"Dónde se usa en el sistema: {pantalla}", f"Rendimiento medido: {cifra}"]
        if nota:
            self.lineas.append(f"Ojo: {nota}")
        self.lineas.append("")

    def copiar(self, origen: Path, nombre: str) -> Path:
        destino = self.dir / (nombre + origen.suffix.lower())
        shutil.copyfile(origen, destino)
        return destino

    def llamar(self, ruta: str, archivo: Path, datos: dict | None = None) -> tuple[dict, int]:
        t0 = time.perf_counter()
        with open(archivo, "rb") as f:
            r = requests.post(API_IA + ruta, files={"file": (archivo.name, f)}, data=datos or {}, timeout=120)
        ms = round((time.perf_counter() - t0) * 1000)
        r.raise_for_status()
        resp = r.json()
        if resp.get("superposicion_png"):
            (self.dir / f"{archivo.stem}__resultado.png").write_bytes(base64.b64decode(resp["superposicion_png"]))
        return resp, ms

    def caso(self, archivo: str, referencia: str, obtenido: str, concuerda: bool | None, ms: int, extra=()):
        marca = {True: "CONCUERDA", False: "NO CONCUERDA", None: "sin referencia"}[concuerda]
        self.lineas += [f"■ {archivo}", f"   Referencia: {referencia}", f"   La red respondió: {obtenido}",
                        *[f"   {e}" for e in extra], f"   Resultado: {marca} · {ms} ms", ""]
        self.casos.append(concuerda)
        print(f"  {archivo}: {obtenido} [{marca}, {ms} ms]")

    def cerrar(self):
        (self.dir / "RESULTADO.txt").write_text("\r\n".join(self.lineas), encoding="utf-8-sig")
        con_ref = [c for c in self.casos if c is not None]
        resumen.append({"modelo": self.titulo, "carpeta": self.dir.name, "muestras": len(self.casos),
                        "concuerdan": f"{sum(con_ref)} de {len(con_ref)}" if con_ref else "sin referencia"})


def plano():
    m = Modelo("01_plano_anatomico", "Plano anatómico de la ecografía", "CNN de clasificación (EfficientNet-B0)",
               "Análisis CNN (IA) → Ecografía → Analizar (decide qué red mide la imagen)",
               "exactitud 92,7 % en 5.271 imágenes de 896 madres no vistas (FETAL_PLANES_DB)")
    vistos = set()
    for f in hoja("Planos"):
        if f["particion"] != "prueba" or f["plano"] in vistos:
            continue
        vistos.add(f["plano"])
        archivo = m.copiar(ENT / "redes_ecografia_real" / f["ruta"], "plano_" + f["plano"].replace(" ", "_"))
        r, ms = m.llamar("/plano-anatomico", archivo)
        m.caso(archivo.name, f["plano"], f"{r['plano']} ({r['confianza']:.0%} de confianza)", r["plano"] == f["plano"], ms)
    m.cerrar()


def cabezas_hc18() -> list[dict]:
    """Una cabeza de prueba de HC18 (otro hospital) por trimestre."""
    elegidas = {}
    for f in hoja("HC18"):
        if f["particion"] == "prueba" and f["trimestre"] not in elegidas:
            elegidas[f["trimestre"]] = f
    return [elegidas[t] for t in ("primero", "segundo", "tercero") if t in elegidas]


def circunferencia_cefalica():
    m = Modelo("02_circunferencia_cefalica_regresion", "Circunferencia cefálica (regresión)",
               "CNN de regresión: devuelve directamente el número en mm",
               "Análisis CNN (IA) → Ecografía → Analizar, con el tamaño de píxel",
               "R² 0,978, error medio 7,0 mm en 146 imágenes de 117 madres no vistas (HC18)")
    for f in cabezas_hc18():
        archivo = m.copiar(ENT / "redes_ecografia_real" / f["ruta"], f"cabeza_{f['trimestre']}_trimestre")
        r, ms = m.llamar("/biometria/circunferencia-cefalica", archivo, {"tamano_pixel_mm": f["tamano_pixel_mm"]})
        ref, hc = float(f["circunferencia_cefalica_mm"]), r["circunferencia_cefalica_mm"]
        m.caso(archivo.name, f"{mm(ref)} mm medida por el ecografista (tamaño de píxel {f['tamano_pixel_mm']} mm)",
               f"{mm(hc)} mm ± {mm(r['margen_mm'])} → edad gestacional {mm(r['edad_gestacional_semanas'])} semanas",
               abs(hc - ref) / ref <= 0.05, ms, [f"Diferencia: {mm(abs(hc - ref))} mm ({abs(hc - ref) / ref:.1%})"])
    m.cerrar()


def unet_cabeza():
    m = Modelo("03_unet_cabeza", "Cabeza fetal (segmentación U-Net)",
               "CNN de segmentación U-Net: pinta cráneo, cavum y ventrículo y mide sobre la silueta",
               "Análisis CNN (IA) → Ecografía → Informe completo, con el tamaño de píxel",
               "error de 4,4 mm en 999 cabezas de otro hospital (HC18); el 92 % dentro del 5 %")
    for f in cabezas_hc18():
        archivo = m.copiar(ENT / "redes_ecografia_real" / f["ruta"], f"cabeza_{f['trimestre']}_trimestre")
        r, ms = m.llamar("/segmentacion/cabeza", archivo, {"tamano_pixel_mm": f["tamano_pixel_mm"]})
        md, ref = r["medidas"], float(f["circunferencia_cefalica_mm"])
        hc = md["circunferencia_cefalica_mm"]
        m.caso(archivo.name, f"{mm(ref)} mm medida por el ecografista",
               f"CC {mm(hc)} mm ± {mm(md['margen_hc_mm'])} · DBP {mm(md['diametro_biparietal_mm'])} mm "
               f"→ {mm(md['edad_gestacional_por_hc_semanas'])} semanas",
               abs(hc - ref) / ref <= 0.05, ms,
               [f"Estructuras vistas: {', '.join(k for k, v in r['estructuras_vistas'].items() if v) or 'ninguna'}",
                f"Imagen dibujada: {archivo.stem}__resultado.png"])
    m.cerrar()


def torax():
    m = Modelo("04_unet_torax", "Tórax fetal (segmentación U-Net)",
               "CNN de segmentación U-Net: pinta tórax y corazón y calcula el índice cardiotorácico",
               "Análisis CNN (IA) → Ecografía → Informe completo",
               "Dice 0,93; índice cardiotorácico con error ±0,02 (FOCUS)")
    for i, f in enumerate([f for f in filas(ENT / "segmentacion/catalogos/torax.csv") if f["particion"] == "prueba"][:2], 1):
        archivo = m.copiar(IA / f["imagen"], f"torax_{i}")
        r, ms = m.llamar("/segmentacion/torax", archivo)
        md = r["medidas"]
        lo, hi = md["referencia_areas"]
        m.caso(archivo.name, f"rango de referencia por áreas: {lo} a {hi}".replace(".", ","),
               f"índice cardiotorácico {md['indice_cardiotoracico_areas']:.3f} ± {md['margen']:.3f} (áreas)".replace(".", ","), None, ms,
               [f"Imagen dibujada: {archivo.stem}__resultado.png"])
    m.cerrar()


def abdomen():
    m = Modelo("05_unet_abdomen", "Abdomen fetal (segmentación U-Net)",
               "CNN de segmentación U-Net: hígado, estómago, vena umbilical y aorta",
               "Análisis CNN (IA) → Ecografía → Informe completo (dice si el corte sirve para medir la CA)",
               "Dice 0,69 a 0,84 según la estructura")
    for i, f in enumerate(filas(ENT / "biometria/salidas/abdomen/prueba_medidas.csv")[:2], 1):
        archivo = m.copiar(MULTI / "Abdomen" / f["imagen"], f"abdomen_{i}")
        r, ms = m.llamar("/segmentacion/abdomen", archivo)
        vistas = [k for k, v in r["estructuras_vistas"].items() if v]
        m.caso(archivo.name, "corte abdominal elegido por el experto para medir la CA",
               f"ve {', '.join(vistas) or 'nada'}; corte adecuado para la CA: "
               f"{'sí' if r['medidas'].get('plano_adecuado_para_ca') else 'no'}",
               bool(r["medidas"].get("plano_adecuado_para_ca")), ms, [f"Imagen dibujada: {archivo.stem}__resultado.png"])
    m.cerrar()


def puntos(carpeta, titulo, csv_tarea, sub, ruta, clave_red, clave_exp, nombre, cifra):
    m = Modelo(carpeta, titulo, "CNN de puntos de referencia: ubica los extremos y mide la distancia",
               "Análisis CNN (IA) → Ecografía → Informe completo, con el tamaño de píxel", cifra)
    for i, f in enumerate(filas(ENT / f"biometria/salidas/{csv_tarea}/prueba_medidas.csv")[:2], 1):
        archivo = m.copiar(MULTI / sub / f["imagen"], f"{nombre}_{i}")
        px = f"{float(f['mm_por_px']):.4f}"
        r, ms = m.llamar(ruta, archivo, {"tamano_pixel_mm": px})
        ref, red = float(f[clave_exp]), r["medidas"][clave_red]
        m.caso(archivo.name, f"{mm(ref)} mm medida por el experto (tamaño de píxel {px} mm)", f"{mm(red)} mm",
               abs(red - ref) / ref <= 0.05, ms,
               [f"Diferencia: {mm(abs(red - ref))} mm ({abs(red - ref) / ref:.1%})",
                f"Imagen dibujada: {archivo.stem}__resultado.png"])
    m.cerrar()


def veredicto_cerebro(r: dict) -> str:
    if not r.get("aplicable", True):
        return f"no la evalúa: el clasificador de planos ve «{r.get('plano_detectado')}», no un corte de la cabeza"
    texto = f"{'ALARMA' if r['alarma_anomalia'] else 'sin alarma'}, P(anomalía) {r['probabilidad_anomalia']:.0%}"
    return texto + (f", familia sospechada: {r['familia_sospechada_nombre']}" if r["alarma_anomalia"] else "")


def anomalias_cerebrales():
    m = Modelo("08_anomalias_cerebrales", "Cribado de anomalías cerebrales", "CNN de clasificación (EfficientNet-B0)",
               "Análisis CNN (IA) → Ecografía → Analizar (corte axial de la cabeza)",
               "1 falsa alarma en 1.866 cabezas normales de otro hospital; la sensibilidad real en ecografías "
               "clínicas no se puede medir con los datos públicos",
               "las imágenes con anomalía forman parte de las 212 con las que se entrenó el modelo final (sus cifras "
               "salen de validación cruzada); las cabezas normales son de HC18, que esta red nunca vio. Es solo cribado.")
    familias = [("ventriculomegaly", "ventriculomegalia_hidrocefalia"), ("encephalocele", "encefalocele"),
                ("arachnoid-cyst", "lesion_quistica_vascular"), ("cerebellah-hypoplasia", "fosa_posterior")]
    for patron, familia in familias:
        origen = next((p for p in sorted(CEREBRO.glob("*.jpg")) if patron in p.name and "_aug" not in p.name), None)
        if not origen:
            continue
        archivo = m.copiar(origen, f"anomalia_{familia}")
        r, ms = m.llamar("/anomalias-cerebrales", archivo)
        m.caso(archivo.name, f"anomalía ({familia.replace('_', ' ')})", veredicto_cerebro(r),
               r.get("aplicable", True) and bool(r.get("alarma_anomalia")), ms, r.get("avisos", [])[:1])
    for f in cabezas_hc18()[1:]:
        archivo = m.copiar(ENT / "redes_ecografia_real" / f["ruta"], f"normal_cabeza_{f['trimestre']}_trimestre")
        r, ms = m.llamar("/anomalias-cerebrales", archivo)
        m.caso(archivo.name, "cabeza normal (HC18, otro hospital)", veredicto_cerebro(r),
               r.get("aplicable", True) and not r.get("alarma_anomalia"), ms)
    m.cerrar()


def intraparto():
    m = Modelo("09_unet_intraparto", "Ángulo de progresión intraparto (segmentación U-Net)",
               "CNN de segmentación U-Net: sínfisis del pubis y cabeza fetal, y de ahí el ángulo",
               "Partos → abrir un parto → Trabajo de parto → Registrar tacto → subir la imagen",
               "error medio de 6,7° en el ángulo de progresión (IUGC 2024)")
    for i, f in enumerate(filas(ENT / "segmentacion/salidas/intraparto/prueba_medidas.csv")[:2], 1):
        archivo = m.copiar(IA / f["imagen"], f"intraparto_{i}")
        r, ms = m.llamar("/segmentacion/intraparto", archivo)
        ref, red = float(f["aop_experto"]), r["medidas"]["angulo_progresion_grados"]
        m.caso(archivo.name, f"{mm(ref)}° medido por el experto", f"{mm(red)}° ± {mm(r['medidas']['margen_grados'])}",
               abs(red - ref) <= r["medidas"]["margen_grados"] * 2, ms,
               [f"Interpretación: {r['medidas'].get('interpretacion', '')}", f"Diferencia: {mm(abs(red - ref))}°",
                f"Imagen dibujada: {archivo.stem}__resultado.png"])
    m.cerrar()


def campos_csv(ruta: Path) -> list[dict]:
    """Catálogos ginecológicos: las cajas del mioma llevan comas dentro de comillas."""
    with open(ruta, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ovario():
    m = Modelo("10_lesion_ovarica", "Masa ovárica (U-Net + 2 clasificadores)",
               "U-Net que pinta la lesión + conjunto de 2 EfficientNet-B0 que votan el tipo y la malignidad",
               "Análisis CNN (IA) → Ecografía ginecológica → Masa ovárica",
               "lesión encontrada en el 88 % (Dice 0,85); tipo acertado en el 68,6 %; detecta 7 de 13 carcinomas",
               "es orientativa: no sirve como tamizaje de cáncer (puede no alarmar ante un carcinoma).")
    catalogo = campos_csv(ENT / "ginecologia/catalogos/ovario.csv")
    for clase in ("teratoma", "cistoadenoma_seroso", "quiste_endometriosico", "carcinoma_seroso_alto_grado",
                  "ovario_normal"):
        f = next((f for f in catalogo if f["particion"] == "prueba" and f["clase_nombre"] == clase), None)
        if not f:
            continue
        archivo = m.copiar(IA / f["imagen"], f"ovario_{clase}")
        r, ms = m.llamar("/ginecologia/ovario", archivo)
        top = r["probabilidades"][0] if r.get("probabilidades") else {}
        mal = r.get("malignidad") or {}
        esperado = clase.replace("_", " ")
        m.caso(archivo.name, f"{esperado} (diagnóstico del hospital)",
               f"tipo probable: {r.get('tipo_probable')} ({top.get('probabilidad', 0):.0%}); "
               f"alarma de malignidad: {'SÍ' if mal.get('alarma') else 'no'} (P {mal.get('probabilidad', 0):.0%})",
               sin_tildes(r.get("tipo_probable") or "").startswith(" ".join(clase.split("_")[:2])), ms,
               [f"Lesión encontrada por la U-Net: {'sí' if r.get('lesion_encontrada') else 'no'}",
                f"Imagen dibujada: {archivo.stem}__resultado.png"])
    m.cerrar()


def mioma():
    m = Modelo("11_mioma", "Mioma uterino (segmentación U-Net)", "CNN de segmentación U-Net: ubica el mioma",
               "Análisis CNN (IA) → Ecografía ginecológica → Mioma",
               "ubica el 96,9 % de los miomas (Dice 0,88) en 128 imágenes de 118 pacientes no vistas",
               "se entrenó solo con úteros con mioma: no sirve para decir que un útero NO tiene mioma.")
    for i, f in enumerate([f for f in campos_csv(ENT / "ginecologia/catalogos/mioma.csv") if f["particion"] == "prueba"][:2], 1):
        archivo = m.copiar(IA / f["imagen"], f"mioma_{i}")
        r, ms = m.llamar("/ginecologia/mioma", archivo)
        m.caso(archivo.name, f"{f.get('miomas') or 'al menos un'} mioma(s) marcados por el especialista",
               f"mioma ubicado: {'sí' if r.get('mioma_ubicado') else 'no'}", bool(r.get("mioma_ubicado")), ms,
               [f"Imagen dibujada: {archivo.stem}__resultado.png"])
    m.cerrar()


def ovario_pco():
    m = Modelo("12_ovario_poliquistico", "Ovario poliquístico", "CNN de clasificación (EfficientNet-B0)",
               "Análisis CNN (IA) → Ecografía ginecológica → Ovario poliquístico",
               "exactitud 80 % en 295 imágenes (validación cruzada de 5 pliegues)",
               "el modelo final se entrenó con todas las imágenes; la cifra fiable es la de validación cruzada. "
               "El SOP se diagnostica con los criterios de Rotterdam, no solo con la imagen.")
    nombres = {"normal": "Ovario normal", "foliculo_dominante": "Folículo dominante", "poliquistico": "Ovario poliquístico"}
    catalogo = campos_csv(ENT / "ginecologia/catalogos/ovario_pco.csv")
    for clase, nombre in nombres.items():
        f = next((f for f in catalogo if f["clase_nombre"] == clase), None)
        if not f:
            continue
        archivo = m.copiar(IA / f["ruta"], f"ovario_{clase}")
        r, ms = m.llamar("/ginecologia/ovario-pco", archivo)
        top = r["probabilidades"][0]
        m.caso(archivo.name, nombre, f"{r['categoria_probable']} ({top['probabilidad']:.0%})",
               r["categoria_probable"] == nombre, ms)
    m.cerrar()


def sesion_backend() -> requests.Session | None:
    clave = os.environ.get("E2E_PASSWORD")
    if not clave:
        print("  (sin E2E_PASSWORD: se omiten cardiotocografía y peso al nacer)")
        return None
    s = requests.Session()
    r = s.post(f"{API}/usuarios/login/", json={"email": EMAIL, "password": clave}, timeout=30)
    if r.status_code != 200 or "user" not in r.json():
        print(f"  (no se pudo entrar como {EMAIL}: HTTP {r.status_code})")
        return None
    s.headers["X-CSRFToken"] = s.cookies.get("csrftoken", "")
    s.headers["Referer"] = API
    return s


def cardiotocografia(s: requests.Session):
    sys.path.insert(0, str(BACKEND))
    from sklearn.model_selection import train_test_split

    from ia_medica.ml import cardiotocografia as ctg

    m = Modelo("13_cardiotocografia", "Cardiotocografía (aprendizaje supervisado)",
               "Gradient Boosting por histogramas (clasificación supervisada sobre una tabla de 21 variables)",
               "Análisis CNN (IA) → pestaña Cardiotocografía → escribir las 21 variables → Clasificar",
               "exactitud 96 % en 423 registros que el modelo no vio; detecta el 94 % de los patológicos")
    X, y, _ = ctg.cargar_datos()
    _, X_p, _, y_p = train_test_split(X, y, test_size=0.20, stratify=y, random_state=ctg.SEMILLA)
    nombres = ["Normal", "Sospechosa", "Patológica"]
    for clase, nombre in enumerate(nombres):
        fila = X_p[y_p == clase].iloc[0]
        valores = {ctg.VARIABLES[c][0]: float(fila[c]) for c in ctg.VARIABLES}
        t0 = time.perf_counter()
        r = s.post(f"{API}/ia/cardiotocografia/", json=valores, timeout=60)
        ms = round((time.perf_counter() - t0) * 1000)
        r.raise_for_status()
        res = r.json()
        entrada = m.dir / f"ctg_{nombre.lower()}.txt"
        entrada.write_text("\r\n".join([f"Registro {nombre.upper()} (consenso de 3 obstetras, conjunto de prueba)",
                                        "Valores a escribir en la pestaña Cardiotocografía:", ""]
                                       + [f"{ctg.VARIABLES[c][1]} ({ctg.VARIABLES[c][2]}) = {float(fila[c]):g}"
                                          for c in ctg.VARIABLES]), encoding="utf-8-sig")
        probs = res.get("probabilidades") or {}
        texto_probs = ", ".join(f"{k} {v:.0%}" for k, v in probs.items()) if isinstance(probs, dict) else ""
        m.caso(entrada.name, f"{nombre} (consenso de 3 obstetras)",
               f"{res.get('clase_nombre')}" + (f" ({texto_probs})" if texto_probs else ""),
               str(res.get("clase_nombre", "")).lower() == nombre.lower(), ms)
    m.cerrar()


def peso_al_nacer(s: requests.Session):
    m = Modelo("14_peso_al_nacer", "Peso al nacer (aprendizaje supervisado)",
               "Regresión Ridge (regresión lineal supervisada) sobre la biometría de la ecografía",
               "Ecografías → abrir una ecografía con biometría → pestaña Biometría → «Peso al nacer previsto» → Calcular",
               "error medio 183 g, pero medido sobre datos SIMULADOS",
               "solo de demostración: no hay datos reales bolivianos de ecografía + peso al nacer para entrenarlo. "
               "La pantalla lo compara con la fórmula clínica de Hadlock.")
    ecos = s.get(f"{API}/ecografias/?page_size=100", timeout=60).json()
    for eco in (ecos.get("results", ecos) if isinstance(ecos, dict) else ecos):
        t0 = time.perf_counter()
        r = s.post(f"{API}/ia/prediccion-peso/", json={"ecografia_id": eco["id"]}, timeout=60)
        ms = round((time.perf_counter() - t0) * 1000)
        if r.status_code != 200:
            continue
        res = r.json()
        m.caso(f"ecografía n.º {eco['id']} de la base", "peso previsto a las 39 semanas",
               f"{res['peso_previsto_g']} g (Hadlock proyectado: {res.get('peso_hadlock_proyectado_g')} g)", None, ms,
               [f"Clase: {res.get('clase') or '-'}"])
        break
    m.cerrar()


def main():
    try:
        requests.get(API_IA.replace("/api", "/health"), timeout=10).raise_for_status()
    except requests.RequestException as e:
        sys.exit(f"El microservicio de IA no responde ({e}). Arranque el sistema con INICIAR.bat.")
    DESTINO.mkdir(parents=True, exist_ok=True)
    pasos = [plano, circunferencia_cefalica, unet_cabeza, torax, abdomen,
             lambda: puntos("06_puntos_femur", "Longitud del fémur (puntos de referencia)", "femur", "Femur",
                            "/biometria/longitud-femur", "longitud_femur_mm", "fl_experto_mm", "femur",
                            "error medio 1,3 mm; el 92 % dentro del 5 % (4 hospitales)"),
             lambda: puntos("07_puntos_circunferencia_abdominal", "Circunferencia abdominal (puntos de referencia)",
                            "abdomen", "Abdomen", "/biometria/circunferencia-abdominal", "circunferencia_abdominal_mm",
                            "ca_experto_mm", "abdomen", "error medio 2,9 %; el 89 % dentro del 5 %"),
             anomalias_cerebrales, intraparto, ovario, mioma, ovario_pco]
    for paso in pasos:
        paso()
    s = sesion_backend()
    if s:
        cardiotocografia(s)
        peso_al_nacer(s)

    lineas = ["MUESTRAS DE IA — Fetal Medical Bolivia",
              f"Generado el {time.strftime('%d/%m/%Y %H:%M')} con el sistema en marcha: cada resultado es la respuesta",
              "real de la red, no un texto escrito a mano. Las imágenes son de pacientes de los conjuntos de PRUEBA",
              "(salvo donde RESULTADO.txt avisa lo contrario).", "",
              f"{'Carpeta':<40} {'Muestras':>8}  Concuerdan con el experto"]
    lineas += [f"{r['carpeta']:<40} {r['muestras']:>8}  {r['concuerdan']}" for r in resumen]
    lineas += ["", "«Concuerda» = misma clase que el experto o medida dentro del 5 % de la suya (ángulo: dentro de",
               "dos márgenes). Cuando una red NO concuerda se deja a la vista: así se ve por qué el sistema",
               "muestra siempre el margen de error y pide la confirmación del especialista."]
    (DESTINO / "LEEME.txt").write_text("\r\n".join(lineas), encoding="utf-8-sig")
    print("\n".join(lineas))


if __name__ == "__main__":
    main()
