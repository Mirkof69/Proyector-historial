@echo off
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║          FETAL MEDICAL AI — SISTEMA COMPLETO                    ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

:: ── 0. Verificar que estamos en el directorio correcto ─────────────────────
set ROOT=%~dp0
cd /d "%ROOT%"

:: ── 1. PostgreSQL ──────────────────────────────────────────────────────────
echo [1/6] Verificando PostgreSQL...
"C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe" status -D "C:\Program Files\PostgreSQL\18\data" >nul 2>&1
if errorlevel 1 (
    start /b "" "C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe" start -D "C:\Program Files\PostgreSQL\18\data" -l "%TEMP%\pg_startup.log"
    timeout /t 4 /nobreak >nul
    echo   [OK] PostgreSQL iniciado
) else (
    echo   [OK] PostgreSQL ya estaba corriendo
)

:: ── 2. Redis ───────────────────────────────────────────────────────────────
echo [2/6] Verificando Redis (broker Celery)...
sc query Redis >nul 2>&1
if errorlevel 1 (
    :: Redis como proceso directo si el servicio no existe
    where redis-server >nul 2>&1
    if not errorlevel 1 (
        start /b "" redis-server
        timeout /t 2 /nobreak >nul
        echo   [OK] Redis iniciado como proceso
    ) else (
        echo   [WARN] Redis no encontrado. Celery funcionara en modo degradado.
        echo         Descarga: https://github.com/microsoftarchive/redis/releases
    )
) else (
    net start Redis >nul 2>&1
    echo   [OK] Servicio Redis iniciado
)

:: ── 3. Django Backend ──────────────────────────────────────────────────────
echo [3/6] Iniciando Django Backend (puerto 8000)...
start "Django Backend :8000" cmd /k "cd /d "%ROOT%Backend" && python manage.py runserver 8000"
timeout /t 3 /nobreak >nul
echo   [OK] Django: http://127.0.0.1:8000

:: ── 4. FastAPI Microservicio IA ────────────────────────────────────────────
echo [4/6] Iniciando Microservicio IA (puerto 8001)...
start "Microservicio IA :8001" cmd /k "cd /d "%ROOT%Backend\Microservicio_IA" && set PYTHONIOENCODING=utf-8 && python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload"
timeout /t 3 /nobreak >nul
echo   [OK] IA API: http://127.0.0.1:8001/docs

:: ── 5. Celery Worker ──────────────────────────────────────────────────────
echo [5/6] Iniciando Celery Worker (broker: Redis)...
start "Celery Worker" cmd /k "cd /d "%ROOT%Backend" && set DJANGO_SETTINGS_MODULE=settings && celery -A celery_app worker --loglevel=info -P solo"
timeout /t 2 /nobreak >nul
echo   [OK] Celery worker iniciado

:: ── 6. React Frontend ──────────────────────────────────────────────────────
echo [6/6] Iniciando Frontend React (puerto 3000)...
start "React Frontend :3000" cmd /k "cd /d "%ROOT%Backend\frontend" && npm start"
timeout /t 2 /nobreak >nul
echo   [OK] Frontend: http://localhost:3000

echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║  SISTEMA LISTO — URLs de Acceso                                  ║
echo ╠══════════════════════════════════════════════════════════════════╣
echo ║  Frontend React:       http://localhost:3000                     ║
echo ║  Django Backend API:   http://127.0.0.1:8000/api/               ║
echo ║  Django Admin:         http://127.0.0.1:8000/admin/             ║
echo ║  Microservicio IA:     http://127.0.0.1:8001/docs               ║
echo ╠══════════════════════════════════════════════════════════════════╣
echo ║  Credenciales Admin:   MirkofAdmin@fetalmedical.com / 25693      ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.
echo  Presiona cualquier tecla para cerrar esta ventana.
echo  Los servidores seguiran corriendo en sus ventanas individuales.
pause >nul
