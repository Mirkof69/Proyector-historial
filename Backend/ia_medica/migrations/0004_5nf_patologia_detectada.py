"""Migration 0004 — 5NF: PatologiaDetectada y AlertaCNN.

Problema de normalización (4NF/5NF):
  AnalisisCNN.patologias = JSONField(list)  → lista de dicts independientes
  AnalisisCNN.alertas    = JSONField(list)  → lista de strings de alerta

  Cada patología detectada es un hecho atómico independiente:
    {pathology, confidence, icd10, recommendation, severity, requires_specialist}
  Guardarlas como lista JSON en una sola fila viola 1NF/4NF.

Solución 5NF:
  PatologiaDetectadaCNN(id, analisis_id FK, patologia, confianza, codigo_cie10,
                        descripcion, recomendacion, severidad, requiere_especialista)
  — 1 fila = 1 patología detectada (hecho atómico).

  AlertaCNNAnalisis(id, analisis_id FK, mensaje, severidad, codigo)
  — 1 fila = 1 alerta del análisis CNN (hecho atómico).

Los JSONField .patologias y .alertas se conservan como caché desnormalizado
por compatibilidad con el código existente.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("ia_medica", "0003_shap_gradcam_fields"),
    ]

    operations = [
        # ── PatologiaDetectadaCNN ─────────────────────────────────────────────
        migrations.CreateModel(
            name="PatologiaDetectadaCNN",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                (
                    "analisis",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="patologias_normalizadas",
                        to="ia_medica.analisiscnn",
                        verbose_name="Análisis CNN",
                        db_index=True,
                    ),
                ),
                (
                    "patologia",
                    models.CharField(
                        max_length=80,
                        verbose_name="Patología",
                        db_index=True,
                        help_text="Código interno de patología (ej: hidrocefalia, espina_bifida)",
                    ),
                ),
                (
                    "confianza",
                    models.FloatField(
                        verbose_name="Confianza",
                        help_text="Probabilidad sigmoid 0.0–1.0 del modelo",
                    ),
                ),
                (
                    "codigo_cie10",
                    models.CharField(
                        max_length=10,
                        blank=True,
                        default="",
                        verbose_name="Código CIE-10",
                    ),
                ),
                (
                    "descripcion",
                    models.TextField(
                        blank=True,
                        default="",
                        verbose_name="Descripción clínica",
                    ),
                ),
                (
                    "recomendacion",
                    models.TextField(
                        blank=True,
                        default="",
                        verbose_name="Recomendación médica",
                    ),
                ),
                (
                    "severidad",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("alta", "Alta"),
                            ("media-alta", "Media-Alta"),
                            ("media", "Media"),
                            ("baja", "Baja"),
                        ],
                        default="media",
                        verbose_name="Severidad",
                        db_index=True,
                    ),
                ),
                (
                    "requiere_especialista",
                    models.BooleanField(
                        default=False,
                        verbose_name="Requiere especialista",
                        db_index=True,
                    ),
                ),
            ],
            options={
                "verbose_name": "Patología Detectada CNN",
                "verbose_name_plural": "Patologías Detectadas CNN",
                "db_table": "ia_medica_patologia_detectada",
                "ordering": ["-confianza"],
                "constraints": [
                    # 5NF: una sola detección por patología por análisis
                    models.UniqueConstraint(
                        fields=["analisis", "patologia"],
                        name="uq_patologia_detectada_analisis",
                    ),
                ],
                "indexes": [
                    models.Index(fields=["patologia", "-confianza"], name="patologia_confianza_idx"),
                    models.Index(fields=["analisis", "severidad"], name="patologia_analisis_sev_idx"),
                ],
            },
        ),
        # ── AlertaCNNAnalisis ─────────────────────────────────────────────────
        migrations.CreateModel(
            name="AlertaCNNAnalisis",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                (
                    "analisis",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="alertas_normalizadas",
                        to="ia_medica.analisiscnn",
                        verbose_name="Análisis CNN",
                        db_index=True,
                    ),
                ),
                (
                    "mensaje",
                    models.TextField(verbose_name="Mensaje de alerta"),
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
                        verbose_name="Código interno",
                        db_index=True,
                    ),
                ),
                (
                    "procesada",
                    models.BooleanField(
                        default=False,
                        verbose_name="Procesada por médico",
                        db_index=True,
                    ),
                ),
            ],
            options={
                "verbose_name": "Alerta de Análisis CNN",
                "verbose_name_plural": "Alertas de Análisis CNN",
                "db_table": "ia_medica_alerta_cnn",
                "ordering": ["-severidad"],
                "indexes": [
                    models.Index(
                        fields=["analisis", "procesada", "-severidad"],
                        name="alerta_cnn_analisis_idx",
                    ),
                ],
            },
        ),
    ]
