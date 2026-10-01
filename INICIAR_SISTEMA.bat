@echo off
:: ============================================================================
:: Arranque de DESARROLLO — Fetal Medical Bolivia
:: (Para el hospital usar INICIAR_PRODUCCION.bat: build real y 8 workers.)
::
::   Backend   uvicorn ASGI con recarga (runserver es WSGI: los WebSockets de
::             notificaciones daban 404 en /ws/)
::   IA        microservicio FastAPI en 8001 (Python del sistema, con torch)
::   Frontend  servidor de desarrollo de React en 3000
:: ============================================================================
title Fetal Medical Bolivia - DESARROLLO
color 0A

echo [1/4] PostgreSQL...
net start postgresql-x64-18 >nul 2>&1
if %errorlevel% equ 0 (echo     OK iniciado) else (echo     OK ya estaba corriendo)
timeout /t 2 /nobreak >nul

echo [2/4] Migraciones (todas las clinicas)...
cd /d "%~dp0Backend"
".venv\Scripts\python.exe" manage.py migrate_schemas --noinput > logs\migraciones.log 2>&1
if %errorlevel% equ 0 (echo     OK al dia) else (
    echo     ERROR en las migraciones: ver Backend\logs\migraciones.log
    pause
    exit /b 1
)

echo [3/4] Backend (8000) y microservicio de IA (8001)...
start "Backend Django (ASGI)" cmd /k "cd /d %~dp0Backend && .venv\Scripts\python.exe -m uvicorn asgi:application --host 127.0.0.1 --port 8000 --reload"
start "Microservicio IA" cmd /k "cd /d %~dp0Backend\Microservicio_IA && python -m uvicorn app.main:app --host 127.0.0.1 --port 8001"

echo [4/4] Frontend (3000)...
start "React Frontend" cmd /k "cd /d %~dp0Backend\frontend && npm start"

echo.
echo   Frontend       http://localhost:3000
echo   API            http://localhost:8000/api/
echo   Salud de IA    http://localhost:8001/health
echo   Pruebas E2E    cd Backend\e2e ^&^& npx playwright test
echo.
pause
