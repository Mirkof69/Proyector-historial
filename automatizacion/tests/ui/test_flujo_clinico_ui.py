"""Flujo clínico por la interfaz: embarazo, control prenatal con alerta, triaje, ecografía, Bishop e IA.

Cada prueba crea su propia paciente sintética QA por la API (recepción) para no depender del orden; lo que se
prueba —el formulario— se hace por la pantalla con el rol que lo usa en la clínica. El resultado se comprueba
también en la API: que el sistema diga «guardado» no basta.
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest
from selenium.webdriver.common.by import By

from conftest import cliente
from data import fabrica
from pages.formularios_clinicos import (BishopPage, ControlFormPage, EcografiaFormPage, EmbarazoFormPage,
                                        IaMedicaPage, TriajeFormPage)

pytestmark = [pytest.mark.ui, pytest.mark.historia_clinica]

IMAGENES = Path(__file__).resolve().parents[2] / "data" / "imagenes_ia"


def _paciente_nueva() -> dict:
    r = cliente("recepcion").post("/pacientes/", fabrica.paciente(), verificar=True).json()
    fabrica.anotar("pacientes", r["id"])
    return r


def _con_embarazo(dias_fum: int = 203) -> tuple[dict, dict]:
    p = _paciente_nueva()
    e = cliente("medico").post("/embarazos/", fabrica.embarazo(p["id"], dias_fum=dias_fum), verificar=True).json()
    return p, e


@pytest.mark.smoke
@pytest.mark.tc("TC-036")
def test_tc036_registrar_embarazo_desde_la_pantalla(navegador):
    """Registrar un embarazo desde la pantalla: se guarda con su edad gestacional."""
    p = _paciente_nueva()
    d = navegador("medico")
    pag = EmbarazoFormPage(d).abrir()
    fum = date.today() - timedelta(days=150)
    pag.registrar(p["ci"], fum).evidencia("formulario", "Paciente QA elegida por su CI y FUM de hace 150 días")
    pag.guardar("Crear Embarazo")
    embarazos = pag.esperar_que(lambda: cliente("medico").lista("/embarazos/", paciente=p["id"]), 25,
                                "El embarazo no llegó a la base")
    pag.evidencia("guardado", "Embarazo registrado")
    assert len(embarazos) == 1, f"Se esperaba 1 embarazo de la paciente QA, hay {len(embarazos)}"
    e = embarazos[0]
    assert e["fecha_ultima_menstruacion"] == fum.isoformat(), f"FUM guardada {e['fecha_ultima_menstruacion']}"
    semanas = e.get("semanas_gestacion") or e.get("edad_gestacional_semanas") or (e.get("edad_gestacional") or {})
    assert semanas, f"El embarazo no muestra edad gestacional: {e}"


@pytest.mark.tc("TC-040")
def test_tc040_registrar_control_desde_la_pantalla(navegador):
    """Registrar un control prenatal: queda con la paciente y el embarazo elegidos."""
    p, e = _con_embarazo()
    d = navegador("medico")
    pag = ControlFormPage(d).abrir(f"{ControlFormPage.RUTA}?paciente={p['id']}&embarazo={e['id']}")
    pag.texto_presente((By.CSS_SELECTOR, ".ant-layout-content"), p["id_clinico"], 20)  # embarazo preelegido
    c = {"numero_control": 1, "edad_gestacional_semanas": 29, "peso_actual": 64, "temperatura": 36.6,
         "presion_arterial_sistolica": 112, "presion_arterial_diastolica": 72, "frecuencia_cardiaca": 80,
         "altura_uterina": 28, "frecuencia_cardiaca_fetal": 142}
    pag.completar(c, date.today()).evidencia("formulario", "Control con signos normales")
    pag.guardar("Guardar Control")
    controles = pag.esperar_que(lambda: cliente("medico").lista("/controles/", embarazo=e["id"]), 25,
                                "El control no llegó a la base")
    pag.evidencia("guardado", "Control registrado")
    assert len(controles) == 1, f"Se esperaba 1 control del embarazo QA, hay {len(controles)}"
    assert controles[0]["embarazo"] == e["id"]


@pytest.mark.tc("TC-045")
def test_tc045_control_con_presion_alta_muestra_alerta(navegador):
    """Un control con PA 150/95 muestra la alerta de hipertensión al abrirlo."""
    p, e = _con_embarazo()
    d = navegador("medico")
    pag = ControlFormPage(d).abrir(f"{ControlFormPage.RUTA}?paciente={p['id']}&embarazo={e['id']}")
    pag.texto_presente((By.CSS_SELECTOR, ".ant-layout-content"), p["id_clinico"], 20)  # embarazo preelegido
    c = {"numero_control": 1, "edad_gestacional_semanas": 29, "peso_actual": 64, "temperatura": 36.6,
         "presion_arterial_sistolica": 150, "presion_arterial_diastolica": 95, "frecuencia_cardiaca": 88,
         "altura_uterina": 28, "frecuencia_cardiaca_fetal": 142}
    pag.completar(c, date.today()).guardar("Guardar Control")
    control = pag.esperar_que(lambda: cliente("medico").lista("/controles/", embarazo=e["id"]), 25,
                              "El control no llegó a la base")[0]
    pag.abrir(f"/dashboard/controles/{control['id']}")
    pag.texto_presente((By.CSS_SELECTOR, ".ant-layout-content"), "ipertensi", 25)
    pag.evidencia("alerta", "Detalle del control con PA 150/95: alerta de hipertensión visible")


@pytest.mark.tc("TC-051")
def test_tc051_triaje_desde_la_pantalla(navegador):
    """Enfermería registra un triaje con el asistente de tres pasos y aparece en la lista."""
    p = _paciente_nueva()
    d = navegador("enfermera")
    pag = TriajeFormPage(d).abrir()
    pag.paso_paciente(p["ci"]).evidencia("paso-1", "Paciente QA elegida")
    pag.continuar()
    t = fabrica.triaje(p["id"], saturacion_oxigeno=98, dolor_escala=0)
    pag.paso_signos(t).evidencia("paso-2", "Signos vitales normales")
    pag.continuar()
    pag.paso_motivo(t["motivo_visita"]).evidencia("paso-3", "Motivo de la visita")
    pag.guardar("Registrar triaje")
    triajes = pag.esperar_que(lambda: cliente("enfermera").lista("/triaje/triajes/", paciente=p["id"]), 25,
                              "El triaje no llegó a la base")
    pag.evidencia("guardado", "Triaje registrado")
    assert len(triajes) == 1, f"Se esperaba 1 triaje de la paciente QA, hay {len(triajes)}"
    assert triajes[0]["saturacion_oxigeno"] in (98, "98", 98.0)


@pytest.mark.tc("TC-067")
def test_tc067_registrar_ecografia_desde_la_pantalla(navegador):
    """Registrar una ecografía con biometría: se guarda con su peso fetal estimado."""
    p, e = _con_embarazo()
    d = navegador("medico")
    pag = EcografiaFormPage(d).abrir(f"{EcografiaFormPage.RUTA}?paciente={p['id']}&embarazo={e['id']}")
    pag.texto_presente((By.CSS_SELECTOR, ".ant-layout-content"), p["id_clinico"], 20)  # embarazo preelegido
    pag.datos_generales(date.today(), 29)
    pag.biometria(dbp=74, cc=270, ca=250, lf=55).evidencia("biometria", "Biometría de 29 semanas")
    pag.conclusiones("QA Embarazo de 29 semanas con biometría acorde a la edad gestacional")
    pag.guardar("Guardar Ecografía")
    ecos = pag.esperar_que(lambda: cliente("medico").lista("/ecografias/", embarazo=e["id"]), 30,
                           "La ecografía no llegó a la base")
    pag.evidencia("guardado", "Ecografía registrada")
    assert len(ecos) == 1, f"Se esperaba 1 ecografía del embarazo QA, hay {len(ecos)}"
    eco = cliente("medico").get(f"/ecografias/{ecos[0]['id']}/").json()
    peso = (eco.get("biometria") or {}).get("peso_fetal_estimado") or eco.get("peso_fetal_estimado")
    assert peso and float(peso) > 0, f"La ecografía no tiene peso fetal estimado: {eco.get('biometria')}"


@pytest.mark.tc("TC-094")
def test_tc094_bishop_desde_la_pantalla(navegador):
    """Score de Bishop: con los cinco parámetros muestra el puntaje."""
    d = navegador("medico")
    pag = BishopPage(d).abrir()
    pag.calcular({"dilatacion": None, "borramiento": None, "estacion": None, "consistencia": None, "posicion": None})
    pag.texto_presente((By.CSS_SELECTOR, ".ant-layout-content"), "Recomendación Clínica", 20)
    pag.evidencia("puntaje", "Score de Bishop calculado")


@pytest.mark.ecografia_ia
@pytest.mark.tc("TC-069")
def test_tc069_analizar_ecografia_con_ia(navegador):
    """Análisis CNN: subir una ecografía del conjunto de prueba y ver el resultado con la imagen marcada."""
    imagen = sorted((IMAGENES / "planos").glob("*.png"))[0] if (IMAGENES / "planos").exists() else \
        sorted(p for p in IMAGENES.glob("*.*") if p.suffix.lower() in (".png", ".jpg", ".jpeg"))[0]
    d = navegador("medico")
    pag = IaMedicaPage(d).abrir()
    pag.subir(str(imagen)).evidencia("subida", f"Imagen de prueba {imagen.name}")
    pag.analizar()
    pag.texto_presente((By.CSS_SELECTOR, ".ant-layout-content"), "%", 60)
    pag.evidencia("resultado", "Resultado de la red con su confianza")
