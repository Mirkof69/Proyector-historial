@echo off
setlocal EnableExtensions
:: ============================================================================
:: FETAL MEDICAL BOLIVIA - un solo lanzador para todo el sistema
::
::   INICIAR.bat              produccion (hospital): build real, API en waitress,
::                            notificaciones en vivo con Redis, 13 redes de IA
::   INICIAR.bat desarrollo   para programar: recarga automatica y React dev
::   INICIAR.bat detener      cierra los servicios del sistema (3000, 8000, 8001, 8010)
::
:: Reemplaza a INICIAR_SISTEMA.bat e INICIAR_PRODUCCION.bat (02/10/2026).
:: Cada paso comprueba que funciono; si algo falla se detiene y dice que hacer.
:: Por que cada pieza esta como esta: docs\sistema\11_despliegue_y_operacion.md
:: ============================================================================
title Fetal Medical Bolivia
color 0A
cd /d "%~dp0"
set "RAIZ=%~dp0"
set "BACK=%RAIZ%Backend"
set "PY=%BACK%\.venv\Scripts\python.exe"
set "PGBIN=C:\Program Files\PostgreSQL\18\bin"
set "PGDATA=C:\Program Files\PostgreSQL\18\data"
set "REDISDIR=C:\Program Files\Redis"
set "MODO=produccion"
if /i "%~1"=="desarrollo" set "MODO=desarrollo"

echo.
echo ================================================================
echo    FETAL MEDICAL BOLIVIA
echo ================================================================

if not exist "%PY%" (
    echo ERROR: falta el entorno del backend ^(Backend\.venv^).
    echo   Crearlo:  cd Backend ^&^& python -m venv .venv ^&^& .venv\Scripts\pip install -r requirements.txt
    goto fallo
)

if /i "%~1"=="detener" (
    echo Deteniendo los servicios del sistema...
    "%PY%" "%BACK%\scripts\arranque.py" detener
    goto fin
)
echo    Modo: %MODO%
echo ================================================================

:: -- 1. Requisitos ------------------------------------------------
echo [1/8] Requisitos...
python -c "import torch, fastapi, timm, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo     AVISO: el Python del sistema no tiene torch/fastapi: la IA no arrancara.
    echo       Instalar:  pip install -r Backend\Microservicio_IA\requirements.txt
    set "SIN_IA=1"
) else (echo     OK)

:: -- 2. Arranque limpio -------------------------------------------
echo [2/8] Cerrando servicios anteriores del sistema...
"%PY%" "%BACK%\scripts\arranque.py" detener

:: -- 3. PostgreSQL ------------------------------------------------
:: Debe ser el SERVICIO de Windows (con APLICAR_AJUSTES_POSTGRES.bat). Si no se
:: puede (sin permisos de administrador) se arranca con pg_ctl, que funciona
:: pero puede colgar conexiones (error 487): sirve para probar, no para el hospital.
echo [3/8] PostgreSQL...
"%PGBIN%\pg_isready.exe" -h 127.0.0.1 -p 5432 >nul 2>&1
if not errorlevel 1 (echo     OK ya estaba en marcha& goto pg_listo)
net start postgresql-x64-18 >nul 2>&1
call :esperar_pg 10
if not errorlevel 1 (echo     OK servicio de Windows iniciado& goto pg_listo)
echo     El servicio no arranco ^(falta ejecutar como administrador^): uso pg_ctl.
start "PostgreSQL" /min "%PGBIN%\pg_ctl.exe" start -D "%PGDATA%" -l "%TEMP%\postgres_fetal.log"
call :esperar_pg 60
if errorlevel 1 (
    echo ERROR: PostgreSQL no responde. Abrir este .bat como administrador
    echo   o revisar %TEMP%\postgres_fetal.log
    goto fallo
)
echo     OK ^(con pg_ctl: en el hospital use el servicio de Windows^)
:pg_listo

