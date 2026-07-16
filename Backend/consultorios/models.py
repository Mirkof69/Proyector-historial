"""=============================================================================
MÓDULO: CONSULTORIOS - MODELS
=============================================================================
Gestión de consultorios y espacios físicos
Para asignación de citas y control de ubicaciones
=============================================================================
"""

from django.db import models


class Consultorio(models.Model):
    """Consultorios y espacios físicos de la clínica
    """

    # ============== IDENTIFICACIÓN ==============
    nombre = models.CharField(
        max_length=50,
        unique=True,
        help_text="Nombre identificador del consultorio (ej: 'Consultorio 1')",
    )

    codigo = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text="Código interno (ej: 'CONS-01')",
    )

    # ============== UBICACIÓN ==============
    ubicacion = models.CharField(
        max_length=100, help_text="Descripción de ubicación general",
    )

    piso = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Piso o nivel (ej: 'Planta Baja', 'Piso 1')",
    )

    edificio = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Edificio (para clínicas con múltiples edificios)",
    )

    # ============== CARACTERÍSTICAS ==============
    tipo_consultorio = models.CharField(
        max_length=30,
        choices=[
            ("general", "Consulta General"),
            ("ginecologia", "Ginecología"),
            ("ecografia", "Ecografía"),
            ("laboratorio", "Laboratorio"),
            ("procedimientos", "Procedimientos"),
            ("urgencias", "Urgencias"),
        ],
        default="general",
    )

    capacidad_personas = models.PositiveIntegerField(
        default=3,
        help_text="Capacidad máxima de personas (incluyendo paciente y médico)",
    )

    tiene_bano = models.BooleanField(default=False)
    tiene_camilla = models.BooleanField(default=True)
    tiene_ecografo = models.BooleanField(default=False)

    # ============== EQUIPAMIENTO ==============
    equipamiento = models.TextField(
        null=True, blank=True, help_text="Lista de equipamiento disponible",
    )

    # ============== ESTADO ==============
    activo = models.BooleanField(
        default=True, help_text="Consultorio disponible para asignación",
    )

    en_mantenimiento = models.BooleanField(
        default=False, help_text="Consultorio temporalmente fuera de servicio",
    )

    observaciones = models.TextField(
        null=True, blank=True, help_text="Observaciones adicionales",
    )

    # ============== METADATOS ==============
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    # Trazabilidad
    created_by = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consultorios_creados",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consultorios_modificados",
        verbose_name="Modificado por",
    )

    class Meta:
        """Meta"""
        verbose_name = "Consultorio"
        verbose_name_plural = "Consultorios"
        db_table = "consultorios"
        ordering = ["nombre"]

    def __str__(self):
        """Str"""
        return f"{self.nombre} - {self.ubicacion}"

    def esta_disponible(self):
        """Verifica si el consultorio está disponible"""
        return self.activo and not self.en_mantenimiento

    def get_descripcion_completa(self):
        """Descripción completa del consultorio"""
        partes = [self.nombre]
        if self.piso:
            partes.append(f"Piso: {self.piso}")
        if self.edificio:
            partes.append(f"Edificio: {self.edificio}")
        partes.append(self.ubicacion)
        return " | ".join(partes)


class HorarioConsultorio(models.Model):
    """Horarios de atención por consultorio y día de la semana"""

    DIAS_SEMANA = [
        (0, "Lunes"),
        (1, "Martes"),
        (2, "Miércoles"),
        (3, "Jueves"),
        (4, "Viernes"),
        (5, "Sábado"),
        (6, "Domingo"),
    ]

    consultorio = models.ForeignKey(
        Consultorio, on_delete=models.CASCADE, related_name="horarios"
    )
    dia_semana = models.IntegerField(choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Horario de consultorio"
        verbose_name_plural = "Horarios de consultorios"
        db_table = "consultorios_horarios"
        ordering = ["dia_semana", "hora_inicio"]
        unique_together = ["consultorio", "dia_semana", "hora_inicio"]

    def __str__(self):
        return (
            f"{self.consultorio.nombre} - "
            f"{self.get_dia_semana_display()} {self.hora_inicio}-{self.hora_fin}"
        )


class OcupacionConsultorio(models.Model):
    """Registro de ocupación de un consultorio en un periodo de tiempo"""

    ESTADOS = [
        ("programada", "Programada"),
        ("en_curso", "En curso"),
        ("finalizada", "Finalizada"),
        ("cancelada", "Cancelada"),
    ]

    consultorio = models.ForeignKey(
        Consultorio, on_delete=models.CASCADE, related_name="ocupaciones"
    )
    paciente = models.ForeignKey(
        "pacientes.Paciente",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    medico = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ocupaciones_medico",
    )
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="programada")
    observaciones = models.TextField(null=True, blank=True)

    created_by = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ocupaciones_creadas",
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ocupación de consultorio"
        verbose_name_plural = "Ocupaciones de consultorios"
        db_table = "consultorios_ocupaciones"
        ordering = ["-fecha_inicio"]

    def __str__(self):
        return f"{self.consultorio.nombre} - {self.fecha_inicio}"


class ReservaConsultorio(models.Model):
    """Reservas anticipadas de consultorios"""

    ESTADOS = [
        ("pendiente", "Pendiente"),
        ("aprobada", "Aprobada"),
        ("rechazada", "Rechazada"),
        ("cancelada", "Cancelada"),
    ]

    consultorio = models.ForeignKey(
        Consultorio, on_delete=models.CASCADE, related_name="reservas"
    )
    paciente = models.ForeignKey(
        "pacientes.Paciente",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    medico = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservas_medico",
    )
    fecha_reserva = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    estado = models.CharField(
        max_length=20, choices=ESTADOS, default="pendiente"
    )
    observaciones = models.TextField(null=True, blank=True)

    created_by = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservas_creadas",
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Reserva de consultorio"
        verbose_name_plural = "Reservas de consultorios"
        db_table = "consultorios_reservas"
        ordering = ["-fecha_reserva", "hora_inicio"]

    def __str__(self):
        return (
            f"Reserva {self.consultorio.nombre} - "
            f"{self.fecha_reserva} {self.hora_inicio}"
        )


class MantenimientoConsultorio(models.Model):
    """Mantenimiento programado o correctivo de consultorios"""

    TIPOS = [
        ("preventivo", "Preventivo"),
        ("correctivo", "Correctivo"),
        ("limpieza", "Limpieza"),
        ("desinfeccion", "Desinfección"),
    ]
    ESTADOS = [
        ("pendiente", "Pendiente"),
        ("completado", "Completado"),
    ]

    consultorio = models.ForeignKey(
        Consultorio, on_delete=models.CASCADE, related_name="mantenimientos"
    )
    fecha_programada = models.DateTimeField()
    fecha_realizacion = models.DateTimeField(null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    descripcion = models.TextField()
    estado = models.CharField(
        max_length=20, choices=ESTADOS, default="pendiente"
    )
    realizado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mantenimientos_realizados",
    )

    created_by = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mantenimientos_creados",
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mantenimiento de consultorio"
        verbose_name_plural = "Mantenimientos de consultorios"
        db_table = "consultorios_mantenimientos"
        ordering = ["-fecha_programada"]

    def __str__(self):
        return (
            f"{self.consultorio.nombre} - "
            f"{self.get_tipo_display()} {self.fecha_programada}"
        )
