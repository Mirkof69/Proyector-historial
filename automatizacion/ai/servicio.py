"""Elige el proveedor, anonimiza, llama y deja constancia de cada uso en ai/registro_uso_ia.jsonl.

AI_PROVIDER=ollama (por defecto: local y, si no está, Claude) | anthropic (solo Claude) | auto.
El registro guarda fecha, tarea, proveedor, modelo, tamaños y duración: no guarda el contenido.
"""
from __future__ import annotations

import json
import time
from datetime import datetime

from ai import proveedor_claude, proveedor_ollama
from ai.anonimizador import anonimizar
from utils import config

REGISTRO = config.RAIZ / "ai" / "registro_uso_ia.jsonl"


def proveedor():
    """(módulo, motivo). módulo es None si no hay ninguno disponible."""
    preferido = config.env("AI_PROVIDER", "ollama").lower()
    orden = [proveedor_claude] if preferido == "anthropic" else [proveedor_ollama, proveedor_claude]
    motivos = []
    for p in orden:
        ok, motivo = p.disponible()
        if ok:
            return p, ""
        motivos.append(motivo)
    return None, " · ".join(motivos)


def estado() -> dict:
    p, motivo = proveedor()
    return {"disponible": p is not None, "proveedor": p.NOMBRE if p else "", "modelo": p.MODELO if p else "",
            "motivo": motivo}


def consultar(tarea: str, sistema: str, contenido: str) -> dict:
    p, motivo = proveedor()
    if p is None:
        return {"disponible": False, "motivo": motivo, "texto": ""}
    limpio = anonimizar(contenido, 12000)
    t0 = time.perf_counter()
    try:
        texto, error = p.completar(sistema, limpio), ""
    except Exception as e:
        texto, error = "", f"{type(e).__name__}: {str(e)[:200]}"
    with open(REGISTRO, "a", encoding="utf-8") as f:
        f.write(json.dumps({"fecha": datetime.now().isoformat(timespec="seconds"), "tarea": tarea,
                            "proveedor": p.NOMBRE, "modelo": p.MODELO, "caracteres_enviados": len(limpio),
                            "caracteres_recibidos": len(texto), "segundos": round(time.perf_counter() - t0, 1),
                            "anonimizado": True, "error": error}, ensure_ascii=False) + "\n")
    return {"disponible": not error, "motivo": error, "texto": texto, "proveedor": p.NOMBRE, "modelo": p.MODELO}