:: -- 4. Redis -----------------------------------------------------
:: La API y los WebSockets son procesos distintos: sin Redis las alertas no
:: llegan en vivo (comprobado el 01/10/2026).
echo [4/8] Redis...
set "REDIS_URL=redis://127.0.0.1:6379/0"
"%REDISDIR%\redis-cli.exe" ping 2>nul | findstr PONG >nul
if not errorlevel 1 goto redis_listo
net start Redis >nul 2>&1
"%REDISDIR%\redis-cli.exe" ping 2>nul | findstr PONG >nul
if not errorlevel 1 goto redis_listo
if exist "%REDISDIR%\redis-server.exe" start "Redis" /min "%REDISDIR%\redis-server.exe" --port 6379 --bind 127.0.0.1
ping -n 4 127.0.0.1 >nul
:redis_listo
"%REDISDIR%\redis-cli.exe" ping 2>nul | findstr PONG >nul
if errorlevel 1 (
    echo     AVISO: Redis no responde: las notificaciones solo se veran al recargar.
    set "REDIS_URL="
) else (echo     OK)

:: -- 5. Migraciones -----------------------------------------------
echo [5/8] Base de datos al dia (todas las clinicas)...
cd /d "%BACK%"
"%PY%" manage.py migrate_schemas --noinput > logs\migraciones.log 2>&1
if errorlevel 1 (
    echo ERROR en las migraciones: ver Backend\logs\migraciones.log
    goto fallo
)
:: Citas de dias pasados que nadie atendio: quedan como "No asistio" (no detiene el arranque).
"%PY%" manage.py cerrar_citas_vencidas >> logs\migraciones.log 2>&1
echo     OK

:: -- 6. Frontend --------------------------------------------------
if /i "%MODO%"=="desarrollo" (
    echo [6/8] Frontend: servidor de desarrollo, sin compilar
    goto front_listo
)
echo [6/8] Frontend compilado...
"%PY%" "%BACK%\scripts\arranque.py" build-vigente
if not errorlevel 1 goto front_ok
echo     Compilando ^(unos minutos^)...
cd /d "%BACK%\frontend"
"%PY%" "%BACK%\scripts\arranque.py" dependencias
if errorlevel 1 call npm install --no-audit --no-fund
call npm run build > "%BACK%\logs\build_frontend.log" 2>&1
if errorlevel 1 (
    echo ERROR al compilar el frontend: ver Backend\logs\build_frontend.log
    goto fallo
)
cd /d "%BACK%"
:front_ok
echo     OK
:front_listo

:: -- 7. Red -------------------------------------------------------
echo [7/8] Red de la clinica...
"%PY%" "%BACK%\scripts\arranque.py" habilitar-red

:: -- 8. Servicios -------------------------------------------------
echo [8/8] Arrancando servicios...
if /i "%MODO%"=="desarrollo" goto servicios_desarrollo
:: API en waitress (WSGI): p95 < 200 ms medido. WebSockets en uvicorn con 1
:: worker (con 2, en Windows, conexiones colgadas). DEBUG=False en produccion.
:: --connection-limit=480: waitress acepta 100 conexiones por defecto y, con
:: 100 abiertas (cada navegador deja las suyas vivas 120 s), deja de aceptar
:: nuevas: en la prueba de carga del 29/10/2026 los usuarios 101 a 150 no
:: pudieron ni iniciar sesion. 480 y no mas porque en Windows select() no
:: admite mas de 512 sockets (quedan el de escucha y el de aviso).
:: --trusted-proxy: waitress borra X-Forwarded-* de quien no es de confianza. Solo
:: el proxy de este equipo (publicacion por tunel) puede indicar IP real y https;
:: un equipo de la red que los invente no cambia nada.
start "Fetal Medical - API (8000)" /min cmd /k "cd /d "%BACK%" && set DEBUG=False&& set REDIS_URL=%REDIS_URL%&& .venv\Scripts\python.exe -m waitress --host=0.0.0.0 --port=8000 --threads=32 --connection-limit=480 --trusted-proxy=127.0.0.1 --trusted-proxy-headers="x-forwarded-for x-forwarded-proto" wsgi:application"
start "Fetal Medical - Notificaciones (8010)" /min cmd /k "cd /d "%BACK%" && set DEBUG=False&& set REDIS_URL=%REDIS_URL%&& .venv\Scripts\python.exe -m uvicorn asgi:application --host 0.0.0.0 --port 8010 --workers 1"
if not defined SIN_IA start "Fetal Medical - IA (8001)" /min cmd /k "cd /d "%BACK%\Microservicio_IA" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001"
start "Fetal Medical - Frontend (3000)" /min cmd /k "cd /d "%BACK%\frontend" && "%PY%" servir_produccion.py 3000"
goto comprobar

