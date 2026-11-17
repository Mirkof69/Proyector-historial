"""Casos automatizados con Selenium IDE: una sola definición para la grabación .side y para el catálogo de casos.

Cada caso tiene sus datos de catálogo (módulo, título, requisito, pasos, resultado esperado) y sus comandos de
Selenium IDE. tools/generar_side.py escribe un proyecto .side por caso y un proyecto completo con una suite por
módulo; data/catalogo_tc.py agrega estos casos al catálogo.

Las credenciales nunca están en la grabación: se usan marcadores (__QA_EMAIL_<ROL>__, __QA_PASSWORD__,
__QA_TOTP_<ROL>__, __QA_CI__) que tools/ejecutar_side.py reemplaza en una copia temporal al reproducir.
Localizadores usados: id=, css=, xpath= y linkText=. Validaciones: assert, assertText, assertValue,
assertElementPresent, assertElementNotPresent y verifyElementPresent.
Los conteos se hacen con executeScript: el ejecutor 4.0.13 no tiene storeXpathCount.
"""
from __future__ import annotations

from data.modulos_busqueda import JS_TERMINO, JS_TERMINO_REAL, LISTADOS, SIN_RESULTADOS, Listado

MFA = {"administrador", "medico"}
ROL_VISIBLE = {"administrador": "ADMINISTRADOR", "medico": "MEDICO", "enfermera": "ENFERMERA",
               "laboratorista": "LABORATORISTA", "recepcion": "RECEPCION"}
NOMBRE_ROL = {"administrador": "administrador", "medico": "médico", "enfermera": "enfermería",
              "laboratorista": "laboratorio", "recepcion": "recepción"}
FILAS = "xpath=//tbody[contains(@class,'ant-table-tbody')]/tr[contains(@class,'ant-table-row')]"
OPCION = ("xpath=(//div[contains(@class,'ant-select-dropdown') and not(contains(@class,'ant-select-dropdown-hidden'))]"
          "//div[contains(@class,'ant-select-item-option')])[%d]")
USUARIO = "css=.user-dropdown-trigger"


def c(comando: str, objetivo: str = "", valor: str = "", comentario: str = "") -> dict:
    return {"command": comando, "target": objetivo, "value": valor, "comment": comentario}


def ingresar(rol: str) -> list[dict]:
    """Inicio de sesión del rol; con doble factor, escribe el código TOTP que inyecta el ejecutor."""
    R = rol.upper()
    L = [c("open", "/login", comentario="Pantalla de inicio de sesión"), c("setWindowSize", "1366x900"),
         c("waitForElementVisible", "id=email", "20000"),
         c("type", "id=email", f"__QA_EMAIL_{R}__"), c("type", "id=password", "__QA_PASSWORD__"),
         c("click", "css=form.login-form button[type='submit']")]
    if rol in MFA:
        L += [c("waitForElementVisible", "id=totp_code", "20000", "Segundo paso: código del autenticador"),
              c("type", "id=totp_code", f"__QA_TOTP_{R}__"),
              c("executeScript", "const b=document.querySelector(\".login-otp-item button[type='submit']\"); if(b){b.click();}")]
    return L + [c("waitForElementVisible", USUARIO, "30000", "Llegó al panel")]


def _buscador(l: Listado) -> str:
    return f"css=input[placeholder='{l.buscador}']"


