@echo off
cls

echo ========================================
echo INSTALACION AUTOMATICA
echo Sistema de Historial Medico
echo ========================================
echo.

echo Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado
    echo Descarga desde: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

echo Verificando Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js no esta instalado
    echo Descarga desde: https://nodejs.org/
    pause
    exit /b 1
)
node --version
npm --version
echo.

echo ========================================
echo INSTALANDO BACKEND
echo ========================================
echo.

cd Backend\historial

echo Creando entorno virtual...
if exist venv rmdir /s /q venv
python -m venv venv
echo.

echo Activando entorno virtual...
call venv\Scripts\activate.bat
echo.

echo Actualizando pip...
python -m pip install --upgrade pip --quiet
echo.

echo Instalando dependencias de Python...
echo Esto puede tardar 5-10 minutos...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: No se pudieron instalar dependencias
    pause
    exit /b 1
)
echo.

echo Creando archivo .env...
if not exist .env (
    echo SECRET_KEY=django-insecure-change-this > .env
    echo DEBUG=True >> .env
    echo ALLOWED_HOSTS=localhost,127.0.0.1 >> .env
    echo CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000 >> .env
)
echo.

echo Aplicando migraciones...
python manage.py migrate
if errorlevel 1 (
    echo ERROR: No se pudieron aplicar migraciones
    pause
    exit /b 1
)
echo.

echo Creando usuario admin...
echo Username: admin
echo Password: admin123
python manage.py shell -c "from usuarios.models import Usuario; Usuario.objects.filter(username='admin').exists() or Usuario.objects.create_superuser('admin', 'admin@example.com', 'admin123', nombre='Admin', apellido='Sistema', rol='admin')" 2>nul
echo.

cd ..\..

echo ========================================
echo INSTALANDO FRONTEND
echo ========================================
echo.

cd frontend

echo Creando archivo .env...
if not exist .env (
    echo REACT_APP_API_URL=http://localhost:8000/api > .env
)
echo.

echo Instalando dependencias de Node.js...
echo Esto puede tardar 3-5 minutos...
npm install
if errorlevel 1 (
    echo ERROR: No se pudieron instalar dependencias
    pause
    exit /b 1
)
echo.

cd ..

cls
echo.
echo ========================================
echo INSTALACION COMPLETADA
echo ========================================
echo.
echo Backend: Instalado
echo Frontend: Instalado
echo Base de datos: Creada
echo Usuario: admin
echo Password: admin123
echo.
echo ========================================
echo PARA INICIAR EL SISTEMA
echo ========================================
echo.
echo 1. Ejecuta: start.bat
echo 2. Abre: http://localhost:3000
echo 3. Login: admin / admin123
echo.
echo ========================================
pause
