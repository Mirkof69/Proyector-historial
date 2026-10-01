"""U-Net con codificador EfficientNet preentrenado (timm) y medidas sobre sus máscaras.

La usan IGUAL el entrenamiento (`entrenamiento/segmentacion/entrenar.py`) y el
microservicio (`app/segmentacion.py`): una sola definición, para que los pesos
entrenados carguen sin sorpresas.

Preprocesado (idéntico al de las otras redes, `app/ecografia_real.py`): gris,
rellenado a cuadrado SIN deformar, reducido al lado de la red y normalizado
con la media y desviación de ImageNet replicada a 3 canales.
"""
from __future__ import annotations

import math

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

MEDIA, DESV = 0.485, 0.229


class _Bloque(nn.Module):
    def __init__(self, entrada: int, salida: int):
        super().__init__()
        self.capas = nn.Sequential(
            nn.Conv2d(entrada, salida, 3, padding=1, bias=False), nn.BatchNorm2d(salida), nn.ReLU(inplace=True),
            nn.Conv2d(salida, salida, 3, padding=1, bias=False), nn.BatchNorm2d(salida), nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.capas(x)


class UNet(nn.Module):
    """Codificador de timm (`features_only`) + decodificador U-Net clásico."""

    def __init__(self, codificador: str = "efficientnet_b2", clases: int = 2, preentrenado: bool = True):
        super().__init__()
        self.codificador = __import__("timm").create_model(codificador, features_only=True,
                                                            pretrained=preentrenado)
        canales = self.codificador.feature_info.channels()          # de menor a mayor profundidad
        anchos = [256, 128, 64, 32][: len(canales) - 1]
        self.bloques = nn.ModuleList()
        actual = canales[-1]
        for salto, ancho in zip(reversed(canales[:-1]), anchos):
            self.bloques.append(_Bloque(actual + salto, ancho))
            actual = ancho
        self.final = nn.Sequential(_Bloque(actual, 16), nn.Conv2d(16, clases, 1))

    def forward(self, x):
        alto, ancho = x.shape[-2:]
        rasgos = self.codificador(x)
        y = rasgos[-1]
        for bloque, salto in zip(self.bloques, reversed(rasgos[:-1])):
            y = F.interpolate(y, size=salto.shape[-2:], mode="bilinear", align_corners=False)
            y = bloque(torch.cat([y, salto], 1))
        y = F.interpolate(y, size=(alto, ancho), mode="bilinear", align_corners=False)
        return self.final(y)


def a_cuadrado(gris: np.ndarray, lado: int, interpolacion=None) -> tuple[np.ndarray, int, tuple[int, int]]:
    """Rellena a cuadrado (centrado) y reduce a `lado`. Devuelve también el lado
    mayor y el desplazamiento, para devolver la máscara a la imagen original."""
    import cv2

    alto, ancho = gris.shape[:2]
    mayor = max(alto, ancho)
    lienzo = np.zeros((mayor, mayor), gris.dtype)
    dy, dx = (mayor - alto) // 2, (mayor - ancho) // 2
    lienzo[dy:dy + alto, dx:dx + ancho] = gris
    modo = cv2.INTER_LINEAR if interpolacion is None else interpolacion
    return cv2.resize(lienzo, (lado, lado), interpolation=modo), mayor, (dy, dx)


def a_original(mascara_cuadrada: np.ndarray, mayor: int, desplazamiento: tuple[int, int],
               forma: tuple[int, int]) -> np.ndarray:
    """Inversa de `a_cuadrado` para una máscara de índices."""
    import cv2

    grande = cv2.resize(mascara_cuadrada.astype(np.uint8), (mayor, mayor), interpolation=cv2.INTER_NEAREST)
    dy, dx = desplazamiento
    return grande[dy:dy + forma[0], dx:dx + forma[1]]


def a_tensor(lote: np.ndarray) -> torch.Tensor:
    x = torch.from_numpy(lote).float().div_(255.0).sub_(MEDIA).div_(DESV)
    return x.unsqueeze(1).repeat(1, 3, 1, 1)


# ───────────────────────────── medidas ─────────────────────────────────────

def mayor_componente(binaria: np.ndarray) -> np.ndarray:
    """Solo la región conexa más grande (quita manchas sueltas)."""
    import cv2

    n, etiquetas, stats, _ = cv2.connectedComponentsWithStats(binaria.astype(np.uint8), 8)
    if n <= 1:
        return np.zeros_like(binaria, dtype=bool)
    return etiquetas == 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))


def elipse(binaria: np.ndarray) -> dict | None:
    """Elipse ajustada al contorno de la región más grande, en píxeles.

    Perímetro con la aproximación de Ramanujan, la misma con la que HC18 y la
    práctica clínica pasan de los diámetros a la circunferencia.
    """
    import cv2

    region = mayor_componente(binaria).astype(np.uint8)
    contornos, _ = cv2.findContours(region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contornos:
        return None
    c = max(contornos, key=cv2.contourArea)
    if len(c) < 5:
        return None
    (cx, cy), (d1, d2), angulo = cv2.fitEllipse(c)
    a, b = max(d1, d2) / 2, min(d1, d2) / 2
    perimetro = math.pi * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b)))
    return {"centro": (float(cx), float(cy)), "eje_mayor": 2 * a, "eje_menor": 2 * b,
            "angulo": float(angulo), "ejes_cv": (float(d1), float(d2)),
            "perimetro": perimetro, "area": float(region.sum())}
