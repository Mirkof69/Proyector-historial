"""Módulo Pacientes: listado con búsqueda y asistente de registro de tres pasos (PacienteWizardModal)."""
from __future__ import annotations

from datetime import date

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from pages.base_page import BasePage


class PacientesPage(BasePage):
    RUTA = "/dashboard/pacientes"
    BUSCAR = (By.CSS_SELECTOR, "input[placeholder='Buscar por nombre, CI o ID...']")
    NUEVA = (By.XPATH, "//button[.//span[normalize-space(.)='Nueva Paciente'] or normalize-space(.)='Nueva Paciente']")
    MODAL = (By.CSS_SELECTOR, ".ant-modal-content")
    SIGUIENTE = (By.XPATH, "//div[contains(@class,'ant-modal')]//button[.//span[normalize-space(.)='Siguiente']]")
    REGISTRAR = (By.XPATH, "//div[contains(@class,'ant-modal')]//button[.//span[contains(.,'Registrar Paciente')]]")
    CONSENTIMIENTO = (By.ID, "consentimiento_datos_aceptado")
    PREGUNTA_EMBARAZO = (By.XPATH, "//div[contains(@class,'ant-modal-confirm')]//button[not(contains(@class,'ant-btn-primary'))]")

    def buscar(self, texto: str):
        caja = self.escribir(self.BUSCAR, texto)
        caja.send_keys(Keys.ENTER)
        self.esperar_carga()
        return self

    def abrir_asistente(self):
        self.clic(self.NUEVA)
        self.visible(self.MODAL)
        return self

    def completar_paso_personal(self, p: dict):
        self.escribir((By.ID, "nombre"), p["nombre"])
        self.escribir((By.ID, "apellido_paterno"), p["apellido_paterno"])
        self.escribir((By.ID, "apellido_materno"), p.get("apellido_materno", ""))
        self.escribir((By.ID, "ci"), p["ci"])
        nac = date.fromisoformat(p["fecha_nacimiento"])
        fecha = self.escribir((By.ID, "fecha_nacimiento"), nac.strftime("%d%m%Y"))
        fecha.send_keys(Keys.ENTER)
        return self

    def siguiente(self):
        self.clic(self.SIGUIENTE)
        return self

    def completar_contacto(self, p: dict):
        self.escribir((By.ID, "telefono"), p.get("telefono", ""))
        return self

    def marcar_consentimiento(self):
        casilla = self.presente(self.CONSENTIMIENTO)   # <input> de Ant Design con opacidad 0
        if not casilla.is_selected():
            self.driver.execute_script("arguments[0].click();", casilla)
        return self

    def registrar(self, doble_clic: bool = False):
        boton = self.clicable(self.REGISTRAR)
        if doble_clic:
            from selenium.webdriver.common.action_chains import ActionChains
            ActionChains(self.driver).double_click(boton).perform()
        else:
            boton.click()
        return self

    def descartar_pregunta_embarazo(self):
        """Tras el alta el sistema pregunta si se registra el embarazo: la prueba de pacientes responde «no»."""
        try:
            self.clic(self.PREGUNTA_EMBARAZO, 10)
        except Exception:
            pass
        return self

    def registrar_paciente(self, p: dict, consentimiento: bool = True, doble_clic: bool = False):
        self.abrir_asistente().completar_paso_personal(p).siguiente().completar_contacto(p).siguiente()
        if consentimiento:
            self.marcar_consentimiento()
        self.registrar(doble_clic)
        return self
