"""Autenticación por la interfaz: login por rol, MFA, login fallido, cierre de sesión y rutas protegidas."""
from __future__ import annotations

import pytest
from selenium.webdriver.common.by import By

from components.menu_lateral import MenuLateral
from pages.login_page import LoginPage, SetupMfaPage
from utils import config, evidencias
from utils.driver_factory import consola

pytestmark = [pytest.mark.ui, pytest.mark.auth]


def _errores_js(driver):
    return [m for m in consola(driver) if m["nivel"] == "SEVERE" and "favicon" not in m["mensaje"]]


@pytest.mark.smoke
@pytest.mark.tc("TC-001")
@pytest.mark.parametrize("rol", ["enfermera", "laboratorista", "recepcion"])
def test_tc001_login_exitoso_por_rol(navegador_limpio, rol):
    """Inicio de sesión exitoso de los roles sin doble factor."""
    login = LoginPage(navegador_limpio).abrir()
    login.evidencia(f"login-{rol}", "Pantalla de inicio de sesión")
    login.ingresar_credenciales(config.ROLES[rol].email, config.PASSWORD)
    assert login.esperar_resultado() == "panel", "No abrió el panel del rol"
    login.esperar_carga()
    login.evidencia(f"panel-{rol}", f"Panel del rol {rol}")
    assert "/dashboard" in navegador_limpio.current_url
    assert not _errores_js(navegador_limpio), f"Errores de JavaScript: {_errores_js(navegador_limpio)}"


@pytest.mark.smoke
@pytest.mark.tc("TC-002")
def test_tc002_login_administrador_con_mfa(navegador_limpio):
    """Inicio de sesión del administrador con código de Google Authenticator."""
    rol = config.ROLES["administrador"]
    login = LoginPage(navegador_limpio).abrir()
    login.ingresar_credenciales(rol.email, config.PASSWORD)
    assert login.esperar_resultado() == "totp", "No pidió el código del segundo factor"
    login.evidencia("pide-codigo", "El sistema pide el código de 6 dígitos")
    from utils import totp
    login.ingresar_totp(totp.codigo(rol.totp_secret))
    assert login.url_contiene("/dashboard", 25)
    login.esperar_carga().evidencia("panel-admin", "Panel del administrador")


@pytest.mark.tc("TC-003")
def test_tc003_primer_ingreso_medico_configura_mfa(navegador_limpio):
    """Primer ingreso del médico: configuración de Google Authenticator."""
    if config.ROLES["medico"].totp_secret:
        pytest.skip("NOT RUN: el MFA del médico ya está configurado (el caso solo se ejecuta en el primer ingreso)")
    login = LoginPage(navegador_limpio).abrir()
    login.ingresar_credenciales(config.ROLES["medico"].email, config.PASSWORD)
    assert login.esperar_resultado() == "setup", "No ofreció configurar el doble factor"
    login.evidencia("setup-requerido", "El rol médico exige configurar el MFA")
    login.clic(login.SETUP_REQUERIDO)
    setup = SetupMfaPage(navegador_limpio)
    secreto = setup.leer_secreto()
    assert len(secreto) >= 16, "El secreto mostrado no es válido"
    # el secreto se guarda en .env ANTES de confirmar: si algo falla después, no se pierde
    config.guardar_en_env("QA_MEDICO_TOTP_SECRET", secreto)
    navegador_limpio.execute_script(
        "document.querySelectorAll('.setup-mfa__secreto code').forEach(e => e.textContent = '•••• (oculto en la evidencia)');")
    setup.evidencia("qr-y-secreto", "QR para Google Authenticator (secreto ocultado en la captura)")
    setup.confirmar(secreto)
    setup.esperar_carga().evidencia("panel-medico", "Panel del médico tras activar el MFA")
    assert "/dashboard" in navegador_limpio.current_url


@pytest.mark.tc("TC-004")
def test_tc004_contrasena_incorrecta(navegador_limpio):
    """Contraseña incorrecta."""
    login = LoginPage(navegador_limpio).abrir()
    login.ingresar_credenciales(config.ROLES["recepcion"].email, "ClaveIncorrecta-QA-1")
    assert login.esperar_resultado() == "error"
    mensaje = login.mensaje_de_error()
    login.evidencia("error-clave", "Mensaje por contraseña incorrecta")
    assert mensaje, "No mostró un mensaje de error"
    assert "/login" in navegador_limpio.current_url
    # un ingreso correcto reinicia el contador de intentos fallidos de la cuenta (se recarga el login para que
    # el aviso del intento anterior no se confunda con el resultado del nuevo)
    login.abrir()
    login.ingresar_credenciales(config.ROLES["recepcion"].email, config.PASSWORD)
    assert login.esperar_resultado() == "panel"


