@echo off
:: ============================================================================
:: Arranque de PRODUCCION — Fetal Medical Bolivia
::
:: Diferencia con INICIAR_SISTEMA.bat: ese levanta el frontend con `npm start`,
:: que es el servidor de DESARROLLO. Entrega el codigo sin minificar, sin
:: comprimir y sin cache, mas la maquinaria de recarga en caliente. Sirve para
:: programar; en la red de una clinica es varias veces mas pesado.
::
:: Este arranca el build real:
::   frontend  397 KB comprimidos, con cache de un ano en los estaticos
::   backend   con GZipMiddleware: el listado de pacientes pasa de 165 a 19 KB
::
:: Medido en 3G lento (400 kbps): la primera visita tarda ~13 s y las
:: siguientes ~0,5 s, porque los estaticos quedan cacheados. En 3G tipico
:: (1,6 Mbps) la primera son ~3,7 s.
:: ============================================================================
title Fetal Medical Bolivia - PRODUCCION
color 0A
echo.
echo ================================================================
echo    FETAL MEDICAL BOLIVIA - ARRANQUE DE PRODUCCION
echo ================================================================
echo.

:: ── 1. PostgreSQL ───────────────────────────────────────────────
echo [1/5] PostgreSQL...
net start postgresql-x64-18 >nul 2>&1
if %errorlevel% equ 0 (echo     OK iniciado) else (echo     OK ya estaba corriendo)
timeout /t 2 /nobreak >nul

:: ── 2. Migraciones ──────────────────────────────────────────────
echo [2/5] Migraciones...
cd /d "%~dp0Backend"
python manage.py migrate --no-input >nul 2>&1
if %errorlevel% equ 0 (echo     OK al dia) else (echo     AVISO: revisar migraciones)

:: ── 3. Compilar el frontend si hace falta ───────────────────────
echo [3/5] Build del frontend...
if not exist "%~dp0Backend\frontend\build\index.html" (
    echo     No hay build. Compilando, esto tarda unos minutos...
    cd /d "%~dp0Backend\frontend"
    call npm run build
) else (
    echo     OK build existente
)

:: ── 4. Backend ──────────────────────────────────────────────────
echo [4/5] Backend Django ^(puerto 8000^)...
start "Backend Django" cmd /k "cd /d %~dp0Backend && set DEBUG=False&& python -m uvicorn asgi:application --host 0.0.0.0 --port 8000 --workers 4"
timeout /t 3 /nobreak >nul

:: ── 5. Microservicio de IA ──────────────────────────────────────
echo [5/5] Microservicio de IA ^(puerto 8001^) y frontend ^(3000^)...
start "Microservicio IA" cmd /k "cd /d %~dp0Backend\Microservicio_IA && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001"
start "Frontend produccion" cmd /k "cd /d %~dp0Backend\frontend && python servir_produccion.py 3000"

echo.
echo ================================================================
echo   LISTO
echo.
echo     Frontend        http://localhost:3000
echo     API             http://localhost:8000/api/
echo     Microservicio   http://localhost:8001/health
echo.
echo   Para servir a otros equipos de la clinica, ver
echo   docs\DESPLIEGUE-NATIVO.md (seccion "Servir en una red IP").
echo ================================================================
echo.
pause
