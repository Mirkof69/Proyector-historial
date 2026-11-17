"""Retesting por la interfaz de defectos corregidos: BUG-005 (detalle de nota) y BUG-008 (triaje sin saturación)."""
from __future__ import annotations

import pytest
from selenium.webdriver.common.by import By

from conftest import cliente
from data import fabrica
from pages.pantalla_page import PantallaPage

pytestmark = [pytest.mark.ui, pytest.mark.historia_clinica]


@pytest.mark.tc("TC-120")
def test_tc120_detalle_de_nota_de_evolucion(navegador):
    """El detalle de una nota de evolución abre sin error (antes: «Objects are not valid as a React child»)."""
    notas = cliente("medico").lista("/notas-evolucion/", page_size=1)
    if not notas:
        pytest.skip("BLOCKED: no hay notas de evolución registradas")
    d = navegador("medico")
    pag = PantallaPage(d)
    salud = pag.abrir_y_medir(f"/dashboard/notas-evolucion/{notas[0]['id']}")
    pag.evidencia("detalle", f"Detalle de la nota {notas[0]['id']}")
    assert not salud.problemas(), f"El detalle de la nota falla: {salud.problemas()}"
    texto = d.find_element(*pag.CONTENIDO).text
    assert "[object Object]" not in texto, "El detalle muestra un objeto sin formatear"
    assert len(texto) > 80, "El detalle de la nota está casi vacío"


@pytest.mark.tc("TC-121")
def test_tc121_triaje_sin_saturacion_dice_sin_dato(navegador):
    """Un triaje sin saturación de oxígeno muestra «Sin dato» y no «0 %»."""
    p = cliente("recepcion").post("/pacientes/", fabrica.paciente(), verificar=True).json()
    fabrica.anotar("pacientes", p["id"])
    r = cliente("enfermera").post("/triaje/triajes/", fabrica.triaje(p["id"]))   # la fábrica no envía saturación
    assert r.status_code == 201, f"No se pudo registrar el triaje QA: {r.status_code} {r.text[:200]}"
    tid = r.json()["id"]
    assert cliente("enfermera").get(f"/triaje/triajes/{tid}/").json().get("saturacion_oxigeno") is None
    d = navegador("enfermera")
    pag = PantallaPage(d)
    salud = pag.abrir_y_medir(f"/dashboard/triaje/{tid}")
    pag.texto_presente((By.CSS_SELECTOR, ".ant-layout-content"), "Sin dato", 20)
    pag.evidencia("sin-dato", "Detalle de un triaje sin saturación registrada")
    assert not salud.problemas(), f"El detalle del triaje falla: {salud.problemas()}"
    assert "0 %" not in d.find_element(*pag.CONTENIDO).text.replace("100 %", ""), "Sigue mostrando 0 % de saturación"