def buscar_y_filtrar(l: Listado) -> list[dict]:
    """Buscador con un término tomado del propio listado, búsqueda sin resultados y filtro desplegable."""
    fila_con = f"xpath=//tr[contains(@class,'ant-table-row')][contains(.,'${{termino}}')]"
    L = ingresar(l.rol) + [
        c("open", l.ruta, comentario=f"Listado de {l.modulo}"),
        c("waitForElementVisible", _buscador(l), "25000"),
        c("waitForElementVisible", "css=.ant-table-tbody tr.ant-table-row", "30000", "El listado tiene registros"),
        c("assertElementPresent", f"xpath=(//thead//th[normalize-space(.)='{l.columna}'])[1]", comentario="Columna esperada"),
        c("executeScript", "return document.querySelectorAll('.ant-table-tbody tr.ant-table-row').length", "filas_antes"),
        c("executeScript", JS_TERMINO % l.columna, "termino", "Palabra del primer registro para buscarla"),
        c("executeScript", "return ${termino}.length > 0", "hay_termino"),
        c("assert", "hay_termino", "true"),
        c("echo", "Buscando: ${termino} (filas antes: ${filas_antes})"),
        c("type", _buscador(l), "${termino}"),
        c("sendKeys", _buscador(l), "${KEY_ENTER}"),
        c("waitForElementVisible", fila_con, "25000", "Aparece un registro con el término"),
        c("assertElementPresent", fila_con),
    ]
    if l.vacio:
        L += [c("type", _buscador(l), SIN_RESULTADOS, "Término que ningún registro contiene"),
              c("sendKeys", _buscador(l), "${KEY_ENTER}"),
              c("waitForElementVisible", "css=.ant-table-placeholder, .ant-empty", "25000", "El listado queda vacío"),
              c("assertElementNotPresent", "css=.ant-table-tbody tr.ant-table-row")]
    if l.filtro:
        select = (f"xpath=//div[contains(@class,'ant-select')][.//span[contains(@class,'ant-select-selection-placeholder') "
                  f"or contains(@class,'ant-select-selection-item')][normalize-space(.)='{l.filtro}']]")
        L += [c("open", l.ruta, comentario="Listado sin búsqueda, para aplicar el filtro"),
              c("waitForElementVisible", "css=.ant-table-tbody tr.ant-table-row", "30000"),
              c("click", select, comentario=f"Filtro «{l.filtro}»"),
              c("waitForElementVisible", OPCION % 1, "15000"),
              c("click", OPCION % (2 if l.filtro.startswith("Tod") else 1)),
              c("waitForElementPresent", "css=.ant-table-tbody", "20000"),
              c("verifyElementPresent", "css=.ant-table-tbody"),
              c("assertElementNotPresent", "css=.ant-result-error", comentario="El filtro no produce un error")]
    return L


def _caso(tc, archivo, modulo, funcionalidad, titulo, requisito, rol, pasos, esperado, comandos, prioridad="Media", tecnica="FL"):
    return {"id": tc, "archivo": archivo, "modulo": modulo, "funcionalidad": funcionalidad, "titulo": titulo,
            "requisito": requisito, "rol": rol, "pasos": pasos, "esperado": esperado, "comandos": comandos,
            "prioridad": prioridad, "tecnica": tecnica}


def _login_rol(tc, rol):
    doble = " con doble factor" if rol in MFA else ""
    return _caso(tc, f"login_{rol}", "Autenticación", "Inicio de sesión", f"Inicio de sesión de {NOMBRE_ROL[rol]}{doble} (Selenium IDE)",
                 "RF-21", rol, "1. Abrir /login. 2. Escribir correo y contraseña. 3. " + ("Escribir el código TOTP. 4. " if rol in MFA else "")
                 + "Comprobar el panel.", f"Se abre el panel y muestra el rol {ROL_VISIBLE[rol]}.",
                 ingresar(rol) + [
                     c("assertElementPresent", "css=.ant-layout-sider .ant-menu", comentario="Menú lateral del rol"),
                     c("assertElementPresent", f"xpath=//*[contains(@class,'user-dropdown-trigger')][contains(.,'{ROL_VISIBLE[rol]}')]"),
                     c("executeScript", "return window.location.pathname.startsWith('/dashboard')", "en_panel"),
                     c("assert", "en_panel", "true")], "Alta")


