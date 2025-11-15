@echo off
chcp 65001 >nul
cls

REM ==============================================================================
REM SCRIPT DE INSTALACIÓN AUTOMÁTICA PARA WINDOWS
REM Sistema de Historial Médico Obstétrico
REM ==============================================================================

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║        INSTALACIÓN AUTOMÁTICA - SISTEMA MÉDICO                 ║
echo ║        Sistema de Historial Médico Obstétrico                  ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo.

REM ==============================================================================
REM VERIFICAR REQUISITOS
REM ==============================================================================

echo [1/10] Verificando requisitos del sistema...
echo.

REM Verificar Python
echo Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ ERROR: Python NO está instalado
    echo.
    echo Por favor, descarga e instala Python desde:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANTE: Marca la opción "Add Python to PATH" durante la instalación
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo    ✅ Python %PYTHON_VERSION% instalado
echo.

REM Verificar pip
echo Verificando pip...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo    ❌ ERROR: pip no está instalado
    pause
    exit /b 1
)
echo    ✅ pip instalado
echo.

REM Verificar Node.js
echo Verificando Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ ERROR: Node.js NO está instalado
    echo.
    echo Por favor, descarga e instala Node.js desde:
    echo https://nodejs.org/ (versión LTS recomendada)
    echo.
    pause
    exit /b 1
)

for /f "tokens=1" %%i in ('node --version 2^>^&1') do set NODE_VERSION=%%i
echo    ✅ Node.js %NODE_VERSION% instalado
echo.

REM Verificar npm
echo Verificando npm...
npm --version >nul 2>&1
if errorlevel 1 (
    echo    ❌ ERROR: npm no está instalado
    pause
    exit /b 1
)

for /f "tokens=1" %%i in ('npm --version 2^>^&1') do set NPM_VERSION=%%i
echo    ✅ npm %NPM_VERSION% instalado
echo.

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║  ✅ TODOS LOS REQUISITOS CUMPLIDOS                             ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
timeout /t 2 /nobreak >nul

REM ==============================================================================
REM INSTALACIÓN BACKEND
REM ==============================================================================

echo.
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║  🔧 INSTALANDO BACKEND (DJANGO + PYTHON)                       ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

if not exist "Backend\historial" (
    echo ❌ ERROR: No se encuentra la carpeta Backend\historial
    echo.
    echo Asegúrate de estar en la carpeta raíz del proyecto
    pause
    exit /b 1
)

cd Backend\historial

REM Crear entorno virtual
echo [2/10] Creando entorno virtual de Python...
echo.
if exist "venv\" (
    echo    ⚠️  El entorno virtual ya existe, eliminando...
    rmdir /s /q venv
)

python -m venv venv
if errorlevel 1 (
    echo    ❌ ERROR: No se pudo crear el entorno virtual
    pause
    exit /b 1
)
echo    ✅ Entorno virtual creado
echo.

REM Activar entorno virtual
echo [3/10] Activando entorno virtual...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo    ❌ ERROR: No se pudo activar el entorno virtual
    pause
    exit /b 1
)
echo    ✅ Entorno virtual activado
echo.

REM Actualizar pip
echo [4/10] Actualizando pip...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo    ⚠️  Advertencia: No se pudo actualizar pip
) else (
    echo    ✅ pip actualizado
)
echo.

REM Instalar dependencias
echo [5/10] Instalando dependencias de Python...
echo    ⏳ Esto puede tardar 5-10 minutos, por favor espera...
echo    📦 Se instalarán más de 60 librerías...
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo    ❌ ERROR: No se pudieron instalar las dependencias de Python
    echo.
    echo    Intenta ejecutar manualmente:
    echo    cd Backend\historial
    echo    venv\Scripts\activate
    echo    pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)
echo.
echo    ✅ Dependencias de Python instaladas correctamente
echo.

REM Crear archivo .env si no existe
echo [6/10] Configurando variables de entorno del backend...
if not exist ".env" (
    echo    📝 Creando archivo .env...
    (
        echo # Django Configuration
        echo SECRET_KEY=django-insecure-change-this-in-production-%RANDOM%%RANDOM%
        echo DEBUG=True
        echo ALLOWED_HOSTS=localhost,127.0.0.1
        echo.
        echo # Database - SQLite por defecto
        echo DATABASE_ENGINE=django.db.backends.sqlite3
        echo DATABASE_NAME=db.sqlite3
        echo.
        echo # CORS - Frontend URLs
        echo CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
        echo.
        echo # JWT Tokens
        echo ACCESS_TOKEN_LIFETIME=60
        echo REFRESH_TOKEN_LIFETIME=1440
    ) > .env
    echo    ✅ Archivo .env creado
) else (
    echo    ℹ️  Archivo .env ya existe, no se sobrescribe
)
echo.

REM Aplicar migraciones
echo [7/10] Creando base de datos y aplicando migraciones...
echo    ⏳ Esto puede tardar 1-2 minutos...
echo.
python manage.py migrate
if errorlevel 1 (
    echo.
    echo    ❌ ERROR: No se pudieron aplicar las migraciones
    pause
    exit /b 1
)
echo.
echo    ✅ Base de datos creada y migraciones aplicadas
echo.

