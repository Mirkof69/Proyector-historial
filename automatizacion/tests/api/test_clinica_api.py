"""Laboratorio, partos, calculadoras, reportes, auditoría y notificaciones por la API."""
from __future__ import annotations

import io

import pytest

from conftest import cliente
from data import fabrica
from utils import config

pytestmark = [pytest.mark.api]


# ---------------------------------------------------------------------- laboratorio
@pytest.fixture(scope="module")
def tipo_con_rango():
    med = cliente("medico")
    for t in med.lista("/laboratorios/tipos-examenes/", page_size=100):
        vals = med.get("/laboratorios/examenes/valores-referencia-por-tipo/", params={"tipo_examen_id": t["id"]}).json()
        vals = vals if isinstance(vals, list) else vals.get("valores_referencia", [])
        numericos = [v for v in vals if v.get("valor_minimo") not in (None, "") and v.get("valor_maximo") not in (None, "")]
        if numericos:
            return t, numericos[0]
    pytest.skip("BLOCKED: ningún tipo de examen con rango numérico")


def _examen(paciente_id, tipo_id, embarazo_id=None):
    r = cliente("medico").post("/laboratorios/examenes/", {"paciente": paciente_id, "tipo_examen": tipo_id,
                                                           **({"embarazo": embarazo_id} if embarazo_id else {})})
    assert r.status_code == 201, r.text[:300]
    return r.json()["id"]


@pytest.mark.laboratorio
@pytest.mark.tc("TC-054")
def test_tc054_catalogo_con_rangos():
    """Catálogo de parámetros con rangos."""
    med = cliente("medico")
    tipos = med.lista("/laboratorios/tipos-examenes/", page_size=100)
    assert len(tipos) >= 30, f"El catálogo tiene {len(tipos)} tipos"
    sin = []
    for t in tipos:
        v = med.get("/laboratorios/examenes/valores-referencia-por-tipo/", params={"tipo_examen_id": t["id"]}).json()
        v = v if isinstance(v, list) else v.get("valores_referencia", [])
        if not v:
            sin.append(t.get("nombre"))
    assert not sin, f"Tipos de examen sin rangos de referencia: {sin}"


@pytest.mark.laboratorio
@pytest.mark.tc("TC-052")
def test_tc052_resultado_se_guarda_y_completa(paciente_qa, embarazo_qa, tipo_con_rango):
    """Solicitar un examen y guardar su resultado."""
    tipo, vr = tipo_con_rango
    eid = _examen(paciente_qa["id"], tipo["id"], embarazo_qa["id"])
    url = f"/laboratorios/examenes/{eid}"
    med = cliente("medico")
    assert med.post(f"{url}/cambiar-estado/", {"estado": "completado"}).status_code == 400, "Completó sin resultados"
    medio = round((float(vr["valor_minimo"]) + float(vr["valor_maximo"])) / 2, 2)
    r = med.post(f"{url}/crear-resultado-multiple/", {"resultados": [{"valor_referencia": vr["id"], "valor_numerico": medio}],
                                                      "completar_examen": True})
    assert r.status_code == 201 and r.json().get("resultados_creados") == 1, r.text[:300]
    assert med.get(f"{url}/").json()["estado"] == "completado"


@pytest.mark.laboratorio
@pytest.mark.tc("TC-053")
@pytest.mark.parametrize("posicion", ["minimo", "maximo", "minimo-1", "maximo+1"])
def test_tc053_evaluacion_contra_el_rango(paciente_qa, tipo_con_rango, posicion):
    """Evaluar un resultado contra su rango de referencia (valores límite)."""
    tipo, vr = tipo_con_rango
    mn, mx = float(vr["valor_minimo"]), float(vr["valor_maximo"])
    paso = max(round((mx - mn) / 100, 3), 0.01)
    valor = {"minimo": mn, "maximo": mx, "minimo-1": round(mn - paso, 3), "maximo+1": round(mx + paso, 3)}[posicion]
    eid = _examen(paciente_qa["id"], tipo["id"])
    med = cliente("medico")
    r = med.post(f"/laboratorios/examenes/{eid}/crear-resultado-multiple/",
                 {"resultados": [{"valor_referencia": vr["id"], "valor_numerico": valor}]})
    assert r.status_code == 201, r.text[:300]
    res = med.lista("/laboratorios/resultados/", examen=eid)
    assert res, "No se guardó el resultado"
    normal = str(res[0].get("interpretacion") or res[0].get("estado") or "").lower()
    dentro = posicion in ("minimo", "maximo")
    if dentro:
        assert "normal" in normal and "anormal" not in normal, f"{valor} (dentro de {mn}-{mx}) evaluado como «{normal}»"
    else:
        assert normal and ("normal" not in normal or "anormal" in normal or "alto" in normal or "bajo" in normal), \
            f"{valor} (fuera de {mn}-{mx}) evaluado como «{normal}»"


