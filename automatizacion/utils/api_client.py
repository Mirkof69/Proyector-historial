"""Cliente de la API del sistema para las pruebas de API y para preparar o limpiar datos de las pruebas de UI.

Reproduce el flujo real de autenticación: cookie CSRF, login con correo y contraseña y, si el rol lo exige,
segundo paso con el código TOTP. La sesión queda en cookies httpOnly, como en el navegador.
"""
from __future__ import annotations

import time

import requests

from utils import config, totp


class ApiError(AssertionError):
    pass


class ApiCliente:
    def __init__(self, rol: config.Rol | None = None):
        self.rol = rol
        self.s = requests.Session()
        self.s.headers["Accept"] = "application/json"
        self.ultima_duracion_ms = 0.0

    # ------------------------------------------------------------------ sesión
    def csrf(self) -> str:
        if "csrftoken" not in self.s.cookies:
            self.s.get(f"{config.SUT_API}/token/csrf/", timeout=30)
        return self.s.cookies.get("csrftoken", "")

    def login(self, email: str | None = None, password: str | None = None, totp_secret: str | None = None):
        email = email or self.rol.email
        password = password if password is not None else config.PASSWORD
        r = self.post("/usuarios/login/", {"email": email, "password": password}, verificar=False)
        datos = _json(r)
        if r.status_code == 200 and datos.get("mfa_required"):
            secreto = totp_secret if totp_secret is not None else (self.rol.totp_secret if self.rol else "")
            r = self.post("/usuarios/mfa-verify/", {"temp_token": datos.get("temp_token"),
                                                     "totp_code": totp.codigo(secreto)}, verificar=False)
        return r

    def iniciar(self):
        r = self.login()
        if r.status_code != 200:
            raise ApiError(f"No se pudo iniciar sesión como {self.rol.clave}: HTTP {r.status_code} {r.text[:200]}")
        return self

    # ------------------------------------------------------------------ HTTP
    def _url(self, ruta: str) -> str:
        return ruta if ruta.startswith("http") else f"{config.SUT_API}{ruta}"

    def _peticion(self, metodo: str, ruta: str, verificar=True, **kw):
        if metodo in ("POST", "PUT", "PATCH", "DELETE"):
            kw.setdefault("headers", {})["X-CSRFToken"] = self.csrf()
            kw["headers"]["Referer"] = config.SUT_URL + "/"
        t0 = time.perf_counter()
        r = self.s.request(metodo, self._url(ruta), timeout=kw.pop("timeout", 60), **kw)
        self.ultima_duracion_ms = (time.perf_counter() - t0) * 1000
        if verificar and r.status_code >= 400:
            raise ApiError(f"{metodo} {ruta} -> HTTP {r.status_code}: {r.text[:300]}")
        return r

    def get(self, ruta, verificar=False, **kw):
        return self._peticion("GET", ruta, verificar, **kw)

    def post(self, ruta, datos=None, verificar=False, archivos=None, **kw):
        if archivos:
            return self._peticion("POST", ruta, verificar, data=datos or {}, files=archivos, **kw)
        return self._peticion("POST", ruta, verificar, json=datos or {}, **kw)

    def patch(self, ruta, datos=None, verificar=False, **kw):
        return self._peticion("PATCH", ruta, verificar, json=datos or {}, **kw)

    def put(self, ruta, datos=None, verificar=False, **kw):
        return self._peticion("PUT", ruta, verificar, json=datos or {}, **kw)

    def delete(self, ruta, verificar=False, **kw):
        return self._peticion("DELETE", ruta, verificar, **kw)

    def lista(self, ruta: str, **params) -> list:
        """Resultados de un listado paginado o simple."""
        d = _json(self.get(ruta, params=params))
        return d.get("results", d) if isinstance(d, dict) else d


def _json(r):
    try:
        return r.json()
    except ValueError:
        return {}
