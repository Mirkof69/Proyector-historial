"""Configuración única de la automatización: se lee de variables de entorno y del archivo .env local.

Ningún secreto vive en el código. `.env.example` documenta cada variable con valores ficticios.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[1]
load_dotenv(RAIZ / ".env")


def env(nombre: str, defecto: str = "") -> str:
    return os.environ.get(nombre, defecto).strip()


@dataclass(frozen=True)
class Rol:
    clave: str          # administrador, medico, enfermera, laboratorista, recepcion
    nombre: str         # cómo se muestra en reportes
    email: str
    totp_secret: str    # vacío si el rol no exige MFA o aún no está configurado
    exige_mfa: bool


def _yaml() -> dict:
    """Valores por defecto no secretos de config/config.yaml (.env y el entorno tienen prioridad)."""
    try:
        import yaml
        return yaml.safe_load((RAIZ / "config" / "config.yaml").read_text(encoding="utf-8")) or {}
    except (OSError, ImportError, ValueError):
        return {}


YAML = _yaml()
SUT_URL = env("SUT_URL", str(YAML.get("base_url", "http://localhost:3000"))).rstrip("/")
SUT_API = env("SUT_API", str(YAML.get("api_url", "http://localhost:8000/api"))).rstrip("/")
PASSWORD = env("QA_PASSWORD")
NAVEGADOR = env("QA_NAVEGADOR", str(YAML.get("navegador", "chrome")))
HEADLESS = env("QA_HEADLESS", "1" if YAML.get("headless", True) else "0") == "1"
TIEMPO_ESPERA = int(env("QA_TIEMPO_ESPERA", str(YAML.get("tiempo_espera_s", 15))))
PREFIJO_DATOS = "QA"   # todo dato sintético que crean las pruebas lleva este prefijo

ROLES: dict[str, Rol] = {
    "administrador": Rol("administrador", "Administrador", env("QA_ADMIN_EMAIL"), env("QA_ADMIN_TOTP_SECRET"), True),
    "medico": Rol("medico", "Médico", env("QA_MEDICO_EMAIL"), env("QA_MEDICO_TOTP_SECRET"), True),
    "enfermera": Rol("enfermera", "Enfermería", env("QA_ENFERMERIA_EMAIL"), "", False),
    "laboratorista": Rol("laboratorista", "Laboratorio", env("QA_LABORATORIO_EMAIL"), "", False),
    "recepcion": Rol("recepcion", "Recepción", env("QA_RECEPCION_EMAIL"), "", False),
}


def guardar_en_env(nombre: str, valor: str) -> None:
    """Escribe o reemplaza una variable en el .env local (por ejemplo, el secreto TOTP del médico tras configurarlo)."""
    ruta = RAIZ / ".env"
    lineas = ruta.read_text(encoding="utf-8").splitlines() if ruta.exists() else []
    nuevas, puesto = [], False
    for l in lineas:
        if l.startswith(f"{nombre}="):
            nuevas.append(f"{nombre}={valor}")
            puesto = True
        else:
            nuevas.append(l)
    if not puesto:
        nuevas.append(f"{nombre}={valor}")
    ruta.write_text("\n".join(nuevas) + "\n", encoding="utf-8")
    os.environ[nombre] = valor