def _menu(tc, rol, presentes, ausentes):
    L = ingresar(rol)
    for r in presentes:
        L.append(c("assertElementPresent", f"css=.ant-menu [data-menu-id$='{r}']", comentario="Módulo permitido"))
    for r in ausentes:
        L.append(c("assertElementNotPresent", f"css=.ant-menu [data-menu-id$='{r}']", comentario="Módulo no permitido"))
    return _caso(tc, f"menu_{rol}", "Roles y permisos", "Menú por rol", f"El menú de {NOMBRE_ROL[rol]} muestra solo sus módulos (Selenium IDE)",
                 "RF-22", rol, "1. Iniciar sesión. 2. Revisar el menú lateral.",
                 f"Están {', '.join(x.rsplit('/', 1)[-1] for x in presentes)}; no están {', '.join(x.rsplit('/', 1)[-1] for x in ausentes)}.",
                 L, "Alta", "TD")


def _prohibida(tc, rol, ruta):
    return _caso(tc, f"url_prohibida_{rol}", "Roles y permisos", "Acceso por URL",
                 f"{NOMBRE_ROL[rol].capitalize()} escribe la URL de un módulo prohibido (Selenium IDE)", "RF-22", rol,
                 f"1. Iniciar sesión. 2. Abrir {ruta}.", "El sistema lleva a /403 y no muestra datos.",
                 ingresar(rol) + [
                     c("open", ruta, comentario="Módulo que el rol no puede abrir"),
                     c("waitForElementVisible", "css=.pagina-estado__titulo-403", "20000", "Pantalla de acceso restringido"),
                     c("assertText", "css=.pagina-estado__titulo-403", "Acceso Restringido (403)"),
                     c("executeScript", "return window.location.pathname", "ruta"),
                     c("assert", "ruta", "/403"),
                     c("assertElementNotPresent", "css=.ant-table-tbody tr.ant-table-row", comentario="Sin filas de datos")], "Alta", "TD")


BUSCADOR_PAC = "css=input[placeholder='Buscar por nombre, CI o ID...']"

CASOS_IDE: list[dict] = [
    # ---------------------------------------------------------------- autenticación
    _caso("TC-109", "login_exitoso", "Autenticación", "Inicio de sesión", "Inicio de sesión exitoso de recepción (Selenium IDE)", "RF-21",
          "recepcion", "1. Abrir /login. 2. Escribir correo y contraseña. 3. Enviar.", "Se abre el panel con el rol RECEPCION.",
          ingresar("recepcion") + [
              c("assertElementPresent", "css=.ant-layout-sider .ant-menu"),
              c("assertElementPresent", "xpath=//*[contains(@class,'user-dropdown-trigger')][contains(.,'RECEPCION')]"),
              c("assertTitle", "Fetal Medical Bolivia", comentario="Título de la aplicación")], "Alta"),
    _caso("TC-110", "login_fallido", "Autenticación", "Inicio de sesión", "Inicio de sesión fallido con una cuenta que no existe (Selenium IDE)",
          "RF-21", "anónimo", "1. Abrir /login. 2. Escribir un correo inexistente y una contraseña. 3. Enviar.",
          "Muestra el error y no abre el panel.", [
              c("open", "/login"), c("setWindowSize", "1366x900"), c("waitForElementVisible", "id=email", "20000"),
              c("type", "id=email", "qa.no.existe@fetalmedical.test"), c("type", "id=password", "Clave-Equivocada-QA1"),
              c("click", "css=form.login-form button[type='submit']"),
              c("waitForElementVisible", "css=.ant-alert-error, .ant-message-error", "20000", "Mensaje de error"),
              c("assertElementNotPresent", USUARIO), c("assertElementPresent", "id=password"),
              c("executeScript", "return window.location.pathname", "ruta"), c("assert", "ruta", "/login")], "Alta", "EP"),
    _login_rol("TC-122", "medico"), _login_rol("TC-123", "administrador"),
    _login_rol("TC-124", "enfermera"), _login_rol("TC-125", "laboratorista"),
    _caso("TC-126", "login_campos_vacios", "Autenticación", "Validación del formulario", "Formulario de inicio de sesión vacío (Selenium IDE)",
          "RF-21", "anónimo", "1. Abrir /login. 2. Pulsar Iniciar sesión sin datos.", "Muestra los mensajes de campo obligatorio.", [
              c("open", "/login"), c("setWindowSize", "1366x900"), c("waitForElementVisible", "id=email", "20000"),
              c("click", "css=form.login-form button[type='submit']"),
              c("waitForElementVisible", "css=.ant-form-item-explain-error", "15000"),
              c("executeScript", "return document.querySelectorAll('.ant-form-item-explain-error').length", "errores"),
              c("executeScript", "return ${errores} >= 2", "dos_errores"), c("assert", "dos_errores", "true"),
              c("assertElementNotPresent", USUARIO)], "Media", "EP"),
    _caso("TC-127", "cerrar_sesion", "Autenticación", "Cierre de sesión", "Cerrar sesión desde el menú del usuario (Selenium IDE)", "RF-21",
          "recepcion", "1. Iniciar sesión. 2. Abrir el menú del usuario. 3. Cerrar sesión.", "Vuelve a /login y el panel ya no está.",
          ingresar("recepcion") + [
              c("click", USUARIO),
              c("waitForElementVisible", "xpath=//li[contains(@class,'ant-dropdown-menu-item')][contains(.,'Cerrar Sesión')]", "10000"),
              c("click", "xpath=//li[contains(@class,'ant-dropdown-menu-item')][contains(.,'Cerrar Sesión')]"),
              c("waitForElementVisible", "id=email", "20000"), c("assertElementNotPresent", USUARIO),
              c("executeScript", "return window.location.pathname", "ruta"), c("assert", "ruta", "/login")], "Alta"),
    # ---------------------------------------------------------------- roles
    _menu("TC-128", "recepcion", ["/dashboard/pacientes", "/dashboard/citas"], ["/dashboard/controles", "/dashboard/partos", "/dashboard/ecografias"]),
    _menu("TC-129", "enfermera", ["/dashboard/triaje", "/dashboard/pacientes"], ["/dashboard/partos", "/dashboard/reportes"]),
    _prohibida("TC-130", "recepcion", "/dashboard/controles"),
    _prohibida("TC-131", "laboratorista", "/dashboard/notas-evolucion"),
]

