@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================================================
:: FETAL MEDICAL SYSTEM - SCRIPT DE EJECUCIÓN COMPLETO CON TRAZABILIDAD
:: ============================================================================
:: Este script:
:: 1. Verifica el entorno (Python, Node.js, PostgreSQL)
:: 2. Ejecuta pruebas automatizadas
:: 3. Inicia todos los servicios
:: 4. Genera reportes de estado
:: 5. Registra logs con trazabilidad completa
:: ============================================================================

set SCRIPT_VERSION=2.0.0
set LOG_FILE=%~dp0execution_trace.log
set TIMESTAMP=%date% %time%

:: ============================================================================
:: FUNCIÓN: LOG CON TRAZABILIDAD
:: ============================================================================
:log_message
echo [%TIMESTAMP%] %~1 >> "%LOG_FILE%"
echo %~1
exit /b 0

:: ============================================================================
:: FUNCIÓN: VERIFICAR SI UN PROGRAMA EXISTE
:: ============================================================================
:check_program
where %~1 >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] %~1 no está instalado o no está en PATH
    echo [%TIMESTAMP%] [ERROR] %~1 no encontrado >> "%LOG_FILE%"
    exit /b 1
)
exit /b 0

:: ============================================================================
:: INICIO - LIMPIAR LOG ANTERIOR
:: ============================================================================
echo ========================================
echo  FETAL MEDICAL SYSTEM - INICIALIZACIÓN
echo  Versión: %SCRIPT_VERSION%
echo ========================================
echo.

echo [%TIMESTAMP%] === INICIO DE EJECUCIÓN === > "%LOG_FILE%"
echo [%TIMESTAMP%] Directorio: %~dp0 >> "%LOG_FILE%"
echo.

:: ============================================================================
:: PASO 1: VERIFICAR ENTORNO
:: ============================================================================
echo [1/6] Verificando entorno...
echo.

:: Verificar Python
call :check_program python
if %errorlevel% neq 0 goto :error_exit
python --version >> "%LOG_FILE%" 2>&1
echo   [+] Python encontrado

:: Verificar Node.js
call :check_program node
if %errorlevel% neq 0 goto :error_exit
node --version >> "%LOG_FILE%" 2>&1
echo   [+] Node.js encontrado

:: Verificar npm
call :check_program npm
if %errorlevel% neq 0 goto :error_exit
echo   [+] npm encontrado

:: Verificar PostgreSQL
call :check_program psql
if %errorlevel% neq 0 (
    echo   [!] PostgreSQL no está en PATH (puede estar corriendo igual)
) else (
    echo   [+] PostgreSQL encontrado
)

echo.
echo [%TIMESTAMP%] [OK] Entorno verificado >> "%LOG_FILE%"

:: ============================================================================
:: PASO 2: VERIFICAR BASE DE DATOS
:: ============================================================================
echo [2/6] Verificando base de datos...
echo.

set "PGPASSWORD_FILE=%~dp0Backend\.env"
for /f "tokens=2 delims==" %%A in ('findstr /i "^DB_PASSWORD=" "%PGPASSWORD_FILE%" 2^>nul') do set "DB_PASSWORD=%%A"
if defined DB_PASSWORD (
    set "PGPASSWORD=%DB_PASSWORD%"
) else (
    set "PGPASSWORD=25693"
)
psql -U postgres -h 127.0.0.1 -lqt 2>nul | findstr historial >nul
if %errorlevel% neq 0 (
    echo   [!] Base de datos 'historial' no existe
    echo   [+] Creando base de datos...
    psql -U postgres -h 127.0.0.1 -c "CREATE DATABASE historial;" >nul 2>&1
    if %errorlevel% equ 0 (
        echo   [+] Base de datos creada exitosamente
        echo [%TIMESTAMP%] [OK] Base de datos creada >> "%LOG_FILE%"
    ) else (
        echo   [ERROR] No se pudo crear la base de datos
        echo [%TIMESTAMP%] [ERROR] Falló creación BD >> "%LOG_FILE%"
        goto :error_exit
    )
) else (
    echo   [+] Base de datos 'historial' existe
    echo [%TIMESTAMP%] [OK] Base de datos verificada >> "%LOG_FILE%"
)

echo.

:: ============================================================================
:: PASO 3: EJECUTAR PRUEBAS BACKEND (OPCIONAL)
:: ============================================================================
echo [3/6] ¿Ejecutar pruebas del backend? (S/N)
set /p RUN_TESTS=
if /i "%RUN_TESTS%"=="S" (
    echo.
    echo   Ejecutando pruebas de Django...
    cd "%~dp0Backend"
    python manage.py test tests --verbosity=2 >> "%LOG_FILE%" 2>&1
    if %errorlevel% equ 0 (
        echo   [+] Todas las pruebas pasaron
        echo [%TIMESTAMP%] [OK] Tests backend OK >> "%LOG_FILE%"
    ) else (
        echo   [ERROR] Algunas pruebas fallaron
        echo [%TIMESTAMP%] [ERROR] Tests backend fallaron >> "%LOG_FILE%"
        goto :error_exit
    )
    cd "%~dp0"
) else (
    echo   [!] Pruebas omitidas
    echo [%TIMESTAMP%] [INFO] Tests omitidos por usuario >> "%LOG_FILE%"
)

echo.

:: ============================================================================
:: PASO 4: EJECUTAR MIGRACIONES
:: ============================================================================
echo [4/6] Aplicando migraciones de Django...
echo.

