"""Entrena una red de segmentación (U-Net) y la mide en pacientes que no vio.

    python entrenamiento/segmentacion/entrenar.py cabeza
    python entrenamiento/segmentacion/entrenar.py abdomen
    python entrenamiento/segmentacion/entrenar.py torax

Antes: `preparar.py`. Deja en `salidas/<tarea>/` el modelo, la historia, las
predicciones de prueba y `metricas.json`; `exportar.py` lo copia al
microservicio.

Cómo se mide (y por qué así)
----------------------------
- Se elige la época con la VALIDACIÓN (Dice medio), nunca con la prueba.
- Dice por estructura en cada imagen de prueba donde el experto la marcó.
- Cabeza: además, circunferencia (HC) y diámetro biparietal (DBP) sacados de
  la elipse de la máscara, comparados con los de la máscara del experto; y
  prueba EXTERNA en las 999 imágenes de HC18 (otro hospital), contra la HC que
  midió el ecografista, en sus imágenes originales.
- Tórax: índice cardiotorácico (circunferencias y áreas) frente al del experto.
- Abdomen: si detecta el estómago y la vena umbilical (los dos marcadores del
  plano correcto para medir la circunferencia abdominal) cuando el experto los
  marcó.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from PIL import Image

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))

from app.unet import UNet, a_cuadrado, a_original, a_tensor, elipse, mayor_componente  # noqa: E402
from entrenamiento.segmentacion.preparar import CLASES  # noqa: E402

DISPOSITIVO = "cuda" if torch.cuda.is_available() else "cpu"
SEMILLA = 2026
CONFIG = {
    "cabeza": {"lado": 384, "epocas": 45, "lote": 16, "lr": 6e-4, "codificador": "efficientnet_b2"},
    "abdomen": {"lado": 384, "epocas": 60, "lote": 16, "lr": 6e-4, "codificador": "efficientnet_b2"},
    "torax": {"lado": 384, "epocas": 120, "lote": 12, "lr": 5e-4, "codificador": "efficientnet_b2"},
    "intraparto": {"lado": 384, "epocas": 50, "lote": 16, "lr": 6e-4, "codificador": "efficientnet_b2"},
}
CLASES = CLASES | {"intraparto": ["fondo", "sinfisis_pubis", "cabeza_fetal"]}
#: catálogo de cada tarea (intraparto lo arma entrenamiento/intraparto/preparar.py)
CATALOGO = {t: AQUI / "catalogos" / f"{t}.csv" for t in ("cabeza", "abdomen", "torax")} | {
    "intraparto": AQUI.parent / "intraparto" / "catalogo.csv"}


def fijar_semilla() -> None:
    import random

    random.seed(SEMILLA)
    np.random.seed(SEMILLA)
    torch.manual_seed(SEMILLA)
    torch.cuda.manual_seed_all(SEMILLA)


def cargar(cat: pd.DataFrame, lado: int) -> tuple[np.ndarray, np.ndarray]:
    import cv2

    X, Y = [], []
    for img, msk in zip(cat["imagen"], cat["mascara"]):
        X.append(a_cuadrado(np.array(Image.open(RAIZ / img)), lado)[0])
        Y.append(a_cuadrado(np.array(Image.open(RAIZ / msk)), lado, cv2.INTER_NEAREST)[0])
    return np.stack(X), np.stack(Y)


def aumentar(x: torch.Tensor, y: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Geometría (volteo, giro ±20°, zoom ±15 %, desplazamiento) igual a imagen y
    máscara; brillo, contraste y gamma solo a la imagen (cada ecógrafo calibra
    distinto). La máscara se transforma con vecino más cercano."""
    n = x.shape[0]
    d = x.device
    ang = (torch.rand(n, device=d) - 0.5) * (40 * np.pi / 180)
    esc = 1 + (torch.rand(n, device=d) - 0.5) * 0.3
    volteo = torch.where(torch.rand(n, device=d) < 0.5, -1.0, 1.0)
    theta = torch.zeros(n, 2, 3, device=d)
    theta[:, 0, 0] = torch.cos(ang) / esc * volteo
    theta[:, 0, 1] = -torch.sin(ang) / esc
    theta[:, 1, 0] = torch.sin(ang) / esc * volteo
    theta[:, 1, 1] = torch.cos(ang) / esc
    theta[:, :, 2] = (torch.rand(n, 2, device=d) - 0.5) * 0.2
    rejilla = F.affine_grid(theta, x.shape, align_corners=False)
    x = F.grid_sample(x, rejilla, align_corners=False, padding_mode="zeros")
    y = F.grid_sample(y.unsqueeze(1).float(), rejilla, mode="nearest", align_corners=False).squeeze(1).long()
    x = x * (1 + (torch.rand(n, 1, 1, 1, device=d) - 0.5) * 0.4) + (torch.rand(n, 1, 1, 1, device=d) - 0.5) * 0.4
    return x, y


