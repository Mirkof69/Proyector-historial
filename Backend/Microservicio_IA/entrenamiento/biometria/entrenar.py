"""Longitud del fémur y diámetros abdominales con una red de puntos, medidos en pacientes no vistas.

    python entrenamiento/biometria/entrenar.py femur
    python entrenamiento/biometria/entrenar.py abdomen

Datos: Multicentre Fetal Biometry 2026 (UCL RDR 10.5522/04/30819911, CC BY-NC-SA):
4.513 imágenes de 1.904 pacientes, 4 hospitales (Barcelona ×2, Radboud, UCLH),
7 ecógrafos, con los puntos de medida marcados por expertos y mm por píxel.

Cómo se mide (fijado antes de mirar la prueba):
  · Partición oficial por paciente (_Train / _Test), menos las pacientes de
    UCLH que la partición oficial pone en los dos lados. Validación: 15 % de las
    pacientes de entrenamiento, para elegir la época (error relativo medio).
  · Una U-Net (la misma de app/unet.py) predice un mapa de calor por diámetro
    con DOS picos (sus extremos). La medida es la distancia entre los dos picos:
    no depende de en qué orden marcó el experto los extremos.
  · Error en mm donde la imagen trae mm por píxel; error relativo en todas.
  · Abdomen: circunferencia abdominal = perímetro de la elipse con ejes TAD y
    APAD (Ramanujan), como la mide el ecografista con dos diámetros.
"""
from __future__ import annotations

import json
import math
import random
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
IA = AQUI.parents[1]
sys.path.insert(0, str(IA))
from app.unet import UNet, a_cuadrado, a_tensor  # noqa: E402

DATOS = IA / "datos" / "extraidos" / "obstetricia" / "FetalBiometry-Multicentre-Landmarks-2026"
DISPOSITIVO = "cuda" if torch.cuda.is_available() else "cpu"
SEMILLA = 2026
LADO = 384
SIGMA = 5.0          # píxeles a 384
SEPARACION = 12      # radio de supresión entre los dos picos de un mismo diámetro
CONFIG = {
    "femur": {"anatomia": "Femur", "diametros": ["fl"], "epocas": 80, "lote": 12, "lr": 6e-4},
    "abdomen": {"anatomia": "Abdomen", "diametros": ["tad", "apad"], "epocas": 80, "lote": 12, "lr": 6e-4},
}


CATALOGO_EXCLUIDAS: dict[str, dict] = {}


def fijar_semilla() -> None:
    random.seed(SEMILLA)
    np.random.seed(SEMILLA)
    torch.manual_seed(SEMILLA)
    torch.cuda.manual_seed_all(SEMILLA)


def paciente(fila) -> str:
    """FP y HC18 traen la paciente; las de UCLH se agrupan por el número del archivo (001_FL, 001_2FL…)."""
    if not pd.isna(fila.get("Patient")):
        return f"p{int(fila['Patient'])}"
    return "ucl" + str(fila["image_name"]).split("_")[0]


def sitio(nombre: str) -> str:
    return "Barcelona (FETAL_PLANES)" if nombre.startswith("Patient") else "Londres (UCLH)"


def catalogo(tarea: str) -> dict[str, pd.DataFrame]:
    cfg = CONFIG[tarea]
    base = DATOS / "annotations" / "MULTICENTRE"
    ent = pd.read_csv(base / f"{cfg['anatomia']}_Train.csv")
    pru = pd.read_csv(base / f"{cfg['anatomia']}_Test.csv")
    for df in (ent, pru):
        df["paciente"] = df.apply(paciente, axis=1)
        df["sitio"] = df["image_name"].map(sitio)
    rng = random.Random(SEMILLA)
    grupos = sorted(ent["paciente"].unique())
    rng.shuffle(grupos)
    val = set(grupos[: round(0.15 * len(grupos))])
    # El README promete partición por paciente, pero hay pacientes de UCLH en los
    # dos lados (p. ej. 031, 034, 056): esas imágenes salen de la prueba.
    compartidas = set(ent["paciente"]) & set(pru["paciente"])
    CATALOGO_EXCLUIDAS[tarea] = {"pacientes_en_ambos_lados": sorted(compartidas),
                                 "imagenes_de_prueba_quitadas": int(pru["paciente"].isin(compartidas).sum())}
    pru = pru[~pru["paciente"].isin(compartidas)]
    return {"entrenamiento": ent[~ent["paciente"].isin(val)].reset_index(drop=True),
            "validacion": ent[ent["paciente"].isin(val)].reset_index(drop=True),
            "prueba": pru.reset_index(drop=True)}


