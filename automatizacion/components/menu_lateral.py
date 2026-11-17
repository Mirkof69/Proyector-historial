"""Componente reutilizable: menú lateral y menú del usuario del panel (MainLayout del sistema)."""
from __future__ import annotations

from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class MenuLateral(BasePage):
    MENU = (By.CSS_SELECTOR, "aside .ant-menu, .ant-layout-sider .ant-menu")
    USUARIO = (By.CSS_SELECTOR, ".user-dropdown-trigger")
    CERRAR_SESION = (By.XPATH, "//li[contains(@class,'ant-dropdown-menu-item')][.//*[contains(normalize-space(.),'Cerrar Sesión')]]")

    def rutas_visibles(self) -> set[str]:
        """Rutas de los ítems del menú (Ant Design guarda la clave del ítem al final de data-menu-id)."""
        self.visible(self.MENU, 20)
        ids = self.driver.execute_script(
            "return [...document.querySelectorAll('.ant-menu [data-menu-id]')].map(e => e.getAttribute('data-menu-id'));")
        rutas = set()
        for i in ids or []:
            pos = i.find("/dashboard/")
            if pos >= 0:
                rutas.add(i[pos:])
        return rutas

    def cerrar_sesion(self):
        self.clic(self.USUARIO)
        self.clic(self.CERRAR_SESION)
        self.url_contiene("/login", 20)
        return self