@pytest.mark.tc("TC-005")
def test_tc005_correo_no_registrado(navegador_limpio):
    """Correo no registrado."""
    login = LoginPage(navegador_limpio).abrir()
    login.ingresar_credenciales("qa.no.existe@fetalmedical.test", "Cualquiera-123")
    assert login.esperar_resultado() == "error"
    mensaje = login.mensaje_de_error().lower()
    login.evidencia("error-correo", "Mensaje por correo no registrado")
    assert "no existe" not in mensaje, "El mensaje revela que el correo no existe"


@pytest.mark.tc("TC-006")
def test_tc006_formulario_vacio_y_correo_invalido(navegador_limpio):
    """Envío del formulario de login vacío y con correo mal formado."""
    login = LoginPage(navegador_limpio).abrir()
    login.clic(login.INGRESAR)
    login.visible(login.ERROR_CAMPO)
    errores = login.errores_de_campos()
    login.evidencia("vacio", "Validación del formulario vacío")
    assert len(errores) >= 2, f"Se esperaban mensajes en correo y contraseña: {errores}"
    login.escribir(login.EMAIL, "usuario@")
    login.clic(login.INGRESAR)
    login.texto_presente(login.ERROR_CAMPO, "")
    assert "/login" in navegador_limpio.current_url
    login.evidencia("correo-invalido", "Validación del correo mal formado")


@pytest.mark.tc("TC-007")
def test_tc007_codigo_totp_incorrecto(navegador_limpio):
    """Código TOTP incorrecto."""
    rol = config.ROLES["administrador"]
    login = LoginPage(navegador_limpio).abrir()
    login.ingresar_credenciales(rol.email, config.PASSWORD)
    assert login.esperar_resultado() == "totp"
    from utils import totp
    malo = "000000" if totp.codigo(rol.totp_secret) != "000000" else "111111"
    login.ingresar_totp(malo)
    mensaje = login.mensaje_de_error()
    login.evidencia("totp-incorrecto", "Código de 6 dígitos rechazado")
    assert mensaje, "No informó el código incorrecto"
    assert "/dashboard" not in navegador_limpio.current_url
    # reinicia el contador de fallos de la cuenta con un ingreso correcto
    login.ingresar_totp(totp.codigo(rol.totp_secret))
    login.url_contiene("/dashboard", 25)


@pytest.mark.tc("TC-008")
def test_tc008_cerrar_sesion_y_volver_atras(navegador_limpio):
    """Cerrar sesión y volver atrás con el navegador."""
    login = LoginPage(navegador_limpio)
    assert login.iniciar_sesion(config.ROLES["recepcion"]) == "panel"
    login.abrir("/dashboard/pacientes")
    menu = MenuLateral(navegador_limpio)
    menu.cerrar_sesion()
    menu.evidencia("sesion-cerrada", "Vuelve al login al cerrar sesión")
    navegador_limpio.back()
    login.esperar_carga()
    login.url_contiene("/login", 20)
    login.evidencia("atras", "Con Atrás no se ve información clínica")
    assert not login.filas_tabla(3), "Se ven datos de pacientes tras cerrar la sesión"


@pytest.mark.tc("TC-009")
def test_tc009_ruta_protegida_sin_sesion(navegador_limpio):
    """Abrir una pantalla interna sin sesión."""
    login = LoginPage(navegador_limpio)
    login.abrir("/dashboard/pacientes")
    login.url_contiene("/login", 20)
    login.evidencia("redirige-login", "Sin sesión, la ruta interna redirige al login")


@pytest.mark.tc("TC-010")
def test_tc010_recargar_mantiene_sesion(navegador_limpio):
    """Recargar la página con la sesión iniciada."""
    login = LoginPage(navegador_limpio)
    assert login.iniciar_sesion(config.ROLES["enfermera"]) == "panel"
    login.abrir("/dashboard/pacientes")
    navegador_limpio.refresh()
    login.esperar_carga()
    assert "/dashboard/pacientes" in navegador_limpio.current_url, "La recarga perdió la sesión"
    login.visible((By.CSS_SELECTOR, ".ant-layout-sider, aside"), 20)
    login.evidencia("tras-recargar", "La sesión se mantiene tras recargar")