def perdida(logits: torch.Tensor, y: torch.Tensor, clases: int) -> torch.Tensor:
    """Entropía cruzada + Dice suave sin el fondo: las estructuras pequeñas
    (cavum, vena umbilical) pesan aunque ocupen el 0,2 % de la imagen."""
    ce = F.cross_entropy(logits, y)
    p = logits.softmax(1)[:, 1:]
    uno = F.one_hot(y, clases).permute(0, 3, 1, 2).float()[:, 1:]
    inter = (p * uno).sum((0, 2, 3))
    union = p.sum((0, 2, 3)) + uno.sum((0, 2, 3))
    dice = 1 - ((2 * inter + 1) / (union + 1)).mean()
    return ce + dice


@torch.no_grad()
def predecir(red, X: np.ndarray, lote: int = 32) -> np.ndarray:
    """Máscara de índices; promedia la imagen y su espejo (volteo en prueba)."""
    red.eval()
    salida = []
    for i in range(0, len(X), lote):
        xb = a_tensor(X[i:i + lote]).to(DISPOSITIVO)
        with torch.autocast("cuda", dtype=torch.float16, enabled=DISPOSITIVO == "cuda"):
            p = red(xb).float().softmax(1) + red(xb.flip(3)).float().softmax(1).flip(3)
        salida.append(p.argmax(1).cpu().numpy().astype(np.uint8))
    return np.concatenate(salida)


def dice_por_clase(pred: np.ndarray, real: np.ndarray, clases: int) -> dict[int, list[float]]:
    """Dice de cada estructura en cada imagen donde el experto la marcó."""
    res = {c: [] for c in range(1, clases)}
    for p, r in zip(pred, real):
        for c in range(1, clases):
            rc, pc = r == c, p == c
            if rc.sum() == 0:
                continue
            res[c].append(float(2 * (rc & pc).sum() / (rc.sum() + pc.sum())))
    return res