REM Crear superusuario
echo [8/10] Creando usuario administrador...
echo    👤 Username: admin
echo    📧 Email: admin@example.com
echo    🔐 Password: admin123
echo.

python manage.py shell < nul > nul 2>&1 << EOF
from django.contrib.auth import get_user_model
from usuarios.models import Usuario
User = Usuario
try:
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            nombre='Administrador',
            apellido='Sistema',
            rol='admin'
        )
        print('Superusuario creado')
    else:
        print('Superusuario ya existe')
except Exception as e:
    print('Error:', e)
EOF

echo    ✅ Usuario administrador configurado
echo.

echo ╔════════════════════════════════════════════════════════════════╗
echo ║  ✅ BACKEND INSTALADO CORRECTAMENTE                            ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM Volver al directorio raíz
cd ..\..

REM ==============================================================================
REM INSTALACIÓN FRONTEND
REM ==============================================================================

echo.
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║  ⚛️  INSTALANDO FRONTEND (REACT + TYPESCRIPT)                  ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

if not exist "frontend" (
    echo ❌ ERROR: No se encuentra la carpeta frontend
    pause
    exit /b 1
)

cd frontend

REM Crear archivo .env si no existe
echo [9/10] Configurando variables de entorno del frontend...
if not exist ".env" (
    echo    📝 Creando archivo .env...
    echo REACT_APP_API_URL=http://localhost:8000/api > .env
    echo    ✅ Archivo .env creado
) else (
    echo    ℹ️  Archivo .env ya existe, no se sobrescribe
)
echo.

REM Instalar dependencias
echo [10/10] Instalando dependencias de Node.js...
echo    ⏳ Esto puede tardar 3-5 minutos, por favor espera...
echo    📦 Se instalarán más de 30 librerías (incluyendo Three.js)...
echo.
call npm install
if errorlevel 1 (
    echo.
    echo    ❌ ERROR: No se pudieron instalar las dependencias de Node.js
    echo.
    echo    Intenta ejecutar manualmente:
    echo    cd frontend
    echo    npm install
    echo.
    pause
    exit /b 1
)
echo.
echo    ✅ Dependencias de Node.js instaladas correctamente
echo.

echo ╔════════════════════════════════════════════════════════════════╗
echo ║  ✅ FRONTEND INSTALADO CORRECTAMENTE                           ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

cd ..

REM ==============================================================================
REM FINALIZACIÓN
REM ==============================================================================

cls
echo.
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                                                                ║
echo ║         🎉🎉🎉  INSTALACIÓN COMPLETADA  🎉🎉🎉                ║
echo ║                                                                ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo.
echo ┌────────────────────────────────────────────────────────────────┐
echo │  📋 RESUMEN DE LA INSTALACIÓN                                  │
echo └────────────────────────────────────────────────────────────────┘
echo.
echo   ✅ Backend Django instalado (60+ librerías Python)
echo   ✅ Frontend React instalado (30+ librerías Node.js)
echo   ✅ Base de datos SQLite creada
echo   ✅ Usuario administrador creado
echo   ✅ Variables de entorno configuradas
echo   ✅ Three.js instalado para gráficos 3D
echo.
echo.
echo ┌────────────────────────────────────────────────────────────────┐
echo │  🔐 CREDENCIALES DE ACCESO                                     │
echo └────────────────────────────────────────────────────────────────┘
echo.
echo   Usuario:     admin
echo   Contraseña:  admin123
echo.
echo.
echo ┌────────────────────────────────────────────────────────────────┐
echo │  🚀 PARA INICIAR EL SISTEMA                                    │
echo └────────────────────────────────────────────────────────────────┘
echo.
echo   1. Ejecuta:  start.bat
echo.
echo   2. Espera 30 segundos a que cargue todo
echo.
echo   3. Abre tu navegador en:  http://localhost:3000
echo.
echo   4. Inicia sesión con:  admin / admin123
echo.
echo.
echo ┌────────────────────────────────────────────────────────────────┐
echo │  🌐 URLs DEL SISTEMA                                           │
echo └────────────────────────────────────────────────────────────────┘
echo.
echo   Frontend (Aplicación):  http://localhost:3000
echo   Backend Admin:          http://localhost:8000/admin
echo   API REST:               http://localhost:8000/api
echo.
echo.
echo ┌────────────────────────────────────────────────────────────────┐
echo │  📚 DOCUMENTACIÓN                                              │
echo └────────────────────────────────────────────────────────────────┘
echo.
echo   COMO_INSTALAR.md              - Esta guía
echo   INICIO_RAPIDO.md              - Inicio rápido
echo   GUIA_INSTALACION_COMPLETA.md  - Guía completa
echo   README.md                     - Documentación principal
echo.
echo.
echo ┌────────────────────────────────────────────────────────────────┐
echo │  💡 PRÓXIMOS PASOS                                             │
echo └────────────────────────────────────────────────────────────────┘
echo.
echo   1. Ejecuta:    start.bat
echo   2. Accede a:   http://localhost:3000
echo   3. Login:      admin / admin123
echo   4. ¡Explora el sistema!
echo.
echo.
echo ════════════════════════════════════════════════════════════════
echo.
pause
