"""CAT_ROLES - MODELS"""

from django.db import models


class CatRol(models.Model):
    """Catálogo de roles del sistema"""

    # Debe coincidir con usuarios.models.Usuario.ROLES (la fuente real de
    # roles que se asignan a cada usuario). Antes este catalogo tenia un
    # conjunto distinto e incompleto ("administrativo" no es un rol real;
    # faltaban laboratorista, administrador y recepcion).
    ROLES = [
        ("medico", "Médico"),
        ("enfermera", "Enfermera"),
        ("laboratorista", "Laboratorista"),
        ("administrador", "Administrador"),
        ("recepcion", "Recepción"),
    ]

    nombre = models.CharField(max_length=30, unique=True, choices=ROLES)
    descripcion = models.TextField()
    permisos = models.JSONField(
        default=dict, help_text="Permisos específicos del rol en formato JSON",
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta"""
        db_table = "cat_roles"
        verbose_name = "Rol"
        verbose_name_plural = "Roles"

    def __str__(self):
        """Str"""
        return getattr(self, 'get_nombre_display')()