def entrenar(tarea: str) -> None:
    cfg = CONFIG[tarea]
    clases = CLASES[tarea]
    salida = AQUI / "salidas" / tarea
    salida.mkdir(parents=True, exist_ok=True)
    registro = open(salida / "entrenamiento.log", "w", encoding="utf-8")

    def log(m: str) -> None:
        print(m, flush=True)
        registro.write(m + "\n")
        registro.flush()

    fijar_semilla()
    cat = pd.read_csv(CATALOGO[tarea])
    if "paciente" not in cat:  # intraparto agrupa por examen (los clips de un mismo examen)
        cat["paciente"] = cat["examen"]
    partes = {p: cat[cat["particion"] == p].reset_index(drop=True)
              for p in ("entrenamiento", "validacion", "prueba")}
    datos = {p: cargar(d, cfg["lado"]) for p, d in partes.items()}
    for p, d in partes.items():
        log(f"{p:<13} {len(d):5d} imágenes · {d['paciente'].nunique()} pacientes")

    red = UNet(cfg["codificador"], len(clases)).to(DISPOSITIVO)
    opt = torch.optim.AdamW(red.parameters(), lr=cfg["lr"], weight_decay=1e-4)
    X_e, Y_e = datos["entrenamiento"]
    pasos = cfg["epocas"] * int(np.ceil(len(X_e) / cfg["lote"]))
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=cfg["lr"], total_steps=pasos, pct_start=0.1)
    escalador = torch.amp.GradScaler("cuda", enabled=DISPOSITIVO == "cuda")
    mejor, mejor_estado, historia = -1.0, None, []

    for ep in range(1, cfg["epocas"] + 1):
        red.train()
        t0, total = time.perf_counter(), 0.0
        orden = np.random.permutation(len(X_e))
        for i in range(0, len(orden), cfg["lote"]):
            idx = orden[i:i + cfg["lote"]]
            if len(idx) < 2:
                continue
            xb = a_tensor(X_e[idx]).to(DISPOSITIVO)
            yb = torch.from_numpy(Y_e[idx]).long().to(DISPOSITIVO)
            xb, yb = aumentar(xb, yb)
            with torch.autocast("cuda", dtype=torch.float16, enabled=DISPOSITIVO == "cuda"):
                logits = red(xb)
            loss = perdida(logits.float(), yb, len(clases))
            opt.zero_grad(set_to_none=True)
            escalador.scale(loss).backward()
            escalador.step(opt)
            escalador.update()
            sched.step()
            total += loss.item() * len(idx)
        X_v, Y_v = datos["validacion"]
        dv = dice_por_clase(predecir(red, X_v), Y_v, len(clases))
        dice_val = float(np.mean([np.mean(v) for v in dv.values() if v]))
        historia.append({"epoca": ep, "perdida": total / len(X_e), "dice_validacion": dice_val})
        if dice_val > mejor:
            mejor = dice_val
            mejor_estado = {k: v.detach().cpu().clone() for k, v in red.state_dict().items()}
        log(f"época {ep:3d}/{cfg['epocas']}  pérdida {total / len(X_e):.4f}  Dice val {dice_val:.4f}"
            f"  ({time.perf_counter() - t0:.0f} s)")

    red.load_state_dict(mejor_estado)
    epoca_elegida = int(np.argmax([h["dice_validacion"] for h in historia])) + 1
    log(f"Época elegida por validación: {epoca_elegida} (Dice {mejor:.4f})")

    X_p, Y_p = datos["prueba"]
    pred_p = predecir(red, X_p)
    dp = dice_por_clase(pred_p, Y_p, len(clases))
    prueba = partes["prueba"]
    metricas = {
        "tarea": tarea,
        "dataset": {"cabeza": "Large-Scale Fetal Head Biometry (Zenodo 8265464) · FETAL_PLANES_DB",
                    "abdomen": "Fetal Abdominal Structures Segmentation (Mendeley Data)",
                    "torax": "FOCUS (Zenodo 14597550)",
                    "intraparto": "IUGC MICCAI 2024 (ecografía intraparto transperineal)"}[tarea],
        "particion": {"torax": "oficial de FOCUS (sin id de paciente)",
                      "intraparto": "prueba oficial del desafío (otros años y exámenes); validación por examen"}.get(
            tarea, "por paciente 70/15/15"),
        "imagenes_prueba": len(prueba),
        "pacientes_prueba": int(prueba["paciente"].nunique()),
        "epoca_elegida": epoca_elegida,
        "dice_validacion": round(mejor, 4),
        "dice_prueba": {clases[c]: {"medio": round(float(np.mean(v)), 4),
                                    "mediano": round(float(np.median(v)), 4),
                                    "imagenes": len(v)} for c, v in dp.items() if v},
    }
    metricas["dice_prueba_medio"] = round(float(np.mean([v["medio"] for v in metricas["dice_prueba"].values()])), 4)
    metricas |= {"cabeza": medir_cabeza, "torax": medir_torax, "abdomen": medir_abdomen,
                 "intraparto": medir_intraparto}[tarea](
        red, prueba, pred_p, Y_p, cfg, log)

    torch.save({"estado": red.state_dict(), "meta": {
        "arquitectura": "unet", "codificador": cfg["codificador"], "clases": clases, "lado": cfg["lado"],
        "media": 0.485, "desv": 0.229, "volteo_prueba": True, "metricas": metricas}},
        salida / f"segmentacion_{tarea}.pth")
    (salida / "metricas.json").write_text(json.dumps(metricas, ensure_ascii=False, indent=2), encoding="utf-8")
    (salida / "historia.json").write_text(json.dumps(historia, indent=1), encoding="utf-8")
    log(json.dumps(metricas, ensure_ascii=False, indent=2))


# ─────────────────────────── medidas por tarea ─────────────────────────────

