@echo off
:: ============================================================================
:: Respaldo diario de la base de datos — Fetal Medical Bolivia
::
:: Crea backend\backups\backup_programado_AAAAMMDD_HHMMSS.sql con pg_dump y
:: borra los respaldos programados de mas de 30 dias. Si falla, sale con
:: codigo 1 y el Programador de tareas lo marca como error.
::
:: Programarlo una vez (todos los dias a las 02:00), en una consola de
:: administrador:
::   schtasks /create /tn "FetalMedical Respaldo" /sc daily /st 02:00 ^
::     /tr "\"%~f0\"" /ru SYSTEM
::
:: Restaurar un respaldo (en una base vacia):
::   createdb -U postgres historial_restaurada
::   psql -U postgres -d historial_restaurada -f backend\backups\<archivo>.sql
:: Verificado el 30/09/2026: 0 errores y las 5.192 pacientes restauradas.
::
:: Copiar la carpeta backend\backups a otro disco o equipo: un respaldo en el
:: mismo disco no protege de una falla del disco.
:: ============================================================================
cd /d "%~dp0..\backend"
".venv\Scripts\python.exe" manage.py respaldar_base --conservar 30 >> logs\respaldos.log 2>&1
exit /b %errorlevel%
