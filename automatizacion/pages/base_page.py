"""Página base del patrón Page Object Model (POM).

Reúne las esperas explícitas que se usan en todas las pantallas (WebDriverWait + expected_conditions, nunca
time.sleep), el manejo de alertas, el cambio de pestañas, el scroll y la lectura de tablas de Ant Design.
Prioridad de selectores: data-testid > id > name > CSS > XPath relativo.
"""
from __future__ import annotations

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils import config, evidencias


class BasePage:
    RUTA = "/"
    SPINNER = (By.CSS_SELECTOR, ".ant-spin-spinning")
    MENSAJE_EXITO = (By.CSS_SELECTOR, ".ant-message-success, .ant-notification-notice-success")
    MENSAJE_ERROR = (By.CSS_SELECTOR, ".ant-message-error, .ant-notification-notice-error, .ant-alert-error")
    ERROR_CAMPO = (By.CSS_SELECTOR, ".ant-form-item-explain-error")

    def __init__(self, driver, espera: int | None = None):
        self.driver = driver
        self.espera = WebDriverWait(driver, espera or config.TIEMPO_ESPERA)

    # ------------------------------------------------------------------ navegación
    def abrir(self, ruta: str | None = None):
        self.driver.get(config.SUT_URL + (ruta or self.RUTA))
        self.esperar_carga()
        return self

    def esperar_carga(self):
        """Espera a que el documento termine de cargar y a que desaparezcan los indicadores de carga."""
        self.espera.until(lambda d: d.execute_script("return document.readyState") == "complete")
        try:
            WebDriverWait(self.driver, 20).until(EC.invisibility_of_element_located(self.SPINNER))
        except TimeoutException:
            pass  # algunas pantallas dejan un spinner pequeño de fondo: no bloquea la prueba
        return self

    def url_contiene(self, texto: str, espera: int | None = None) -> bool:
        WebDriverWait(self.driver, espera or config.TIEMPO_ESPERA).until(EC.url_contains(texto))
        return True

    # ------------------------------------------------------------------ esperas explícitas
    def visible(self, loc, espera: int | None = None):
        return WebDriverWait(self.driver, espera or config.TIEMPO_ESPERA,
                             ignored_exceptions=(NoSuchElementException, StaleElementReferenceException)
                             ).until(EC.visibility_of_element_located(loc))

    def presente(self, loc, espera: int | None = None):
        """El elemento está en el DOM aunque no se vea (casillas de Ant Design: el <input> real tiene opacidad 0)."""
        return WebDriverWait(self.driver, espera or config.TIEMPO_ESPERA).until(EC.presence_of_element_located(loc))

    def todos_visibles(self, loc, espera: int | None = None):
        return WebDriverWait(self.driver, espera or config.TIEMPO_ESPERA).until(
            EC.visibility_of_all_elements_located(loc))

    def clicable(self, loc, espera: int | None = None):
        # React puede redibujar el elemento mientras la espera lo evalúa: ese «stale» se reintenta, no es un fallo
        return WebDriverWait(self.driver, espera or config.TIEMPO_ESPERA,
                             ignored_exceptions=(NoSuchElementException, StaleElementReferenceException)
                             ).until(EC.element_to_be_clickable(loc))

    def texto_presente(self, loc, texto: str, espera: int | None = None) -> bool:
        return WebDriverWait(self.driver, espera or config.TIEMPO_ESPERA).until(
            EC.text_to_be_present_in_element(loc, texto))

    def existe(self, loc) -> bool:
        try:
            self.driver.find_element(*loc)
            return True
        except NoSuchElementException:
            return False

    # ------------------------------------------------------------------ acciones
    def clic(self, loc, espera: int | None = None):
        """Clic con espera explícita. Si React redibuja el botón entre la espera y el clic (stale), lo vuelve a
        buscar; si un elemento flotante (tooltip) lo tapa, hace el clic por JavaScript."""
        for intento in range(3):
            try:
                # tras un «stale» el botón pudo desaparecer porque el clic ya navegó: se busca con espera corta
                el = self.clicable(loc, espera if intento == 0 else 3)
            except TimeoutException:
                if intento == 0:
                    raise
                return None   # el botón ya no está: la acción anterior cambió la pantalla (la prueba lo verifica)
            try:
                self.desplazar_a(el)
                try:
                    el.click()
                except StaleElementReferenceException:
                    raise
                except Exception:
                    self.driver.execute_script("arguments[0].click();", el)
                return el
            except StaleElementReferenceException:
                if intento == 2:
                    raise
        return None

    def esperar_que(self, condicion, espera: int = 20, mensaje: str = ""):
        """Espera explícita sobre cualquier condición (por ejemplo, que el registro ya esté en la API)."""
        return WebDriverWait(self.driver, espera, poll_frequency=1).until(lambda _d: condicion(), mensaje)

    def escribir(self, loc, texto: str, limpiar: bool = True):
        el = self.visible(loc)
        if limpiar:
            el.send_keys(Keys.CONTROL, "a")
            el.send_keys(Keys.DELETE)
        el.send_keys(texto)
        return el

    def desplazar_a(self, elemento):
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
        return elemento

    def desplazar_al_final(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def boton_por_texto(self, texto: str):
        """Localizador XPath relativo con contains(): botón cuyo texto incluye `texto`."""
        return (By.XPATH, f"//button[.//span[contains(normalize-space(.), '{texto}')] or contains(normalize-space(.), '{texto}')]")

    def elegir_opcion_select(self, campo_id: str, texto: str):
        """Select de Ant Design: abre el desplegable del campo, escribe y elige la opción con ese texto."""
        sel = self.clicable((By.ID, campo_id))
        sel.send_keys(texto)
        opcion = (By.XPATH, f"//div[contains(@class,'ant-select-item-option') and not(contains(@class,'disabled'))]"
                            f"[.//*[contains(normalize-space(.), '{texto}')] or contains(@title, '{texto}')]")
        self.clic(opcion)

    # ------------------------------------------------------------------ mensajes
    def mensaje_exito(self, espera: int = 15) -> str:
        return self.visible(self.MENSAJE_EXITO, espera).text

    def mensaje_error(self, espera: int = 15) -> str:
        return self.visible(self.MENSAJE_ERROR, espera).text

    def errores_de_campos(self) -> list[str]:
        return [e.text for e in self.driver.find_elements(*self.ERROR_CAMPO) if e.text]

    # ------------------------------------------------------------------ alertas y pestañas
    def aceptar_alerta(self, espera: int = 5) -> str:
        alerta = WebDriverWait(self.driver, espera).until(EC.alert_is_present())
        texto = alerta.text
        alerta.accept()
        return texto

    def confirmar_popconfirm(self):
        """Confirmación de Ant Design (Popconfirm o Modal.confirm): pulsa el botón primario del cuadro."""
        self.clic((By.CSS_SELECTOR, ".ant-popover:not(.ant-popover-hidden) .ant-btn-primary, "
                                     ".ant-modal-confirm .ant-btn-primary, .ant-modal-confirm-btns .ant-btn-dangerous"))

    def cambiar_a_pestana_nueva(self, cantidad_previa: int):
        WebDriverWait(self.driver, 15).until(EC.number_of_windows_to_be(cantidad_previa + 1))
        self.driver.switch_to.window(self.driver.window_handles[-1])

    # ------------------------------------------------------------------ tablas de Ant Design
    FILAS = (By.CSS_SELECTOR, ".ant-table-tbody tr.ant-table-row")

    def filas_tabla(self, espera: int | None = None):
        try:
            return self.todos_visibles(self.FILAS, espera or 15)
        except TimeoutException:
            return []

    def texto_tabla(self) -> str:
        """Texto de las filas; si React redibuja la tabla durante la lectura, se vuelve a leer."""
        def leer(d):
            try:
                return " ".join(f.text for f in d.find_elements(*self.FILAS)) or None
            except StaleElementReferenceException:
                return None
        try:
            return WebDriverWait(self.driver, 15).until(leer)
        except TimeoutException:
            return ""

    def tabla_contiene(self, *textos: str, espera: int = 20) -> bool:
        """Espera a que alguna fila contenga alguno de los textos (la búsqueda filtra en el servidor)."""
        def hay(d):
            try:
                texto = " ".join(f.text for f in d.find_elements(*self.FILAS))
            except StaleElementReferenceException:
                return False
            return any(x in texto for x in textos)
        try:
            return WebDriverWait(self.driver, espera).until(hay)
        except TimeoutException:
            return False

    def tabla_vacia(self) -> bool:
        return self.existe((By.CSS_SELECTOR, ".ant-table-placeholder .ant-empty"))

    # ------------------------------------------------------------------ evidencias
    def evidencia(self, paso: str, descripcion: str = ""):
        evidencias.captura(self.driver, paso, descripcion)
        return self
