"""Proveedor local: Ollama (http://localhost:11434). Nada sale del equipo."""
from __future__ import annotations

import requests

from utils import config

URL = config.env("OLLAMA_URL", "http://localhost:11434").rstrip("/")
MODELO = config.env("OLLAMA_MODEL", "qwen2.5:7b")
NOMBRE = "ollama"


def disponible() -> tuple[bool, str]:
    try:
        r = requests.get(f"{URL}/api/tags", timeout=3)
        modelos = [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return False, f"Ollama no responde en {URL} (instalar desde ollama.com y ejecutar: ollama pull {MODELO})"
    if not any(m.split(":")[0] == MODELO.split(":")[0] for m in modelos):
        return False, f"Ollama está en marcha pero falta el modelo: ollama pull {MODELO}"
    return True, ""


def completar(sistema: str, usuario: str) -> str:
    r = requests.post(f"{URL}/api/chat", timeout=300, json={
        "model": MODELO, "stream": False, "options": {"temperature": 0.2},
        "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": usuario}]})
    r.raise_for_status()
    return r.json()["message"]["content"].strip()
