"""Formularios clínicos: embarazo, control prenatal, triaje, ecografía, Score de Bishop e IA médica.

Los localizadores salen del DOM real (tools/sonda_dom.py): los campos de Ant Design usan como id el `name` del
Form.Item; los selectores de paciente y embarazo (SelectoresClinicos.tsx) no tienen id y se ubican por su
aria-label. Los selectores de fecha usan máscara DD/MM/YYYY: se escriben solo los dígitos y se confirma con ENTER.
"""
from __future__ import annotations

from datetime import date

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from pages.base_page import BasePage

DESPLEGABLE = ("//div[contains(@class,'ant-select-dropdown') and not(contains(@class,'ant-select-dropdown-hidden'))]"
               "//div[contains(@class,'ant-select-item-option') and not(contains(@class,'disabled'))]")


class FormularioClinico(BasePage):
    PACIENTE = (By.CSS_SELECTOR, "input[aria-label='Paciente']")
    EMBARAZO = (By.CSS_SELECTOR, "input[aria-label='Embarazo']")

    def _abrir_select(self, caja):
        """Abre un Select de Ant Design: el <input> está dentro del selector que recibe el clic."""
        self.desplazar_a(caja)
        selector = caja.find_element(By.XPATH, "./ancestor::div[contains(@class,'ant-select')][1]")
        try:
            selector.click()
        except Exception:
            self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));",
                                       selector)
        return caja

    def buscar_y_elegir(self, loc, texto: str, opcion: str | None = None, espera: int = 20):
        """Select con búsqueda en el servidor: escribe `texto` y elige la opción que contiene `opcion`."""
        caja = self._abrir_select(self.presente(loc))
        caja.send_keys(texto)
        self.clic((By.XPATH, f"{DESPLEGABLE}[contains(normalize-space(.), '{opcion or texto}')]"))
        return self

    def elegir(self, campo_id: str, opcion: str | None = None):
        """Select fijo: elige la opción con ese texto, o la primera si no se indica."""
        self._abrir_select(self.presente((By.ID, campo_id)))
        loc = f"{DESPLEGABLE}[contains(normalize-space(.), '{opcion}')]" if opcion else f"({DESPLEGABLE})[1]"
        self.clic((By.XPATH, loc))
        return self

    def fecha(self, campo_id: str, dia: date, confirmar=Keys.ENTER):
        """Fecha con máscara DD/MM/YYYY. `confirmar`: ENTER cierra el calendario; en un formulario cuyo único campo
        pendiente es la fecha, ENTER además lo ENVÍA (pasa en el de embarazo): ahí se confirma con TAB."""
        caja = self.visible((By.ID, campo_id))
        self.desplazar_a(caja)
        caja.click()
        caja.send_keys(Keys.CONTROL, "a")
        caja.send_keys(dia.strftime("%d%m%Y"))
        caja.send_keys(confirmar)
        return self

    def numero(self, campo_id: str, valor):
        self.escribir((By.ID, campo_id), str(valor))
        return self

    def texto(self, campo_id: str, valor: str):
        self.escribir((By.ID, campo_id), valor)
        return self

    def guardar(self, texto_boton: str):
        self.clic(self.boton_por_texto(texto_boton))
        return self


class EmbarazoFormPage(FormularioClinico):
    RUTA = "/dashboard/embarazos/nuevo"

    def registrar(self, ci: str, fum: date):
        """El número de gesta lo calcula el sistema con los antecedentes de la paciente (campo deshabilitado)."""
        self.buscar_y_elegir(self.PACIENTE, ci, f"CI {ci}")
        self.fecha("fecha_ultima_menstruacion", fum, Keys.TAB)
        # la FPP se calcula sola a partir de la FUM: el aviso «FPP Calculada» confirma que la fecha quedó tomada
        self.texto_presente((By.CSS_SELECTOR, ".ant-layout-content"), "FPP Calculada", 10)
        return self


