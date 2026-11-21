"""Redes entrenadas con ecografías REALES, con anotación de experto.

1. Circunferencia cefálica (regresión) — HC18, Zenodo 1327317, CC BY 4.0.
   999 imágenes de 779 madres, medidas por ecografistas del Radboud UMC.
2. Plano anatómico (clasificación, 6 clases) — FETAL_PLANES_DB, Zenodo
   3904280, CC BY 4.0. 12.400 imágenes de 1.792 madres, Barcelona.
3. Anomalías cerebrales (normal + 4 familias) — Fetal Brain Abnormalities
   (Roboflow, 212 imágenes originales) + cortes normales de FETAL_PLANES_DB.
   Se entrena en `entrenamiento/patologias_cerebrales/` y sus métricas (validación
   cruzada agrupada y prueba externa) viajan DENTRO del .pth.

Se entrenan en `redes-neuronales/entrenamiento/redes_ecografia_real/redes_ecografia_real.ipynb`
y los pesos se copian a `modelos-ia/redes/`. El preprocesado de aquí tiene que
ser idéntico al del entrenamiento (`cnn_ecografia.py`): gris, relleno a
cuadrado sin deformar, reducción al lado de la red y normalización ImageNet.
Si se cambia uno, hay que cambiar el otro.

A diferencia de la EfficientNet-B4 de `models.py`, estas dos redes sí tienen
métricas medidas sobre madres que no vieron al entrenar (METRICAS_PRUEBA).
"""

from __future__ import annotations

import logging
import threading
from typing import Any

import numpy as np
from PIL import Image

from .config import MODELS_DIR, huella_sha256

logger = logging.getLogger(__name__)

MEDIA = 0.485
DESV = 0.229

ARCHIVO_HC = "circunferencia_cefalica_hc18"
ARCHIVO_PLANO = "plano_anatomico_fetal_planes"
ARCHIVO_CEREBRO = "anomalias_cerebrales_fetales"

# Probabilidad mínima de «cerebro fetal» (clasificador de planos) para pasar la
# imagen a la red de anomalías. Medido el 30/09/2026:
#   · de 110 cabezas CON anomalía, el clasificador de planos solo ve «cerebro»
#     como plano más probable en 66 (la anomalía deforma la cabeza); con
#     P(cerebro) ≥ 0,02 se analizan 104;
#   · en 3.199 imágenes de prueba que NO son cabezas (no usadas para elegir el
#     umbral) quedan 13 falsas alarmas (0,4 %; cuello uterino 9/495).
# Sin este corte, el cuello uterino daba alarma en el 70 % de los casos.
PROB_MINIMA_CEREBRO = 0.02

NOMBRES_FAMILIA = {
    "normal": "Sin anomalía visible",
    "ventriculomegalia_hidrocefalia": "Ventriculomegalia / hidrocefalia",
    "fosa_posterior": "Anomalía de fosa posterior",
    "encefalocele": "Encefalocele",
    "lesion_quistica_vascular": "Lesión quística, hemorrágica o vascular",
}

# Medido en el notebook sobre el conjunto de prueba (madres no vistas).
METRICAS_PRUEBA = {
    ARCHIVO_HC: {
        "imagenes_prueba": 146,
        "madres_prueba": 117,
        "r2": 0.978,
        "error_medio_mm": 7.0,
        "error_mediano_mm": 5.4,
        "error_medio_semanas": 0.62,
    },
    ARCHIVO_PLANO: {
        "imagenes_prueba": 5271,
        "madres_prueba": 896,
        "exactitud": 0.927,
        "auc_medio": 0.992,
        # Las 999 cabezas de HC18: otro hospital (Radboud) y otros ecógrafos.
        "cabezas_otro_hospital_reconocidas": 0.931,
        "cabezas_primer_trimestre_reconocidas": 0.588,
    },
}

# Por debajo de esto la respuesta lleva aviso: la red duda entre planos.
CONFIANZA_MINIMA_PLANO = 0.70
# Rango de circunferencia cefálica que había en HC18 (unos 44–346 mm).
# Fuera de él la red extrapola y no hay nada medido que respalde el número.
HC_MIN_MM, HC_MAX_MM = 45.0, 350.0
# Unos 100 mm de cabeza son la semana 14 (Hadlock 1984).
HC_PRIMER_TRIMESTRE_MM = 100.0


