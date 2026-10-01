"""Redes de segmentación (U-Net) entrenadas con ecografías REALES y sus medidas.

| Archivo                 | Estructuras                                   | Medido en datos no vistos |
|-------------------------|-----------------------------------------------|---------------------------|
| segmentacion_cabeza     | cráneo, cavum del septum pellucidum, ventrículo lateral | Dice cráneo 0,968; HC en HC18 (otro hospital): 4,4 mm, 92 % dentro del 5 % |
| segmentacion_torax      | tórax, corazón                                | Dice 0,93; índice cardiotorácico ±0,02 |
| segmentacion_abdomen    | hígado, estómago, vena umbilical, aorta       | Dice 0,69–0,84; estómago visto en el 92 %, vena en el 98 % |

Se entrenan en `entrenamiento/segmentacion/` (ver `metricas.json` de cada una);
las métricas viajan dentro del .pth y en el .json de al lado.

Las medidas salen de la máscara, no de una regresión «a ciegas»: la elipse
del cráneo da la circunferencia y el diámetro biparietal; las áreas y
perímetros de corazón y tórax dan el índice cardiotorácico. Por eso cada
resultado se puede ver dibujado sobre la imagen y comprobar a ojo.
"""
from __future__ import annotations

import base64
import json
import logging
import threading
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from .config import MODELS_DIR, huella_sha256
from .unet import a_cuadrado, a_original, a_tensor, elipse, mayor_componente

logger = logging.getLogger(__name__)

TAREAS = ("cabeza", "torax", "abdomen")

#: color RGB por estructura en la superposición
COLORES = {
    "craneo": (59, 130, 246), "csp": (234, 179, 8), "ventriculo_lateral": (239, 68, 68),
    "torax": (59, 130, 246), "corazon": (239, 68, 68),
    "higado": (168, 85, 247), "estomago": (34, 197, 94), "vena_umbilical": (234, 179, 8), "aorta": (239, 68, 68),
}
NOMBRES = {
    "craneo": "Cráneo", "csp": "Cavum del septum pellucidum", "ventriculo_lateral": "Ventrículo lateral",
    "torax": "Tórax", "corazon": "Corazón", "higado": "Hígado", "estomago": "Estómago",
    "vena_umbilical": "Vena umbilical", "aorta": "Aorta",
}
#: Una estructura cuenta como vista si ocupa al menos esta fracción de la imagen
#: (el mismo umbral con el que se midió la detección en el entrenamiento).
FRACCION_MINIMA = 0.0005
#: Índice cardiotorácico por áreas: el rango de referencia habitual es 0,25–0,35.
#: FOCUS solo tiene corazones normales, así que lo que está validado es la MEDIDA
#: (±0,02), no la capacidad de detectar cardiomegalia.
ICT_AREA_REFERENCIA = (0.25, 0.35)


def edad_por_dbp_hadlock_1982(dbp_mm: float) -> float:
    """Hadlock FP et al., J Ultrasound Med 1982: EG = 9,54 + 1,482·DBP + 0,1676·DBP² (cm)."""
    d = dbp_mm / 10
    return 9.54 + 1.482 * d + 0.1676 * d * d


