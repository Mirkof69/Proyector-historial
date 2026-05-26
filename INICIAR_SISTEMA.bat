@echo off
title Fetal Medical Bolivia — Inicio del Sistema
color 0A
echo.
echo ================================================
echo    FETAL MEDICAL BOLIVIA — INICIANDO SISTEMA
echo ================================================
echo.

:: ── 1. PostgreSQL ────────────────────────────────
echo [1/5] Iniciando PostgreSQL...
net start postgresql-x64-18 >nul 2>&1
if %errorlevel% equ 0 (
    echo     OK PostgreSQL iniciado
) else (
    echo     OK PostgreSQL ya estaba corriendo
)
timeout /t 2 /nobreak >nul

:: ── 2. Migrar BD ────────────────────────────────
echo [2/5] Aplicando migraciones...
cd /d "%~dp0Backend"
python manage.py migrate --run-syncdb 2>&1 | findstr /v "^$\|Applying\|Unapplied"
if %errorlevel% equ 0 echo     OK Migraciones aplicadas
timeout /t 1 /nobreak >nul

:: ── 3. Django check ─────────────────────────────
echo [3/5] Verificando Django...
python manage.py check >nul 2>&1
if %errorlevel% equ 0 (
    echo     OK Django check: 0 errores
) else (
    echo     ERROR en Django check — ver log
)

:: ── 4. Backend Django ───────────────────────────
echo [4/5] Iniciando backend Django (puerto 8000)...
start "Django Backend" cmd /k "cd /d %~dp0Backend && python manage.py runserver 0.0.0.0:8000"
timeout /t 3 /nobreak >nul

:: ── 5. Frontend React ───────────────────────────
echo [5/5] Iniciando frontend React (puerto 3000)...
start "React Frontend" cmd /k "cd /d %~dp0Backend\frontend && npm start"

echo.
echo ================================================
echo  Sistema iniciado:
echo    Backend:  http://localhost:8000
echo    Frontend: http://localhost:3000
echo    Admin:    http://localhost:8000/admin
echo    API Docs: http://localhost:8000/api/docs/
echo.
echo  Usuarios demo:
echo    Medico:     dra.garcia@fetalmedical.bo / Demo2026!
echo    Enfermera:  enf.mamani@fetalmedical.bo / Demo2026!
echo    Recepcion:  recep.flores@fetalmedical.bo / Demo2026!
echo ================================================
echo.
echo Presiona cualquier tecla para cerrar esta ventana...
pause >nul
