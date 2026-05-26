@echo off
title Fetal Medical — Migraciones y Seed Data
color 0B
echo.
echo ================================================
echo   FETAL MEDICAL — MIGRAR BD + SEED DEMO
echo ================================================
echo.
cd /d "%~dp0Backend"

echo [1/4] Aplicando TODAS las migraciones...
python manage.py migrate 2>&1
echo.

echo [2/4] Migracion especifica auditoria (trigger BD)...
python manage.py migrate auditoria 2>&1
echo.

echo [3/4] Verificando Django check...
python manage.py check
echo.

echo [4/4] Ejecutando seed de datos demo...
python manage.py seed_demo 2>&1
echo.

echo ================================================
echo  Verificando estado final de la BD...
echo ================================================
python manage.py shell -c "
import django
from django_tenants.utils import schema_context

with schema_context('clinica_demo'):
    from pacientes.models import Paciente
    from embarazos.models import Embarazo
    from controles.models import ControlPrenatal
    from ia_medica.models import AnalisisCNN, PatologiaDetectadaCNN, AlertaCNNAnalisis
    from calculadoras.models import AlertaLaboratorio, MedicionEcografica
    from auditoria.models import RegistroAuditoria

    print('')
    print('ESTADO BD — clinica_demo')
    print('='*50)
    print(f'Pacientes:              {Paciente.objects.count()}')
    print(f'Embarazos activos:      {Embarazo.objects.filter(estado=\"activo\").count()}')
    print(f'Embarazos finalizados:  {Embarazo.objects.filter(estado=\"finalizado\").count()}')
    print(f'Controles prenatales:   {ControlPrenatal.objects.count()}')
    print(f'Analisis CNN:           {AnalisisCNN.objects.count()}')
    print(f'PatologiaDetectadaCNN:  {PatologiaDetectadaCNN.objects.count()}')
    print(f'AlertaCNNAnalisis:      {AlertaCNNAnalisis.objects.count()}')
    print(f'AlertaLaboratorio 5NF:  {AlertaLaboratorio.objects.count()}')
    print(f'MedicionEcografica 5NF: {MedicionEcografica.objects.count()}')
    print('='*50)

from usuarios.models import Usuario
print('')
print('USUARIOS DEL SISTEMA:')
for u in Usuario.objects.all():
    print(f'  {u.rol:15} {u.email}')
print('')
"

echo.
echo ================================================
echo  Migracion y seed completados.
echo  Puedes iniciar el sistema con INICIAR_SISTEMA.bat
echo ================================================
pause
