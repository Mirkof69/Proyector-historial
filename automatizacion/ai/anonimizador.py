"""Anonimiza todo texto antes de enviarlo a un modelo de IA (también al local).

Aunque las pruebas usan datos sintéticos QA, un error o un HTML capturado podría arrastrar un dato de la base
real: correos, cédulas, teléfonos, tokens y claves se reemplazan por marcadores. Regla del plan: ningún dato
clínico ni credencial sale del equipo sin anonimizar.
"""
from __future__ import annotations

import re

from utils import config

_REGLAS = [
    (re.compile(r"eyJ[\w-]{10,}\.[\w-]{10,}\.[\w-]{5,}"), "<token>"),                      # JWT
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "<correo>"),
    (re.compile(r"\b[A-Z2-7]{16,64}\b"), "<secreto>"),                                     # clave TOTP en base32
    (re.compile(r"(?i)(password|contraseña|clave|token|secret|csrf\w*|sessionid)([\"'\s:=]+)[^\s\"',}]+"),
     r"\1\2<oculto>"),
    (re.compile(r"\bPAC-[0-9A-F]{6,}\b"), "<id_clinico>"),
    (re.compile(r"\b\d{5,}\b"), "<numero>"),                                               # CI, teléfonos, historias
    (re.compile(r"\bQA [A-ZÁÉÍÓÚÑ][\wáéíóúñ]+(?: [A-ZÁÉÍÓÚÑ][\wáéíóúñ]+){0,3}"), "<paciente QA>"),
]


def anonimizar(texto: str, limite: int = 6000) -> str:
    if not texto:
        return ""
    if config.PASSWORD:
        texto = texto.replace(config.PASSWORD, "<oculto>")
    for patron, marcador in _REGLAS:
        texto = patron.sub(marcador, texto)
    return texto[:limite]
