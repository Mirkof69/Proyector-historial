# scripts

Lanzadores de operación. El arranque diario es `..\INICIAR.bat`; estos se usan aparte.

| Archivo | Para qué sirve |
|---|---|
| `RESPALDO_DIARIO.bat` | Respaldo de la base con `pg_dump` en `backend\backups\` (lo ejecuta la tarea programada «FetalMedical Respaldo») |
| `APLICAR_AJUSTES_POSTGRES.bat` | Ajustes de rendimiento de PostgreSQL; se ejecuta como administrador |
| `instalar_postgres.ps1` | Instalación guiada de PostgreSQL |
| `MIGRAR_Y_SEED.bat` | Solo para una base de desarrollo: migra y carga datos de demostración |
| `PUBLICAR_WEB.bat` | Publica el sistema por Internet con el túnel de `..\infraestructura\tunel` (local, fuera de Git) |