def cargar(df: pd.DataFrame, cfg: dict) -> tuple[np.ndarray, np.ndarray, list]:
    """Imágenes a LADO y puntos en coordenadas de LADO: (N, diámetros, 2 extremos, xy)."""
    X, P, geo = [], [], []
    for _, r in df.iterrows():
        gris = np.array(Image.open(DATOS / "images" / "MULTICENTRE" / cfg["anatomia"] / r["image_name"]).convert("L"))
        cuadrada, mayor, (dy, dx) = a_cuadrado(gris, LADO)
        f = LADO / mayor
        P.append([[[(r[f"{d}_{k}_x"] + dx) * f, (r[f"{d}_{k}_y"] + dy) * f] for k in (1, 2)]
                  for d in cfg["diametros"]])
        X.append(cuadrada)
        geo.append((mayor, dy, dx))
    return np.stack(X), np.asarray(P, dtype=np.float32), geo


def mapas(puntos: torch.Tensor) -> torch.Tensor:
    """(N, D, 2, 2) → (N, D, LADO, LADO): un mapa por diámetro con sus dos picos gaussianos."""
    yy, xx = torch.meshgrid(torch.arange(LADO, device=puntos.device), torch.arange(LADO, device=puntos.device),
                            indexing="ij")
    px = puntos[..., 0][..., None, None]
    py = puntos[..., 1][..., None, None]
    g = torch.exp(-((xx - px) ** 2 + (yy - py) ** 2) / (2 * SIGMA ** 2))
    return g.max(dim=2).values


