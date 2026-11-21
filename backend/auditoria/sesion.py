"""Identificador de sesión para la auditoría.

Con JWT no hay sesión de Django: al iniciar sesión se genera un `sid` que
viaja dentro del token (claim «sid», se copia al access y sobrevive a los
refresh). Cada registro de auditoría lo guarda, así se puede reconstruir qué
hizo una persona entre que entró y salió.
"""
import uuid

CLAIM = "sid"


def nuevo_sid() -> str:
    return uuid.uuid4().hex


def sesion_de(request) -> str:
    """El sid del request: el fijado a mano (login/logout) o el del token."""
    if request is None:
        return ""
    for candidato in (request, getattr(request, "_request", None)):
        if candidato is None:
            continue
        explicito = getattr(candidato, "_sesion_auditoria", "")
        if explicito:
            return explicito
        token = getattr(candidato, "auth", None)
        try:
            sid = token.get(CLAIM) if token is not None and hasattr(token, "get") else None
        except Exception:
            sid = None
        if sid:
            return str(sid)
    return ""


def fijar_sesion(request, sid: str) -> None:
    """Asocia el sid a este request (el token aún no existe o ya expiró)."""
    for candidato in (request, getattr(request, "_request", None)):
        if candidato is not None:
            try:
                candidato._sesion_auditoria = sid
            except Exception:
                pass