:servicios_desarrollo
start "Fetal Medical - Backend dev (8000)" /min cmd /k "cd /d "%BACK%" && set REDIS_URL=%REDIS_URL%&& .venv\Scripts\python.exe -m uvicorn asgi:application --host 127.0.0.1 --port 8000 --reload"
if not defined SIN_IA start "Fetal Medical - IA (8001)" /min cmd /k "cd /d "%BACK%\Microservicio_IA" && python -m uvicorn app.main:app --host 127.0.0.1 --port 8001"
start "Fetal Medical - Frontend dev (3000)" /min cmd /k "cd /d "%BACK%\frontend" && set BROWSER=none&& npm start"

:comprobar
echo.
echo Comprobando que cada servicio responda...
"%PY%" "%BACK%\scripts\arranque.py" esperar http://127.0.0.1:8000/api/health/ 90
if errorlevel 1 (echo     ERROR: la API no responde ^(ventana "API"^)& set "HAY_FALLO=1") else (echo     OK API)
if defined SIN_IA goto sin_ia
"%PY%" "%BACK%\scripts\arranque.py" esperar http://127.0.0.1:8001/health 180
if errorlevel 1 (echo     AVISO: la IA no responde ^(ventana "IA"^)& set "HAY_FALLO=1") else (echo     OK IA con sus redes precargadas)
:sin_ia
"%PY%" "%BACK%\scripts\arranque.py" esperar http://127.0.0.1:3000/ 240
if errorlevel 1 (echo     ERROR: el frontend no responde& set "HAY_FALLO=1") else (echo     OK frontend)
if /i not "%MODO%"=="produccion" goto resumen
"%PY%" "%BACK%\scripts\arranque.py" esperar http://127.0.0.1:8010/ 30
if errorlevel 1 (echo     AVISO: notificaciones en vivo sin responder& set "HAY_FALLO=1") else (echo     OK notificaciones en vivo)

:resumen
echo.
echo ================================================================
if defined HAY_FALLO (echo   ARRANCADO CON AVISOS: revise las ventanas minimizadas) else (echo   LISTO)
echo.
echo     Sistema     http://localhost:3000
echo     API         http://localhost:8000/api/
echo     IA          http://localhost:8001/health
if /i "%MODO%"=="produccion" ("%PY%" "%BACK%\scripts\arranque.py" red --produccion) else ("%PY%" "%BACK%\scripts\arranque.py" red)
echo.
echo   Para cerrar todo:  INICIAR.bat detener
echo ================================================================
if not defined SIN_NAVEGADOR start "" http://localhost:3000
goto fin

:fallo
echo.
echo El sistema NO se inicio. Corrija lo indicado y vuelva a ejecutar INICIAR.bat
set "HAY_FALLO=1"

:fin
if not defined SIN_PAUSA pause
if defined HAY_FALLO exit /b 1
exit /b 0

:: Espera hasta %1 segundos a que PostgreSQL acepte conexiones. pg_isready -t
:: no reintenta: si el servidor aun no escucha, falla al instante (asi se
:: cortaba el arranque el 14/10/2026 con PostgreSQL ya casi listo). La pausa es
:: con ping porque "timeout" falla si la entrada no es una consola.
:esperar_pg
set /a "PG_INTENTOS=%~1 / 2"
:esperar_pg_otra
"%PGBIN%\pg_isready.exe" -h 127.0.0.1 -p 5432 -t 2 >nul 2>&1
if not errorlevel 1 exit /b 0
set /a PG_INTENTOS-=1
if %PG_INTENTOS% LEQ 0 exit /b 1
ping -n 3 127.0.0.1 >nul
goto esperar_pg_otra
