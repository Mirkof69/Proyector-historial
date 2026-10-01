@echo off
:: ============================================================================
:: Migraciones + datos de DEMOSTRACION - Fetal Medical Bolivia
::
::   Aplica las migraciones en todas las clinicas (migrate_schemas), carga la
::   demo (usuarios con clave Demo2026!) y muestra cuantos registros hay.
::   Los grupos de permisos por rol se sincronizan solos al migrar.
::   NO usar en el hospital: carga pacientes ficticios.
:: ============================================================================
title Fetal Medical - Migraciones y demo
color 0B
cd /d "%~dp0Backend"
set PY=.venv\Scripts\python.exe
if not exist "%PY%" (
    echo ERROR: no existe Backend\.venv. Cree el entorno e instale requirements.txt.
    pause
    exit /b 1
)

echo [1/3] Migraciones (todas las clinicas)...
"%PY%" manage.py migrate_schemas --noinput
if %errorlevel% neq 0 (echo ERROR en las migraciones & pause & exit /b 1)

echo [2/3] Datos de demostracion en clinica_demo...
"%PY%" manage.py tenant_command seed_demo --schema=clinica_demo
if %errorlevel% neq 0 (echo ERROR al cargar la demo & pause & exit /b 1)

echo [3/3] Estado de la base...
"%PY%" manage.py tenant_command shell --schema=clinica_demo -c "from pacientes.models import Paciente; from embarazos.models import Embarazo; from usuarios.models import Usuario; print('Pacientes', Paciente.objects.count(), '- embarazos', Embarazo.objects.count()); [print('  ', u.rol, u.email) for u in Usuario.objects.order_by('rol')]"

echo.
echo Listo. Arranque el sistema con INICIAR_SISTEMA.bat
pause
