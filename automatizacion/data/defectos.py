"""Registro único de defectos (fuente de docs/defectos/BUG-XXX.md y registro_defectos.csv).

Cada defecto salió de una ejecución real: el caso o la herramienta que lo detectó está en «detectado_por» y su
evidencia en «evidencia». El estado y el commit de corrección se actualizan en la Fase 2.
"""
from __future__ import annotations

DEFECTOS = [
    {
        "id": "BUG-001", "titulo": "La API no aplica la tabla de roles: enfermería y laboratorio escriben en módulos de solo lectura y el laboratorista lee módulos ajenos",
        "modulo": "Roles y permisos", "pantalla_endpoint": "core/permissions.py · FetalMedicalPermission (POST /api/embarazos/, /api/ecografias/, /api/controles/, /api/partos/, /api/notas-evolucion/, /api/vacunas/registros/; GET /api/partos/, /api/reportes/dashboard-kpis/)",
        "pasos": "1. Iniciar sesión por la API como laboratorista. 2. POST /api/partos/ con cuerpo vacío. 3. GET /api/partos/. 4. Repetir con enfermería sobre /api/embarazos/ y /api/ecografias/.",
        "esperado": "403: según usuarios/permisos_por_rol.py (que el código declara alineada con la API), el laboratorista no tiene partos, notas, vacunas ni reportes y solo LEE embarazos, controles y ecografías; enfermería solo LEE embarazos y ecografías.",
        "obtenido": "400 en las escrituras (el permiso deja pasar la petición y solo la frena la validación) y 200 en las lecturas de partos, notas, vacunas y reportes para el laboratorista.",
        "severidad": "Alta", "prioridad": "Alta", "estado": "Abierto", "responsable": "Miguel Mirkof Becerra Guzmán",
        "caso": "TC-016", "detectado_por": "tests/api/test_permisos_api.py",
        "evidencia": "results.json de la corrida (13 casos TC-016 en FAIL) y docs/defectos/evidencias/BUG-001.txt",
        "causa_raiz": "FetalMedicalPermission da «acceso clínico completo» a médico y laboratorista, y a enfermería todo salvo partos y reportes, sin consultar la tabla de roles por módulo y acción que usa el frontend.",
    },
    {
        "id": "BUG-002", "titulo": "Cualquier rol lista todas las cuentas del sistema con correo, teléfono y si son superusuarios",
        "modulo": "Usuarios", "pantalla_endpoint": "GET /api/usuarios/",
        "pasos": "1. Iniciar sesión como recepción. 2. GET /api/usuarios/.",
        "esperado": "403, o solo la propia cuenta (o los médicos con los campos mínimos para agendar).",
        "obtenido": "200 con las 6 cuentas activas, incluidos correo, teléfono, is_superuser e is_staff.",
        "severidad": "Media", "prioridad": "Media", "estado": "Abierto", "responsable": "Miguel Mirkof Becerra Guzmán",
        "caso": "TC-016", "detectado_por": "tests/api/test_permisos_api.py::test_tc016_listado_de_usuarios_solo_para_administracion",
        "evidencia": "results.json (TC-016 listado de usuarios en FAIL)",
        "causa_raiz": "UsuarioViewSet usa el queryset completo y el serializador administrativo para todos los roles.",
    },
    {
        "id": "BUG-003", "titulo": "Glucosa en ayunas de 100 a 125 mg/dL en una gestante se informa como «prediabetes» y no como diabetes gestacional (IADPSG)",
        "modulo": "Laboratorio / calculadoras", "pantalla_endpoint": "POST /api/calculadoras/bioquimicas/ (Bioquimica.clasificar_automaticamente)",
        "pasos": "1. Registrar una bioquímica de una paciente CON embarazo activo. 2. glucosa_ayunas = 100 (o 125). 3. Leer las alertas.",
        "esperado": "«Diabetes gestacional (IADPSG: ayunas ≥ 92 mg/dL)» para 92 a 125 mg/dL en el embarazo; «diabetes» desde 126.",
        "obtenido": "«Prediabetes (glucosa 100-125 mg/dL)»: el criterio de no gestantes se evalúa antes que el de IADPSG.",
        "severidad": "Alta", "prioridad": "Alta", "estado": "Abierto", "responsable": "Miguel Mirkof Becerra Guzmán",
        "caso": "TC-091", "detectado_por": "tests/api/test_clinica_api.py::test_tc091_glucosa_en_ayunas_iadpsg",
        "evidencia": "results.json (TC-091 [100] y [125] en FAIL)",
        "causa_raiz": "Orden de la cadena if/elif en calculadoras/models_laboratorio.py: «≥ 100» se evalúa antes que «embarazo y ≥ 92».",
    },
    {
        "id": "BUG-004", "titulo": "Abrir /setup-mfa con el doble factor ya activo reemplaza la clave del MFA y deja la cuenta sin acceso",
        "modulo": "Autenticación", "pantalla_endpoint": "/setup-mfa · POST /api/usuarios/mfa/setup/",
        "pasos": "1. Iniciar sesión como administrador (MFA activo). 2. Abrir /setup-mfa (por ejemplo, desde el historial del navegador). 3. Salir sin confirmar. 4. Volver a iniciar sesión con el código del celular.",
        "esperado": "La pantalla no genera una clave nueva si el MFA ya está activo (o la nueva solo reemplaza a la anterior después de confirmarla).",
        "obtenido": "El servidor guarda una clave nueva al abrir la pantalla: el código del celular deja de ser válido y la cuenta queda fuera («Código MFA inválido o expirado»). Pasó con admin@ y medico@ en el recorrido del explorador; se restauraron sus claves desde la copia previa.",
        "severidad": "Crítica", "prioridad": "Alta", "estado": "Abierto", "responsable": "Miguel Mirkof Becerra Guzmán",
        "caso": "TC-002", "detectado_por": "tools/explorer.py (recorrido de todas las pantallas) y verificación de la clave en la base",
        "evidencia": "reports/explorador.log (/setup-mfa visitada por administrador y médico) y docs/defectos/evidencias/BUG-004.txt",
        "causa_raiz": "La acción mfa/setup del UsuarioViewSet genera y guarda un secreto nuevo sin comprobar mfa_enabled, y la pantalla lo pide al montarse.",
    },
    {
        "id": "BUG-005", "titulo": "El detalle de una nota de evolución se cae con «Objects are not valid as a React child»",
        "modulo": "Notas de evolución", "pantalla_endpoint": "/dashboard/notas-evolucion/:id",
        "pasos": "1. Iniciar sesión (médico, enfermería o administrador). 2. Abrir Notas de Evolución. 3. Abrir el detalle de una nota.",
        "esperado": "Se muestra el detalle de la nota.",
        "obtenido": "Error de JavaScript «Objects are not valid as a React child (found: object …)» y la pantalla no muestra la nota.",
        "severidad": "Alta", "prioridad": "Alta", "estado": "Abierto", "responsable": "Miguel Mirkof Becerra Guzmán",
        "caso": "TC-102", "detectado_por": "tools/explorer.py",
        "evidencia": "docs/inventario/capturas/medico/dashboard_notas_evolucion_2162.png y reports/explorador/ultimo.json",
        "causa_raiz": "El componente de detalle renderiza directamente un campo que la API devuelve como objeto.",
    },
    {
        "id": "BUG-006", "titulo": "Pantallas permitidas al rol piden a la API datos que el rol no puede leer (403 en la consola y secciones vacías)",
        "modulo": "Interfaz / permisos", "pantalla_endpoint": "/dashboard/access-logs (4 roles), /dashboard/reportes (enfermería y recepción), historia clínica (enfermería → /api/partos/, recepción → /api/embarazos/), /dashboard/consultorios y calculadora de IMC (laboratorio)",
        "pasos": "1. Iniciar sesión como enfermería. 2. Abrir /dashboard/access-logs o /dashboard/reportes. 3. Revisar la consola.",
        "esperado": "La pantalla no se ofrece al rol, o solo pide lo que el rol puede ver.",
        "obtenido": "La ruta abre (no exige permiso) y la API responde 403 a sus consultas; quedan errores en la consola y paneles vacíos o con esqueleto de carga permanente.",
        "severidad": "Media", "prioridad": "Media", "estado": "Abierto", "responsable": "Miguel Mirkof Becerra Guzmán",
        "caso": "TC-102", "detectado_por": "tools/explorer.py",
        "evidencia": "docs/inventario/capturas/<rol>/dashboard_access_logs.png, dashboard_reportes.png y reports/explorador/ultimo.json",
        "causa_raiz": "Rutas sin requiredPermission en AppRoutes.tsx y componentes que consultan módulos sin revisar el permiso del usuario.",
    },
    {
        "id": "BUG-007", "titulo": "Botones de solo ícono sin nombre accesible en 207 pantallas",
        "modulo": "Interfaz / accesibilidad", "pantalla_endpoint": "Botones de acción de las tablas y encabezados (Ant Design con icon y sin texto)",
        "pasos": "1. Recorrer las pantallas con un lector de pantalla o con el explorador.",
        "esperado": "Cada botón tiene texto, aria-label o title (WCAG 2.2, criterio 4.1.2).",
        "obtenido": "207 de las pantallas visitadas tienen al menos un botón sin nombre accesible.",
        "severidad": "Baja", "prioridad": "Baja", "estado": "Abierto", "responsable": "Miguel Mirkof Becerra Guzmán",
        "caso": "TC-102", "detectado_por": "tools/explorer.py (control de accesibilidad básica)",
        "evidencia": "reports/explorador/ultimo.json (campo a11y.botonesSinNombre)",
        "causa_raiz": "Botones <Button icon={...} /> sin aria-label.",
    },
    {
        "id": "BUG-008", "titulo": "El detalle del triaje muestra «Oxigenación periférica 0 %» cuando la saturación no se registró",
        "modulo": "Triaje", "pantalla_endpoint": "/dashboard/triaje/:id",
        "pasos": "1. Registrar un triaje sin saturación de oxígeno. 2. Abrir su detalle.",
        "esperado": "«Sin dato» (un valor no registrado no debe mostrarse como 0).",
        "obtenido": "Indicador circular con 0 % de oxigenación.",
        "severidad": "Baja", "prioridad": "Media", "estado": "Abierto", "responsable": "Miguel Mirkof Becerra Guzmán",
        "caso": "TC-102", "detectado_por": "tools/explorer.py (revisión de capturas)",
        "evidencia": "docs/inventario/capturas/medico/dashboard_triaje_1768.png",
        "causa_raiz": "El indicador usa saturacion_oxigeno ?? 0.",
    },
]


