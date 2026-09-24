"""Dos redes entrenadas con ecografías REALES, con anotación de experto.

1. Circunferencia cefálica (regresión) — HC18, Zenodo 1327317, CC BY 4.0.
   999 imágenes de 779 madres, medidas por ecografistas del Radboud UMC.
2. Plano anatómico (clasificación, 6 clases) — FETAL_PLANES_DB, Zenodo
   3904280, CC BY 4.0. 12.400 imágenes de 1.792 madres, Barcelona.

Se entrenan en `historial/datos_ecografia_reales/redes_ecografia_real.ipynb`
y los pesos se copian a `trained_models/`. El preprocesado de aquí tiene que
ser idéntico al del entrenamiento (`cnn_ecografia.py`): gris, relleno a
cuadrado sin deformar, reducción al lado de la red y normalización ImageNet.
Si se cambia uno, hay que cambiar el otro.

A diferencia de la EfficientNet-B4 de `models.py`, estas dos redes sí tienen
métricas medidas sobre madres que no vieron al entrenar (METRICAS_PRUEBA).
"""

from __future__ import annotations

import logging
import threading

import numpy as np
from PIL import Image

from .config import MODELS_DIR

logger = logging.getLogger(__name__)

MEDIA = 0.485
DESV = 0.229

ARCHIVO_HC = "circunferencia_cefalica_hc18"
ARCHIVO_PLANO = "plano_anatomico_fetal_planes"

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
    return np.asarray(lienzo.resize((lado, lado), Image.BILINEAR), dtype=np.uint8), mayor


class RedesEcografiaReal:
    """Carga las dos redes una sola vez por proceso, la primera vez que se piden."""

    def __init__(self, carpeta=MODELS_DIR):
        self.carpeta = carpeta
        self._redes: dict[str, tuple[object, dict]] = {}
        self._cerrojo = threading.Lock()
        self._dispositivo = None

    def disponible(self, nombre: str) -> bool:
        return (self.carpeta / f"{nombre}.pth").exists()

    def estado(self) -> dict:
        """Qué redes medidas están disponibles, con sus métricas en prueba."""
        return {
            nombre: {"disponible": self.disponible(nombre), "metricas_prueba": METRICAS_PRUEBA.get(nombre)}
            for nombre in (ARCHIVO_PLANO, ARCHIVO_HC)
        }

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
                    "historial/datos_ecografia_reales/redes_ecografia_real.ipynb "
                    "y copiando modelos/*.pth a trained_models/."
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
                       "metricas_prueba": METRICAS_PRUEBA[ARCHIVO_HC]},
        }


redes = RedesEcografiaReal()

