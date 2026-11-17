"""Pantalla de inicio de sesión (/login) y sus pasos de doble factor."""
from __future__ import annotations

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pages.base_page import BasePage
from utils import config, totp


class LoginPage(BasePage):
    RUTA = "/login"
    EMAIL = (By.ID, "email")
    PASSWORD = (By.ID, "password")
    INGRESAR = (By.CSS_SELECTOR, "form.login-form button[type='submit']")
    TOTP = (By.ID, "totp_code")
    VERIFICAR = (By.CSS_SELECTOR, ".login-otp-item button[type='submit']")
    SETUP_REQUERIDO = (By.XPATH, "//button[.//span[contains(., 'Configurar Google Authenticator')]]")
    ALERTA = (By.CSS_SELECTOR, ".ant-alert-error, .ant-message-error, .ant-form-item-explain-error")

    def ingresar_credenciales(self, email: str, password: str):
        self.escribir(self.EMAIL, email)
        self.escribir(self.PASSWORD, password)
        self.clic(self.INGRESAR)
        return self

    def esperar_resultado(self, espera: int = 20) -> str:
        """Devuelve qué mostró el sistema: 'panel', 'totp', 'setup' o 'error'."""
        def resultado(d):
            if "/dashboard" in d.current_url:
                return "panel"
            if d.find_elements(*self.TOTP):
                return "totp"
            if d.find_elements(*self.SETUP_REQUERIDO):
                return "setup"
            if any(e.is_displayed() and e.text for e in d.find_elements(*self.ALERTA)):
                return "error"
            return False
        return WebDriverWait(self.driver, espera).until(resultado)

    def ingresar_totp(self, codigo: str):
        self.escribir(self.TOTP, codigo)
        if self.existe(self.VERIFICAR):
            self.clic(self.VERIFICAR)
        return self

    def iniciar_sesion(self, rol: config.Rol, password: str | None = None):
        """Flujo completo hasta el panel: credenciales y, si el rol lo exige, el código TOTP."""
        self.abrir()
        self.ingresar_credenciales(rol.email, password if password is not None else config.PASSWORD)
        r = self.esperar_resultado()
        if r == "totp":
            self.ingresar_totp(totp.codigo(rol.totp_secret))
            self.url_contiene("/dashboard", 25)
            r = "panel"
        return r

    def mensaje_de_error(self) -> str:
        try:
            return self.visible(self.ALERTA, 10).text
        except TimeoutException:
            return ""


class SetupMfaPage(BasePage):
    """Configuración inicial del doble factor (/setup-mfa): QR, secreto y código de verificación."""
    RUTA = "/setup-mfa"
    SECRETO = (By.CSS_SELECTOR, ".setup-mfa__secreto code")
    CONTINUAR = (By.XPATH, "//button[.//span[contains(., 'Ya escaneé el QR')]]")
    CODIGO = (By.ID, "code")
    CONFIRMAR = (By.CSS_SELECTOR, "form button[type='submit']")

    def leer_secreto(self) -> str:
        return self.visible(self.SECRETO, 25).text.strip()

    def confirmar(self, secreto: str):
        self.clic(self.CONTINUAR)
        self.escribir(self.CODIGO, totp.codigo(secreto))
        self.clic(self.CONFIRMAR)
        WebDriverWait(self.driver, 25).until(EC.url_contains("/dashboard"))
        return self
