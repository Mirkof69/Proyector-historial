"""Buscadores y filtros de cada listado con Selenium WebDriver, y uso explícito de los cuatro tipos de localizador.

- TC-154 a TC-170: en los 17 listados (data/modulos_busqueda.py), con el rol que usa cada uno, se busca una palabra
  del primer registro, se busca un texto inexistente y se aplica el filtro desplegable. Cada paso deja captura.
- TC-171: flujo completo con localizadores por ID, Name, XPath y CSS Selector, validaciones (assert) y capturas.
- TC-172: búsqueda avanzada de pacientes con ID, XPath y CSS Selector.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from data.modulos_busqueda import JS_TERMINO, JS_TERMINO_REAL, LISTADOS, SIN_RESULTADOS
from pages.base_page import BasePage
from pages.pantalla_page import PantallaPage
from utils import config, evidencias, totp
from utils.driver_factory import crear_driver

pytestmark = [pytest.mark.ui, pytest.mark.busqueda]

FILAS = (By.CSS_SELECTOR, ".ant-table-tbody tr.ant-table-row")
VACIO = (By.CSS_SELECTOR, ".ant-table-placeholder, .ant-empty")
OPCIONES = ("//div[contains(@class,'ant-select-dropdown') and not(contains(@class,'ant-select-dropdown-hidden'))]"
            "//div[contains(@class,'ant-select-item-option')]")
PRIMER_TC = 154


class ListadoPage(PantallaPage):
    """Listado con buscador y filtros de Ant Design."""

    def __init__(self, driver, listado):
        super().__init__(driver)
        self.l = listado
        self.BUSCADOR = (By.CSS_SELECTOR, f"input[placeholder='{listado.buscador}']")

    def abrir_listado(self):
        self.abrir(self.l.ruta)
        self.visible(self.BUSCADOR, 25)
        WebDriverWait(self.driver, 30).until(lambda d: d.find_elements(*FILAS))
        return self

    def termino(self) -> str:
        return self.driver.execute_script(JS_TERMINO % self.l.columna)

    def buscar(self, texto: str):
        caja = self.escribir(self.BUSCADOR, texto)
        caja.send_keys(Keys.ENTER)
        return self

    def elegir_filtro(self):
        select = (By.XPATH, f"//div[contains(@class,'ant-select')][.//span[contains(@class,'ant-select-selection-placeholder') "
                            f"or contains(@class,'ant-select-selection-item')][normalize-space(.)='{self.l.filtro}']]")
        self.clic(select)
        n = 2 if self.l.filtro.startswith("Tod") else 1
        opcion = self.visible((By.XPATH, f"({OPCIONES})[{n}]"), 15)
        texto = opcion.text
        self.clic((By.XPATH, f"({OPCIONES})[{n}]"))
        self.esperar_carga()
        return texto


@pytest.mark.parametrize("listado", LISTADOS, ids=[x.clave for x in LISTADOS])
def test_buscador_y_filtro_del_listado(request, navegador, listado):
    """Buscador y filtro de cada listado con el rol que lo usa."""
    tc = f"TC-{PRIMER_TC + LISTADOS.index(listado)}"
    request.node.add_marker(pytest.mark.tc(tc))
    evidencias.CASO_ACTUAL["tc"] = tc
    d = navegador(listado.rol)
    pag = ListadoPage(d, listado).abrir_listado()
    termino = pag.termino()
    assert termino, f"No se pudo tomar una palabra de la columna «{listado.columna}» del primer registro"
    pag.buscar(termino)
    encontrada = pag.tabla_contiene(termino, espera=25)
    pag.evidencia("busqueda", f"{listado.modulo}: búsqueda de «{termino}»")
    assert encontrada, f"El buscador de {listado.modulo} no muestra ningún registro con «{termino}»"   # validación 1
    if listado.vacio:
        pag.buscar(SIN_RESULTADOS)
        pag.visible(VACIO, 25)
        pag.evidencia("sin-resultados", f"{listado.modulo}: búsqueda sin coincidencias")
        assert not d.find_elements(*FILAS), f"{listado.modulo}: quedaron filas con un texto inexistente"   # validación 2
    if listado.filtro:
        pag.abrir_listado()
        opcion = pag.elegir_filtro()
        salud = pag.medir()
        pag.evidencia("filtro", f"{listado.modulo}: filtro «{listado.filtro}» = {opcion}")
        assert not salud.http_5xx, f"El filtro de {listado.modulo} produjo un error del servidor"   # validación 3
        assert d.find_elements(By.CSS_SELECTOR, ".ant-table-tbody"), "La tabla desapareció al filtrar"


@pytest.mark.smoke
@pytest.mark.ecografia_ia
@pytest.mark.tc("TC-171")
def test_tc171_cuatro_tipos_de_localizador():
    """Inicio de sesión y análisis de una ecografía usando localizadores por ID, Name, XPath y CSS Selector."""
    imagen = sorted((Path(__file__).resolve().parents[2] / "data" / "imagenes_ia").glob("*Plane*.png"))[0]
    rol = config.ROLES["medico"]
    d = crear_driver()
    espera = WebDriverWait(d, 30)
    try:
        d.get(config.SUT_URL + "/login")
        espera.until(EC.visibility_of_element_located((By.ID, "email"))).send_keys(rol.email)            # ID
        d.find_element(By.ID, "password").send_keys(config.PASSWORD)                                     # ID
        d.find_element(By.CSS_SELECTOR, "form.login-form button[type='submit']").click()                 # CSS Selector
        espera.until(EC.visibility_of_element_located((By.ID, "totp_code"))).send_keys(totp.codigo(rol.totp_secret))
        boton = d.find_elements(By.CSS_SELECTOR, ".login-otp-item button[type='submit']")
        if boton:
            boton[0].click()
        espera.until(EC.url_contains("/dashboard"))
        evidencias.captura(d, "panel", "Panel del médico tras el doble factor")
        assert "/dashboard" in d.current_url, "No llegó al panel"                                         # validación 1
        usuario = espera.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".user-dropdown-trigger")))
        assert "MEDICO" in usuario.text.upper(), f"El panel no muestra el rol del médico: {usuario.text}"  # validación 2

        d.get(config.SUT_URL + "/dashboard/ia-medica/imagenes")
        archivo = espera.until(EC.presence_of_element_located((By.NAME, "file")))                        # Name
        archivo.send_keys(str(imagen))
        evidencias.captura(d, "imagen", f"Ecografía de prueba cargada ({imagen.name})")
        analizar = espera.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[normalize-space(.)='Analizar' or .//span[normalize-space(.)='Analizar']]")))   # XPath
        d.execute_script("arguments[0].scrollIntoView({block: 'center'});", analizar)
        analizar.click()
        WebDriverWait(d, 90).until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".ant-layout-content"), "%"))
        evidencias.captura(d, "resultado", "Resultado del análisis con su confianza")
        contenido = d.find_element(By.CSS_SELECTOR, ".ant-layout-content").text                          # CSS Selector
        assert "%" in contenido, "El análisis no muestra la confianza de la red"                          # validación 3
        assert not d.find_elements(By.CSS_SELECTOR, ".ant-result-error"), "La pantalla de IA terminó en error"
    finally:
        d.quit()


@pytest.mark.pacientes
@pytest.mark.tc("TC-172")
def test_tc172_busqueda_avanzada_de_pacientes(navegador):
    """Búsqueda avanzada por nombre: el filtro conserva lo escrito y devuelve pacientes con ese nombre."""
    d = navegador("recepcion")
    buscar = (By.XPATH, "//button[.//span[normalize-space(.)='Buscar'] or normalize-space(.)='Buscar']")    # XPath
    pag = BasePage(d).abrir("/dashboard/pacientes/buscar")
    pag.clic(buscar)                                    # sin filtros: lista las pacientes activas
    WebDriverWait(d, 30).until(lambda x: x.find_elements(*FILAS))
    termino = d.execute_script(JS_TERMINO_REAL)
    assert termino, "La búsqueda avanzada sin filtros no devolvió ninguna paciente activa"
    pag.escribir((By.ID, "nombre"), termino)                                                             # ID
    pag.clic(buscar)
    encontrada = pag.tabla_contiene(termino, espera=25)
    pag.evidencia("avanzada", f"Búsqueda avanzada por «{termino}»")
    assert encontrada, f"La búsqueda avanzada no devolvió pacientes con «{termino}»"                      # validación 1
    assert d.find_element(By.ID, "nombre").get_attribute("value") == termino                              # validación 2
    assert len(d.find_elements(By.CSS_SELECTOR, ".ant-table-tbody tr.ant-table-row")) >= 1                # CSS Selector
