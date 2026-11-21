"""Longitud del fémur y circunferencia abdominal con una red de puntos (U-Net).

| Red                | Mide                                | Medido en pacientes no vistas |
|--------------------|-------------------------------------|-------------------------------|
| biometria_femur    | Longitud del fémur (LF)              | ver `metricas_prueba` (Multicentre Fetal Biometry 2026) |
| biometria_abdomen  | Diámetros transverso y anteroposterior → circunferencia abdominal | ídem |

La red marca los dos extremos de cada diámetro (como el ecografista con los
calibres); la medida es la distancia entre ellos y se dibuja sobre la imagen.
Con `tamano_pixel_mm` (del ecógrafo o del DICOM) la medida sale en mm.
Se entrenan en `entrenamiento/biometria/entrenar.py`.
"""
from __future__ import annotations

import json
import logging
import math
import threading
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from .config import MODELS_DIR, huella_sha256
from .segmentacion import _png_base64
from .unet import a_cuadrado, a_tensor

logger = logging.getLogger(__name__)

TAREAS_BIOMETRIA = ("femur", "abdomen")
COLOR = {"fl": (34, 197, 94), "tad": (59, 130, 246), "apad": (234, 179, 8)}
NOMBRE = {"fl": "Longitud del fémur", "tad": "Diámetro abdominal transverso",
          "apad": "Diámetro abdominal anteroposterior"}


def picos(mapa: np.ndarray, separacion: int) -> np.ndarray:
    """Los dos máximos del mapa de un diámetro (igual que en entrenamiento/biometria/entrenar.py)."""
    lado = mapa.shape[0]
    m = mapa.copy()
    salida = []
    for _ in range(2):
        y, x = np.unravel_index(np.argmax(m), m.shape)
        y0, y1, x0, x1 = max(0, y - 2), min(lado, y + 3), max(0, x - 2), min(lado, x + 3)
        ventana = np.clip(mapa[y0:y1, x0:x1], 0, None)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        s = ventana.sum() or 1.0
        salida.append([(ventana * xx).sum() / s, (ventana * yy).sum() / s])
        m[max(0, y - separacion):y + separacion + 1, max(0, x - separacion):x + separacion + 1] = -1e9
    return np.asarray(salida)


def perimetro_elipse(a: float, b: float) -> float:
    """Ramanujan con los ejes completos."""
    a, b = a / 2, b / 2
    h = ((a - b) / (a + b)) ** 2
    return math.pi * (a + b) * (1 + 3 * h / (10 + math.sqrt(4 - 3 * h)))


class RedesBiometria:
    def __init__(self, carpeta: Path = MODELS_DIR):
        self.carpeta = carpeta
        self._redes: dict[str, tuple[Any, dict]] = {}
        self._cerrojo = threading.Lock()
        self._dispositivo = "cpu"

    def _ruta(self, tarea: str) -> Path:
        return self.carpeta / f"biometria_{tarea}.pth"

    def disponible(self, tarea: str) -> bool:
        return self._ruta(tarea).exists()

    def metricas(self, tarea: str) -> dict | None:
        ficha = self.carpeta / f"biometria_{tarea}.json"
        return json.loads(ficha.read_text(encoding="utf-8")) if ficha.exists() else None

    def estado(self) -> dict:
        return {f"biometria_{t}": {"disponible": self.disponible(t), "metricas_prueba": self.metricas(t),
                                   "sha256": huella_sha256(self._ruta(t))} for t in TAREAS_BIOMETRIA}

    def _cargar(self, tarea: str):
        with self._cerrojo:
            if tarea in self._redes:
                return self._redes[tarea]
            import torch

            from .unet import UNet

            ruta = self._ruta(tarea)
            if not ruta.exists():
                raise FileNotFoundError(f"No está el modelo {ruta.name}. Se entrena con "
                                        f"entrenamiento/biometria/entrenar.py {tarea} y se copia a modelos-ia/redes/.")
            self._dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
            paquete = torch.load(ruta, map_location=self._dispositivo, weights_only=True)
            meta = paquete["meta"]
            red = UNet(meta["codificador"], len(meta["diametros"]), preentrenado=False)
            red.load_state_dict(paquete["estado"])
            self._redes[tarea] = (red.eval().to(self._dispositivo), meta)
            return self._redes[tarea]

    def puntos(self, tarea: str, imagen) -> tuple[np.ndarray, dict[str, np.ndarray], dict]:
        """(gris, {diámetro: 2 puntos en la imagen original}, ficha)."""
        import torch

        red, meta = self._cargar(tarea)
        img = imagen if isinstance(imagen, Image.Image) else Image.fromarray(np.asarray(imagen))
        gris = np.array(img.convert("L"))
        cuadrada, mayor, (dy, dx) = a_cuadrado(gris, meta["lado"])
        x = a_tensor(cuadrada[None]).to(self._dispositivo)
        with torch.inference_mode():
            h = red(x).float().sigmoid()
            if meta.get("volteo_prueba"):
                h = h + red(x.flip(3)).float().sigmoid().flip(3)
        f = mayor / meta["lado"]
        salida = {}
        for d, mapa in zip(meta["diametros"], h[0].cpu().numpy()):
            p = picos(mapa, meta["separacion"]) * f
            salida[d] = p - np.array([dx, dy])
        return gris, salida, meta

    def medir(self, tarea: str, imagen, tamano_pixel_mm: float | None = None) -> dict:
        import cv2

        gris, pts, meta = self.puntos(tarea, imagen)
        largo_px = {d: float(np.linalg.norm(p[0] - p[1])) for d, p in pts.items()}
        met = meta["metricas"]["prueba"]
        medidas: dict = {}
        avisos = []
        if tamano_pixel_mm:
            if tarea == "femur":
                medidas = {"longitud_femur_mm": round(largo_px["fl"] * tamano_pixel_mm, 1),
                           "margen_lf_mm": met["fl"]["error_medio_mm"]}
            else:
                tad, apad = largo_px["tad"] * tamano_pixel_mm, largo_px["apad"] * tamano_pixel_mm
                medidas = {"diametro_abdominal_transverso_mm": round(tad, 1),
                           "diametro_abdominal_anteroposterior_mm": round(apad, 1),
                           "circunferencia_abdominal_mm": round(perimetro_elipse(tad, apad), 1),
                           "margen_ca_mm": met["ca"]["error_medio_mm"]}
        else:
            medidas = {f"{d}_px": round(v, 1) for d, v in largo_px.items()}
            avisos.append("Sin milímetros por píxel la medida queda en píxeles: indíquelos (ecógrafo o DICOM) "
                          "para obtener milímetros.")
        lienzo = np.stack([gris] * 3, axis=-1).copy()
        for d, p in pts.items():
            a, b = tuple(int(v) for v in p[0]), tuple(int(v) for v in p[1])
            cv2.line(lienzo, a, b, COLOR[d], 2)
            for q in (a, b):
                cv2.drawMarker(lienzo, q, COLOR[d], cv2.MARKER_CROSS, 14, 2)
        return {"tarea": tarea, "medidas": medidas,
                "puntos": {d: p.round(1).tolist() for d, p in pts.items()},
                "avisos": avisos, "superposicion_png": _png_base64(lienzo),
                "modelo": {"archivo": f"biometria_{tarea}", "dataset": meta["metricas"].get("dataset"),
                           "sha256": huella_sha256(self._ruta(tarea)), "metricas_prueba": meta["metricas"]}}


biometria = RedesBiometria()
