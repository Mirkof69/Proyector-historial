"""Autenticación y sesión por la API: token temporal del MFA, bloqueo por intentos y endpoints sin sesión."""
from __future__ import annotations

import pytest

from conftest import cliente
from utils import config
from utils.api_client import ApiCliente, _json

pytestmark = [pytest.mark.api, pytest.mark.auth]

PROTEGIDOS = ["/pacientes/", "/embarazos/", "/controles/", "/ecografias/", "/partos/", "/laboratorios/examenes/",
              "/citas/citas/", "/usuarios/", "/auditoria/", "/reportes/dashboard-kpis/"]


@pytest.mark.smoke
@pytest.mark.tc("TC-013")
@pytest.mark.parametrize("ruta", PROTEGIDOS)
def test_tc013_endpoint_protegido_sin_sesion(api_anonima, ruta):
    """Endpoints protegidos sin sesión."""
    r = api_anonima.get(ruta)
    assert r.status_code == 401, f"{ruta} respondió {r.status_code} sin sesión"


@pytest.mark.tc("TC-011")
def test_tc011_token_temporal_no_es_sesion():
    """El token temporal del MFA no sirve como sesión."""
    c = ApiCliente()
    r = c.post("/usuarios/login/", {"email": config.ROLES["administrador"].email, "password": config.PASSWORD})
    datos = _json(r)
    assert r.status_code == 200 and datos.get("mfa_required"), f"No pidió MFA: {r.status_code} {datos}"
    temporal = datos["temp_token"]
    sin_cookies = ApiCliente()
    r2 = sin_cookies.get("/usuarios/me/", headers={"Authorization": f"Bearer {temporal}"})
    assert r2.status_code == 401, f"El token temporal abrió sesión (HTTP {r2.status_code})"


@pytest.mark.tc("TC-119")
def test_tc119_setup_con_mfa_activo_no_cambia_la_clave():
    """Pedir un QR nuevo con el doble factor ya activo no cambia la clave (regresión de BUG-004).

    Se prueba con una cuenta temporal QA que activa su propio doble factor: si el defecto volviera, la clave que
    cambiaría sería la de esa cuenta y no la del celular de un usuario real.
    """
    from data import fabrica
    from utils import totp
    admin = cliente("administrador")
    email = f"qa.mfa.{fabrica.ci_sintetica()}@fetalmedical.test"
    clave = "QaTemporal-2026!"
    alta = admin.post("/usuarios/", {"email": email, "nombre": f"{config.PREFIJO_DATOS} Doble factor",
                                     "apellido_paterno": "Prueba", "rol": "recepcion",
                                     "password": clave, "password_confirm": clave})
    assert alta.status_code in (200, 201), f"No se pudo crear la cuenta temporal: {alta.status_code} {alta.text[:300]}"
    uid = _json(alta).get("id")
    try:
        temporal = ApiCliente()
        assert temporal.login(email, clave).status_code == 200
        secreto = _json(temporal.post("/usuarios/mfa/setup/", {})).get("secret")
        assert secreto, "La cuenta sin doble factor no recibió su QR"
        assert temporal.post("/usuarios/mfa/confirm/", {"code": totp.codigo(secreto)}).status_code == 200

        r = temporal.post("/usuarios/mfa/setup/", {})
        assert r.status_code == 409, f"Con el MFA activo generó un QR nuevo (HTTP {r.status_code}): la clave cambió"
        assert "secret" not in _json(r), "La respuesta trae un secreto nuevo"
        otra = ApiCliente().login(email, clave, totp_secret=secreto)
        assert otra.status_code == 200, f"El código del celular dejó de servir (HTTP {otra.status_code})"
    finally:
        if uid:
            admin.post(f"/usuarios/{uid}/desactivar/", {})


@pytest.mark.tc("TC-012")
def test_tc012_bloqueo_tras_cinco_fallos():
    """Bloqueo de la cuenta tras 5 contraseñas erróneas (con una cuenta temporal QA)."""
    from data import fabrica
    admin = cliente("administrador")
    email = f"qa.bloqueo.{fabrica.ci_sintetica()}@fetalmedical.test"
    alta = admin.post("/usuarios/", {"email": email, "nombre": f"{config.PREFIJO_DATOS} Bloqueo", "apellido_paterno": "Prueba",
                                     "rol": "recepcion", "password": "QaTemporal-2026!", "password_confirm": "QaTemporal-2026!"})
    assert alta.status_code in (200, 201), f"No se pudo crear la cuenta temporal: {alta.status_code} {alta.text[:300]}"
    uid = _json(alta).get("id")
    try:
        c = ApiCliente()
        for _ in range(4):
            assert c.post("/usuarios/login/", {"email": email, "password": "mala-clave"}).status_code in (400, 401)
        # límite: con 4 fallos la cuenta aún entra con la clave correcta
        assert c.post("/usuarios/login/", {"email": email, "password": "QaTemporal-2026!"}).status_code == 200
        c2 = ApiCliente()
        for _ in range(5):
            c2.post("/usuarios/login/", {"email": email, "password": "mala-clave"})
        r = c2.post("/usuarios/login/", {"email": email, "password": "QaTemporal-2026!"})
        assert r.status_code in (403, 423, 429), f"Tras 5 fallos la cuenta no quedó bloqueada (HTTP {r.status_code})"
        assert "bloque" in r.text.lower(), f"El mensaje no informa el bloqueo: {r.text[:200]}"
    finally:
        if uid:
            admin.post(f"/usuarios/{uid}/desactivar/", {})
