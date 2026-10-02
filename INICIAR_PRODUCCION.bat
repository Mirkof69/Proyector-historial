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
echo [1/6] PostgreSQL...
net start postgresql-x64-18 >nul 2>&1
if %errorlevel% equ 0 (echo     OK iniciado) else (echo     OK ya estaba corriendo)
timeout /t 2 /nobreak >nul

:: ── 2. Redis ───────────────────────────────────────────────────
:: Las notificaciones las crea la API (waitress) y las entrega otro proceso, el
:: de los WebSockets (uvicorn): sin Redis no cruzan, y como el frontend deja de
:: sondear cuando el WebSocket conecta, las alertas no se veian hasta recargar
:: (comprobado el 01/10/2026). Si el servicio no arranca, se lanza el ejecutable.
echo [2/6] Redis...
set REDIS_URL=redis://127.0.0.1:6379/0
net start Redis >nul 2>&1
"C:\Program Files\Redis\redis-cli.exe" ping 2>nul | findstr PONG >nul || (
    if exist "C:\Program Files\Redis\redis-server.exe" start "Redis" /min "C:\Program Files\Redis\redis-server.exe" --port 6379 --bind 127.0.0.1
    timeout /t 2 /nobreak >nul
)
"C:\Program Files\Redis\redis-cli.exe" ping 2>nul | findstr PONG >nul && (echo     OK) || (echo     AVISO: Redis no responde; las notificaciones solo se veran al recargar la pagina)

:: ── 3. Migraciones ──────────────────────────────────────────────
echo [3/6] Migraciones...
cd /d "%~dp0Backend"
:: migrate_schemas (no migrate): cada clinica es un esquema de django-tenants.
:: Antes usaba el python del sistema y ocultaba los errores con >nul.
".venv\Scripts\python.exe" manage.py migrate_schemas --noinput > logs\migraciones.log 2>&1
if %errorlevel% equ 0 (echo     OK al dia) else (
    echo     ERROR en las migraciones: ver Backend\logs\migraciones.log
    pause
    exit /b 1
)

:: ── 4. Compilar el frontend si hace falta ───────────────────────
echo [4/6] Build del frontend...
if not exist "%~dp0Backend\frontend\build\index.html" (
    echo     No hay build. Compilando, esto tarda unos minutos...
    cd /d "%~dp0Backend\frontend"
    call npm run build
) else (
    echo     OK build existente
)

:: ── 5. Backend ──────────────────────────────────────────────────
echo [5/6] Backend Django: API ^(8000^) y notificaciones en tiempo real ^(8010^)...
:: La API la sirve waitress (WSGI): medido el 01/10/2026 con la demo de 3.200
:: pacientes, 5-53 ms de mediana y menos de 60 ms en el 95 %% de las peticiones.
:: Con uvicorn (ASGI) en Windows cada peticion sumaba 50-100 ms de puente entre
:: hilos: 100-250 ms. Uvicorn queda solo para los WebSockets (puerto 8010), que
:: el frontend de produccion busca ahi solo. Un solo worker: es asincrono y
:: atiende cientos de sockets; con varios, en Windows, las conexiones quedaban
:: colgadas en el socket compartido. REDIS_URL (paso 2) llega a los dos procesos.
:: El python del entorno virtual (.venv), que es donde estan las dependencias.
start "Backend API (WSGI)" cmd /k "cd /d %~dp0Backend && set DEBUG=False&& .venv\Scripts\python.exe -m waitress --host=0.0.0.0 --port=8000 --threads=32 wsgi:application"
start "Backend WebSockets (ASGI)" cmd /k "cd /d %~dp0Backend && set DEBUG=False&& .venv\Scripts\python.exe -m uvicorn asgi:application --host 0.0.0.0 --port 8010 --workers 1"
timeout /t 3 /nobreak >nul

:: ── 6. Microservicio de IA ──────────────────────────────────────
echo [6/6] Microservicio de IA ^(puerto 8001^) y frontend ^(3000^)...
start "Microservicio IA" cmd /k "cd /d %~dp0Backend\Microservicio_IA && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001"
start "Frontend produccion" cmd /k "cd /d %~dp0Backend\frontend && python servir_produccion.py 3000"

:: ── Comprobacion: que los tres servicios respondan de verdad ─────
echo.
echo Comprobando servicios (hasta 60 s)...
set /a intentos=0
:esperar
timeout /t 3 /nobreak >nul
set /a intentos+=1
curl -s -o nul -w "%%{http_code}" http://localhost:8000/api/ | findstr /r "200 401 403" >nul || (if %intentos% lss 20 goto esperar)
curl -s -o nul -w "%%{http_code}" http://localhost:8000/api/ | findstr /r "200 401 403" >nul && (echo     OK backend) || (echo     ERROR: el backend no responde)
curl -s -o nul -w "%%{http_code}" http://localhost:8001/health | findstr "200" >nul && (echo     OK microservicio de IA con modelo cargado) || (echo     AVISO: IA sin modelo o sin responder, ver http://localhost:8001/health)
curl -s -o nul http://localhost:3000 && (echo     OK frontend) || (echo     AVISO: el frontend aun no responde)

echo.
echo ================================================================
echo   LISTO
echo.
echo     Frontend        http://localhost:3000
echo     API             http://localhost:8000/api/
echo     Notificaciones  ws://localhost:8010/ws/notifications/
echo     Microservicio   http://localhost:8001/health
echo.
echo   Para servir a otros equipos de la clinica, ver
echo   docs\DESPLIEGUE-NATIVO.md (seccion "Servir en una red IP").
echo ================================================================
echo.
pause
