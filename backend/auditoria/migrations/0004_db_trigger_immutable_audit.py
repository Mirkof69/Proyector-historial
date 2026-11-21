"""
Migración: TRIGGER PostgreSQL para protección inmutable de auditoria_registros.
Refuerza a nivel de base de datos (no solo Python) la política append-only
requerida por Ley 164 Bolivia y RM 1328.
- Bloquea UPDATE en cualquier fila de auditoria_registros
- Bloquea DELETE en cualquier fila de auditoria_registros
"""

from django.db import migrations


TRIGGER_SQL = """
-- Función que levanta excepción ante cualquier modificación
CREATE OR REPLACE FUNCTION auditoria_enforce_immutable()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION
        'VIOLACIÓN DE SEGURIDAD [Ley 164 Bolivia]: '
        'Los registros de auditoría son inmutables. '
        'Operación % bloqueada en fila id=%. '
        'Este intento ha sido registrado.',
        TG_OP,
        COALESCE(OLD.id::text, 'desconocido');
    RETURN NULL;
END;
$$;

-- Trigger BEFORE UPDATE
DROP TRIGGER IF EXISTS trg_audit_no_update ON auditoria_registros;
CREATE TRIGGER trg_audit_no_update
    BEFORE UPDATE ON auditoria_registros
    FOR EACH ROW EXECUTE FUNCTION auditoria_enforce_immutable();

-- Trigger BEFORE DELETE
DROP TRIGGER IF EXISTS trg_audit_no_delete ON auditoria_registros;
CREATE TRIGGER trg_audit_no_delete
    BEFORE DELETE ON auditoria_registros
    FOR EACH ROW EXECUTE FUNCTION auditoria_enforce_immutable();
"""

ROLLBACK_SQL = """
DROP TRIGGER IF EXISTS trg_audit_no_update ON auditoria_registros;
DROP TRIGGER IF EXISTS trg_audit_no_delete ON auditoria_registros;
DROP FUNCTION IF EXISTS auditoria_enforce_immutable();
"""


def apply_trigger(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(TRIGGER_SQL)


def rollback_trigger(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(ROLLBACK_SQL)


class Migration(migrations.Migration):

    dependencies = [
        ("auditoria", "0003_extend_auditoria_model"),
    ]

    operations = [
        migrations.RunPython(
            apply_trigger,
            reverse_code=rollback_trigger,
        ),
    ]

