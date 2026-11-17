"""Citas por la API: agendar en un turno libre y rechazo de un turno ya ocupado (recepción)."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from conftest import cliente
from data import fabrica
from utils.api_client import _json

pytestmark = [pytest.mark.api, pytest.mark.citas]


def _paciente() -> dict:
    r = cliente("recepcion").post("/pacientes/", fabrica.paciente(), verificar=True).json()
    fabrica.anotar("pacientes", r["id"])
    return r


@pytest.fixture(scope="module")
def turno_libre():
    """Primer turno libre del médico QA en los próximos 21 días hábiles (horarios-disponibles del sistema)."""
    medico_id = cliente("medico").get("/usuarios/me/").json()["id"]
    dia = date.today() + timedelta(days=1)
    for _ in range(21):
        if dia.weekday() < 5:
            r = cliente("recepcion").get("/citas/disponibilidades/horarios-disponibles/",
                                         params={"medico_id": medico_id, "fecha": dia.isoformat()})
            libres = [h["hora"] for h in _json(r).get("horarios", []) if h.get("disponible")]
            if libres:
                return {"medico": medico_id, "fecha": dia.isoformat(), "hora": libres[-1]}
        dia += timedelta(days=1)
    pytest.skip("BLOCKED: el médico QA no tiene turnos libres en los próximos 21 días")


@pytest.mark.smoke
@pytest.mark.tc("TC-046")
def test_tc046_agendar_en_turno_libre(turno_libre):
    """Recepción agenda una cita en un turno libre: HTTP 201 y la cita queda agendada."""
    p = _paciente()
    cita = {"paciente": p["id"], "medico": turno_libre["medico"], "fecha_cita": turno_libre["fecha"],
            "hora_cita": turno_libre["hora"], "tipo_cita": "control", "motivo": "QA control prenatal"}
    r = cliente("recepcion").post("/citas/citas/", cita)
    assert r.status_code == 201, f"No se agendó en el turno libre: HTTP {r.status_code} {r.text[:300]}"
    datos = r.json()
    fabrica.anotar("citas", datos["id"])
    guardada = cliente("recepcion").get(f"/citas/citas/{datos['id']}/").json()
    assert guardada["estado"] == "agendada", f"Estado de la cita nueva: {guardada['estado']}"
    assert str(guardada["hora_cita"]).startswith(str(turno_libre["hora"])[:5])
    turno_libre["cita_id"] = datos["id"]


@pytest.mark.tc("TC-047")
def test_tc047_turno_ocupado_se_rechaza(turno_libre):
    """Otra paciente en el mismo turno del mismo médico: HTTP 400 con el motivo."""
    if "cita_id" not in turno_libre:
        pytest.skip("BLOCKED: depende de TC-046 (no hay cita en el turno)")
    p = _paciente()
    cita = {"paciente": p["id"], "medico": turno_libre["medico"], "fecha_cita": turno_libre["fecha"],
            "hora_cita": turno_libre["hora"], "tipo_cita": "control", "motivo": "QA turno ocupado"}
    r = cliente("recepcion").post("/citas/citas/", cita)
    if r.status_code in (200, 201):
        fabrica.anotar("citas", r.json()["id"])
    assert r.status_code == 400, f"Se agendó una segunda cita en un turno ocupado (HTTP {r.status_code})"
    assert "horario" in r.text.lower() or "ocupad" in r.text.lower(), f"El rechazo no explica el motivo: {r.text[:200]}"