def _en_original(pred_cuadrada: np.ndarray, forma: tuple[int, int], lado: int) -> np.ndarray:
    mayor = max(forma)
    return a_original(pred_cuadrada, mayor, ((mayor - forma[0]) // 2, (mayor - forma[1]) // 2), forma)


def medir_cabeza(red, prueba, pred_p, Y_p, cfg, log) -> dict:
    filas = []
    for (_, r), pc in zip(prueba.iterrows(), pred_p):
        real = np.array(Image.open(RAIZ / r["mascara"]))
        pred = _en_original(pc, real.shape, cfg["lado"])
        er, ep = elipse(real > 0), elipse(pred > 0)
        if er is None:
            continue
        mm = r["tamano_pixel_mm"]
        filas.append({"imagen": r["imagen"],
                      "hc_experto_mm": er["perimetro"] * mm, "dbp_experto_mm": er["eje_menor"] * mm,
                      "hc_red_mm": ep["perimetro"] * mm if ep else np.nan,
                      "dbp_red_mm": ep["eje_menor"] * mm if ep else np.nan})
    t = pd.DataFrame(filas)
    t.to_csv(AQUI / "salidas" / "cabeza" / "prueba_medidas.csv", index=False)
    err_hc = (t["hc_red_mm"] - t["hc_experto_mm"]).abs()
    err_dbp = (t["dbp_red_mm"] - t["dbp_experto_mm"]).abs()
    interno = {"imagenes": int(t["hc_red_mm"].notna().sum()),
               "hc_error_medio_mm": round(float(err_hc.mean()), 2),
               "hc_error_mediano_mm": round(float(err_hc.median()), 2),
               "hc_error_relativo_medio": round(float((err_hc / t["hc_experto_mm"]).mean()), 4),
               "dbp_error_medio_mm": round(float(err_dbp.mean()), 2),
               "dbp_error_relativo_medio": round(float((err_dbp / t["dbp_experto_mm"]).mean()), 4)}
    log(f"Prueba interna (máscara del experto): {interno}")
    return {"medidas_prueba": interno, "prueba_externa_hc18": prueba_externa_hc18(red, cfg, log)}


def prueba_externa_hc18(red, cfg, log) -> dict:
    """HC de la red sobre las 999 imágenes ORIGINALES de HC18 (Radboud), con su
    tamaño de píxel, frente a la HC que midió el ecografista. Ninguna de estas
    imágenes se usó para entrenar ni para elegir la época."""
    hc18 = pd.read_excel(RAIZ / "entrenamiento" / "redes_ecografia_real" / "catalogo_imagenes.xlsx",
                         sheet_name="HC18")
    filas = []
    for _, r in hc18.iterrows():
        gris = np.array(Image.open(RAIZ / "entrenamiento" / "redes_ecografia_real" / r["ruta"]).convert("L"))
        cuadrada = a_cuadrado(gris, cfg["lado"])[0]
        pred = _en_original(predecir(red, cuadrada[None])[0], gris.shape, cfg["lado"])
        e = elipse(pred > 0)
        filas.append({"archivo": r["archivo"], "particion_hc18": r["particion"], "trimestre": r["trimestre"],
                      "hc_ecografista_mm": r["circunferencia_cefalica_mm"],
                      "hc_red_mm": e["perimetro"] * r["tamano_pixel_mm"] if e else np.nan})
    t = pd.DataFrame(filas)
    t["error_mm"] = (t["hc_red_mm"] - t["hc_ecografista_mm"]).abs()
    t.to_csv(AQUI / "salidas" / "cabeza" / "externa_hc18.csv", index=False)
    sub = t[t["particion_hc18"] == "prueba"]
    res = {"imagenes": len(t), "sin_cabeza_detectada": int(t["hc_red_mm"].isna().sum()),
           "hc_error_medio_mm": round(float(t["error_mm"].mean()), 2),
           "hc_error_mediano_mm": round(float(t["error_mm"].median()), 2),
           "hc_error_relativo_medio": round(float((t["error_mm"] / t["hc_ecografista_mm"]).mean()), 4),
           "dentro_de_5_por_ciento": round(float(((t["error_mm"] / t["hc_ecografista_mm"]) <= 0.05).mean()), 4),
           "r2": round(float(1 - ((t["hc_red_mm"] - t["hc_ecografista_mm"]) ** 2).sum()
                             / ((t["hc_ecografista_mm"] - t["hc_ecografista_mm"].mean()) ** 2).sum()), 4),
           "por_trimestre_error_medio_mm": {k: round(float(v), 2) for k, v in
                                            t.groupby("trimestre")["error_mm"].mean().items()},
           "mismas_146_de_prueba_que_la_red_de_regresion": {
               "imagenes": len(sub), "hc_error_medio_mm": round(float(sub["error_mm"].mean()), 2)}}
    log(f"Prueba externa HC18: {res}")
    return res


def medir_torax(red, prueba, pred_p, Y_p, cfg, log) -> dict:
    filas = []
    for (_, r), pc in zip(prueba.iterrows(), pred_p):
        real = np.array(Image.open(RAIZ / r["mascara"]))
        pred = _en_original(pc, real.shape, cfg["lado"])
        fila = {"imagen": r["imagen"]}
        for nombre, m in (("experto", real), ("red", pred)):
            torax, corazon = elipse(m >= 1), elipse(m == 2)
            fila[f"ict_circ_{nombre}"] = corazon["perimetro"] / torax["perimetro"] if torax and corazon else np.nan
            fila[f"ict_area_{nombre}"] = (mayor_componente(m == 2).sum() / mayor_componente(m >= 1).sum()
                                          if (m >= 1).any() and (m == 2).any() else np.nan)
        filas.append(fila)
    t = pd.DataFrame(filas)
    t.to_csv(AQUI / "salidas" / "torax" / "prueba_medidas.csv", index=False)
    res = {"ict_circunferencias_error_medio": round(float((t["ict_circ_red"] - t["ict_circ_experto"]).abs().mean()), 4),
           "ict_circunferencias_experto_medio": round(float(t["ict_circ_experto"].mean()), 4),
           "ict_areas_error_medio": round(float((t["ict_area_red"] - t["ict_area_experto"]).abs().mean()), 4),
           "ict_areas_experto_medio": round(float(t["ict_area_experto"].mean()), 4),
           "imagenes": int(t["ict_circ_red"].notna().sum())}
    log(f"Índice cardiotorácico: {res}")
    return {"indice_cardiotoracico_prueba": res}


def medir_abdomen(red, prueba, pred_p, Y_p, cfg, log) -> dict:
    """¿Ve el estómago y la vena umbilical cuando el experto los marcó? Una
    estructura cuenta como vista si ocupa al menos 0,05 % de la imagen."""
    minimo = 0.0005 * Y_p.shape[1] * Y_p.shape[2]
    res = {}
    for c, nombre in ((2, "estomago"), (3, "vena_umbilical")):
        real = (Y_p == c).reshape(len(Y_p), -1).sum(1) > minimo
        pred = (pred_p == c).reshape(len(pred_p), -1).sum(1) > minimo
        res[nombre] = {"sensibilidad": round(float((pred & real).sum() / max(real.sum(), 1)), 4),
                       "especificidad": round(float((~pred & ~real).sum() / max((~real).sum(), 1)), 4),
                       "con_estructura": int(real.sum()), "sin_estructura": int((~real).sum())}
    log(f"Detección de marcadores del plano abdominal: {res}")
    return {"marcadores_plano_abdominal": res}


def medir_intraparto(red, prueba, pred_p, Y_p, cfg, log) -> dict:
    """Ángulo de progresión de la red frente al medido por el experto (IUGC).

    Se informa también el error del MISMO cálculo sobre la máscara del experto:
    es el piso del método (dónde pone el experto los puntos frente a los
    extremos del eje de la sínfisis), para separar el error de la red del del
    método."""
    from app.angulo_progresion import angulo_progresion

    filas = []
    for (_, r), pc in zip(prueba.iterrows(), pred_p):
        real = np.array(Image.open(RAIZ / r["mascara"]))
        pred = _en_original(pc, real.shape, cfg["lado"])
        a_red, a_mascara = angulo_progresion(pred), angulo_progresion(real)
        filas.append({"imagen": r["imagen"], "aop_experto": r["aop"],
                      "aop_red": a_red["aop"] if a_red else np.nan,
                      "aop_mascara_experto": a_mascara["aop"] if a_mascara else np.nan})
    t = pd.DataFrame(filas)
    t.to_csv(AQUI / "salidas" / "intraparto" / "prueba_medidas.csv", index=False)
    e = (t["aop_red"] - t["aop_experto"]).abs()
    piso = (t["aop_mascara_experto"] - t["aop_experto"]).abs()
    corte = 120
    clase_real, clase_red = t["aop_experto"] >= corte, t["aop_red"] >= corte
    validas = t["aop_red"].notna()
    res = {"imagenes": int(validas.sum()), "sin_estructuras": int((~validas).sum()),
           "aop_error_medio_grados": round(float(e.mean()), 2), "aop_error_mediano_grados": round(float(e.median()), 2),
           "aop_dentro_de_5_grados": round(float((e <= 5).mean()), 4),
           "aop_dentro_de_10_grados": round(float((e <= 10).mean()), 4),
           "piso_del_metodo_mascara_experto_error_medio": round(float(piso.mean()), 2),
           "acuerdo_corte_120_grados": round(float((clase_real[validas] == clase_red[validas]).mean()), 4),
           "casos_aop_120_o_mas": int(clase_real.sum()),
           # El acuerdo global lo dominan los < 120°: se informan por separado.
           "sensibilidad_aop_120": round(float((clase_red & clase_real).sum() / max(1, clase_real.sum())), 4),
           "especificidad_aop_120": round(float((~clase_red & ~clase_real).sum() / max(1, (~clase_real).sum())), 4)}
    log(f"Ángulo de progresión: {res}")
    return {"angulo_progresion_prueba": res}


if __name__ == "__main__":
    entrenar(sys.argv[1])
