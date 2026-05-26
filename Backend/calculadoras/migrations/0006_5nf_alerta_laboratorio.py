"""Migration 0006 — 5NF: AlertaLaboratorio table.

Problema de normalización (4NF/5NF):
  Hemograma.alertas, Bioquimica.alertas y MarcadorEmbarazo.alertas
  son JSONField(list) — atributos multivaluados que violan 4NF.

  4NF requiere que no existan dependencias multivaluadas en una tabla
  que no sean superclaves. Una lista de alertas [A1, A2, A3] para
  un Hemograma es exactamente eso.

Solución 5NF:
  AlertaLaboratorio(id, content_type, object_id, mensaje, severidad, fecha)
  — tabla de alertas genérica con FK polimórfico (ContentType) que
  sirve para cualquier modelo de laboratorio.

Los campos .alertas JSONField se conservan como caché desnormalizado
por compatibilidad con el código existente. Las nuevas funciones deben
usar AlertaLaboratorio.
"""
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("calculadoras", "0005_dopplermaterno"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="AlertaLaboratorio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                # FK polimórfico — sirve para Hemograma, Bioquimica, MarcadorEmbarazo, etc.
                (
                    "content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.contenttype",
                        verbose_name="Tipo de modelo",
                        help_text="Modelo al que pertenece esta alerta",
                        db_index=True,
                    ),
                ),
                (
                    "object_id",
                    models.PositiveBigIntegerField(
                        verbose_name="ID del registro",
                        db_index=True,
                    ),
                ),
                # Datos de la alerta (1 fila = 1 alerta atómica)
                (
                    "mensaje",
                    models.TextField(
                        verbose_name="Mensaje de alerta",
                        help_text="Texto completo de la alerta clínica",
                    ),
                ),
                (
                    "severidad",
                    models.CharField(
                        max_length=10,
                        choices=[
                            ("CRITICO", "Crítico"),
                            ("ALTO", "Alto"),
                            ("MEDIO", "Medio"),
                            ("BAJO", "Bajo"),
                            ("INFO", "Informativo"),
                        ],
                        default="MEDIO",
                        verbose_name="Severidad",
                        db_index=True,
                    ),
                ),
                (
                    "codigo",
                    models.CharField(
                        max_length=50,
                        blank=True,
                        default="",
                        verbose_name="Código de alerta",
                        help_text="Código interno para categorización (ej: ANEMIA_SEVERA)",
                        db_index=True,
                    ),
                ),
                (
                    "fecha",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        verbose_name="Fecha de generación",
                        db_index=True,
                    ),
                ),
                (
                    "procesada",
                    models.BooleanField(
                        default=False,
                        verbose_name="Procesada",
                        help_text="Indica si el médico revisó esta alerta",
                        db_index=True,
                    ),
                ),
                (
                    "procesada_por_id",
                    models.PositiveBigIntegerField(
                        null=True, blank=True,
                        verbose_name="ID del usuario que procesó",
                    ),
                ),
                (
                    "procesada_en",
                    models.DateTimeField(null=True, blank=True, verbose_name="Fecha de procesamiento"),
                ),
            ],
            options={
                "verbose_name": "Alerta de Laboratorio",
                "verbose_name_plural": "Alertas de Laboratorio",
                "db_table": "calculadoras_alerta_laboratorio",
                "ordering": ["-fecha", "-severidad"],
                "indexes": [
                    # Índice compuesto para lookup polimórfico eficiente
                    models.Index(
                        fields=["content_type", "object_id", "-fecha"],
                        name="alerta_lab_ct_obj_fecha_idx",
                    ),
                    models.Index(
                        fields=["severidad", "procesada", "-fecha"],
                        name="alerta_lab_sev_proc_idx",
                    ),
                ],
            },
        ),
    ]
