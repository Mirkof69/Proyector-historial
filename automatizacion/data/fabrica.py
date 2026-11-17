"""Datos sintéticos para las pruebas (Faker con locale «es»). Nunca datos de pacientes reales.

Todo lo que se crea lleva el prefijo «QA» en el nombre o en el motivo, y se anota en `CREADOS` para limpiarlo al
final de la corrida (ver tests/conftest de limpieza). La CI empieza con 99 y tiene 9 dígitos, un rango que no
usan las cédulas bolivianas reales.
"""
from __future__ import annotations

import random
from datetime import date, datetime, timedelta

from faker import Faker

from utils import config

fake = Faker("es")
CREADOS: list[tuple[str, int]] = []   # (ruta del recurso, id) en orden de creación


def ci_sintetica() -> str:
    return "99" + "".join(random.choice("0123456789") for _ in range(7))


def dia(n: int = 0) -> str:
    return (date.today() + timedelta(days=n)).isoformat()


def dia_habil(desde: int = 1) -> str:
    d = date.today() + timedelta(days=desde)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d.isoformat()


def paciente(**cambios) -> dict:
    datos = {
        "nombre": f"{config.PREFIJO_DATOS} {fake.first_name_female()}",
        "apellido_paterno": fake.last_name(),
        "apellido_materno": fake.last_name(),
        "fecha_nacimiento": fake.date_of_birth(minimum_age=18, maximum_age=40).isoformat(),
        "ci": ci_sintetica(),
        "genero": "femenino",
        "telefono": "7" + "".join(random.choice("0123456789") for _ in range(7)),
        "consentimiento_datos_aceptado": True,
    }
    datos.update(cambios)
    return datos


def embarazo(paciente_id: int, dias_fum: int = 200, **cambios) -> dict:
    return {"paciente": paciente_id, "numero_gesta": 1, "fecha_ultima_menstruacion": dia(-dias_fum), **cambios}


def control(paciente_id: int, embarazo_id: int, semanas: int = 29, **cambios) -> dict:
    return {"embarazo": embarazo_id, "paciente": paciente_id, "numero_control": 1, "fecha_control": dia(0),
            "semanas_gestacion": semanas, "peso_actual": "64.0", "talla": "158", "presion_arterial_sistolica": 112,
            "presion_arterial_diastolica": 72, "frecuencia_cardiaca_fetal": 142, **cambios}


def triaje(paciente_id: int, **cambios) -> dict:
    return {"paciente": paciente_id, "prioridad": "normal", "peso_kg": "64.0", "talla_cm": "158.0", "presion_sistolica": 112,
            "presion_diastolica": 72, "temperatura": "36.6", "frecuencia_cardiaca": 82, "frecuencia_respiratoria": 16,
            "motivo_visita": f"{config.PREFIJO_DATOS} control prenatal", **cambios}


def ahora_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def anotar(ruta: str, ident: int) -> int:
    CREADOS.append((ruta, ident))
    return ident
