# Base de Datos Historial

**Archivo:** historial_backup.sql
**Fecha:** 17/10/2025
**Tamaño:** 242 KB
**Base:** PostgreSQL 18
**Puerto:** 5433
**Contenido:** 35 tablas + funciones + vistas + triggers + datos

## Restaurar:
```bash
psql -U postgres -h localhost -p 5433 -d Historial -f historial_backup.sql
```