# ---------------------------------------------------------------- buscadores y filtros de cada módulo
_n = 132
for _l in LISTADOS:
    _tc = "TC-111" if _l.clave == "pacientes" else f"TC-{_n}"
    if _l.clave != "pacientes":
        _n += 1
    CASOS_IDE.append(_caso(
        _tc, f"buscar_{_l.clave}", _l.modulo, "Búsqueda y filtros",
        f"Buscador{' y filtro' if _l.filtro else ''} del listado de {_l.modulo.lower()} (Selenium IDE)", _l.requisito, _l.rol,
        "1. Iniciar sesión. 2. Abrir el listado. 3. Buscar una palabra del primer registro."
        + (" 4. Buscar un texto inexistente." if _l.vacio else "")
        + (f" 5. Aplicar el filtro «{_l.filtro}»." if _l.filtro else ""),
        "La búsqueda muestra el registro" + ("; el texto inexistente deja el listado vacío" if _l.vacio else "")
        + ("; el filtro se aplica sin error." if _l.filtro else "."), buscar_y_filtrar(_l), "Alta", "EP"))

CASOS_IDE += [
    _caso(f"TC-{_n}", "busqueda_avanzada_pacientes", "Pacientes", "Búsqueda avanzada", "Búsqueda avanzada de pacientes por nombre (Selenium IDE)",
          "RF-02", "recepcion", "1. Abrir Búsqueda avanzada y buscar sin filtros. 2. Tomar el nombre del primer resultado. 3. Escribirlo y pulsar Buscar.",
          "Aparece al menos un resultado con ese nombre.",
          ingresar("recepcion") + [
              c("open", "/dashboard/pacientes/buscar"), c("waitForElementVisible", "id=nombre", "20000"),
              c("click", "xpath=//button[.//span[normalize-space(.)='Buscar'] or normalize-space(.)='Buscar']"),
              c("waitForElementVisible", "css=.ant-table-tbody tr.ant-table-row", "30000", "Sin filtros lista las pacientes activas"),
              c("executeScript", JS_TERMINO_REAL, "termino", "Nombre de una paciente activa"),
              c("executeScript", "return ${termino}.length > 0", "hay_termino"), c("assert", "hay_termino", "true"),
              c("type", "id=nombre", "${termino}"),
              c("click", "xpath=//button[.//span[normalize-space(.)='Buscar'] or normalize-space(.)='Buscar']"),
              c("waitForElementVisible", "xpath=//tr[contains(@class,'ant-table-row')][contains(.,'${termino}')]", "25000"),
              c("assertElementPresent", "xpath=//tr[contains(@class,'ant-table-row')][contains(.,'${termino}')]"),
              c("assertValue", "id=nombre", "${termino}", "El filtro conserva lo escrito")], "Media", "EP"),
    _caso(f"TC-{_n + 1}", "registrar_paciente", "Pacientes", "Registro", "Registrar una paciente con el asistente y buscarla (Selenium IDE)",
          "RF-01", "recepcion", "1. Nueva Paciente. 2. Datos personales. 3. Contacto. 4. Consentimiento. 5. Registrar. 6. Buscar su CI.",
          "La paciente se registra y aparece al buscar su cédula.",
          ingresar("recepcion") + [
              c("open", "/dashboard/pacientes"), c("waitForElementVisible", BUSCADOR_PAC, "25000"),
              c("click", "xpath=//button[.//span[normalize-space(.)='Nueva Paciente']]"),
              c("waitForElementVisible", "id=nombre", "15000"),
              c("type", "id=nombre", "QA Selenium"), c("type", "id=apellido_paterno", "Ide"), c("type", "id=apellido_materno", "Prueba"),
              c("type", "id=ci", "__QA_CI__"), c("type", "id=fecha_nacimiento", "15051996"), c("sendKeys", "id=fecha_nacimiento", "${KEY_ENTER}"),
              c("assertValue", "id=ci", "__QA_CI__"),
              c("click", "xpath=//div[contains(@class,'ant-modal')]//button[.//span[normalize-space(.)='Siguiente']]"),
              c("waitForElementVisible", "id=telefono", "10000"), c("type", "id=telefono", "71234567"),
              c("click", "xpath=//div[contains(@class,'ant-modal')]//button[.//span[normalize-space(.)='Siguiente']]"),
              c("waitForElementPresent", "id=consentimiento_datos_aceptado", "10000"),
              c("executeScript", "document.getElementById('consentimiento_datos_aceptado').click()", comentario="Casilla de consentimiento (Ley 164)"),
              c("click", "xpath=//div[contains(@class,'ant-modal')]//button[.//span[contains(.,'Registrar Paciente')]]"),
              c("waitForElementVisible", "css=.ant-message-success, .ant-notification-notice-success", "25000", "Mensaje de registro"),
              c("open", "/dashboard/pacientes"), c("waitForElementVisible", BUSCADOR_PAC, "25000"),
              c("type", BUSCADOR_PAC, "__QA_CI__"), c("sendKeys", BUSCADOR_PAC, "${KEY_ENTER}"),
              c("waitForElementVisible", "xpath=//tr[contains(@class,'ant-table-row')][contains(.,'__QA_CI__')]", "25000"),
              c("assertElementPresent", "xpath=//tr[contains(@class,'ant-table-row')][contains(.,'__QA_CI__')]")], "Alta"),
    _caso(f"TC-{_n + 2}", "guia_ia", "IA", "Guía de IA", "La Guía de IA lista los modelos disponibles (Selenium IDE)", "RF-33", "medico",
          "1. Iniciar sesión como médico. 2. Abrir la Guía de IA. 3. Contar los modelos.", "Hay al menos 10 modelos con el botón «Usar ahora».",
          ingresar("medico") + [
              c("open", "/dashboard/ia-guia"),
              c("waitForElementVisible", "xpath=(//button[normalize-space(.)='Usar ahora'])[1]", "25000"),
              c("assertText", "css=h1, h2, .ant-page-header-heading-title", "Guía de IA"),
              c("executeScript", "return [...document.querySelectorAll('button')].filter(b=>b.innerText.trim()==='Usar ahora').length", "modelos"),
              c("executeScript", "return ${modelos} >= 10", "suficientes"), c("assert", "suficientes", "true"),
              c("echo", "Modelos listados: ${modelos}")], "Media"),
    _caso(f"TC-{_n + 3}", "centro_reportes", "Reportes", "Centro de reportes", "El Centro de reportes cambia de pestaña (Selenium IDE)", "RF-18",
          "administrador", "1. Iniciar sesión como administrador. 2. Abrir Reportes. 3. Abrir las pestañas KPIs e Indicadores.",
          "Cada pestaña queda activa sin error.",
          ingresar("administrador") + [
              c("open", "/dashboard/reportes"),
              c("waitForElementVisible", "xpath=//div[contains(@class,'ant-tabs-tab')][normalize-space(.)='KPIs']", "25000"),
              c("click", "xpath=//div[contains(@class,'ant-tabs-tab')][normalize-space(.)='KPIs']"),
              c("waitForElementVisible", "xpath=//div[contains(@class,'ant-tabs-tab-active')][normalize-space(.)='KPIs']", "15000"),
              c("assertElementPresent", "xpath=//div[contains(@class,'ant-tabs-tab-active')][normalize-space(.)='KPIs']"),
              c("click", "xpath=//div[contains(@class,'ant-tabs-tab')][normalize-space(.)='Indicadores y metas']"),
              c("waitForElementVisible", "xpath=//div[contains(@class,'ant-tabs-tab-active')][normalize-space(.)='Indicadores y metas']", "15000"),
              c("assertElementNotPresent", "css=.ant-result-error")], "Media"),
    _caso(f"TC-{_n + 4}", "calculadora_imc", "Calculadoras", "IMC y ganancia de peso", "Calculadora de IMC y ganancia ponderal (Selenium IDE)", "RF-17",
          "medico", "1. Abrir la calculadora. 2. Peso 60, talla 160, peso actual 68, semana 28. 3. Calcular.",
          "Muestra el IMC pregestacional 23,4.",
          ingresar("medico") + [
              c("open", "/dashboard/calculadoras/imc-ganancia"), c("waitForElementVisible", "id=peso_pregestacional", "25000"),
              c("type", "id=peso_pregestacional", "60"), c("type", "id=talla", "160"), c("type", "id=peso_actual", "68"),
              c("type", "id=semanas_gestacion", "28"),
              c("assertElementPresent", "id=talla"),
              c("click", "xpath=//button[.//span[contains(.,'Calcular IMC')]]"),
              c("waitForElementVisible", "xpath=//*[contains(text(),'23.4') or contains(text(),'23,4')]", "20000", "IMC = 60 / 1,60²"),
              c("assertElementPresent", "xpath=//*[contains(text(),'23.4') or contains(text(),'23,4')]")], "Media", "VL"),
    _caso(f"TC-{_n + 5}", "perfil_usuario", "Usuarios", "Perfil", "El perfil muestra el correo de la cuenta (Selenium IDE)", "RF-21", "enfermera",
          "1. Iniciar sesión como enfermería. 2. Abrir Mi perfil.", "El campo de correo tiene el de la cuenta y el rol es ENFERMERA.",
          ingresar("enfermera") + [
              c("open", "/dashboard/perfil"), c("waitForElementVisible", "id=email", "25000"),
              c("assertValue", "id=email", "__QA_EMAIL_ENFERMERA__"),
              c("assertElementPresent", "xpath=//*[contains(@class,'user-dropdown-trigger')][contains(.,'ENFERMERA')]"),
              c("verifyElementPresent", "xpath=//button[.//span[normalize-space(.)='Guardar Cambios']]")], "Baja"),
]

ULTIMO_TC = f"TC-{_n + 5}"