@pytest.mark.laboratorio
@pytest.mark.tc("TC-118")
def test_tc118_editar_resultado_no_duplica_interpretacion(paciente_qa, tipo_con_rango):
    """Editar un resultado de laboratorio."""
    tipo, vr = tipo_con_rango
    eid = _examen(paciente_qa["id"], tipo["id"])
    med = cliente("medico")
    mn, mx = float(vr["valor_minimo"]), float(vr["valor_maximo"])
    med.post(f"/laboratorios/examenes/{eid}/crear-resultado-multiple/",
             {"resultados": [{"valor_referencia": vr["id"], "valor_numerico": mn}]}, verificar=True)
    res = med.lista("/laboratorios/resultados/", examen=eid)[0]
    r = med.patch(f"/laboratorios/resultados/{res['id']}/", {"valor_numerico": round((mn + mx) / 2, 2)})
    assert r.status_code == 200, r.text[:300]
    texto = str(r.json().get("interpretacion") or "")
    assert texto.count(texto[:20]) <= 1 if texto else True, f"Interpretación duplicada: {texto[:200]}"
    assert len(med.lista("/laboratorios/resultados/", examen=eid)) == 1, "La edición creó otro resultado"


# ---------------------------------------------------------------------- partos
@pytest.fixture(scope="module")
def embarazo_a_termino():
    p = cliente("recepcion").post("/pacientes/", fabrica.paciente(), verificar=True).json()
    fabrica.anotar("pacientes", p["id"])
    e = cliente("medico").post("/embarazos/", fabrica.embarazo(p["id"], dias_fum=273), verificar=True).json()
    return p, e


@pytest.mark.historia_clinica
@pytest.mark.tc("TC-085")
@pytest.mark.parametrize("cambio", [{"edad_gestacional_parto": "50"}], ids=["parto-50-semanas"])
def test_tc085_parto_imposible(embarazo_a_termino, cambio):
    """Parto a las 50 semanas (valor límite)."""
    p, e = embarazo_a_termino
    parto = {"paciente": p["id"], "embarazo": e["id"], "edad_gestacional_parto": "39", "tipo_parto": "vaginal_espontaneo",
             "parto_finalizado": True, "fecha_parto": fabrica.ahora_iso(), **cambio}
    assert cliente("medico").post("/partos/", parto).status_code == 400


@pytest.mark.historia_clinica
@pytest.mark.tc("TC-084")
def test_tc084_parto_recien_nacido_epicrisis_y_firma(embarazo_a_termino):
    """Parto con recién nacido y epicrisis: el embarazo queda finalizado."""
    p, e = embarazo_a_termino
    med = cliente("medico")
    r = med.post("/partos/", {"paciente": p["id"], "embarazo": e["id"], "edad_gestacional_parto": "39",
                              "tipo_parto": "vaginal_espontaneo", "parto_finalizado": True, "fecha_parto": fabrica.ahora_iso()})
    assert r.status_code == 201, r.text[:300]
    parto = r.json()["id"]
    rn = {"parto": parto, "fecha_nacimiento": fabrica.ahora_iso(), "sexo": "femenino", "peso_nacimiento": 3250,
          "talla_nacimiento": "49.5", "apgar_1_minuto": 8, "apgar_5_minutos": 9}
    assert med.post("/partos/recien-nacidos/", {**rn, "peso_nacimiento": 50}).status_code == 400, "Aceptó un RN de 50 g"
    assert med.post("/partos/recien-nacidos/", {**rn, "apgar_5_minutos": 11}).status_code == 400, "Aceptó Apgar 11"
    assert med.post("/partos/recien-nacidos/", rn).status_code == 201
    ep = med.post("/partos/epicrisis/", {"parto": parto, "fecha_egreso": fabrica.ahora_iso(),
                                         "diagnostico_ingreso": "Embarazo de 39 semanas en trabajo de parto",
                                         "diagnostico_egreso": "Puerperio inmediato sin complicaciones",
                                         "resumen_clinico": f"{config.PREFIJO_DATOS} parto eutócico"})
    assert ep.status_code == 201, ep.text[:300]
    assert med.get(f"/embarazos/{e['id']}/").json()["estado"] == "finalizado"
    _EPICRISIS["id"] = ep.json()["id"]


