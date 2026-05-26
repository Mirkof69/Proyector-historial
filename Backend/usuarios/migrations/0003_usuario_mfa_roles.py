from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("usuarios", "0002_usuario_descripcion_usuario_foto_horarioatencion"),
    ]

    operations = [
        # Expandir choices de rol (no cambia la columna, solo Django-level)
        migrations.AlterField(
            model_name="usuario",
            name="rol",
            field=models.CharField(
                max_length=20,
                choices=[
                    ("medico", "Médico"),
                    ("enfermera", "Enfermera"),
                    ("laboratorista", "Laboratorista"),
                    ("administrador", "Administrador"),
                    ("recepcion", "Recepción"),
                ],
                verbose_name="Rol",
            ),
        ),
        # Campos MFA
        migrations.AddField(
            model_name="usuario",
            name="mfa_enabled",
            field=models.BooleanField(default=False, verbose_name="MFA Activado"),
        ),
        migrations.AddField(
            model_name="usuario",
            name="mfa_secret",
            field=models.CharField(
                blank=True, max_length=64, null=True, verbose_name="Secreto MFA",
            ),
        ),
        migrations.AddField(
            model_name="usuario",
            name="intentos_fallidos",
            field=models.PositiveSmallIntegerField(
                default=0, verbose_name="Intentos fallidos de login",
            ),
        ),
        migrations.AddField(
            model_name="usuario",
            name="bloqueado_hasta",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="Bloqueado hasta",
            ),
        ),
        migrations.AddField(
            model_name="usuario",
            name="ultimo_login_ip",
            field=models.GenericIPAddressField(
                blank=True, null=True, verbose_name="Última IP de acceso",
            ),
        ),
    ]
