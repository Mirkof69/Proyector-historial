"""Ángulo de progresión (AoP) a partir de las máscaras de pubis y cabeza fetal.

Definición (ISUOG, ecografía intraparto transperineal; la misma del desafío
IUGC 2024, comprobada contra sus anotaciones): ángulo con vértice en el
extremo INFERIOR de la sínfisis del pubis, entre el eje largo de la sínfisis
(hacia su extremo superior) y la recta tangente al contorno óseo de la cabeza
fetal. Cuanto más desciende la cabeza, mayor el ángulo; > 120° se asocia a
parto vaginal espontáneo.

Pasos:
1. Eje de la sínfisis: componente principal de sus píxeles; sus dos extremos.
2. Extremo inferior: el de la DERECHA de la imagen, en la orientación de
   presentación de IUGC (en el 100 % de sus 2.915 anotaciones el vértice del
   experto es el extremo derecho). Antes se tomaba «el más lejano a la
   cabeza»: fallaba justo cuando la cabeza ya descendió (AoP ≥ 120°), porque
   entonces queda junto al borde inferior — 1 de 23 detectados. Con la
   orientación, sobre la máscara del experto: error medio 3,4° y 20 de 23.
   Si el ecógrafo muestra la imagen espejada, hay que voltearla antes.
3. Tangente: el punto del contorno de la cabeza que hace MÁXIMO el ángulo
   visto desde el extremo inferior (la recta que roza la cabeza).
"""
from __future__ import annotations

import numpy as np


def _extremos_sinfisis(pubis: np.ndarray) -> tuple[np.ndarray, np.ndarray] | None:
    ys, xs = np.nonzero(pubis)
    if len(xs) < 10:
        return None
    puntos = np.stack([xs, ys], axis=1).astype(float)
    centro = puntos.mean(0)
    _, _, vt = np.linalg.svd(puntos - centro, full_matrices=False)
    eje = vt[0]
    proy = (puntos - centro) @ eje
    return centro + eje * proy.min(), centro + eje * proy.max()


def _contorno(cabeza: np.ndarray) -> np.ndarray | None:
    import cv2

    contornos, _ = cv2.findContours(cabeza.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contornos:
        return None
    return max(contornos, key=cv2.contourArea).reshape(-1, 2).astype(float)


def angulo_progresion(mascara: np.ndarray, pubis: int = 1, cabeza: int = 2) -> dict | None:
    """{aop, extremo_inferior, extremo_superior, tangente} en píxeles, o None si falta una estructura."""
    from .unet import mayor_componente

    extremos = _extremos_sinfisis(mayor_componente(mascara == pubis))
    contorno = _contorno(mayor_componente(mascara == cabeza))
    if extremos is None or contorno is None:
        return None
    a, b = extremos
    inferior, superior = (a, b) if a[0] > b[0] else (b, a)
    eje = superior - inferior
    vectores = contorno - inferior
    cos = (vectores @ eje) / (np.linalg.norm(vectores, axis=1) * np.linalg.norm(eje) + 1e-9)
    angulos = np.degrees(np.arccos(np.clip(cos, -1, 1)))
    i = int(np.argmax(angulos))
    return {"aop": float(angulos[i]), "extremo_inferior": inferior.tolist(), "extremo_superior": superior.tolist(),
            "tangente": contorno[i].tolist()}


def interpretar(aop: float) -> str:
    if aop >= 120:
        return "AoP ≥ 120°: descenso compatible con parto vaginal espontáneo."
    if aop >= 110:
        return "AoP entre 110° y 120°: descenso intermedio; reevaluar según la evolución."
    return "AoP < 110°: cabeza alta; vigilar el progreso del trabajo de parto."


__all__ = ["angulo_progresion", "interpretar"]
