"""Pacientes por la interfaz: registro con el asistente, validaciones, búsqueda, doble envío e historia clínica."""
from __future__ import annotations

import pytest
from selenium.webdriver.common.by import By

from conftest import cliente
from data import fabrica
from pages.pacientes_page import PacientesPage

pytestmark = [pytest.mark.ui, pytest.mark.pacientes]


def _id_por_ci(ci: str):
    filas = cliente("recepcion").lista("/pacientes/", search=ci)
    return [p["id"] for p in filas if p.get("ci") == ci]


@pytest.mark.smoke
@pytest.mark.tc("TC-021")
def test_tc021_registrar_paciente_con_consentimiento(navegador):
    """Registrar una paciente con consentimiento."""
    d = navegador("recepcion")
    pag = PacientesPage(d).abrir()
    p = fabrica.paciente()
    pag.abrir_asistente().completar_paso_personal(p).evidencia("paso-1", "Paso 1 del asistente con datos sintéticos QA")
    pag.siguiente().completar_contacto(p).siguiente().marcar_consentimiento().evidencia("paso-3", "Consentimiento marcado")
    pag.registrar()
    pag.mensaje_exito(20)
    pag.evidencia("registrada", "Mensaje de paciente registrada")
    pag.descartar_pregunta_embarazo()
    ids = _id_por_ci(p["ci"])
    for i in ids:
        fabrica.anotar("pacientes", i)
    assert len(ids) == 1, f"Se esperaba 1 paciente con la CI {p['ci']}, hay {len(ids)}"


@pytest.mark.tc("TC-024")
def test_tc024_campos_obligatorios_vacios(navegador):
    """Campos obligatorios vacíos en el asistente de registro."""
    d = navegador("recepcion")
    pag = PacientesPage(d).abrir().abrir_asistente()
    pag.siguiente()
    pag.visible(pag.ERROR_CAMPO)
    errores = pag.errores_de_campos()
    pag.evidencia("obligatorios", "El asistente no avanza sin los datos obligatorios")
    assert len(errores) >= 3, f"Se esperaban mensajes en nombre, apellido y CI: {errores}"
    assert pag.existe(pag.SIGUIENTE), "El asistente avanzó sin los datos obligatorios"
    d.find_element(By.CSS_SELECTOR, ".ant-modal-close").click()


@pytest.mark.tc("TC-024")
def test_tc024_ci_con_letras(navegador):
    """CI con letras: el asistente la rechaza (patrón de 5 a 10 dígitos)."""
    d = navegador("recepcion")
    pag = PacientesPage(d).abrir().abrir_asistente()
    p = fabrica.paciente(ci="12AB45")
    pag.completar_paso_personal(p).siguiente()
    pag.texto_presente(pag.ERROR_CAMPO, "dígitos")
    pag.evidencia("ci-invalida", "La CI con letras se rechaza")
    d.find_element(By.CSS_SELECTOR, ".ant-modal-close").click()


@pytest.mark.tc("TC-031")
def test_tc031_doble_clic_no_duplica(navegador):
    """Doble clic en Guardar no duplica la paciente."""
    d = navegador("recepcion")
    pag = PacientesPage(d).abrir()
    p = fabrica.paciente()
    pag.registrar_paciente(p, doble_clic=True)
    pag.mensaje_exito(20)
    pag.descartar_pregunta_embarazo()
    ids = _id_por_ci(p["ci"])
    for i in ids:
        fabrica.anotar("pacientes", i)
    pag.evidencia("doble-clic", "Tras el doble clic")
    assert len(ids) == 1, f"El doble clic creó {len(ids)} pacientes"


@pytest.mark.tc("TC-026")
def test_tc026_busqueda_sin_tilde(navegador):
    """Buscar por apellido sin tilde (datos cifrados)."""
    p = fabrica.paciente(apellido_paterno="Ñúñez")
    pid = fabrica.anotar("pacientes", cliente("recepcion").post("/pacientes/", p, verificar=True).json()["id"])
    d = navegador("recepcion")
    pag = PacientesPage(d).abrir().buscar("nunez")
    pag.evidencia("busqueda", "Búsqueda «nunez» sin tilde ni ñ")
    assert p["ci"] in pag.texto_tabla() or "Ñúñez" in pag.texto_tabla(), \
        f"La búsqueda sin tilde no encontró a la paciente {pid}"


@pytest.mark.tc("TC-028")
def test_tc028_editar_telefono(navegador):
    """Editar el teléfono de una paciente."""
    p = fabrica.paciente()
    pid = fabrica.anotar("pacientes", cliente("recepcion").post("/pacientes/", p, verificar=True).json()["id"])
    d = navegador("recepcion")
    pag = PacientesPage(d).abrir(f"/dashboard/pacientes/{pid}/editar")
    nuevo = "71234567"
    pag.escribir((By.ID, "telefono"), nuevo)
    pag.evidencia("editando", "Teléfono modificado en el formulario")
    pag.clic(pag.boton_por_texto("Guardar"))
    pag.mensaje_exito(20)
    assert cliente("recepcion").get(f"/pacientes/{pid}/").json()["telefono"] == nuevo


@pytest.mark.tc("TC-032")
def test_tc032_historia_clinica(navegador, paciente_qa, embarazo_qa):
    """Abrir la historia clínica de una paciente."""
    d = navegador("medico")
    pag = PacientesPage(d).abrir(f"/dashboard/pacientes/{paciente_qa['id']}/historia")
    # la cabecera de la historia muestra el nombre y la CI de la paciente
    pag.texto_presente((By.CSS_SELECTOR, ".ant-layout-content"), paciente_qa["ci"], 25)
    pag.evidencia("historia", "Historia clínica de la paciente QA")
