"""Segunda ronda del clasificador de lesión ovárica: ¿una red más grande o un ensamble rinden más?

    python entrenamiento/ginecologia/mejorar_ovario.py

Fijado ANTES de entrenar (la prueba ya se había mirado una vez con la primera
ronda, así que la elección se hace SOLO con la validación y se informan en la
prueba todas las candidatas, la elegida y las descartadas):

  A  roi + EfficientNet-B0, 384 px        (la elegida en la primera ronda)
  B  roi + EfficientNet-B2, 448 px
  C  ensamble: promedio de A e «imagen + EfficientNet-B0»
  D  ensamble: promedio de B e «imagen + EfficientNet-B0»

Gana la de mayor exactitud balanceada en validación; ante empate (±0,005), la
más simple (A < B < C < D).
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np
import pandas as pd
import torch
from PIL import Image

from clasificar import (AQUI, CONFIG, DESV, IA, MEDIA, UMBRAL_MALIGNIDAD, cuadrado, entrenar,
                        exactitud_balanceada, malignidad, mascaras_unet, metricas, predecir, recorte_lesion)

B0, B2 = "efficientnet_b0.ra_in1k", "efficientnet_b2.ra_in1k"


def main() -> None:
    inicio = time.time()
    cfg = CONFIG["ovario"]
    clases, n = cfg["clases"], len(cfg["clases"])
    cat = pd.read_csv(AQUI / "catalogos" / "ovario.csv")
    partes = {p: cat[cat["particion"] == p].reset_index(drop=True) for p in ("entrenamiento", "validacion", "prueba")}
    imagenes = {p: [Image.open(IA / r).convert("RGB") for r in d["imagen"]] for p, d in partes.items()}
    expertas = [np.array(Image.open(IA / r)) > 0 for r in partes["entrenamiento"]["mascara"]]
    de_red = {p: mascaras_unet(partes[p]) for p in ("validacion", "prueba")}
    y = {p: d["clase"].to_numpy() for p, d in partes.items()}

    def tensores(variante: str, lado: int) -> dict:
        if variante == "imagen":
            return {p: [cuadrado(im, lado) for im in imagenes[p]] for p in partes}
        return {"entrenamiento": [cuadrado(recorte_lesion(im, m), lado)
                                  for im, m in zip(imagenes["entrenamiento"], expertas)],
                **{p: [cuadrado(recorte_lesion(im, m), lado) for im, m in zip(imagenes[p], de_red[p])]
                   for p in ("validacion", "prueba")}}

    miembros = {"roi_b0": ("roi", B0, 384), "roi_b2": ("roi", B2, 448), "imagen_b0": ("imagen", B0, 384)}
    redes, prob = {}, {}
    for nombre, (variante, arq, lado) in miembros.items():
        x = tensores(variante, lado)
        red, _, val = entrenar(x["entrenamiento"], y["entrenamiento"], x["validacion"], y["validacion"], n, lado,
                               nombre, arq)
        redes[nombre] = red
        prob[nombre] = {p: predecir(red, x[p], lado) for p in ("validacion", "prueba")}
        print(f"{nombre}: exactitud balanceada en validación {val:.4f}", flush=True)

    candidatas = {"A": ["roi_b0"], "B": ["roi_b2"], "C": ["roi_b0", "imagen_b0"], "D": ["roi_b2", "imagen_b0"]}

    def promedio(nombres: list[str], parte: str) -> np.ndarray:
        return np.mean([prob[m][parte] for m in nombres], axis=0)

    val = {c: exactitud_balanceada(y["validacion"], promedio(m, "validacion").argmax(1), n)
           for c, m in candidatas.items()}
    mejor = max(val.values())
    elegida = next(c for c in "ABCD" if val[c] >= mejor - 0.005)
    print(f"Validación: { {k: round(v, 4) for k, v in val.items()} } → elegida {elegida}", flush=True)

    i_mal = clases.index("carcinoma_seroso_alto_grado")
    informe = {"tarea": "ovario", "ronda": 2, "candidatas": {c: "+".join(m) for c, m in candidatas.items()},
               "validacion_exactitud_balanceada": {k: round(v, 4) for k, v in val.items()}, "elegida": elegida}
    for c, m in candidatas.items():
        p = promedio(m, "prueba")
        informe[f"prueba_{c}"] = metricas(y["prueba"], p, clases) | {"malignidad": malignidad(y["prueba"], p, i_mal)}
    anterior = json.loads((AQUI / "salidas" / "ovario" / "metricas.json").read_text(encoding="utf-8"))
    final = anterior | {"ronda_2": {k: v for k, v in informe.items() if not k.startswith("prueba_")}
                        | {"prueba_por_candidata": {c: {k: informe[f"prueba_{c}"][k] for k in
                                                         ("exactitud", "exactitud_balanceada", "f1_macro")}
                                                    | {"malignidad": informe[f"prueba_{c}"]["malignidad"]}
                                                    for c in candidatas}},
                        "prueba": informe[f"prueba_{elegida}"],
                        "variante_elegida": "+".join(candidatas[elegida])}
    salida = AQUI / "salidas" / "ovario"
    (salida / "metricas_ronda2.json").write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
    (salida / "metricas.json").write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")

    tabla = partes["prueba"][["imagen", "clase_nombre"]].copy()
    p = promedio(candidatas[elegida], "prueba")
    tabla["predicha"] = [clases[i] for i in p.argmax(1)]
    for i, c in enumerate(clases):
        tabla[f"p_{c}"] = p[:, i].round(4)
    tabla.to_csv(salida / "predicciones_prueba.csv", index=False)

    torch.save({"estado": [redes[m].state_dict() for m in candidatas[elegida]], "meta": {
        "arquitectura": "ensamble" if len(candidatas[elegida]) > 1 else miembros[candidatas[elegida][0]][1],
        "miembros": [{"nombre": m, "variante": miembros[m][0], "arquitectura": miembros[m][1].split(".")[0],
                      "lado": miembros[m][2]} for m in candidatas[elegida]],
        "clases": clases, "nombres": cfg["nombres"], "media": MEDIA, "desv": DESV,
        "umbral_malignidad": UMBRAL_MALIGNIDAD, "volteo_prueba": True, "metricas": final}},
        salida / "clasificador_ovario.pth")
    print(json.dumps({k: v for k, v in informe.items() if not k.startswith("prueba_")}, ensure_ascii=False, indent=2))
    print(json.dumps({k: informe[f"prueba_{elegida}"][k] for k in
                      ("exactitud", "exactitud_balanceada", "exactitud_ic95", "f1_macro", "malignidad")},
                     ensure_ascii=False, indent=2))
    print(f"Listo en {(time.time() - inicio) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    sys.path.insert(0, str(AQUI))
    main()
