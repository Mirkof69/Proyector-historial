@echo off
setlocal enabledelayedexpansion

cls
echo ========================================
echo INSTALACION AUTOMATICA
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no instalado
    pause
    exit /b 1
)

node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js no instalado
    pause
    exit /b 1
)

echo Python: OK
echo Node.js: OK
echo.
echo Iniciando instalacion...
echo.

REM ===== BACKEND =====
echo [1/6] Instalando Backend...
cd Backend\historial

echo [2/6] Creando entorno virtual Python...
if exist venv rmdir /s /q venv
python -m venv venv
call venv\Scripts\activate.bat

echo [3/6] Instalando librerias Python (5-10 min)...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo [4/6] Configurando base de datos...
if not exist .env (
    echo SECRET_KEY=django-insecure-change-this>.env
    echo DEBUG=True>>.env
    echo ALLOWED_HOSTS=localhost,127.0.0.1>>.env
    echo CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000>>.env
)

python manage.py migrate --noinput

echo [5/6] Creando usuario admin...
python manage.py shell -c "from usuarios.models import Usuario; u=Usuario.objects.filter(username='admin'); u.delete() if u.exists() else None; Usuario.objects.create_superuser('admin','admin@example.com','admin123',nombre='Admin',apellido='Sistema',rol='admin')"

cd ..\..

REM ===== FRONTEND =====
echo [6/6] Instalando Frontend (3-5 min)...
cd frontend

if not exist .env (
    echo REACT_APP_API_URL=http://localhost:8000/api>.env
)

call npm install

cd ..

cls
echo.
echo ========================================
echo INSTALACION COMPLETADA
echo ========================================
echo.
echo Backend: INSTALADO
echo Frontend: INSTALADO
echo Usuario: admin
echo Password: admin123
echo.
echo Ejecuta: start.bat
echo Accede: http://localhost:3000
echo.
echo ========================================
pause
