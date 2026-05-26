"""Migration 0005 — 5NF: MedicionEcografia table.

Problema de normalización (4NF/5NF):
  ImagenEcografia.mediciones_incluidas = JSONField(dict)
  almacena múltiples mediciones biométricas como dict.
  Esto viola 1NF/4NF: varios hechos independientes en un solo campo.

  Por ejemplo: {"BPD": 82.3, "HC": 285.1, "FL": 61.2}
  son 3 hechos atómicos distintos que deben estar en 3 filas.

Solución 5NF:
  MedicionEcografia(id, imagen_id FK, tipo_medicion, valor_mm, valor_texto,
                    percentil, dentro_rango, fecha_medicion)
  — 1 fila = 1 medición atómica = 1 hecho indivisible (5NF compliant).

Nota sobre BiometriaFetal:
  El modelo BiometriaFetal (tabla biometria_fetal) ya almacena biometría
  por embarazo. MedicionEcografia es diferente: almacena las mediciones
  específicas registradas en una IMAGEN ecográfica particular con el
  valor exacto visto en esa imagen (puede diferir de la biometría del embarazo).
"""
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("ecografias", "0004_anatomiafetal_created_by_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="MedicionEcografia",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                (
                    "imagen",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="mediciones",
                        to="ecografias.imagenecografia",
                        verbose_name="Imagen ecográfica",
                        db_index=True,
                    ),
                ),
                # Tipo de medición — 1NF: una sola medición por fila
                (
                    "tipo_medicion",
                    models.CharField(
                        max_length=50,
                        choices=[
                            # Biometría fetal estándar
                            ("BPD", "Diámetro Biparietal (mm)"),
                            ("HC", "Circunferencia Cefálica (mm)"),
                            ("AC", "Circunferencia Abdominal (mm)"),
                            ("FL", "Longitud Femoral (mm)"),
                            ("HL", "Longitud Humeral (mm)"),
                            ("OFD", "Diámetro Occipito-Frontal (mm)"),
                            ("TCD", "Diámetro Transverso Cerebelar (mm)"),
                            ("CRL", "Longitud Cráneo-Caudal (mm)"),
                            ("NT", "Translucencia Nucal (mm)"),
                            # Placenta
                            ("GROSOR_PLACENTA", "Grosor Placenta (mm)"),
                            ("LONGITUD_CERVICAL", "Longitud Cervical (mm)"),
                            # Líquido amniótico
                            ("ILA", "Índice Líquido Amniótico (cm)"),
                            ("BOLSILLO_MAXIMO", "Bolsillo Máximo Vertical (cm)"),
                            # Doppler
                            ("IP_AU", "Índice de Pulsatilidad A. Umbilical"),
                            ("IR_AU", "Índice de Resistencia A. Umbilical"),
                            ("IP_ACM", "Índice de Pulsatilidad A. Cerebral Media"),
                            ("IP_DV", "Índice de Pulsatilidad Ductus Venosus"),
                            # Estimaciones
                            ("PESO_ESTIMADO", "Peso Fetal Estimado (g)"),
                            ("OTRO", "Otra medición"),
                        ],
                        verbose_name="Tipo de medición",
                        db_index=True,
                    ),
                ),
                # Valores — separados para mantener tipos de datos correctos (1NF/2NF)
                (
                    "valor_numerico",
                    models.DecimalField(
                        max_digits=8,
                        decimal_places=2,
                        null=True,
                        blank=True,
                        verbose_name="Valor numérico",
                        help_text="Valor medido en unidades estándar del tipo de medición",
                    ),
                ),
                (
                    "valor_texto",
                    models.CharField(
                        max_length=100,
                        blank=True,
                        default="",
                        verbose_name="Valor texto",
                        help_text="Para mediciones que no son numéricas",
                    ),
                ),
                # Contexto clínico — datos derivados importantes para la interpretación
                (
                    "percentil",
                    models.DecimalField(
                        max_digits=5,
                        decimal_places=2,
                        null=True,
                        blank=True,
                        verbose_name="Percentil",
                        help_text="Percentil según tablas OMS para edad gestacional",
                    ),
                ),
                (
                    "dentro_rango_normal",
                    models.BooleanField(
                        null=True,
                        blank=True,
                        verbose_name="Dentro de rango normal",
                        help_text="True=normal, False=fuera de rango, None=no determinado",
                    ),
                ),
                (
                    "edad_gestacional_semanas",
                    models.PositiveSmallIntegerField(
                        null=True,
                        blank=True,
                        verbose_name="Edad gestacional al medir (semanas)",
                        help_text="EG en el momento de esta medición específica",
                    ),
                ),
                (
                    "numero_feto",
                    models.PositiveSmallIntegerField(
                        default=1,
                        verbose_name="Número de feto",
                        help_text="1=único, 2=gemelo B, etc.",
                    ),
                ),
                (
                    "observaciones",
                    models.CharField(
                        max_length=200,
                        blank=True,
                        default="",
                        verbose_name="Observaciones",
                    ),
                ),
                (
                    "fecha_medicion",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        verbose_name="Fecha/hora de medición",
                        db_index=True,
                    ),
                ),
            ],
            options={
                "verbose_name": "Medición Ecográfica",
                "verbose_name_plural": "Mediciones Ecográficas",
                "db_table": "ecografias_medicion",
                "ordering": ["imagen", "tipo_medicion", "numero_feto"],
                "constraints": [
                    # 5NF: Una imagen no puede tener 2 mediciones del mismo tipo para el mismo feto
                    # (excepto OTRO). Esto garantiza que cada medición es un hecho único.
                    models.UniqueConstraint(
                        fields=["imagen", "tipo_medicion", "numero_feto"],
                        condition=~models.Q(tipo_medicion="OTRO"),
                        name="uq_medicion_imagen_tipo_feto",
                    ),
                ],
                "indexes": [
                    models.Index(
                        fields=["imagen", "tipo_medicion"],
                        name="medicion_imagen_tipo_idx",
                    ),
                    models.Index(
                        fields=["tipo_medicion", "dentro_rango_normal"],
                        name="medicion_tipo_rango_idx",
                    ),
                ],
            },
        ),
    ]