def aumentar(x: torch.Tensor, puntos: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Giro ±20°, escala ±15 %, desplazamiento y volteo; brillo y contraste solo a la imagen."""
    n, d = x.shape[0], x.device
    ang = (torch.rand(n, device=d) - 0.5) * (40 * math.pi / 180)
    esc = 1 + (torch.rand(n, device=d) - 0.5) * 0.3
    volteo = torch.where(torch.rand(n, device=d) < 0.5, -1.0, 1.0)
    desp = (torch.rand(n, 2, device=d) - 0.5) * 0.2
    theta = torch.zeros(n, 2, 3, device=d)
    theta[:, 0, 0] = torch.cos(ang) / esc * volteo
    theta[:, 0, 1] = -torch.sin(ang) / esc
    theta[:, 1, 0] = torch.sin(ang) / esc * volteo
    theta[:, 1, 1] = torch.cos(ang) / esc
    theta[:, :, 2] = desp
    x = F.grid_sample(x, F.affine_grid(theta, x.shape, align_corners=False), align_corners=False)
    # Los puntos van con la transformación inversa de la rejilla: salida = A^-1 (entrada - t)
    normal = puntos / LADO * 2 - 1
    A = theta[:, :, :2]
    inv = torch.linalg.inv(A)
    rel = normal - desp[:, None, None, :]
    nuevos = torch.einsum("nij,ndkj->ndki", inv, rel)
    x = x * (1 + (torch.rand(n, 1, 1, 1, device=d) - 0.5) * 0.4) + (torch.rand(n, 1, 1, 1, device=d) - 0.5) * 0.4
    return x, (nuevos + 1) / 2 * LADO


def picos(mapa: np.ndarray) -> np.ndarray:
    """Los dos máximos de un mapa (refinados con el centroide 5×5)."""
    m = mapa.copy()
    salida = []
    for _ in range(2):
        y, x = np.unravel_index(np.argmax(m), m.shape)
        y0, y1, x0, x1 = max(0, y - 2), min(LADO, y + 3), max(0, x - 2), min(LADO, x + 3)
        ventana = np.clip(mapa[y0:y1, x0:x1], 0, None)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        s = ventana.sum() or 1.0
        salida.append([(ventana * xx).sum() / s, (ventana * yy).sum() / s])
        m[max(0, y - SEPARACION):y + SEPARACION + 1, max(0, x - SEPARACION):x + SEPARACION + 1] = -1e9
    return np.asarray(salida)


@torch.no_grad()
def predecir(red, X: np.ndarray) -> np.ndarray:
    """(N, D, 2, 2) en coordenadas de LADO. Promedia con el volteo horizontal."""
    red.eval()
    salida = []
    for i in range(0, len(X), 16):
        xb = a_tensor(X[i:i + 16]).to(DISPOSITIVO)
        with torch.autocast("cuda", dtype=torch.float16, enabled=DISPOSITIVO == "cuda"):
            h = red(xb).float().sigmoid() + red(xb.flip(3)).float().sigmoid().flip(3)
        for mapa in h.cpu().numpy():
            salida.append([picos(c) for c in mapa])
    return np.asarray(salida)


def longitudes(p: np.ndarray, geo: list) -> np.ndarray:
    """Distancia de cada diámetro en píxeles de la imagen ORIGINAL."""
    f = np.array([g[0] / LADO for g in geo])[:, None]
    return np.linalg.norm(p[:, :, 0] - p[:, :, 1], axis=-1) * f


def elipse_perimetro(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Ramanujan con los ejes completos a y b."""
    a, b = a / 2, b / 2
    h = ((a - b) / (a + b)) ** 2
    return math.pi * (a + b) * (1 + 3 * h / (10 + np.sqrt(4 - 3 * h)))


def resumir(sub: pd.DataFrame, medidas: list[str]) -> dict:
    """Errores sobre las imágenes donde la medida existe: la CA solo se calcula con
    mm por píxel, así que se cuenta sobre esas (antes las vacías se contaban como
    fuera del 5 %)."""
    r = {"imagenes": len(sub)}
    con_mm = sub[sub["mm_por_px"].notna()]
    for m in medidas:
        rel = sub[f"{m}_error_relativo"].dropna()
        e_mm = (con_mm[f"{m}_red_mm"] - con_mm[f"{m}_experto_mm"]).abs()
        r[m] = {"imagenes": int(len(rel)), "error_relativo_medio": round(float(rel.mean()), 4),
                "dentro_de_5_por_ciento": round(float((rel <= 0.05).mean()), 4),
                "imagenes_con_mm": int(len(con_mm)),
                "error_medio_mm": round(float(e_mm.mean()), 2) if len(con_mm) else None,
                "error_mediano_mm": round(float(e_mm.median()), 2) if len(con_mm) else None}
    return r


def entrenar(tarea: str) -> None:
    cfg = CONFIG[tarea]
    salida = AQUI / "salidas" / tarea
    salida.mkdir(parents=True, exist_ok=True)
    fijar_semilla()
    partes = catalogo(tarea)
    datos = {p: cargar(d, cfg) for p, d in partes.items()}
    for p, d in partes.items():
        print(f"{p:<13} {len(d)} imágenes · {d['paciente'].nunique()} pacientes · "
              f"{d['sitio'].value_counts().to_dict()}", flush=True)
    n_d = len(cfg["diametros"])
    red = UNet("efficientnet_b2", n_d).to(DISPOSITIVO)
    opt = torch.optim.AdamW(red.parameters(), lr=cfg["lr"], weight_decay=1e-4)
    X_e, P_e, _ = datos["entrenamiento"]
    pasos = cfg["epocas"] * int(np.ceil(len(X_e) / cfg["lote"]))
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=cfg["lr"], total_steps=pasos, pct_start=0.1)
    escala = torch.amp.GradScaler("cuda", enabled=DISPOSITIVO == "cuda")
    X_v, P_v, geo_v = datos["validacion"]
    real_v = longitudes(P_v, geo_v)
    mejor, mejor_estado, historia = 1e9, None, []
    for ep in range(1, cfg["epocas"] + 1):
        red.train()
        t0, total = time.perf_counter(), 0.0
        orden = np.random.permutation(len(X_e))
        for i in range(0, len(orden), cfg["lote"]):
            idx = orden[i:i + cfg["lote"]]
            if len(idx) < 2:
                continue
            xb = a_tensor(X_e[idx]).to(DISPOSITIVO)
            pb = torch.from_numpy(P_e[idx]).to(DISPOSITIVO)
            xb, pb = aumentar(xb, pb)
            objetivo = mapas(pb)
            with torch.autocast("cuda", dtype=torch.float16, enabled=DISPOSITIVO == "cuda"):
                logits = red(xb)
            # Los píxeles cerca de un extremo pesan más: si no, «todo cero» ya da un error bajo.
            peso = 1 + 20 * objetivo
            loss = (peso * F.binary_cross_entropy_with_logits(logits.float(), objetivo, reduction="none")).mean()
            opt.zero_grad(set_to_none=True)
            escala.scale(loss).backward()
            escala.step(opt)
            escala.update()
            sched.step()
            total += loss.item() * len(idx)
        pred_v = longitudes(predecir(red, X_v), geo_v)
        err = float(np.mean(np.abs(pred_v - real_v) / real_v))
        historia.append({"epoca": ep, "perdida": total / len(X_e), "error_relativo_val": err})
        if err < mejor:
            mejor, mejor_estado = err, {k: v.detach().cpu().clone() for k, v in red.state_dict().items()}
        print(f"época {ep:3d}/{cfg['epocas']}  pérdida {total / len(X_e):.4f}  error relativo val {err:.4f}"
              f"{'  *' if err == mejor else ''}  ({time.perf_counter() - t0:.0f} s)", flush=True)

    red.load_state_dict(mejor_estado)
    epoca = int(np.argmin([h["error_relativo_val"] for h in historia])) + 1
    X_p, P_p, geo_p = datos["prueba"]
    pred_p, real_p = longitudes(predecir(red, X_p), geo_p), longitudes(P_p, geo_p)
    prueba = partes["prueba"].copy()
    mm = prueba["px_to_mm_rate"].to_numpy(dtype=float)
    filas = {"imagen": prueba["image_name"], "sitio": prueba["sitio"], "mm_por_px": mm}
    for j, d in enumerate(cfg["diametros"]):
        filas[f"{d}_experto_mm"] = real_p[:, j] * mm
        filas[f"{d}_red_mm"] = pred_p[:, j] * mm
        filas[f"{d}_error_relativo"] = np.abs(pred_p[:, j] - real_p[:, j]) / real_p[:, j]
    t = pd.DataFrame(filas)
    if tarea == "abdomen":
        t["ca_experto_mm"] = elipse_perimetro(t["tad_experto_mm"], t["apad_experto_mm"])
        t["ca_red_mm"] = elipse_perimetro(t["tad_red_mm"], t["apad_red_mm"])
        t["ca_error_relativo"] = (t["ca_red_mm"] - t["ca_experto_mm"]).abs() / t["ca_experto_mm"]
    t.to_csv(salida / "prueba_medidas.csv", index=False)

    medidas = ["fl"] if tarea == "femur" else ["tad", "apad", "ca"]

    resumen = lambda sub: resumir(sub, medidas)  # noqa: E731

    metricas = {"tarea": tarea, "dataset": "Multicentre Fetal Biometry 2026 (UCL RDR 10.5522/04/30819911)",
                "particion": "oficial por paciente (_Train/_Test) sin las pacientes de UCLH que aparecían en los "
                             "dos lados; validación 15 % de las pacientes de entrenamiento",
                "fuga_en_la_particion_oficial": CATALOGO_EXCLUIDAS.get(tarea),
                "imagenes_prueba": len(t), "pacientes_prueba": int(partes["prueba"]["paciente"].nunique()),
                "epoca_elegida": epoca, "error_relativo_validacion": round(mejor, 4),
                "prueba": resumen(t), "por_sitio": {s: resumen(g) for s, g in t.groupby("sitio")}}
    torch.save({"estado": red.state_dict(), "meta": {
        "arquitectura": "unet_puntos", "codificador": "efficientnet_b2", "diametros": cfg["diametros"],
        "lado": LADO, "separacion": SEPARACION, "media": 0.485, "desv": 0.229, "volteo_prueba": True,
        "metricas": metricas}}, salida / f"biometria_{tarea}.pth")
    (salida / "metricas.json").write_text(json.dumps(metricas, ensure_ascii=False, indent=2), encoding="utf-8")
    (salida / "historia.json").write_text(json.dumps(historia, indent=1), encoding="utf-8")
    print(json.dumps(metricas, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    entrenar(sys.argv[1])