def edad_gestacional_hadlock_1984(hc_mm: float) -> float:
    """Semanas de gestación a partir de la circunferencia cefálica.

    Hadlock FP et al. Radiology 1984;152:497-501:
        EG = 8,96 + 0,540·HC + 0,0003·HC³   (HC en cm)
    """
    hc_cm = hc_mm / 10.0
    return 8.96 + 0.540 * hc_cm + 0.0003 * hc_cm**3


def a_cuadrado_gris(imagen: np.ndarray | Image.Image, lado: int) -> tuple[np.ndarray, int]:
    """Gris, rellenado a cuadrado SIN deformar, reducido a `lado`.

    Devuelve también el lado mayor original en píxeles, que es con lo que la
    salida de la red (fracción del lado mayor) se pasa a milímetros.
    """
    img = imagen if isinstance(imagen, Image.Image) else Image.fromarray(imagen)
    img = img.convert("L")
    w, h = img.size
    mayor = max(w, h)
    lienzo = Image.new("L", (mayor, mayor), 0)
    lienzo.paste(img, ((mayor - w) // 2, (mayor - h) // 2))
    return np.array(lienzo.resize((lado, lado), Image.BILINEAR), dtype=np.uint8), mayor


class RedesEcografiaReal:
    """Carga las dos redes una sola vez por proceso, la primera vez que se piden."""

    def __init__(self, carpeta=MODELS_DIR):
        self.carpeta = carpeta
        self._redes: dict[str, tuple[Any, dict]] = {}
        self._cerrojo = threading.Lock()
        self._dispositivo = None

    def disponible(self, nombre: str) -> bool:
        return (self.carpeta / f"{nombre}.pth").exists()

    def estado(self) -> dict:
        """Qué redes medidas están disponibles, con sus métricas en prueba."""
        return {
            nombre: {"disponible": self.disponible(nombre), "metricas_prueba": METRICAS_PRUEBA.get(nombre),
                     "sha256": huella_sha256(self.carpeta / f"{nombre}.pth")}
            for nombre in (ARCHIVO_PLANO, ARCHIVO_HC)
        } | {
            ARCHIVO_CEREBRO: {"disponible": self.disponible(ARCHIVO_CEREBRO),
                              "metricas_prueba": self._metricas_cerebro(),
                              "sha256": huella_sha256(self.carpeta / f"{ARCHIVO_CEREBRO}.pth")}
        }

    def _metricas_cerebro(self) -> dict | None:
        """Métricas de la ficha .json que acompaña al .pth (sin cargar la red)."""
        ficha = self.carpeta / f"{ARCHIVO_CEREBRO}.json"
        if not ficha.exists():
            return None
        import json

        return json.loads(ficha.read_text(encoding="utf-8")).get("metricas")

    def _cargar(self, nombre: str):
        with self._cerrojo:
            if nombre in self._redes:
                return self._redes[nombre]
            import timm
            import torch

            ruta = self.carpeta / f"{nombre}.pth"
            if not ruta.exists():
                raise FileNotFoundError(
                    f"No está el modelo {ruta.name}. Se genera ejecutando "
                    "redes-neuronales/entrenamiento/redes_ecografia_real/redes_ecografia_real.ipynb "
                    "(o entrenamiento/patologias_cerebrales/exportar.py para la de anomalías) "
                    "y copiando los .pth a modelos-ia/redes/."
                )
            self._dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
            paquete = torch.load(ruta, map_location=self._dispositivo, weights_only=True)
            meta = paquete["meta"]
            salidas = len(meta["clases"]) if "clases" in meta else 1
            red = timm.create_model(meta["arquitectura"], pretrained=False, num_classes=salidas)
            red.load_state_dict(paquete["estado"])
            red.eval().to(self._dispositivo)
            self._redes[nombre] = (red, meta)
            logger.info("Red %s cargada en %s", nombre, self._dispositivo)
            return self._redes[nombre]

    def _inferir(self, nombre: str, imagen) -> tuple[np.ndarray, int, dict]:
        import torch

        red, meta = self._cargar(nombre)
        cuadrada, mayor = a_cuadrado_gris(imagen, meta["lado"])
        x = torch.from_numpy(cuadrada).float().div_(255.0).sub_(meta["media"]).div_(meta["desv"])
        x = x.unsqueeze(0).unsqueeze(0).repeat(1, 3, 1, 1).to(self._dispositivo)
        with torch.inference_mode():
            salida = red(x).float().cpu().numpy()[0]
        return salida, mayor, meta

    def probabilidades_cerebro(self, imagen) -> dict[str, float]:
        """Salida de la red de anomalías (normal + 4 familias), sin filtros."""
        import torch

        red, meta = self._cargar(ARCHIVO_CEREBRO)
        cuadrada, _ = a_cuadrado_gris(imagen, meta["lado"])
        margen = (meta["lado"] - meta["recorte"]) // 2
        cuadrada = cuadrada[margen:margen + meta["recorte"], margen:margen + meta["recorte"]]
        x = torch.from_numpy(np.ascontiguousarray(cuadrada)).float().div_(255.0)
        x = x.sub_(meta["media"]).div_(meta["desv"]).unsqueeze(0).unsqueeze(0).repeat(1, 3, 1, 1)
        x = x.to(self._dispositivo)
        with torch.inference_mode():
            p = torch.softmax(red(x).float(), 1)
            if meta.get("volteo_prueba"):
                p = (p + torch.softmax(red(torch.flip(x, [3])).float(), 1)) / 2
        p = p.cpu().numpy()[0]
        return {c: float(p[i]) for i, c in enumerate(meta["clases"])}

    def detectar_anomalia_cerebral(self, imagen) -> dict:
        """Normal o una de 4 familias de anomalía, sobre un corte axial de cabeza.

        El clasificador de planos se entrenó con cabezas normales y no ve
        «cerebro» como plano más probable en el 40 % de las cabezas CON
        anomalía (la anomalía deforma la cabeza). Por eso no se exige que sea
        el plano más probable, sino P(cerebro) ≥ PROB_MINIMA_CEREBRO:
          · plano más probable = cerebro → se clasifica normalmente;
          · P(cerebro) ≥ mínimo y la red da alarma → se informa con aviso
            (perder una anomalía es peor que revisar una imagen de más);
          · en otro caso → «no aplicable»: no se afirma que una imagen de
            abdomen tenga un cerebro normal.
        """
        _, meta = self._cargar(ARCHIVO_CEREBRO)
        base = {"modelo": {"archivo": ARCHIVO_CEREBRO, "dataset": meta["dataset"],
                           "sha256": huella_sha256(self.carpeta / f"{ARCHIVO_CEREBRO}.pth"),
                           "metricas_prueba": meta["metricas"]},
                "uso": "Apoyo al cribado. No es un diagnóstico: toda alarma la confirma un especialista."}
        plano = self.clasificar_plano(imagen) if self.disponible(ARCHIVO_PLANO) else None
        es_cabeza = plano is None or plano["plano"] == "cerebro fetal"
        quiza_cabeza = plano is None or plano["probabilidades"]["cerebro fetal"] >= PROB_MINIMA_CEREBRO

        probs = self.probabilidades_cerebro(imagen)
        p_anomalia = 1.0 - probs["normal"]
        alarma = p_anomalia >= meta["umbral"]
        if not es_cabeza and not (quiza_cabeza and alarma):
            return base | {"aplicable": False, "plano_detectado": plano["plano"], "avisos": [
                f"El clasificador de planos ve «{plano['plano']}», no un corte de la cabeza. "
                "La red de anomalías cerebrales solo analiza cortes axiales del cerebro fetal. "
                "Si la imagen SÍ es una cabeza (una malformación grave puede deformarla tanto "
                "que no se reconozca), la red no pudo evaluarla: no descarta nada."]}

        familias = {c: v for c, v in probs.items() if c != "normal"}
        sospecha = max(familias, key=familias.get)
        avisos = []
        if not es_cabeza:
            avisos.append(
                f"El clasificador de planos ve «{plano['plano']}» y no un corte de la cabeza, "
                "pero la red de anomalías da alarma. Las anomalías que deforman la cabeza "
                "(encefalocele, hidrocefalia grave) a menudo no se reconocen como cerebro. "
                "Revise la imagen: si no es una cabeza, ignore esta alarma."
            )
        if alarma and familias[sospecha] / max(p_anomalia, 1e-9) < 0.6:
            avisos.append("La red ve una anomalía pero duda entre familias: tome la familia como orientativa.")
        if es_cabeza and plano and plano["confianza"] < CONFIANZA_MINIMA_PLANO:
            avisos.append("El plano de corte no es claro; el resultado es menos fiable.")
        return base | {
            "aplicable": True,
            "alarma_anomalia": alarma,
            "probabilidad_anomalia": round(p_anomalia, 4),
            "umbral": meta["umbral"],
            "familia_sospechada": sospecha if alarma else None,
            "familia_sospechada_nombre": NOMBRES_FAMILIA.get(sospecha) if alarma else None,
            "probabilidades": {c: round(v, 4) for c, v in probs.items()},
            "plano_detectado": plano["plano"] if plano else None,
            "avisos": avisos,
        }

    def clasificar_plano(self, imagen) -> dict:
        logits, _, meta = self._inferir(ARCHIVO_PLANO, imagen)
        p = np.exp(logits - logits.max())
        p /= p.sum()
        orden = np.argsort(p)[::-1]
        clases = meta["clases"]
        plano, confianza = clases[orden[0]], float(p[orden[0]])
        avisos = []
        if confianza < CONFIANZA_MINIMA_PLANO:
            avisos.append(
                f"Confianza baja ({confianza:.0%}): la red duda entre "
                f"«{plano}» y «{clases[orden[1]]}». Revise la imagen."
            )
        return {
            "plano": plano,
            "confianza": round(confianza, 4),
            "probabilidades": {clases[i]: round(float(p[i]), 4) for i in orden},
            "avisos": avisos,
            "modelo": {"archivo": ARCHIVO_PLANO, "dataset": meta["dataset"],
                       "sha256": huella_sha256(self.carpeta / f"{ARCHIVO_PLANO}.pth"),
                       "metricas_prueba": METRICAS_PRUEBA[ARCHIVO_PLANO]},
        }

    def medir_circunferencia(self, imagen, tamano_pixel_mm: float) -> dict:
        if not (0.01 <= tamano_pixel_mm <= 2.0):
            raise ValueError(
                "tamano_pixel_mm fuera de rango (0,01–2,0 mm). Es el tamaño de un "
                "píxel en milímetros, lo da el ecógrafo o la cabecera DICOM."
            )
        salida, mayor, meta = self._inferir(ARCHIVO_HC, imagen)
        hc_mm = float(salida[0]) * mayor * tamano_pixel_mm

        avisos = []
        plano = self.clasificar_plano(imagen) if self.disponible(ARCHIVO_PLANO) else None
        if plano and plano["plano"] != "cerebro fetal":
            aviso = (
                f"El clasificador de planos ve «{plano['plano']}», no un corte de la "
                "cabeza. La medida solo vale sobre el plano transtalámico. Si la "
                "imagen sí es una cabeza, este aviso es una falsa alarma: pasa en 7 "
                "de cada 100 cabezas de otro hospital (medido en las 999 de HC18)."
            )
            if hc_mm < HC_PRIMER_TRIMESTRE_MM:
                aviso += (
                    " Antes de la semana 14 pasa en 4 de cada 10: el clasificador se "
                    "entrenó con ecografías de 18 a 40 semanas."
                )
            avisos.append(aviso)
        semanas = None
        if HC_MIN_MM <= hc_mm <= HC_MAX_MM:
            semanas = round(edad_gestacional_hadlock_1984(hc_mm), 1)
        else:
            avisos.append(
                f"{hc_mm:.0f} mm está fuera del rango con el que se entrenó la red "
                f"({HC_MIN_MM:.0f}–{HC_MAX_MM:.0f} mm). No se da edad gestacional."
            )
        return {
            "circunferencia_cefalica_mm": round(hc_mm, 1),
            "margen_mm": METRICAS_PRUEBA[ARCHIVO_HC]["error_medio_mm"],
            "edad_gestacional_semanas": semanas,
            "formula_edad": "Hadlock 1984: 8,96 + 0,540·HC + 0,0003·HC³ (cm)",
            "plano_detectado": plano["plano"] if plano else None,
            "avisos": avisos,
            "modelo": {"archivo": ARCHIVO_HC, "dataset": meta["dataset"],
                       "sha256": huella_sha256(self.carpeta / f"{ARCHIVO_HC}.pth"),
                       "metricas_prueba": METRICAS_PRUEBA[ARCHIVO_HC]},
        }


redes = RedesEcografiaReal()

