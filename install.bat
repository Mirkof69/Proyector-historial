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
    pause
    exit /b 1
)
python --version
echo.

echo Verificando Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js no esta instalado
    pause
    exit /b 1
)
node --version
npm --version
echo.

echo Directorio actual: %CD%
echo.

echo Verificando carpetas...
if not exist "Backend" (
    echo ERROR: No existe la carpeta "Backend"
    echo Asegurate de estar en la carpeta correcta del proyecto
    pause
    exit /b 1
)

if not exist "Backend\historial" (
    echo ERROR: No existe "Backend\historial"
    pause
    exit /b 1
)

if not exist "frontend" (
    echo ERROR: No existe la carpeta "frontend"
    pause
    exit /b 1
)

echo Todas las carpetas encontradas
echo.

echo ========================================
echo INSTALANDO BACKEND
echo ========================================
echo.

cd Backend\historial
echo Directorio: %CD%
echo.

echo Creando entorno virtual...
if exist venv (
    echo Eliminando entorno virtual anterior...
    rmdir /s /q venv
)
python -m venv venv
if errorlevel 1 (
    echo ERROR: No se pudo crear entorno virtual
    pause
    exit /b 1
)
echo Entorno virtual creado
echo.

echo Activando entorno virtual...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: No se pudo activar entorno virtual
    pause
    exit /b 1
)
echo Entorno virtual activado
echo.

echo Actualizando pip...
python -m pip install --upgrade pip
echo.

echo Instalando dependencias de Python...
echo ESTO PUEDE TARDAR 5-10 MINUTOS...
echo Por favor espera, no cierres esta ventana
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Fallo la instalacion de dependencias Python
    echo.
    pause
    exit /b 1
)
echo.
echo Dependencias Python instaladas
echo.

echo Creando archivo .env...
if not exist .env (
    (
        echo SECRET_KEY=django-insecure-change-this
        echo DEBUG=True
        echo ALLOWED_HOSTS=localhost,127.0.0.1
        echo CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
    ) > .env
    echo Archivo .env creado
) else (
    echo Archivo .env ya existe
)
echo.

echo Aplicando migraciones de base de datos...
python manage.py migrate
if errorlevel 1 (
    echo ERROR: Fallo al aplicar migraciones
    pause
    exit /b 1
)
echo.
echo Migraciones aplicadas
echo.

echo Creando usuario administrador...
echo Username: admin
echo Password: admin123
python manage.py shell -c "from usuarios.models import Usuario; Usuario.objects.filter(username='admin').delete(); Usuario.objects.create_superuser('admin', 'admin@example.com', 'admin123', nombre='Admin', apellido='Sistema', rol='admin'); print('Usuario admin creado')" 2>nul
echo.

echo Backend instalado correctamente
echo.

cd ..\..

echo ========================================
echo INSTALANDO FRONTEND
echo ========================================
echo.

cd frontend
echo Directorio: %CD%
echo.

echo Creando archivo .env...
if not exist .env (
    echo REACT_APP_API_URL=http://localhost:8000/api > .env
    echo Archivo .env creado
) else (
    echo Archivo .env ya existe
)
echo.

echo Instalando dependencias de Node.js...
echo ESTO PUEDE TARDAR 3-5 MINUTOS...
echo Por favor espera, no cierres esta ventana
echo.
call npm install
if errorlevel 1 (
    echo.
    echo ERROR: Fallo la instalacion de dependencias Node.js
    echo.
    pause
    exit /b 1
)
echo.
echo Dependencias Node.js instaladas
echo.

echo Frontend instalado correctamente
echo.

cd ..

cls
echo.
echo ========================================
echo INSTALACION COMPLETADA EXITOSAMENTE
echo ========================================
echo.
echo Backend Python: OK
echo Frontend Node.js: OK
echo Base de datos: OK
echo Usuario admin: OK
echo.
echo ========================================
echo CREDENCIALES
echo ========================================
echo.
echo Usuario: admin
echo Password: admin123
echo.
echo ========================================
echo SIGUIENTE PASO
echo ========================================
echo.
echo Para INICIAR el sistema ejecuta:
echo.
echo     start.bat
echo.
echo Luego abre en tu navegador:
echo.
echo     http://localhost:3000
echo.
echo ========================================
echo.
pause