def _png_base64(rgb: np.ndarray) -> str:
    buf = BytesIO()
    Image.fromarray(rgb).save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def superposicion(gris: np.ndarray, mascara: np.ndarray, clases: list[str], elipse_craneo: dict | None = None) -> str:
    """Imagen con cada estructura coloreada (35 % de opacidad) y su contorno."""
    import cv2

    rgb = np.stack([gris] * 3, axis=-1).astype(np.float32)
    capa = rgb.copy()
    for i, nombre in enumerate(clases[1:], start=1):
        zona = mascara == i
        if zona.any():
            capa[zona] = COLORES.get(nombre, (255, 255, 255))
    mezcla = (0.65 * rgb + 0.35 * capa).astype(np.uint8)
    for i, nombre in enumerate(clases[1:], start=1):
        contornos, _ = cv2.findContours((mascara == i).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(mezcla, contornos, -1, COLORES.get(nombre, (255, 255, 255)), 2)
    if elipse_craneo:
        (cx, cy), (d1, d2) = elipse_craneo["centro"], elipse_craneo["ejes_cv"]
        cv2.ellipse(mezcla, ((cx, cy), (d1, d2), elipse_craneo["angulo"]), (255, 255, 255), 2)
    return _png_base64(mezcla)


class RedesSegmentacion:
    """Carga cada U-Net una sola vez por proceso, la primera vez que se pide."""

    def __init__(self, carpeta: Path = MODELS_DIR):
        self.carpeta = carpeta
        self._redes: dict[str, tuple[Any, dict]] = {}
        self._cerrojo = threading.Lock()
        self._dispositivo = None

    def _ruta(self, tarea: str) -> Path:
        return self.carpeta / f"segmentacion_{tarea}.pth"

    def disponible(self, tarea: str) -> bool:
        return self._ruta(tarea).exists()

    def metricas(self, tarea: str) -> dict | None:
        ficha = self.carpeta / f"segmentacion_{tarea}.json"
        return json.loads(ficha.read_text(encoding="utf-8")) if ficha.exists() else None

    def estado(self) -> dict:
        return {f"segmentacion_{t}": {"disponible": self.disponible(t), "metricas_prueba": self.metricas(t),
                                      "sha256": huella_sha256(self._ruta(t))} for t in TAREAS}

    def _cargar(self, tarea: str):
        with self._cerrojo:
            if tarea in self._redes:
                return self._redes[tarea]
            import torch

            from .unet import UNet

            ruta = self._ruta(tarea)
            if not ruta.exists():
                raise FileNotFoundError(
                    f"No está el modelo {ruta.name}. Se entrena con "
                    f"entrenamiento/segmentacion/entrenar.py {tarea} y se copia a trained_models/.")
            self._dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
            paquete = torch.load(ruta, map_location=self._dispositivo, weights_only=True)
            meta = paquete["meta"]
            red = UNet(meta["codificador"], len(meta["clases"]), preentrenado=False)
            red.load_state_dict(paquete["estado"])
            red.eval().to(self._dispositivo)
            self._redes[tarea] = (red, meta)
            logger.info("U-Net %s cargada en %s", tarea, self._dispositivo)
            return self._redes[tarea]

    def segmentar(self, tarea: str, imagen) -> tuple[np.ndarray, np.ndarray, dict]:
        """(gris original, máscara de índices del mismo tamaño, ficha del modelo)."""
        import torch

        red, meta = self._cargar(tarea)
        img = imagen if isinstance(imagen, Image.Image) else Image.fromarray(np.asarray(imagen))
        gris = np.array(img.convert("L"))
        cuadrada, mayor, desplazamiento = a_cuadrado(gris, meta["lado"])
        x = a_tensor(cuadrada[None]).to(self._dispositivo)
        with torch.inference_mode():
            p = red(x).float().softmax(1)
            if meta.get("volteo_prueba"):
                p = p + red(x.flip(3)).float().softmax(1).flip(3)
        pred = p.argmax(1)[0].cpu().numpy().astype(np.uint8)
        return gris, a_original(pred, mayor, desplazamiento, gris.shape), meta

    def _modelo(self, tarea: str, meta: dict) -> dict:
        return {"archivo": f"segmentacion_{tarea}", "dataset": meta["metricas"].get("dataset"),
                "sha256": huella_sha256(self._ruta(tarea)), "metricas_prueba": meta["metricas"]}

    @staticmethod
    def _vistas(mascara: np.ndarray, clases: list[str]) -> dict[str, bool]:
        minimo = FRACCION_MINIMA * mascara.size
        return {c: bool((mascara == i).sum() > minimo) for i, c in enumerate(clases) if i}

    def medir_cabeza(self, imagen, tamano_pixel_mm: float | None = None) -> dict:
        gris, m, meta = self.segmentar("cabeza", imagen)
        clases = meta["clases"]
        vistas = self._vistas(m, clases)
        e = elipse(m > 0)
        avisos, medidas = [], {}
        if e is None or not vistas["craneo"]:
            avisos.append("No se encontró el contorno del cráneo: no se mide nada.")
        else:
            medidas["relacion_ejes"] = round(e["eje_menor"] / e["eje_mayor"], 3)
            if tamano_pixel_mm:
                hc = e["perimetro"] * tamano_pixel_mm
                dbp = e["eje_menor"] * tamano_pixel_mm
                medidas |= {"circunferencia_cefalica_mm": round(hc, 1), "diametro_biparietal_mm": round(dbp, 1),
                            "margen_hc_mm": meta["metricas"]["prueba_externa_hc18"]["hc_error_medio_mm"],
                            "margen_dbp_mm": meta["metricas"]["medidas_prueba"]["dbp_error_medio_mm"]}
                if 45 <= hc <= 350:
                    from .ecografia_real import edad_gestacional_hadlock_1984

                    medidas["edad_gestacional_por_hc_semanas"] = round(edad_gestacional_hadlock_1984(hc), 1)
                if 20 <= dbp <= 100:
                    medidas["edad_gestacional_por_dbp_semanas"] = round(edad_por_dbp_hadlock_1982(dbp), 1)
            else:
                avisos.append("Sin el tamaño del píxel (mm) no se pueden dar milímetros: indíquelo para medir HC y DBP.")
        if vistas.get("ventriculo_lateral") or vistas.get("csp"):
            avisos.append("Cavum y ventrículo se dibujan como orientación (Dice 0,76 y 0,71): no se miden.")
        return {"tarea": "cabeza", "estructuras_vistas": {NOMBRES[k]: v for k, v in vistas.items()},
                "medidas": medidas, "avisos": avisos,
                "superposicion_png": superposicion(gris, m, clases, e), "modelo": self._modelo("cabeza", meta)}

    def medir_torax(self, imagen) -> dict:
        gris, m, meta = self.segmentar("torax", imagen)
        clases = meta["clases"]
        vistas = self._vistas(m, clases)
        avisos, medidas = [], {}
        torax, corazon = elipse(m >= 1), elipse(m == 2)
        if torax and corazon and vistas["torax"] and vistas["corazon"]:
            area = mayor_componente(m == 2).sum() / mayor_componente(m >= 1).sum()
            medidas = {"indice_cardiotoracico_areas": round(float(area), 3),
                       "indice_cardiotoracico_circunferencias": round(corazon["perimetro"] / torax["perimetro"], 3),
                       "margen": meta["metricas"]["indice_cardiotoracico_prueba"]["ict_areas_error_medio"],
                       "referencia_areas": list(ICT_AREA_REFERENCIA)}
            if area > ICT_AREA_REFERENCIA[1]:
                avisos.append(f"Índice cardiotorácico por áreas {area:.2f}, por encima de {ICT_AREA_REFERENCIA[1]}: "
                              "valorar cardiomegalia. La red se validó midiendo, no diagnosticando (FOCUS solo trae "
                              "corazones normales).")
        else:
            avisos.append("No se encontraron a la vez el tórax y el corazón: no se calcula el índice.")
        return {"tarea": "torax", "estructuras_vistas": {NOMBRES[k]: v for k, v in vistas.items()},
                "medidas": medidas, "avisos": avisos,
                "superposicion_png": superposicion(gris, m, clases), "modelo": self._modelo("torax", meta)}

    def analizar_abdomen(self, imagen) -> dict:
        gris, m, meta = self.segmentar("abdomen", imagen)
        clases = meta["clases"]
        vistas = self._vistas(m, clases)
        plano_ok = vistas["estomago"] and vistas["vena_umbilical"]
        avisos = [] if plano_ok else [
            "Falta el estómago o la vena umbilical: el corte no parece el adecuado para medir la circunferencia abdominal."]
        return {"tarea": "abdomen", "estructuras_vistas": {NOMBRES[k]: v for k, v in vistas.items()},
                "medidas": {"plano_adecuado_para_ca": plano_ok}, "avisos": avisos,
                "superposicion_png": superposicion(gris, m, clases), "modelo": self._modelo("abdomen", meta)}


segmentacion = RedesSegmentacion()
