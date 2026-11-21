"""Redes de ecografía ginecológica, entrenadas con datos reales y medidas en pacientes no vistas.

| Red                         | Qué hace                                          | Datos |
|-----------------------------|---------------------------------------------------|-------|
| segmentacion_ovario (U-Net) | Dibuja la lesión ovárica                          | MMOTU, Beijing Shijitan Hospital |
| clasificador_ovario (CNN)   | Tipo de lesión (8 clases) y alarma de malignidad  | MMOTU, con informe de anatomía patológica |
| segmentacion_mioma (U-Net)  | Ubica el mioma uterino (caja)                     | Mendeley n2zcmcypgb, 788 pacientes |
| clasificador_ovario_pco     | Ovario normal / folículo dominante / poliquístico | Borna et al. 2025, 295 pacientes |

Las métricas medidas viajan en cada respuesta (`modelo.metricas_prueba`). Se
entrenan en `entrenamiento/ginecologia/` y `entrenamiento/segmentacion/`.

Es apoyo: el diagnóstico de una masa anexial lo da la clasificación O-RADS del
especialista y, al final, la anatomía patológica; el de síndrome de ovario
poliquístico, los criterios de Rotterdam (clínica, hormonas y ecografía).
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
from .segmentacion import _png_base64, segmentacion
from .unet import mayor_componente

logger = logging.getLogger(__name__)

CLASIFICADORES = ("ovario", "ovario_pco")
MEDIA, DESV = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)
COLOR_LESION = (234, 88, 12)


def recorte_lesion(img: Image.Image, mascara: np.ndarray | None, margen: float = 0.2) -> Image.Image:
    """Igual que al entrenar (entrenamiento/ginecologia/clasificar.py)."""
    if mascara is None or not mascara.any():
        return img
    ys, xs = np.nonzero(mascara)
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    medio = max(max(xs.max() - xs.min(), ys.max() - ys.min()) * (1 + 2 * margen) / 2, 32)
    return img.crop((int(cx - medio), int(cy - medio), int(cx + medio), int(cy + medio)))


def _cuadrado(img: Image.Image, lado: int) -> np.ndarray:
    img = img.convert("RGB")
    img.thumbnail((lado, lado))
    lienzo = Image.new("RGB", (lado, lado))
    lienzo.paste(img, ((lado - img.width) // 2, (lado - img.height) // 2))
    return np.asarray(lienzo)


def _dibujar(rgb: np.ndarray, mascara: np.ndarray | None, caja: tuple | None = None) -> str:
    import cv2

    lienzo = rgb.astype(np.float32).copy()
    if mascara is not None and mascara.any():
        capa = lienzo.copy()
        capa[mascara] = COLOR_LESION
        lienzo = 0.65 * lienzo + 0.35 * capa
    lienzo = lienzo.astype(np.uint8)
    if mascara is not None and mascara.any():
        contornos, _ = cv2.findContours(mascara.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(lienzo, contornos, -1, COLOR_LESION, 2)
    if caja:
        cv2.rectangle(lienzo, (int(caja[0]), int(caja[1])), (int(caja[2]), int(caja[3])), (255, 255, 255), 2)
    return _png_base64(lienzo)


class RedesGinecologia:
    """Carga cada clasificador una sola vez por proceso."""

    def __init__(self, carpeta: Path = MODELS_DIR):
        self.carpeta = carpeta
        self._redes: dict[str, tuple[Any, dict]] = {}
        self._cerrojo = threading.Lock()
        self._dispositivo = "cpu"

    def _ruta(self, nombre: str) -> Path:
        return self.carpeta / f"clasificador_{nombre}.pth"

    def disponible(self, nombre: str) -> bool:
        return self._ruta(nombre).exists()

    def metricas(self, nombre: str) -> dict | None:
        ficha = self.carpeta / f"clasificador_{nombre}.json"
        return json.loads(ficha.read_text(encoding="utf-8")) if ficha.exists() else None

    def estado(self) -> dict:
        return {f"clasificador_{n}": {"disponible": self.disponible(n), "metricas_prueba": self.metricas(n),
                                      "sha256": huella_sha256(self._ruta(n))} for n in CLASIFICADORES}

    def _cargar(self, nombre: str):
        with self._cerrojo:
            if nombre in self._redes:
                return self._redes[nombre]
            import timm
            import torch

            ruta = self._ruta(nombre)
            if not ruta.exists():
                raise FileNotFoundError(f"No está el modelo {ruta.name}. Se entrena con "
                                        f"entrenamiento/ginecologia/clasificar.py y se copia a modelos-ia/redes/.")
            self._dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
            paquete = torch.load(ruta, map_location=self._dispositivo, weights_only=True)
            meta = paquete["meta"]
            # Una red, o un ensamble (lista de redes cuyas probabilidades se promedian).
            miembros = meta.get("miembros") or [{"arquitectura": "efficientnet_b0", "lado": meta["lado"],
                                                 "variante": meta.get("variante", "imagen")}]
            estados = paquete["estado"] if isinstance(paquete["estado"], list) else [paquete["estado"]]
            redes = []
            for miembro, estado in zip(miembros, estados):
                red = timm.create_model(miembro["arquitectura"], pretrained=False, num_classes=len(meta["clases"]))
                red.load_state_dict(estado)
                redes.append((red.eval().to(self._dispositivo), miembro))
            self._redes[nombre] = (redes, meta)
            logger.info("Clasificador %s cargado en %s", nombre, self._dispositivo)
            return self._redes[nombre]

    def probabilidades(self, nombre: str, img: Image.Image,
                       lesion: np.ndarray | None = None) -> tuple[np.ndarray, dict]:
        """Promedio de los miembros; los «roi» clasifican el recorte de la lesión
        (igual que al medir la red en entrenamiento/ginecologia/)."""
        import torch

        redes, meta = self._cargar(nombre)
        salida = []
        for red, miembro in redes:
            entrada = recorte_lesion(img, lesion) if miembro["variante"] == "roi" else img
            x = torch.from_numpy(_cuadrado(entrada, miembro["lado"])).permute(2, 0, 1).float().div(255)
            x = ((x - torch.tensor(MEDIA)[:, None, None]) / torch.tensor(DESV)[:, None, None])[None]
            x = x.to(self._dispositivo)
            with torch.inference_mode():
                p = red(x).float().softmax(1)
                if meta.get("volteo_prueba"):
                    p = (p + red(x.flip(3)).float().softmax(1)) / 2
            salida.append(p[0].cpu().numpy())
        return np.mean(salida, axis=0), meta

    def _modelo(self, nombre: str, meta: dict) -> dict:
        return {"archivo": f"clasificador_{nombre}", "dataset": meta["metricas"].get("dataset"),
                "sha256": huella_sha256(self._ruta(nombre)), "metricas_prueba": meta["metricas"]}

    # ────────────────────────────── ovario ───────────────────────────────

    def analizar_ovario(self, imagen, tamano_pixel_mm: float | None = None) -> dict:
        """Lesión ovárica: contorno (U-Net), tipo (8 clases) y alarma de malignidad."""
        img = imagen if isinstance(imagen, Image.Image) else Image.fromarray(np.asarray(imagen))
        img = img.convert("RGB")
        _, m, meta_seg = segmentacion.segmentar("ovario", img)
        lesion = mayor_componente(m > 0)
        prob, meta = self.probabilidades("ovario", img, lesion) if self.disponible("ovario") else (None, None)
        avisos = ["Apoyo al diagnóstico: la conducta ante una masa anexial la decide el especialista con la "
                  "clasificación O-RADS y, al final, la anatomía patológica."]
        hallazgos, medidas = [], {}
        if lesion.any():
            ys, xs = np.nonzero(lesion)
            ancho, alto = int(xs.max() - xs.min()), int(ys.max() - ys.min())
            medidas = {"lesion_ancho_px": ancho, "lesion_alto_px": alto, "lesion_area_px": int(lesion.sum())}
            if tamano_pixel_mm:
                medidas |= {"lesion_ancho_mm": round(ancho * tamano_pixel_mm, 1),
                            "lesion_alto_mm": round(alto * tamano_pixel_mm, 1)}
        else:
            avisos.append("La red no encontró una lesión en la imagen: el tipo se calcula con la imagen entera.")
        respuesta: dict = {"tarea": "ovario", "lesion_encontrada": bool(lesion.any()), "medidas": medidas,
                           "superposicion_png": _dibujar(np.asarray(img), lesion),
                           "modelos": [segmentacion._modelo("ovario", meta_seg)]}
        if prob is not None:
            orden = np.argsort(prob)[::-1]
            nombres = meta["nombres"]
            i_mal = meta["clases"].index("carcinoma_seroso_alto_grado")
            p_mal = float(prob[i_mal])
            met_mal = meta["metricas"]["prueba"].get("malignidad", {})
            alarma = p_mal >= meta["umbral_malignidad"]
            respuesta |= {
                "tipo_probable": nombres[orden[0]],
                "probabilidades": [{"tipo": nombres[i], "probabilidad": round(float(prob[i]), 4)} for i in orden[:3]],
                "malignidad": {"probabilidad": round(p_mal, 4), "alarma": bool(alarma),
                               "umbral": meta["umbral_malignidad"],
                               "sensibilidad_medida": met_mal.get("sensibilidad"),
                               "especificidad_medida": met_mal.get("especificidad")},
            }
            respuesta["modelos"].append(self._modelo("ovario", meta))
            if alarma:
                hallazgos.append("Rasgos compatibles con carcinoma seroso de alto grado: derivar a ginecología "
                                 "oncológica para evaluación (O-RADS, marcadores, anatomía patológica).")
            else:
                sens = met_mal.get("sensibilidad")
                avisos.append("Sin alarma de malignidad, pero eso NO la descarta: en pacientes que la red no vio "
                              f"detectó {round(sens * 100) if sens is not None else '—'} % de los carcinomas. "
                              "Una masa sospechosa por O-RADS se evalúa igual.")
            if float(prob[orden[0]]) < 0.5:
                avisos.append("La red duda entre varios tipos: tómese como orientación, no como diagnóstico.")
        respuesta |= {"hallazgos": hallazgos, "avisos": avisos}
        return respuesta

    # ─────────────────────────────── mioma ───────────────────────────────

    def ubicar_mioma(self, imagen, tamano_pixel_mm: float | None = None) -> dict:
        """Caja del mioma más grande que encuentra la U-Net (entrenada con cajas)."""
        img = imagen if isinstance(imagen, Image.Image) else Image.fromarray(np.asarray(imagen))
        img = img.convert("RGB")
        _, m, meta = segmentacion.segmentar("mioma", img)
        zona = mayor_componente(m > 0)
        avisos = ["La red se entrenó solo con úteros CON mioma: ubica el mioma, pero no sirve para "
                  "descartar que lo haya. Si no marca nada, no significa ausencia."]
        medidas, caja = {}, None
        if zona.any():
            ys, xs = np.nonzero(zona)
            caja = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
            medidas = {"caja_px": list(caja), "ancho_px": caja[2] - caja[0], "alto_px": caja[3] - caja[1]}
            if tamano_pixel_mm:
                medidas |= {"ancho_mm": round((caja[2] - caja[0]) * tamano_pixel_mm, 1),
                            "alto_mm": round((caja[3] - caja[1]) * tamano_pixel_mm, 1)}
        return {"tarea": "mioma", "mioma_ubicado": caja is not None, "medidas": medidas, "hallazgos": [],
                "avisos": avisos, "superposicion_png": _dibujar(np.asarray(img), None, caja),
                "modelos": [segmentacion._modelo("mioma", meta)]}

    # ─────────────────────────── ovario poliquístico ─────────────────────

    def clasificar_ovario_pco(self, imagen) -> dict:
        img = imagen if isinstance(imagen, Image.Image) else Image.fromarray(np.asarray(imagen))
        prob, meta = self.probabilidades("ovario_pco", img.convert("RGB"))
        orden = np.argsort(prob)[::-1]
        avisos = ["El síndrome de ovario poliquístico se diagnostica con los criterios de Rotterdam (2 de 3: "
                  "oligo/anovulación, hiperandrogenismo, morfología ecográfica): la imagen sola no basta."]
        if float(prob[orden[0]]) < 0.5:
            avisos.append("La red duda entre varias categorías: tómese como orientación.")
        return {"tarea": "ovario_pco", "categoria_probable": meta["nombres"][orden[0]],
                "probabilidades": [{"categoria": meta["nombres"][i], "probabilidad": round(float(prob[i]), 4)}
                                   for i in orden],
                "hallazgos": [], "avisos": avisos, "modelos": [self._modelo("ovario_pco", meta)]}


ginecologia = RedesGinecologia()


def decodificar(png_b64: str) -> np.ndarray:
    """Para las pruebas: superposición base64 → array."""
    return np.array(Image.open(BytesIO(base64.b64decode(png_b64))))
