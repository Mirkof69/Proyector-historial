@echo off
:: ============================================================================
:: Aplica los ajustes de PostgreSQL que necesitan reinicio del servicio.
::
:: Los valores ya estan escritos en postgresql.auto.conf mediante ALTER SYSTEM.
:: Lo unico que falta es reiniciar el servicio, y eso pide administrador.
::
::   max_connections   100 -> 300     (era la causa de los errores HTTP 500
::                                     "ya tenemos demasiados clientes")
::   shared_buffers  128 MB -> 4 GB   (el valor por defecto asume una maquina
::                                     de 1 GB; esta tiene 60 GB)
::
:: Doble clic sobre este archivo. Windows pedira permiso de administrador.
:: ============================================================================
title Fetal Medical Bolivia - Aplicar ajustes de PostgreSQL

:: --- Elevarse a administrador si aun no lo esta ---
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Solicitando permisos de administrador...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

color 0A
echo.
echo ================================================================
echo   APLICANDO AJUSTES DE POSTGRESQL
echo ================================================================
echo.

echo [1/3] Deteniendo el servicio...
net stop postgresql-x64-18
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo   ERROR: no se pudo detener el servicio.
    echo   Cierre el backend de Django y el microservicio de IA, y reintente.
    pause
    exit /b 1
)

echo.
echo [2/3] Iniciando el servicio con la configuracion nueva...
net start postgresql-x64-18
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo   ERROR: el servicio no arranco. Revise:
    echo   "C:\Program Files\PostgreSQL\18\data\log"
    echo.
    echo   Causa mas probable: shared_buffers=4GB no cabe. Bajarlo a 2GB con:
    echo     ALTER SYSTEM SET shared_buffers = '2GB';
    pause
    exit /b 1
)

echo.
echo [3/3] Verificando...
cd /d "%~dp0Backend"
python -c "import psycopg; c=psycopg.connect(dbname='historial',user='postgres',password='<DB_PASSWORD>',host='127.0.0.1'); cur=c.cursor(); cur.execute('SHOW max_connections'); mc=cur.fetchone()[0]; cur.execute('SHOW shared_buffers'); sb=cur.fetchone()[0]; print(''); print('   max_connections = ' + mc + '   (esperado: 300)'); print('   shared_buffers  = ' + sb + '   (esperado: 4GB)'); c.close()"

echo.
echo ================================================================
echo   LISTO
echo.
echo   Si max_connections dice 300, ahora puede anadir esta linea
echo   a Backend\.env para ganar 8x de velocidad en los listados:
echo.
echo       DB_CONN_MAX_AGE=60
echo.
echo   IMPORTANTE: solo despues de este reinicio. Antes, esa linea
echo   reintroduce los errores HTTP 500 por falta de conexiones.
echo ================================================================
echo.
pause