_EPICRISIS: dict = {}   # la epicrisis QA que crea TC-084 y firma TC-087


@pytest.mark.historia_clinica
@pytest.mark.tc("TC-087")
def test_tc087_epicrisis_firmada_no_se_edita():
    """Una epicrisis firmada ya no se puede editar."""
    if "id" not in _EPICRISIS:
        pytest.skip("BLOCKED: depende de TC-084 (no hay epicrisis QA para firmar)")
    epicrisis_id = _EPICRISIS["id"]
    med = cliente("medico")
    f = med.post(f"/partos/epicrisis/{epicrisis_id}/firmar/", {"matricula_profesional": "QA-MAT-001"})
    assert f.status_code in (200, 201), f"No se pudo firmar: {f.status_code} {f.text[:200]}"
    e = med.patch(f"/partos/epicrisis/{epicrisis_id}/", {"resumen_clinico": "Cambio tras la firma"})
    assert e.status_code in (400, 403, 409), f"Se editó una epicrisis firmada (HTTP {e.status_code})"


# ---------------------------------------------------------------------- calculadoras
@pytest.mark.calculadoras
@pytest.mark.tc("TC-091")
@pytest.mark.parametrize("glucosa,esperado", [(91, ""), (92, "diabetes gestacional"), (100, "diabetes gestacional"),
                                              (125, "diabetes gestacional"), (126, "diabetes")],
                         ids=["91", "92", "100", "125", "126"])
def test_tc091_glucosa_en_ayunas_iadpsg(paciente_qa, embarazo_qa, glucosa, esperado):
    """Glucosa en ayunas en el embarazo con criterios IADPSG (valores límite)."""
    med = cliente("medico")
    yo = med.get("/usuarios/me/").json()["id"]
    r = med.post("/calculadoras/bioquimicas/", {"paciente": paciente_qa["id"], "embarazo": embarazo_qa["id"],
                                                "medico_solicitante": yo, "fecha_toma": fabrica.dia(0),
                                                "glucosa_ayunas": glucosa})
    assert r.status_code == 201, r.text[:300]
    alertas = " ".join(r.json().get("alertas") or []).lower() if isinstance(r.json().get("alertas"), list) \
        else str(r.json().get("alertas") or "").lower()
    if not esperado:
        assert "diabetes" not in alertas, f"Glucosa {glucosa}: alertó «{alertas}»"
    else:
        assert esperado in alertas, f"Glucosa {glucosa} mg/dL en el embarazo: se esperaba «{esperado}» y alertó «{alertas}»"


# ---------------------------------------------------------------------- reportes y auditoría
@pytest.mark.reportes
@pytest.mark.tc("TC-095")
def test_tc095_kpis_del_panel():
    """Centro de reportes y KPIs."""
    r = cliente("administrador").get("/reportes/dashboard-kpis/")
    assert r.status_code == 200 and r.json() is not None


@pytest.mark.reportes
@pytest.mark.tc("TC-096")
def test_tc096_natalidad_del_periodo():
    """Natalidad del período."""
    r = cliente("administrador").get("/reportes/natalidad/")
    assert r.status_code == 200, r.text[:300]


@pytest.mark.reportes
@pytest.mark.tc("TC-097")
def test_tc097_exportar_pacientes_a_excel_y_auditar():
    """Exportar el listado de pacientes a Excel y quedar auditado."""
    import openpyxl
    admin = cliente("administrador")
    r = admin.get("/pacientes/exportar-excel/", params={"search": "QA"}, timeout=180)
    assert r.status_code == 200, r.text[:200]
    libro = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True)
    assert libro.worksheets, "El archivo exportado no es un Excel válido"
    aud = admin.lista("/auditoria/", accion="EXPORTAR", page_size=5)
    assert aud, "La exportación no quedó auditada"


@pytest.mark.reportes
@pytest.mark.tc("TC-098")
def test_tc098_inicio_de_sesion_auditado():
    """El inicio de sesión queda auditado."""
    aud = cliente("administrador").lista("/auditoria/", accion="LOGIN", page_size=5)
    assert aud, "No hay inicios de sesión en la auditoría"


@pytest.mark.tc("TC-101")
def test_tc101_listado_de_notificaciones():
    """Listado de notificaciones del usuario."""
    assert cliente("medico").get("/notificaciones/").status_code == 200