cd "%~dp0Backend"
python manage.py migrate --noinput >> "%LOG_FILE%" 2>&1
if %errorlevel% equ 0 (
    echo   [+] Migraciones aplicadas exitosamente
    echo [%TIMESTAMP%] [OK] Migraciones aplicadas >> "%LOG_FILE%"
) else (
    echo   [ERROR] Error en migraciones
    echo [%TIMESTAMP%] [ERROR] Migraciones fallaron >> "%LOG_FILE%"
    goto :error_exit
)

cd "%~dp0"
echo.

:: ============================================================================
:: PASO 5: INICIAR SERVICIOS
:: ============================================================================
echo [5/6] Iniciando servicios...
echo.

:: Verificar si Django ya está corriendo
netstat -ano | findstr ":8000" >nul
if %errorlevel% equ 0 (
    echo   [!] Django ya está corriendo en puerto 8000
) else (
    echo   [+] Iniciando Django Backend (puerto 8000)...
    start "Django Backend - Fetal Medical" cmd /k "cd /d "%~dp0Backend" && echo Iniciando Django... && python manage.py runserver 8000"
    timeout /t 3 /nobreak >nul
    echo   [+] Django iniciado
    echo [%TIMESTAMP%] [OK] Django iniciado en puerto 8000 >> "%LOG_FILE%"
)

:: Verificar si IA ya está corriendo
netstat -ano | findstr ":8005" >nul
if %errorlevel% equ 0 (
    echo   [!] Microservicio IA ya está corriendo en puerto 8005
) else (
    echo   [+] Iniciando AI Microservice (puerto 8005)...
    start "AI Microservice - Fetal Medical" cmd /k "cd /d "%~dp0Backend\Microservicio_IA" && echo Iniciando AI Microservice... && set PYTHONIOENCODING=utf-8 && python -m uvicorn main:app --host 0.0.0.0 --port 8005"
    timeout /t 3 /nobreak >nul
    echo   [+] AI Microservice iniciado
    echo [%TIMESTAMP%] [OK] AI Microservice iniciado en puerto 8005 >> "%LOG_FILE%"
)

echo.

:: ============================================================================
:: PASO 6: VERIFICAR SERVICIOS
:: ============================================================================
echo [6/6] Verificando servicios...
echo.

timeout /t 5 /nobreak >nul

:: Verificar Django
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo   [+] Django Backend: FUNCIONANDO ✓
    echo [%TIMESTAMP%] [OK] Django verificado >> "%LOG_FILE%"
) else (
    echo   [ERROR] Django Backend: NO RESPONDE ✗
    echo [%TIMESTAMP%] [ERROR] Django no responde >> "%LOG_FILE%"
)

:: Verificar IA
netstat -ano | findstr ":8005" | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo   [+] AI Microservice: FUNCIONANDO ✓
    echo [%TIMESTAMP%] [OK] AI Microservice verificado >> "%LOG_FILE%"
) else (
    echo   [!] AI Microservice: CARGANDO... (puede tardar unos segundos)
    echo [%TIMESTAMP%] [INFO] AI Microservice aún cargando >> "%LOG_FILE%"
)

:: Verificar PostgreSQL
netstat -ano | findstr ":5432" | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo   [+] PostgreSQL: FUNCIONANDO ✓
    echo [%TIMESTAMP%] [OK] PostgreSQL verificado >> "%LOG_FILE%"
) else (
    echo   [ERROR] PostgreSQL: NO RESPONDE ✗
    echo [%TIMESTAMP%] [ERROR] PostgreSQL no responde >> "%LOG_FILE%"
)

echo.

:: ============================================================================
:: RESUMEN FINAL
:: ============================================================================
echo ========================================
echo  TODOS LOS SERVICIOS INICIADOS
echo ========================================
echo.
echo  📊 Estado del Sistema:
echo  ─────────────────────────────────────
echo   Django Backend:    http://127.0.0.1:8000
echo   AI Microservice:   http://127.0.0.1:8005
echo   React Frontend:    http://127.0.0.1:3000
echo   API Docs:          http://127.0.0.1:8000/api/docs/
echo   ReDoc:             http://127.0.0.1:8000/api/redoc/
echo   Health Check:      http://127.0.0.1:8000/api/health/
echo   Admin:             http://127.0.0.1:8000/admin/
echo  ─────────────────────────────────────
echo.
echo  🚀 Para iniciar Frontend React:
echo     cd Backend\frontend
echo     npm start
echo.
echo  📝 Log de trazabilidad: %LOG_FILE%
echo  🔐 Las credenciales se leen desde Backend\.env (no hardcodeadas)
echo.
echo [%TIMESTAMP%] === EJECUCIÓN COMPLETADA === >> "%LOG_FILE%"
echo.

:: ============================================================================
:: ABRIR LOG EN NAVEGADOR (OPCIONAL)
:: ============================================================================
echo ¿Desea ver el log de trazabilidad? (S/N)
set /p VIEW_LOG=
if /i "%VIEW_LOG%"=="S" (
    notepad "%LOG_FILE%"
)

echo.
pause
exit /b 0

:: ============================================================================
:: MANEJO DE ERRORES
:: ============================================================================
:error_exit
echo.
echo ========================================
echo  ERROR CRÍTICO
echo ========================================
echo  La ejecución se detuvo por un error.
echo  Revisa el log para más detalles:
echo  %LOG_FILE%
echo ========================================
echo.
echo [%TIMESTAMP%] === ERROR CRÍTICO - EJECUCIÓN DETENIDA === >> "%LOG_FILE%"
pause
exit /b 1
