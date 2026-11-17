"""Proveedor en la nube: Claude con el SDK oficial de Anthropic. Solo recibe texto ya anonimizado.

Se activa con ANTHROPIC_API_KEY en .env (AI_PROVIDER=anthropic, o como respaldo si Ollama no está). El
pensamiento adaptativo viene activo por defecto en el modelo; la profundidad se regula con output_config.effort.
Se pide el respaldo del servidor ante un rechazo del clasificador de seguridad (fallbacks="default").
"""
from __future__ import annotations

import anthropic

from utils import config

MODELO = config.env("ANTHROPIC_MODEL", "claude-opus-5-5")
NOMBRE = "anthropic"


def disponible() -> tuple[bool, str]:
    if not config.env("ANTHROPIC_API_KEY"):
        return False, "Falta ANTHROPIC_API_KEY en .env"
    return True, ""


def completar(sistema: str, usuario: str) -> str:
    cliente = anthropic.Anthropic()
    try:
        r = cliente.beta.messages.create(
            model=MODELO, max_tokens=4000, system=sistema,
            output_config={"effort": "low"},
            betas=["server-side-fallback-2026-07-01"], fallbacks="default",
            messages=[{"role": "user", "content": usuario}])
    except anthropic.AuthenticationError as e:
        raise RuntimeError("La llave de Anthropic no es válida") from e
    except anthropic.RateLimitError as e:
        raise RuntimeError("Límite de uso de la API de Anthropic alcanzado; reintentar más tarde") from e
    except anthropic.APIStatusError as e:
        raise RuntimeError(f"Error {e.status_code} de la API de Anthropic: {e.message}") from e
    except anthropic.APIConnectionError as e:
        raise RuntimeError("Sin conexión con la API de Anthropic") from e
    if r.stop_reason == "refusal":
        raise RuntimeError("El modelo declinó la solicitud")
    return "".join(b.text for b in r.content if b.type == "text").strip()
