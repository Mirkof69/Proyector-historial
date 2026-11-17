"""Pantalla genérica del panel: abrirla y medir su «salud» (errores de JavaScript, respuestas de la API, blanco).

Lo usan las pruebas de carga de pantallas (agenda, laboratorio, partos, reportes, guía de IA) y el barrido de
TC-102. La consola y el registro de red de Chrome se vacían antes de abrir la pantalla para medir solo lo suyo.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from pages.base_page import BasePage
from utils import config
from utils.driver_factory import consola, respuestas_http


@dataclass
class Salud:
    url_final: str
    errores_js: list[str] = field(default_factory=list)
    http_error: list[dict] = field(default_factory=list)
    caracteres: int = 0

    @property
    def http_5xx(self) -> list[dict]:
        return [h for h in self.http_error if h["estado"] >= 500]

    @property
    def denegada(self) -> bool:
        return "/403" in self.url_final or "/login" in self.url_final

    def problemas(self) -> list[str]:
        p = []
        if self.denegada:
            p.append(f"terminó en {self.url_final}")
        if self.caracteres < 20:
            p.append("pantalla en blanco")
        if self.http_5xx:
            p.append(f"API 5xx: {[h['url'].split('/api')[-1] for h in self.http_5xx][:3]}")
        if self.errores_js:
            p.append(f"errores de JavaScript: {self.errores_js[:2]}")
        return p


class PantallaPage(BasePage):
    CONTENIDO = (By.CSS_SELECTOR, ".ant-layout-content")
    # pestañas del primer nivel (las de un Tabs anidado dentro de una pestaña quedan fuera)
    NAV_PRINCIPAL = "(//div[contains(@class,'ant-tabs ')])[1]/div[contains(@class,'ant-tabs-nav')]"
    PESTANAS = (By.XPATH, NAV_PRINCIPAL + "//div[contains(@class,'ant-tabs-tab ') or @class='ant-tabs-tab']")

    def abrir_y_medir(self, ruta: str) -> Salud:
        consola(self.driver), respuestas_http(self.driver)   # vacía lo anterior
        self.abrir(ruta)
        self._esperar_contenido()
        return self.medir()

    def _esperar_contenido(self):
        try:
            WebDriverWait(self.driver, 20).until(
                lambda d: "Cargando" not in d.find_element(By.TAG_NAME, "body").text
                and not d.find_elements(By.CSS_SELECTOR, ".ant-skeleton-active"))
        except Exception:
            pass  # la medición siguiente reporta la pantalla en blanco si no terminó de cargar

    def medir(self) -> Salud:
        errores = [m["mensaje"] for m in consola(self.driver) if m["nivel"] == "SEVERE" and "favicon" not in m["mensaje"]]
        http = [h for h in respuestas_http(self.driver) if h["estado"] >= 400 and "/api/" in h["url"]]
        texto = self.driver.execute_script(
            "const c = document.querySelector('.ant-layout-content') || document.body; return c.innerText.trim().length;")
        return Salud(self.driver.current_url.replace(config.SUT_URL, ""), errores, http, texto or 0)

    def pestanas(self) -> list[str]:
        return [p.text.strip() for p in self.driver.find_elements(*self.PESTANAS) if p.text.strip()]

    def abrir_pestana(self, nombre: str):
        consola(self.driver), respuestas_http(self.driver)
        self.clic((By.XPATH, f"{self.NAV_PRINCIPAL}//div[contains(@class,'ant-tabs-tab')][normalize-space(.)='{nombre}']"))
        self.esperar_carga()
        self._esperar_contenido()
        return self.medir()