class ControlFormPage(FormularioClinico):
    RUTA = "/dashboard/controles/nuevo"

    def completar(self, c: dict, fecha_control: date):
        self.numero("numero_control", c["numero_control"])
        self.fecha("fecha_control", fecha_control)
        self.numero("edad_gestacional_semanas", c["edad_gestacional_semanas"])
        self.numero("peso_actual", c["peso_actual"])
        self.numero("temperatura", c["temperatura"])
        self.numero("presion_arterial_sistolica", c["presion_arterial_sistolica"])
        self.numero("presion_arterial_diastolica", c["presion_arterial_diastolica"])
        self.numero("frecuencia_cardiaca", c["frecuencia_cardiaca"])
        self.numero("altura_uterina", c["altura_uterina"])
        self.numero("frecuencia_cardiaca_fetal", c["frecuencia_cardiaca_fetal"])
        self.elegir("presentacion_fetal", c.get("presentacion", "Cefálica"))   # obligatoria desde la semana 20
        return self


class TriajeFormPage(FormularioClinico):
    """Asistente de tres pasos: Paciente → Signos vitales → Motivo y evaluación."""
    RUTA = "/dashboard/triaje/nuevo"
    PACIENTE_TRIAJE = (By.CSS_SELECTOR, "input[aria-label='Paciente'], .ant-select input[type='search']")

    def continuar(self):
        self.clic(self.boton_por_texto("Continuar"))
        return self

    def paso_paciente(self, ci: str, prioridad: str | None = None):
        self.buscar_y_elegir(self.PACIENTE_TRIAJE, ci, ci)
        if prioridad:
            self.elegir("prioridad", prioridad)
        return self

    def paso_signos(self, t: dict):
        for campo in ("presion_sistolica", "presion_diastolica", "temperatura", "frecuencia_cardiaca",
                      "frecuencia_respiratoria", "saturacion_oxigeno", "dolor_escala", "peso_kg", "talla_cm"):
            self.numero(campo, t[campo])
        return self

    def paso_motivo(self, motivo: str):
        self.texto("motivo_visita", motivo)
        return self


class EcografiaFormPage(FormularioClinico):
    RUTA = "/dashboard/ecografias/nuevo"

    def pestana(self, nombre: str):
        self.clic((By.XPATH, f"//div[contains(@class,'ant-tabs-tab')][.//*[normalize-space(.)='{nombre}']]"))
        return self

    def datos_generales(self, fecha_eco: date, semanas: int, fcf: int = 142):
        self.fecha("fecha_ecografia", fecha_eco)
        self.elegir("tipo_ecografia")
        self.numero("edad_gestacional_semanas", semanas)
        self.numero("frecuencia_cardiaca_fetal", fcf)
        return self

    def biometria(self, dbp: float, cc: float, ca: float, lf: float):
        self.pestana("Biometría Fetal")
        self.numero("biometria_diametro_biparietal", dbp)
        self.numero("biometria_circunferencia_cefalica", cc)
        self.numero("biometria_circunferencia_abdominal", ca)
        self.numero("biometria_longitud_femur", lf)
        return self

    def conclusiones(self, diagnostico: str):
        self.pestana("Imágenes y Conclusiones")
        self.texto("diagnostico", diagnostico)
        return self

    def peso_estimado(self) -> str:
        return self.presente((By.ID, "biometria_peso_fetal_estimado")).get_attribute("value") or ""


class BishopPage(FormularioClinico):
    RUTA = "/dashboard/calculadoras/bishop"
    RESULTADO = (By.XPATH, "//*[contains(normalize-space(.),'Score') and contains(normalize-space(.),'/ 13') "
                           "or contains(@class,'ant-statistic-content-value')]")

    def calcular(self, opciones: dict[str, str | None]):
        for campo, opcion in opciones.items():
            self.elegir(campo, opcion)
        self.clic(self.boton_por_texto("Calcular Score"))
        return self


class IaMedicaPage(FormularioClinico):
    RUTA = "/dashboard/ia-medica/imagenes"
    ARCHIVO = (By.CSS_SELECTOR, "input[type='file']")

    def subir(self, ruta_imagen: str):
        self.presente(self.ARCHIVO).send_keys(ruta_imagen)
        return self

    def analizar(self):
        self.clic((By.XPATH, "//button[normalize-space(.)='Analizar' or .//span[normalize-space(.)='Analizar']]"))
        return self
