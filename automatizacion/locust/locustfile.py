"""Pruebas de rendimiento con Locust (TC-112 a TC-115) contra la API del sistema.

Cada usuario virtual inicia sesión con un rol real (doble factor incluido para médico y administrador) y recorre
las consultas que ese rol hace en un turno: SOLO LECTURAS, para no llenar la base real con datos de carga.
Mezcla de usuarios según la clínica: recepción 3, médico 3, enfermería 2, laboratorio 1, administración 1.

Escenarios (variable ESCENARIO):
  carga        TC-112  40 usuarios, 4 nuevos por segundo, 3 minutos (se pasa -u 40 -r 4 -t 3m)
  estres       TC-113  escalones de 20 usuarios cada 60 s hasta 200: busca el punto de degradación
  pico         TC-114  10 usuarios, salto a 150 durante 60 s y vuelta a 10: ¿se recupera?
  resistencia  TC-115  40 usuarios durante 15 minutos: ¿se degrada con el tiempo?
Los tres últimos pueden saturar el equipo: se ejecutan solo con autorización (punto de control del plan).

    set ESCENARIO=carga
    .venv\\Scripts\\locust -f locust\\locustfile.py --headless -u 40 -r 4 -t 3m --host http://localhost:8000 ^
        --csv reports\\locust\\carga --html reports\\locust\\carga.html
"""
from __future__ import annotations

import os
import random
import sys
from datetime import date
from pathlib import Path

from locust import HttpUser, LoadTestShape, between, task

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils import config, totp  # noqa: E402

ESCENARIO = os.environ.get("ESCENARIO", "carga")
PAGINA = {"page_size": 20}


class UsuarioClinica(HttpUser):
    abstract = True
    wait_time = between(1, 4)   # tiempo de lectura entre una pantalla y la siguiente
    rol = "recepcion"

    def on_start(self):
        self.client.get("/api/token/csrf/", name="/api/token/csrf/")
        rol = config.ROLES[self.rol]
        r = self._post("/api/usuarios/login/", {"email": rol.email, "password": config.PASSWORD})
        datos = r.json() if r.ok else {}
        if datos.get("mfa_required"):
            self._post("/api/usuarios/mfa-verify/", {"temp_token": datos.get("temp_token"),
                                                     "totp_code": totp.codigo(rol.totp_secret)})
        self.pacientes = [p["id"] for p in self._lista("/api/pacientes/", nombre="/api/pacientes/ (inicio)")] or [0]

    def _post(self, ruta: str, cuerpo: dict):
        cabeceras = {"X-CSRFToken": self.client.cookies.get("csrftoken", ""), "Referer": config.SUT_URL + "/"}
        return self.client.post(ruta, json=cuerpo, headers=cabeceras, name=ruta)

    def _lista(self, ruta: str, nombre: str | None = None, **params) -> list[dict]:
        r = self.client.get(ruta, params={**PAGINA, **params}, name=nombre or ruta)
        if not r.ok:
            return []
        datos = r.json()
        return datos.get("results", datos) if isinstance(datos, dict) else datos

    def _paciente(self) -> int:
        return random.choice(self.pacientes)


class Recepcion(UsuarioClinica):
    weight = 3
    rol = "recepcion"

    @task(3)
    def buscar_paciente(self):
        self._lista("/api/pacientes/", nombre="/api/pacientes/?search", search=random.choice(["QA", "Mar", "Ro", "99"]))

    @task(2)
    def agenda_de_hoy(self):
        self._lista("/api/citas/citas/", nombre="/api/citas/citas/?fecha", fecha_cita=date.today().isoformat())

    @task(1)
    def ficha(self):
        self.client.get(f"/api/pacientes/{self._paciente()}/", name="/api/pacientes/{id}/")


class Medico(UsuarioClinica):
    weight = 3
    rol = "medico"

    @task(3)
    def embarazos(self):
        self._lista("/api/embarazos/")

    @task(2)
    def controles(self):
        self._lista("/api/controles/")

    @task(2)
    def historia(self):
        pid = self._paciente()
        self.client.get(f"/api/pacientes/{pid}/", name="/api/pacientes/{id}/")
        self._lista("/api/controles/", nombre="/api/controles/?paciente", paciente=pid)
        self._lista("/api/ecografias/", nombre="/api/ecografias/?paciente", paciente=pid)

    @task(1)
    def panel(self):
        self.client.get("/api/reportes/dashboard-kpis/", name="/api/reportes/dashboard-kpis/")


class Enfermeria(UsuarioClinica):
    weight = 2
    rol = "enfermera"

    @task(3)
    def triajes(self):
        self._lista("/api/triaje/triajes/")

    @task(2)
    def controles(self):
        self._lista("/api/controles/")


class Laboratorio(UsuarioClinica):
    weight = 1
    rol = "laboratorista"

    @task
    def examenes(self):
        self._lista("/api/laboratorios/examenes/")


class Administracion(UsuarioClinica):
    weight = 1
    rol = "administrador"

    @task(2)
    def auditoria(self):
        self._lista("/api/auditoria/")

    @task(1)
    def usuarios(self):
        self._lista("/api/usuarios/")


if ESCENARIO == "estres":
    class Escalones(LoadTestShape):
        """TC-113: +20 usuarios cada 60 s hasta 200 (10 escalones, 10 minutos)."""
        def tick(self):
            t = self.get_run_time()
            escalon = int(t // 60) + 1
            return (min(20 * escalon, 200), 10) if t < 600 else None

elif ESCENARIO == "pico":
    class Pico(LoadTestShape):
        """TC-114: 10 usuarios 2 min, 150 durante 1 min, 10 otros 2 min."""
        def tick(self):
            t = self.get_run_time()
            if t < 120:
                return 10, 5
            if t < 180:
                return 150, 50
            return (10, 50) if t < 300 else None

elif ESCENARIO == "resistencia":
    class Resistencia(LoadTestShape):
        """TC-115: 40 usuarios estables durante 15 minutos."""
        def tick(self):
            return (40, 4) if self.get_run_time() < 900 else None
