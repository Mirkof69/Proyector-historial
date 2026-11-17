"""Embarazo, control prenatal, triaje, notas y vacunas por la API (valores límite y transición de estados)."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from conftest import cliente
from data import fabrica
from utils import config

pytestmark = [pytest.mark.api, pytest.mark.historia_clinica]


def _nueva_paciente_con_embarazo(dias_fum=203):
    p = cliente("recepcion").post("/pacientes/", fabrica.paciente(), verificar=True).json()
    fabrica.anotar("pacientes", p["id"])
    e = cliente("medico").post("/embarazos/", fabrica.embarazo(p["id"], dias_fum=dias_fum), verificar=True).json()
    return p, e


@pytest.mark.smoke
@pytest.mark.tc("TC-033")
def test_tc033_embarazo_eg_y_fpp_naegele():
    """Registrar un embarazo y calcular EG y FPP (Naegele)."""
    p = cliente("recepcion").post("/pacientes/", fabrica.paciente(), verificar=True).json()
    fabrica.anotar("pacientes", p["id"])
    fum = date.today() - timedelta(days=280)
    r = cliente("medico").post("/embarazos/", {"paciente": p["id"], "numero_gesta": 1,
                                               "fecha_ultima_menstruacion": fum.isoformat()})
    assert r.status_code == 201, r.text[:300]
    e = r.json()
    assert str(e.get("fecha_probable_parto"))[:10] == (fum + timedelta(days=280)).isoformat(), \
        f"FPP {e.get('fecha_probable_parto')} distinta de FUM + 280 días"
    eg = e.get("edad_gestacional_semanas") or (e.get("edad_gestacional") or {}).get("semanas")
    assert int(float(eg)) == 40, f"EG {eg} en vez de 40 semanas"


@pytest.mark.tc("TC-034")
def test_tc034_fum_futura_rechazada(paciente_qa):
    """FUM futura rechazada."""
    r = cliente("medico").post("/embarazos/", fabrica.embarazo(paciente_qa["id"], dias_fum=-1))
    assert r.status_code == 400, f"Aceptó una FUM futura (HTTP {r.status_code})"


@pytest.mark.tc("TC-035")
def test_tc035_segundo_embarazo_activo(paciente_qa, embarazo_qa):
    """Segundo embarazo activo de la misma paciente."""
    r = cliente("medico").post("/embarazos/", fabrica.embarazo(paciente_qa["id"], numero_gesta=2))
    assert r.status_code == 400, f"Aceptó un segundo embarazo activo (HTTP {r.status_code})"


def _alertas(ctrl: dict) -> str:
    return str(ctrl.get("alertas") or ctrl.get("alertas_detectadas") or ctrl.get("tiene_alertas")).lower()


@pytest.mark.tc("TC-041")
@pytest.mark.parametrize("pas,pad,hay_alerta", [(139, 89, False), (140, 89, True), (139, 90, True), (160, 110, True)],
                         ids=["139-89", "140-89", "139-90", "160-110"])
def test_tc041_limites_presion_arterial(pas, pad, hay_alerta):
    """Valores límite de la presión arterial."""
    p, e = _nueva_paciente_con_embarazo()
    r = cliente("medico").post("/controles/", fabrica.control(p["id"], e["id"], presion_arterial_sistolica=pas,
                                                             presion_arterial_diastolica=pad))
    assert r.status_code == 201, r.text[:300]
    c = cliente("medico").get(f"/controles/{r.json()['id']}/").json()
    tiene = bool(c.get("tiene_alertas")) or "hipertens" in _alertas(c)
    assert tiene == hay_alerta, f"{pas}/{pad} mmHg: alerta={tiene}, se esperaba {hay_alerta}. Respuesta: {_alertas(c)[:200]}"


@pytest.mark.tc("TC-042")
@pytest.mark.parametrize("fcf,hay_alerta", [(109, True), (110, False), (160, False), (161, True)],
                         ids=["109", "110", "160", "161"])
def test_tc042_limites_fcf(fcf, hay_alerta):
    """Valores límite de la frecuencia cardiaca fetal."""
    p, e = _nueva_paciente_con_embarazo()
    r = cliente("medico").post("/controles/", fabrica.control(p["id"], e["id"], frecuencia_cardiaca_fetal=fcf))
    assert r.status_code == 201, r.text[:300]
    c = cliente("medico").get(f"/controles/{r.json()['id']}/").json()
    tiene = bool(c.get("tiene_alertas"))
    assert tiene == hay_alerta, f"FCF {fcf} lpm: alerta={tiene}, se esperaba {hay_alerta}"


@pytest.mark.tc("TC-043")
@pytest.mark.parametrize("cambio,campo", [({"fecha_control": fabrica.dia(3)}, "fecha_control"),
                                          ({"presion_arterial_sistolica": 70, "presion_arterial_diastolica": 110},
                                           "presion_arterial_sistolica"),
                                          ({"frecuencia_cardiaca_fetal": 320}, "frecuencia_cardiaca_fetal")],
                         ids=["fecha-futura", "presion-invertida", "fcf-320"])
def test_tc043_control_con_datos_imposibles(paciente_qa, embarazo_qa, cambio, campo):
    """Control con fecha futura, presión invertida o FCF imposible."""
    r = cliente("medico").post("/controles/", fabrica.control(paciente_qa["id"], embarazo_qa["id"], **cambio))
    assert r.status_code == 400, f"Aceptó {cambio} (HTTP {r.status_code})"
    assert campo in r.json(), f"El error no señala «{campo}»: {r.text[:200]}"


@pytest.mark.tc("TC-044")
def test_tc044_filtro_con_alertas():
    """Filtro «con alertas» del listado de controles."""
    # la pantalla usa ?alerta_critica=true, el mismo criterio de la columna «tiene_alertas» (CP-020)
    filas = cliente("medico").lista("/controles/", alerta_critica="true", page_size=50)
    assert filas, "El filtro no devolvió controles"
    sin = [c["id"] for c in filas if not c.get("tiene_alertas")]
    assert not sin, f"El filtro «con alertas» devolvió controles sin alertas: {sin[:10]}"
    sin_alerta = cliente("medico").lista("/controles/", alerta_critica="false", page_size=50)
    con = [c["id"] for c in sin_alerta if c.get("tiene_alertas")]
    assert not con, f"El filtro «sin alertas» devolvió controles con alertas: {con[:10]}"


@pytest.mark.tc("TC-049")
def test_tc049_triaje_con_prioridad(paciente_qa):
    """Registrar un triaje con prioridad."""
    r = cliente("enfermera").post("/triaje/triajes/", fabrica.triaje(paciente_qa["id"], prioridad="alto"))
    assert r.status_code == 201, r.text[:300]
    assert r.json()["prioridad"] == "alto"


@pytest.mark.tc("TC-050")
@pytest.mark.parametrize("cambio,campo", [({"presion_sistolica": 60, "presion_diastolica": 120}, "presion_sistolica"),
                                          ({"temperatura": "50.0"}, "temperatura"),
                                          ({"saturacion_oxigeno": 120}, "saturacion_oxigeno")],
                         ids=["presion-60-120", "temperatura-50", "saturacion-120"])
def test_tc050_triaje_signos_imposibles(paciente_qa, cambio, campo):
    """Signos vitales imposibles en el triaje."""
    r = cliente("enfermera").post("/triaje/triajes/", fabrica.triaje(paciente_qa["id"], **cambio))
    assert r.status_code == 400 and campo in r.json(), f"Aceptó {cambio} (HTTP {r.status_code}) {r.text[:200]}"


@pytest.mark.tc("TC-062")
def test_tc062_nota_de_evolucion(paciente_qa):
    """Registrar una nota de evolución."""
    med = cliente("medico")
    yo = med.get("/usuarios/me/").json()["id"]
    r = med.post("/notas-evolucion/", {"paciente": paciente_qa["id"], "medico": yo, "fecha_consulta": fabrica.ahora_iso(),
                                       "motivo_consulta": f"{config.PREFIJO_DATOS} control de rutina",
                                       "examen_fisico": "Sin hallazgos", "diagnosticos": "Embarazo normoevolutivo",
                                       "plan_tratamiento": "Control en 4 semanas"})
    assert r.status_code == 201, r.text[:300]


@pytest.mark.tc("TC-059")
def test_tc059_registrar_dosis_de_vacuna(paciente_qa):
    """Registrar una dosis de vacuna."""
    enf = cliente("enfermera")
    tipos = enf.lista("/vacunas/tipos-vacunas/")
    assert tipos, "No hay tipos de vacuna en el catálogo"
    r = enf.post("/vacunas/registros/", {"paciente": paciente_qa["id"], "tipo_vacuna": tipos[0]["id"],
                                         "fecha_aplicacion": fabrica.dia(0), "numero_dosis": 1, "lote": "QA-LOTE-01",
                                         "laboratorio": "QA Laboratorio", "via_administracion": "intramuscular",
                                         "sitio_aplicacion": "deltoides_izquierdo"})
    assert r.status_code == 201, r.text[:400]


@pytest.mark.tc("TC-060")
def test_tc060_listado_de_vacunas_cuenta_todas():
    """Listado y cifras con más de 200 vacunas."""
    d = cliente("enfermera").get("/vacunas/registros/", params={"page_size": 10}).json()
    assert d.get("count", 0) >= len(d.get("results", [])) and len(d.get("results", [])) <= 10
