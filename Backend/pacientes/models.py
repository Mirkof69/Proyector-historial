"""Models module."""
from django.db import models

from .fields import EncryptedCharField, EncryptedEmailField, EncryptedTextField


class Paciente(models.Model):
    """Modelo de Paciente"""

    GENERO_CHOICES = (
        ("femenino", "Femenino"),
        ("masculino", "Masculino"),
        ("otro", "Otro"),
    )

    # Identificación
    id_clinico = models.CharField(
        max_length=50, unique=True, editable=False, verbose_name="ID Clínico",
    )

    # Datos personales (Cifrados en reposo AES-256)
    nombre = EncryptedCharField(max_length=255, verbose_name="Nombre")
    apellido_paterno = EncryptedCharField(
        max_length=255, verbose_name="Apellido Paterno",
    )
    apellido_materno = EncryptedCharField(
        max_length=255, blank=True, null=True, verbose_name="Apellido Materno",
    )
    fecha_nacimiento = models.DateField(verbose_name="Fecha de Nacimiento")
    genero = models.CharField(
        max_length=20, choices=GENERO_CHOICES, verbose_name="Género",
    )

    # Documentos
    ci = EncryptedCharField(
        max_length=255,
        verbose_name="Cédula de Identidad",
        # unique=True no funciona en campos Fernet (IV aleatorio → ciphertext diferente cada vez).
        # La unicidad real se garantiza con ci_hash (HMAC-SHA256 del valor plano).
    )
    ci_hash = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        null=True,
        blank=True,
        verbose_name="Hash CI (unicidad)",
        help_text="HMAC-SHA256 del CI en texto plano — usado para constraint de unicidad",
        db_index=True,
    )

    # Contacto
    telefono = EncryptedCharField(
        max_length=255, blank=True, null=True, verbose_name="Teléfono",
    )
    email = EncryptedEmailField(
        max_length=255, blank=True, null=True, verbose_name="Correo Electrónico",
    )

    # Dirección
    direccion = EncryptedTextField(blank=True, null=True, verbose_name="Dirección")
    ciudad = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Ciudad",
    )
    pais = models.CharField(max_length=100, default="Bolivia", verbose_name="País")

    # Información personal adicional
    estado_civil = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ("soltero", "Soltero/a"),
            ("casado", "Casado/a"),
            ("divorciado", "Divorciado/a"),
            ("viudo", "Viudo/a"),
            ("union_libre", "Unión Libre"),
        ],
        verbose_name="Estado Civil",
    )

    ocupacion = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Ocupación",
    )

    # ✅ NUEVOS CAMPOS - Contacto de emergencia
    contacto_emergencia_nombre = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Nombre del Contacto de Emergencia",
        help_text="Nombre completo de la persona a contactar en caso de emergencia",
    )

    contacto_emergencia_telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Teléfono de Emergencia",
        help_text="Teléfono del contacto de emergencia",
    )

    contacto_emergencia_relacion = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Relación con el Paciente",
        help_text="Ej: Esposo, Madre, Hermana, etc.",
    )

    # ✅ NUEVOS CAMPOS - Información médica adicional
    tipo_sangre = models.CharField(
        max_length=5,
        blank=True,
        null=True,
        choices=[
            ("A+", "A+"),
            ("A-", "A-"),
            ("B+", "B+"),
            ("B-", "B-"),
            ("O+", "O+"),
            ("O-", "O-"),
            ("AB+", "AB+"),
            ("AB-", "AB-"),
        ],
        verbose_name="Tipo de Sangre",
    )

    factor_rh = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        choices=[
            ("positivo", "Positivo"),
            ("negativo", "Negativo"),
        ],
        verbose_name="Factor RH",
    )

    numero_seguro_social = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Número de Seguro Social",
        help_text="Número de afiliación al seguro social",
    )

    # Estado del Paciente
    estado_paciente = models.CharField(
        max_length=20,
        choices=[
            ("activo", "Activo"),
            ("inactivo", "Inactivo"),
            ("fallecido", "Fallecido"),
        ],
        default="activo",
        verbose_name="Estado del Paciente",
    )
    fecha_baja = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de Baja del Sistema",
    )

    # Metadatos
    fecha_registro = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Registro",
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True, verbose_name="Última Actualización",
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")

    # Trazabilidad
    created_by = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pacientes_creados",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pacientes_modificados",
        verbose_name="Modificado por",
    )

    # Observaciones
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones",
    )

    # ✅ NUEVOS CAMPOS - Datos antropométricos
    peso_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Peso (kg)",
        help_text="Peso del paciente en kilogramos",
    )

    altura_cm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Altura (cm)",
        help_text="Altura del paciente en centímetros",
    )

    class Meta:
        """Meta"""
        db_table = "pacientes"
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"
        ordering = ["-fecha_registro"]
        indexes = [
            models.Index(fields=["ci"]),
            models.Index(fields=["id_clinico"]),
            models.Index(fields=["fecha_nacimiento"]),
            models.Index(fields=["estado_paciente"]),  # Nuevo índice
        ]
        constraints = [
            # La unicidad de CI se garantiza via ci_hash (HMAC-SHA256 del valor plano).
            # UniqueConstraint sobre 'ci' (campo Fernet) no funciona porque el ciphertext
            # varía en cada llamada (IV aleatorio). ci_hash tiene unique=True en el campo.
        ]

    def save(self, *args, **kwargs):
        """Genera ID clínico y ci_hash antes de guardar."""
        import uuid

        from .fields import compute_search_hash

        if not self.id_clinico:
            unique_id = str(uuid.uuid4().hex[:8].upper())
            self.id_clinico = f"PAC-{unique_id}"

        # Calcular HMAC-SHA256 del CI para constraint de unicidad real
        if self.ci:
            self.ci_hash = compute_search_hash(str(self.ci))

        super().save(*args, **kwargs)

    @property
    def nombre_completo(self):
        """Retorna el nombre completo del paciente"""
        if self.apellido_materno:
            return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}"
        return f"{self.nombre} {self.apellido_paterno}"

    @property
    def edad(self):
        """Calcula la edad del paciente"""
        from datetime import date

        today = date.today()
        return (
            today.year
            - self.fecha_nacimiento.year
            - (
                (today.month, today.day)
                < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
            )
        )

    @property
    def imc(self):
        """Calcula el Índice de Masa Corporal (IMC) del paciente"""
        if self.peso_kg and self.altura_cm:
            # IMC = peso (kg) / (altura (m))^2
            altura_m = float(self.altura_cm) / 100  # Convertir cm a metros
            imc_value = float(self.peso_kg) / (altura_m**2)
            return round(imc_value, 2)
        return None

    # ✅ NUEVOS MÉTODOS
    def get_embarazos_activos(self):
        """Obtiene los embarazos activos del paciente"""
        return self.embarazos.filter(estado="activo")

    def get_ultimo_control(self):
        """Obtiene el último control prenatal registrado"""
        # Seguro ante múltiples posibles relaciones reverse
        for rel in ("controles_prenatales", "controles_prenatales_set"):
            if hasattr(self, rel):
                manager = getattr(self, rel)
                try:
                    return manager.order_by("-fecha_control").first()
                except Exception:
                    continue
        return None

    def get_proxima_cita(self):
        """Obtiene la próxima cita agendada"""
        from django.utils import timezone

        return (
            self.citas.filter(
                fecha_cita__gte=timezone.now().date(),
                estado__in=["agendada", "confirmada"],
            )
            .order_by("fecha_cita", "hora_cita")
            .first()
        )

    def tiene_alergias(self):
        """Verifica si el paciente tiene alergias registradas"""
        antecedentes = self.antecedentes_patologicos.filter(tipo="alergia")
        return antecedentes.exists()

    def get_contacto_emergencia_completo(self):
        """Obtiene la información completa del contacto de emergencia"""
        if self.contacto_emergencia_nombre:
            return f"{self.contacto_emergencia_nombre} ({self.contacto_emergencia_relacion}) - {self.contacto_emergencia_telefono}"
        return "No registrado"

    def __str__(self):
        """Str"""
        return f"{self.nombre_completo} - {self.ci}"
