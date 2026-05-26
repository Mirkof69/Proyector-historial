"""Migration 0002: AuditLog BD-level append-only enforcement.

Changes:
  1. registro_id: IntegerField → CharField(max_length=64) para soportar UUID PKs
  2. REVOKE UPDATE, DELETE en auditoria_registros para el usuario de aplicación
     Esto hace el AuditLog inmutable a nivel de PostgreSQL (RM 1328 / ISO 27001)
"""

import re

from django.db import migrations, models


def revoke_auditlog_write_permissions(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        print("INFO: Revocación de permisos BD solo aplica a PostgreSQL. Saltando.")
        return
    db_user = schema_editor.connection.settings_dict.get("USER", "")
    if not db_user or not re.match(r"^[a-zA-Z0-9_]+$", db_user):
        print(f"WARN: Usuario BD '{db_user}' no válido para REVOKE. Saltando.")
        return
    try:
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(
                f'REVOKE UPDATE, DELETE ON TABLE auditoria_registros FROM "{db_user}";',
            )
        print(
            f"✅ UPDATE/DELETE revocados en auditoria_registros para usuario '{db_user}'.",
        )
    except Exception as e:
        print(f"WARN: REVOKE no aplicado (puede que ya estuviera revocado): {e}")


def restore_auditlog_write_permissions(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    db_user = schema_editor.connection.settings_dict.get("USER", "")
    if not db_user or not re.match(r"^[a-zA-Z0-9_]+$", db_user):
        return
    try:
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(
                f'GRANT UPDATE, DELETE ON TABLE auditoria_registros TO "{db_user}";',
            )
    except Exception as e:
        print(f"WARN: GRANT no aplicado: {e}")


class Migration(migrations.Migration):
    dependencies = [
        ("auditoria", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="registroauditoria",
            name="registro_id",
            field=models.CharField(
                max_length=64,
                help_text="ID del registro afectado (int o UUID)",
            ),
        ),
        migrations.RunPython(
            revoke_auditlog_write_permissions,
            reverse_code=restore_auditlog_write_permissions,
        ),
    ]
