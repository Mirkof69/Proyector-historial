@echo off
REM ==============================================================================
REM SCRIPT PARA INICIAR EL SISTEMA COMPLETO EN WINDOWS
REM Sistema de Historial Médico Obstétrico
REM ==============================================================================

echo ==================================
echo INICIANDO SISTEMA
echo Sistema de Historial Medico
echo ==================================
echo.

REM Verificar que las instalaciones están completas
if not exist "Backend\historial\venv" (
    echo ERROR: Backend no esta instalado
    echo Ejecuta primero: install.bat
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo ERROR: Frontend no esta instalado
    echo Ejecuta primero: install.bat
    pause
    exit /b 1
)

echo Iniciando Backend...
start "Backend Server" cmd /k "cd Backend\historial && venv\Scripts\activate && python manage.py runserver"

timeout /t 5 /nobreak > nul

echo Iniciando Frontend...
start "Frontend Server" cmd /k "cd frontend && npm start"

echo.
echo ==================================
echo SISTEMA INICIADO
echo ==================================
echo.
echo ACCESO:
echo    Frontend: http://localhost:3000
echo    Backend Admin: http://localhost:8000/admin
echo.
echo CREDENCIALES:
echo    Username: admin
echo    Password: admin123
echo.
echo Para detener: Cierra las ventanas del Backend y Frontend
echo.
echo ==================================
pause
