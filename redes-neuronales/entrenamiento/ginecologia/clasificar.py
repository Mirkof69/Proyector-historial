"""Redes de clasificación ginecológicas (EfficientNet-B0), medidas sin trampas.

    python entrenamiento/ginecologia/clasificar.py ovario       # 8 tipos de lesión ovárica (MMOTU)
    python entrenamiento/ginecologia/clasificar.py ovario_pco   # normal / folículo dominante / poliquístico

Decisiones fijadas ANTES de mirar la prueba:
  · EfficientNet-B0 preentrenada en ImageNet, imagen en color (MMOTU trae 216
    Doppler color: el color es información diagnóstica), volteo en la prueba.
  · La época se elige con la VALIDACIÓN (exactitud balanceada); la prueba no
    se toca hasta el final.
  · Muestreo equilibrado por clase: las clases raras (carcinoma, quiste simple)
    pesan igual que las frecuentes.
  · Ovario: se entrenan DOS variantes y se elige la mejor por validación:
      - «imagen»: la ecografía entera;
      - «roi»: recorte alrededor de la lesión (con la máscara del experto al
        entrenar; en validación y prueba, con la máscara de la U-Net de
        `segmentacion/entrenar.py ovario`, como pasará en el sistema).
  · Alarma de malignidad (carcinoma seroso de alto grado): P >= 0,25, fijado
    de antemano (con 6 casos de validación no se puede ajustar con honestidad).
  · Poliquístico: 295 pacientes, una imagen cada una: 5 pliegues. Las métricas
    son las de las predicciones fuera de pliegue; el modelo final se entrena
    con todo (15 % para elegir la época).
"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import timm
import torch
import torch.nn.functional as F
from PIL import Image
from sklearn.metrics import confusion_matrix, f1_score, roc_auc_score
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision.transforms import v2 as T

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
IA = AQUI.parents[1]
sys.path.insert(0, str(IA))
sys.path.insert(0, str(IA.parent / "servicio-ia"))
from preparar import CLASES_OVARIO, CLASES_PCO, NOMBRES_OVARIO  # noqa: E402

DISPOSITIVO = "cuda" if torch.cuda.is_available() else "cpu"
SEMILLA = 2026
EPOCAS = 30
LOTE = 32
UMBRAL_MALIGNIDAD = 0.25
MEDIA, DESV = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)
CONFIG = {
    "ovario": {"lado": 384, "clases": CLASES_OVARIO, "nombres": NOMBRES_OVARIO},
    "ovario_pco": {"lado": 320, "clases": CLASES_PCO,
                   "nombres": ["Ovario normal", "Folículo dominante", "Ovario poliquístico"]},
}


def fijar_semilla(s: int = SEMILLA) -> None:
    random.seed(s)
    np.random.seed(s)
    torch.manual_seed(s)
    torch.cuda.manual_seed_all(s)


def cuadrado(img: Image.Image, lado: int) -> torch.Tensor:
    """Letterbox a lado×lado (uint8, 3×H×W)."""
    img = img.convert("RGB")
    img.thumbnail((lado, lado))
    lienzo = Image.new("RGB", (lado, lado))
    lienzo.paste(img, ((lado - img.width) // 2, (lado - img.height) // 2))
    return torch.from_numpy(np.array(lienzo)).permute(2, 0, 1).contiguous()


def recorte_lesion(img: Image.Image, mascara: np.ndarray | None, margen: float = 0.2) -> Image.Image:
    """Cuadrado alrededor de la lesión con 20 % de margen; sin lesión, la imagen entera."""
    if mascara is None or not mascara.any():
        return img
    ys, xs = np.nonzero(mascara)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    medio = max(x1 - x0, y1 - y0) * (1 + 2 * margen) / 2
    medio = max(medio, 32)
    return img.crop((int(cx - medio), int(cy - medio), int(cx + medio), int(cy + medio)))


class Imagenes(Dataset):
    def __init__(self, tensores: list[torch.Tensor], y: list[int], lado: int, entrenar: bool):
        self.x, self.y, self.entrenar = tensores, y, entrenar
        self.aumento = T.Compose([T.RandomResizedCrop(lado, scale=(0.8, 1.0), ratio=(0.9, 1.1), antialias=True),
                                  T.RandomHorizontalFlip(), T.RandomAffine(degrees=10),
                                  T.ColorJitter(brightness=0.25, contrast=0.25)])

    def __len__(self) -> int:
        return len(self.x)

    def __getitem__(self, i):
        x = self.x[i]
        if self.entrenar:
            x = self.aumento(x)
        x = x.float().div(255)
        return T.functional.normalize(x, MEDIA, DESV), self.y[i]


def nueva_red(n: int, arquitectura: str = "efficientnet_b0.ra_in1k"):
    return timm.create_model(arquitectura, pretrained=True, num_classes=n, drop_rate=0.3).to(DISPOSITIVO)


@torch.no_grad()
def predecir(red, tensores: list[torch.Tensor], lado: int) -> np.ndarray:
    red.eval()
    carga = DataLoader(Imagenes(tensores, [0] * len(tensores), lado, False), batch_size=64)
    salida = []
    for x, _ in carga:
        x = x.to(DISPOSITIVO)
        with torch.autocast("cuda", dtype=torch.float16, enabled=DISPOSITIVO == "cuda"):
            p = F.softmax(red(x).float(), 1) + F.softmax(red(torch.flip(x, [3])).float(), 1)
        salida.append((p / 2).cpu())
    return torch.cat(salida).numpy()


def exactitud_balanceada(y: np.ndarray, pred: np.ndarray, n: int) -> float:
    return float(np.mean([(pred[y == c] == c).mean() for c in range(n) if (y == c).any()]))


def entrenar(x_e, y_e, x_v, y_v, n: int, lado: int, etiqueta: str,
             arquitectura: str = "efficientnet_b0.ra_in1k"):
    fijar_semilla()
    red = nueva_red(n, arquitectura)
    frec = np.bincount(y_e, minlength=n)
    pesos = (1.0 / frec[y_e]).astype(float)
    carga = DataLoader(Imagenes(x_e, list(y_e), lado, True), batch_size=LOTE,
                       sampler=WeightedRandomSampler(pesos, num_samples=len(y_e), replacement=True))
    opt = torch.optim.AdamW(red.parameters(), lr=3e-4, weight_decay=1e-2)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=3e-4, total_steps=EPOCAS * len(carga), pct_start=0.1)
    escala = torch.amp.GradScaler("cuda", enabled=DISPOSITIVO == "cuda")
    mejor, mejor_estado, historia = -1.0, None, []
    for epoca in range(1, EPOCAS + 1):
        red.train()
        total = 0.0
        for x, y in carga:
            x, y = x.to(DISPOSITIVO), y.to(DISPOSITIVO)
            with torch.autocast("cuda", dtype=torch.float16, enabled=DISPOSITIVO == "cuda"):
                perdida = F.cross_entropy(red(x).float(), y, label_smoothing=0.05)
            opt.zero_grad(set_to_none=True)
            escala.scale(perdida).backward()
            escala.step(opt)
            escala.update()
            sched.step()
            total += perdida.item()
        bal = exactitud_balanceada(np.asarray(y_v), predecir(red, x_v, lado).argmax(1), n)
        historia.append({"epoca": epoca, "perdida": total / len(carga), "exactitud_balanceada_val": bal})
        if bal > mejor:
            mejor, mejor_estado = bal, {k: v.detach().cpu().clone() for k, v in red.state_dict().items()}
        print(f"  [{etiqueta}] época {epoca:2d}  pérdida {total / len(carga):.3f}  "
              f"exactitud balanceada val {bal:.3f}{'  *' if bal == mejor else ''}", flush=True)
    red.load_state_dict(mejor_estado)
    return red, historia, mejor


def intervalo(y: np.ndarray, pred: np.ndarray, n: int, veces: int = 2000) -> dict:
    rng = np.random.default_rng(SEMILLA)
    ex, bal = [], []
    for _ in range(veces):
        i = rng.integers(0, len(y), len(y))
        ex.append((y[i] == pred[i]).mean())
        bal.append(exactitud_balanceada(y[i], pred[i], n))
    return {"exactitud_ic95": [round(float(np.percentile(ex, 2.5)), 4), round(float(np.percentile(ex, 97.5)), 4)],
            "exactitud_balanceada_ic95": [round(float(np.percentile(bal, 2.5)), 4),
                                          round(float(np.percentile(bal, 97.5)), 4)]}


def metricas(y: np.ndarray, prob: np.ndarray, clases: list[str]) -> dict:
    n = len(clases)
    pred = prob.argmax(1)
    cm = confusion_matrix(y, pred, labels=list(range(n)))
    por_clase = {}
    for c, nombre in enumerate(clases):
        reales, predichos = cm[c].sum(), cm[:, c].sum()
        por_clase[nombre] = {"casos": int(reales),
                             "sensibilidad": round(float(cm[c, c] / reales), 4) if reales else None,
                             "valor_predictivo_positivo": round(float(cm[c, c] / predichos), 4) if predichos else None}
    try:
        auc = round(float(roc_auc_score(y, prob, multi_class="ovr", average="macro", labels=list(range(n)))), 4)
    except ValueError:
        auc = None
    return {"imagenes": int(len(y)), "exactitud": round(float((pred == y).mean()), 4),
            "exactitud_balanceada": round(exactitud_balanceada(y, pred, n), 4),
            "f1_macro": round(float(f1_score(y, pred, average="macro")), 4), "auc_macro_ovr": auc,
            **intervalo(y, pred, n), "por_clase": por_clase,
            "matriz_confusion": {"filas_real_columnas_predicha": clases, "valores": cm.tolist()}}


def malignidad(y: np.ndarray, prob: np.ndarray, indice: int) -> dict:
    real = y == indice
    p = prob[:, indice]
    alarma = p >= UMBRAL_MALIGNIDAD
    return {"casos_malignos": int(real.sum()), "casos_no_malignos": int((~real).sum()),
            "auc": round(float(roc_auc_score(real, p)), 4) if real.any() and (~real).any() else None,
            "umbral_fijado_de_antemano": UMBRAL_MALIGNIDAD,
            "sensibilidad": round(float((alarma & real).sum() / max(1, real.sum())), 4),
            "especificidad": round(float((~alarma & ~real).sum() / max(1, (~real).sum())), 4),
            "alarmas": int(alarma.sum()), "falsas_alarmas": int((alarma & ~real).sum())}


# ───────────────────────────────── ovario ──────────────────────────────────

def mascaras_unet(cat: pd.DataFrame) -> list[np.ndarray]:
    """Máscara de la lesión según la U-Net entrenada (mayor componente), en la imagen original."""
    from app.unet import UNet, a_cuadrado, mayor_componente
    from entrenamiento.segmentacion.entrenar import _en_original
    from entrenamiento.segmentacion.entrenar import predecir as segmentar

    pesos = IA / "entrenamiento" / "segmentacion" / "salidas" / "ovario" / "segmentacion_ovario.pth"
    datos = torch.load(pesos, map_location=DISPOSITIVO, weights_only=False)
    meta = datos["meta"]
    red = UNet(meta["codificador"], len(meta["clases"]), preentrenado=False).to(DISPOSITIVO)
    red.load_state_dict(datos["estado"])
    salida = []
    for ruta in cat["imagen"]:
        gris = np.array(Image.open(IA / ruta).convert("L"))
        pred = segmentar(red, a_cuadrado(gris, meta["lado"])[0][None])[0]
        salida.append(mayor_componente(_en_original(pred, gris.shape, meta["lado"]) > 0))
    del red
    torch.cuda.empty_cache()
    return salida


def ovario() -> None:
    cfg = CONFIG["ovario"]
    lado, clases = cfg["lado"], cfg["clases"]
    cat = pd.read_csv(AQUI / "catalogos" / "ovario.csv")
    partes = {p: cat[cat["particion"] == p].reset_index(drop=True) for p in ("entrenamiento", "validacion", "prueba")}
    for p, d in partes.items():
        print(f"{p:<13} {len(d)} imágenes · {d['grupo'].nunique()} grupos", flush=True)
    imagenes = {p: [Image.open(IA / r).convert("RGB") for r in d["imagen"]] for p, d in partes.items()}
    expertas = {p: [np.array(Image.open(IA / r)) > 0 for r in d["mascara"]] for p, d in partes.items()}
    print("Segmentando validación y prueba con la U-Net…", flush=True)
    de_red = {p: mascaras_unet(partes[p]) for p in ("validacion", "prueba")}

    variantes = {
        "imagen": {p: [cuadrado(im, lado) for im in imagenes[p]] for p in partes},
        "roi": {"entrenamiento": [cuadrado(recorte_lesion(im, m), lado)
                                  for im, m in zip(imagenes["entrenamiento"], expertas["entrenamiento"])],
                **{p: [cuadrado(recorte_lesion(im, m), lado) for im, m in zip(imagenes[p], de_red[p])]
                   for p in ("validacion", "prueba")}},
    }
    y = {p: d["clase"].to_numpy() for p, d in partes.items()}
    resultados = {}
    for nombre, x in variantes.items():
        red, historia, val = entrenar(x["entrenamiento"], y["entrenamiento"], x["validacion"], y["validacion"],
                                      len(clases), lado, nombre)
        resultados[nombre] = {"red": red, "historia": historia, "val": val}
        print(f"Variante {nombre}: exactitud balanceada en validación {val:.4f}", flush=True)
    elegida = max(resultados, key=lambda k: resultados[k]["val"])
    print(f"Elegida por validación: {elegida}", flush=True)

    salida = AQUI / "salidas" / "ovario"
    salida.mkdir(parents=True, exist_ok=True)
    m = {"tarea": "ovario", "dataset": "MMOTU OTU_2d · Beijing Shijitan Hospital · etiquetas con informe de "
                                       "anatomía patológica (27 especialistas)",
         "particion": "prueba oficial por paciente sin casi copias de entrenamiento ni diagnósticos contradictorios",
         "variantes_validacion": {k: round(v["val"], 4) for k, v in resultados.items()},
         "variante_elegida": elegida}
    for nombre, r in resultados.items():  # se informan las dos: la elegida y la descartada
        prob = predecir(r["red"], variantes[nombre]["prueba"], lado)
        m[f"prueba_{nombre}"] = metricas(y["prueba"], prob, clases) | {
            "malignidad": malignidad(y["prueba"], prob, clases.index("carcinoma_seroso_alto_grado"))}
        if nombre == elegida:
            tabla = partes["prueba"][["imagen", "clase_nombre"]].copy()
            tabla["predicha"] = [clases[i] for i in prob.argmax(1)]
            for i, c in enumerate(clases):
                tabla[f"p_{c}"] = prob[:, i].round(4)
            tabla.to_csv(salida / "predicciones_prueba.csv", index=False)
    m["prueba"] = m[f"prueba_{elegida}"]
    red = resultados[elegida]["red"]
    torch.save({"estado": red.state_dict(), "meta": {
        "arquitectura": "efficientnet_b0", "clases": clases, "nombres": cfg["nombres"], "lado": lado,
        "media": MEDIA, "desv": DESV, "variante": elegida, "umbral_malignidad": UMBRAL_MALIGNIDAD,
        "volteo_prueba": True, "metricas": m}}, salida / "clasificador_ovario.pth")
    (salida / "metricas.json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    (salida / "historia.json").write_text(
        json.dumps({k: v["historia"] for k, v in resultados.items()}, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in m.items() if not k.startswith("prueba_")}, ensure_ascii=False, indent=2))


# ──────────────────────────────── poliquístico ─────────────────────────────

def ovario_pco() -> None:
    cfg = CONFIG["ovario_pco"]
    lado, clases = cfg["lado"], cfg["clases"]
    cat = pd.read_csv(AQUI / "catalogos" / "ovario_pco.csv")
    x = [cuadrado(Image.open(IA / r), lado) for r in cat["ruta"]]
    y = cat["clase"].to_numpy()
    oof = np.zeros((len(cat), len(clases)))
    historias = {}
    rng = random.Random(SEMILLA)
    for k in range(5):
        prueba = np.where(cat["pliegue"] == k)[0]
        resto = np.where(cat["pliegue"] != k)[0].tolist()
        val = []
        for c in range(len(clases)):  # 15 % de cada clase del resto, para la época
            de_c = [i for i in resto if y[i] == c]
            rng.shuffle(de_c)
            val += de_c[:max(1, round(len(de_c) * 0.15))]
        ent = [i for i in resto if i not in set(val)]
        red, historias[f"pliegue_{k}"], _ = entrenar([x[i] for i in ent], y[ent], [x[i] for i in val], y[val],
                                                     len(clases), lado, f"p{k}")
        oof[prueba] = predecir(red, [x[i] for i in prueba], lado)
        del red
        torch.cuda.empty_cache()
    m = {"tarea": "ovario_pco", "dataset": "Borna et al. 2025 (Frontiers in Physiology): 301 ecografías "
                                           "transvaginales de pacientes distintas, una ginecobstetra",
         "particion": "5 pliegues estratificados; métricas fuera de pliegue (cada imagen predicha por un modelo "
                      "que no la vio)",
         "prueba": metricas(y, oof, clases)}
    salida = AQUI / "salidas" / "ovario_pco"
    salida.mkdir(parents=True, exist_ok=True)
    tabla = cat[["ruta", "clase_nombre", "pliegue"]].copy()
    tabla["predicha"] = [clases[i] for i in oof.argmax(1)]
    tabla.to_csv(salida / "predicciones_fuera_de_pliegue.csv", index=False)

    print("Modelo final con todas las pacientes", flush=True)
    todos = list(range(len(cat)))
    rng.shuffle(todos)
    val = [i for i in todos if i % 7 == 0]
    ent = [i for i in todos if i % 7 != 0]
    red, historias["final"], _ = entrenar([x[i] for i in ent], y[ent], [x[i] for i in val], y[val],
                                          len(clases), lado, "final")
    torch.save({"estado": red.state_dict(), "meta": {
        "arquitectura": "efficientnet_b0", "clases": clases, "nombres": cfg["nombres"], "lado": lado,
        "media": MEDIA, "desv": DESV, "variante": "imagen", "volteo_prueba": True, "metricas": m}},
        salida / "clasificador_ovario_pco.pth")
    (salida / "metricas.json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    (salida / "historia.json").write_text(json.dumps(historias, indent=1), encoding="utf-8")
    print(json.dumps(m, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    inicio = time.time()
    {"ovario": ovario, "ovario_pco": ovario_pco}[sys.argv[1]]()
    print(f"Listo en {(time.time() - inicio) / 60:.1f} min", flush=True)
