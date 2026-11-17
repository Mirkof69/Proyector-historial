"""Pacientes por la API: consentimiento, duplicados, caracteres especiales, búsqueda y paginación."""
from __future__ import annotations

import pytest

from conftest import cliente
from data import fabrica

pytestmark = [pytest.mark.api, pytest.mark.pacientes]


@pytest.mark.smoke
@pytest.mark.tc("TC-022")
def test_tc022_sin_consentimiento_se_rechaza():
    """Registrar una paciente sin consentimiento de datos (Ley 164)."""
    r = cliente("recepcion").post("/pacientes/", fabrica.paciente(consentimiento_datos_aceptado=False))
    assert r.status_code == 400, f"Se registró sin consentimiento (HTTP {r.status_code})"
    assert "consentimiento_datos_aceptado" in r.json()


@pytest.mark.tc("TC-023")
def test_tc023_ci_duplicada_y_nacimiento_futuro(paciente_qa):
    """CI duplicada y fecha de nacimiento futura."""
    rec = cliente("recepcion")
    dup = rec.post("/pacientes/", fabrica.paciente(ci=paciente_qa["ci"]))
    assert dup.status_code == 400 and "ci" in dup.json(), f"Aceptó una CI duplicada (HTTP {dup.status_code})"
    fut = rec.post("/pacientes/", fabrica.paciente(fecha_nacimiento=fabrica.dia(1)))
    assert fut.status_code == 400 and "fecha_nacimiento" in fut.json(), f"Aceptó nacimiento futuro (HTTP {fut.status_code})"


@pytest.mark.tc("TC-025")
def test_tc025_tildes_ene_y_espacios():
    """Nombres con tildes, ñ y espacios al inicio o final."""
    rec = cliente("recepcion")
    r = rec.post("/pacientes/", fabrica.paciente(apellido_paterno="  Ñañez Ávila  ", apellido_materno="Güemes"))
    assert r.status_code == 201, r.text[:300]
    pid = fabrica.anotar("pacientes", r.json()["id"])
    leida = rec.get(f"/pacientes/{pid}/").json()
    assert leida["apellido_paterno"] == "Ñañez Ávila", f"Se guardó «{leida['apellido_paterno']}»"
    assert leida["apellido_materno"] == "Güemes"


@pytest.mark.tc("TC-027")
def test_tc027_ci_parcial_no_devuelve_otra_paciente(paciente_qa):
    """Una CI parcial no devuelve a otra paciente."""
    parcial = paciente_qa["ci"][:5]
    filas = cliente("recepcion").lista("/pacientes/", search=parcial)
    otras = [p for p in filas if p.get("ci") and p.get("ci") != paciente_qa["ci"]]
    assert not otras, f"La búsqueda por «{parcial}» devolvió otras pacientes: {[p.get('id') for p in otras]}"


@pytest.mark.tc("TC-026")
def test_tc026_busqueda_sin_tilde_api():
    """Buscar por apellido sin tilde (datos cifrados), por la API."""
    rec = cliente("recepcion")
    r = rec.post("/pacientes/", fabrica.paciente(apellido_paterno="Álvarez"))
    assert r.status_code == 201
    pid = fabrica.anotar("pacientes", r.json()["id"])
    filas = rec.lista("/pacientes/", search="alvarez", page_size=100)
    assert pid in [p["id"] for p in filas], "La búsqueda «alvarez» no encontró a la paciente «Álvarez»"


@pytest.mark.tc("TC-029")
def test_tc029_listado_paginado_en_servidor():
    """Listado paginado en el servidor."""
    r = cliente("recepcion").get("/pacientes/", params={"page": 1, "page_size": 20})
    d = r.json()
    assert r.status_code == 200
    assert len(d["results"]) == 20, f"Trajo {len(d['results'])} filas en vez de 20"
    assert d["count"] > 1000, f"El total ({d['count']}) no es el de la base"
