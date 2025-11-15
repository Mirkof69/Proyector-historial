@echo off
REM ==============================================================================
REM SCRIPT DE INSTALACIÓN AUTOMÁTICA PARA WINDOWS
REM Sistema de Historial Médico Obstétrico
REM ==============================================================================

echo ==================================
echo INSTALACION AUTOMATICA
echo Sistema de Historial Medico
echo ==================================
echo.

REM ==============================================================================
REM VERIFICAR REQUISITOS
REM ==============================================================================

echo Verificando requisitos...
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado
    echo Descarga Python desde: https://www.python.org/downloads/
    pause
    exit /b 1
) else (
    python --version
)

REM Verificar pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip no esta instalado
    pause
    exit /b 1
) else (
    echo pip instalado
)

REM Verificar Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js no esta instalado
    echo Descarga Node.js desde: https://nodejs.org/
    pause
    exit /b 1
) else (
    node --version
)

REM Verificar npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm no esta instalado
    pause
    exit /b 1
) else (
    npm --version
)

echo.
echo ==================================
echo Todos los requisitos cumplidos
echo ==================================
echo.

REM ==============================================================================
REM INSTALACIÓN BACKEND
REM ==============================================================================

echo INSTALANDO BACKEND...
echo.

cd Backend\historial

REM Crear entorno virtual
echo Creando entorno virtual...
python -m venv venv

REM Activar entorno virtual
echo Activando entorno virtual...
call venv\Scripts\activate.bat

REM Actualizar pip
echo Actualizando pip...
python -m pip install --upgrade pip --quiet

REM Instalar dependencias
echo Instalando dependencias de Python (puede tardar 2-3 minutos)...
pip install -r requirements.txt --quiet

if errorlevel 1 (
    echo ERROR: Error instalando dependencias de Python
    pause
    exit /b 1
) else (
    echo Dependencias de Python instaladas
)

REM Crear archivo .env si no existe
if not exist .env (
    echo Creando archivo .env...
    (
        echo # Django
        echo SECRET_KEY=django-insecure-change-this-in-production-%RANDOM%
        echo DEBUG=True
        echo ALLOWED_HOSTS=localhost,127.0.0.1
        echo.
        echo # Base de datos ^(SQLite por defecto^)
        echo DATABASE_ENGINE=django.db.backends.sqlite3
        echo DATABASE_NAME=db.sqlite3
        echo.
        echo # CORS
        echo CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
        echo.
        echo # JWT
        echo ACCESS_TOKEN_LIFETIME=60
        echo REFRESH_TOKEN_LIFETIME=1440
    ) > .env
    echo Archivo .env creado
) else (
    echo Archivo .env ya existe, no se sobrescribe
)

REM Aplicar migraciones
echo Aplicando migraciones de base de datos...
python manage.py migrate

if errorlevel 1 (
    echo ERROR: Error aplicando migraciones
    pause
    exit /b 1
) else (
    echo Migraciones aplicadas correctamente
)

REM Crear superusuario
echo Creando superusuario por defecto...
echo    Username: admin
echo    Password: admin123
python manage.py shell < nul > nul 2>&1 << EOF
from django.contrib.auth import get_user_model
from usuarios.models import Usuario

User = Usuario
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123',
        nombre='Administrador',
        apellido='Sistema',
        rol='admin'
    )
    print('Superusuario creado exitosamente')
else:
    print('Superusuario ya existe')
EOF

echo Backend instalado correctamente
echo.

REM Volver al directorio raíz
cd ..\..

REM ==============================================================================
REM INSTALACIÓN FRONTEND
REM ==============================================================================

echo INSTALANDO FRONTEND...
echo.

cd frontend

REM Crear archivo .env si no existe
if not exist .env (
    echo Creando archivo .env para frontend...
    echo REACT_APP_API_URL=http://localhost:8000/api > .env
    echo Archivo .env creado
) else (
    echo Archivo .env ya existe, no se sobrescribe
)

REM Instalar dependencias
echo Instalando dependencias de Node.js (puede tardar 3-5 minutos)...
call npm install

if errorlevel 1 (
    echo ERROR: Error instalando dependencias de Node.js
    pause
    exit /b 1
) else (
    echo Dependencias de Node.js instaladas
)

cd ..

REM ==============================================================================
REM FINALIZACIÓN
REM ==============================================================================

echo.
echo ==================================
echo INSTALACION COMPLETADA
echo ==================================
echo.
echo CREDENCIALES DE ACCESO:
echo    Username: admin
echo    Password: admin123
echo.
echo PARA INICIAR EL SISTEMA:
echo.
echo Terminal 1 - Backend:
echo    cd Backend\historial
echo    venv\Scripts\activate
echo    python manage.py runserver
echo.
echo Terminal 2 - Frontend:
echo    cd frontend
echo    npm start
echo.
echo ACCESO:
echo    Frontend: http://localhost:3000
echo    Backend Admin: http://localhost:8000/admin
echo.
echo DOCUMENTACION:
echo    Ver GUIA_INSTALACION_COMPLETA.md para mas detalles
echo.
echo ==================================
pause