# ---------------------------------------------------------------------------------------------------------------
# Cierre de la Fase 2: corrección, commit, retesting y regresión de cada defecto (datos de las corridas reales).
RETEST = "20261114-111459"       # corrida de retesting: solo los casos que detectaron los defectos
REGRESION = "20261115-091110"         # corrida de regresión completa posterior a todas las correcciones

_CIERRE = {
    "BUG-001": {
        "estado": "Verificado", "commit": "2f7cd6a", "fecha_correccion": "13/11/2026",
        "correccion": "core/permissions.py consulta la tabla de roles por módulo y acción también para enfermería y "
                      "laboratorio (módulos sin acceso, módulos de solo lectura y consultas que se hacen por POST).",
        "retesting": f"TC-016: 74 de 74 combinaciones rol × endpoint en PASS (corrida {RETEST}); antes, 13 en FAIL.",
        "regresion": "La regresión encontró dos efectos de esta corrección, ambos corregidos: el panel del laboratorio "
                     "pedía estadísticas de reportes (commit 53b0849) y la historia clínica dejaba de cargar para el "
                     f"laboratorio (commit e833f3c). Regresión completa posterior: corrida {REGRESION}.",
        "observacion": "Dos regresiones detectadas por el barrido y corregidas (53b0849, e833f3c)",
    },
    "BUG-002": {
        "estado": "Verificado", "commit": "32de93d", "fecha_correccion": "13/11/2026",
        "correccion": "El listado de usuarios usa un serializador básico (nombre, rol, cargo, especialidad) para quien "
                      "no es administrador: sin correo, teléfono ni banderas de administración.",
        "retesting": f"TC-016 (listado de usuarios): PASS en la corrida {RETEST}; recepción recibe 200 sin campos sensibles.",
        "regresion": f"Las pantallas que eligen un médico (citas, embarazos) siguen funcionando: corrida {REGRESION}.",
        "observacion": "Se conserva el listado básico porque las pantallas lo usan para elegir al profesional",
    },
    "BUG-003": {
        "estado": "Verificado", "commit": "deede8f", "fecha_correccion": "13/11/2026",
        "correccion": "En calculadoras/models_laboratorio.py el criterio IADPSG del embarazo (ayunas ≥ 92 mg/dL) se "
                      "evalúa antes que el de prediabetes de no gestantes. Cambio de lógica clínica aprobado por el responsable.",
        "retesting": f"TC-091: los cinco valores (91, 92, 100, 125 y 126 mg/dL) en PASS en la corrida {RETEST}; antes, 100 y 125 en FAIL.",
        "regresion": f"Pruebas de laboratorio y calculadoras de la suite del sistema y corrida {REGRESION}.",
        "observacion": "Lógica clínica: corregida con aprobación previa",
    },
    "BUG-004": {
        "estado": "Verificado", "commit": "445f6f3", "fecha_correccion": "13/11/2026", "caso_retest": "TC-119",
        "correccion": "La acción mfa/setup responde 409 si la cuenta ya tiene el doble factor activo y no genera otra "
                      "clave. Contención previa: se restauraron las claves de las dos cuentas afectadas.",
        "retesting": f"TC-119 en PASS (corrida {RETEST}): con el doble factor activo, pedir otro QR responde 409, no trae "
                     "clave y la original sigue sirviendo. Se prueba con una cuenta temporal QA.",
        "regresion": f"Autenticación completa (TC-001 a TC-013) en la corrida {REGRESION}.",
        "observacion": "Crítico. Reapareció una vez al reprobar contra el servidor sin reiniciar; TC-119 ya no usa cuentas reales",
    },
    "BUG-005": {
        "estado": "Verificado", "commit": "3379295", "fecha_correccion": "13/11/2026", "caso_retest": "TC-120",
        "correccion": "DetalleNotaEvolucion.tsx muestra el nombre de la paciente y del médico aunque la API los envíe como objeto.",
        "retesting": f"TC-120 en PASS (corrida {RETEST}): el detalle abre sin error de JavaScript.",
        "regresion": f"Barrido de pantallas TC-102 de los cinco roles en PASS en la corrida {RETEST} y en la {REGRESION}.",
        "observacion": "Se agregó el caso TC-120 como prueba de regresión propia",
    },
    "BUG-006": {
        "estado": "Verificado", "commit": "a3864a8, e833f3c", "fecha_correccion": "14/11/2026", "caso_retest": "TC-102",
        "correccion": "Las rutas exigen el mismo permiso que la API pide a sus consultas (a3864a8) y la historia clínica "
                      "y la ficha de la paciente piden cada apartado solo si el rol puede leerlo (e833f3c).",
        "retesting": f"TC-102 de los cinco roles en PASS (corrida {RETEST}): ninguna pantalla permitida deja 403 ni errores en la consola.",
        "regresion": f"TC-014 y TC-015 (menú por rol y URL prohibidas) en PASS; corrida {REGRESION}.",
        "observacion": "Corregido en dos commits; el segundo cerró el residuo en la historia clínica",
    },
    "BUG-007": {
        "estado": "Abierto con propuesta", "observacion": "Accesibilidad, severidad baja. Propuesta: aria-label en los botones "
                                                          "de solo ícono, empezando por las acciones de las tablas",
    },
    "BUG-008": {
        "estado": "Verificado", "commit": "3447380", "fecha_correccion": "13/11/2026", "caso_retest": "TC-121",
        "correccion": "PanelRiesgoClinico.tsx muestra «Sin dato» cuando la saturación no se registró, en lugar de 0 %.",
        "retesting": f"TC-121 en PASS (corrida {RETEST}): un triaje QA sin saturación muestra «Sin dato».",
        "regresion": f"Triaje por la pantalla (TC-051) y por la API (TC-049, TC-050) en la corrida {REGRESION}.",
        "observacion": "Se agregó el caso TC-121 como prueba de regresión propia",
    },
}
for _d in DEFECTOS:
    _d.update(_CIERRE.get(_d["id"], {}))
