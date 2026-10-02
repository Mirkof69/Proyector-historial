"""Cargos del hospital: otros funcionarios sin programar.

Antes este módulo tenía `CatRol`, un catálogo de los cinco roles con un campo
«permisos» que ningún código leía: el administrador marcaba permisos
(«recetar», «gestionar_roles»…) y no cambiaba nada. Ni siquiera dejaba crear un
nombre nuevo, porque el nombre estaba atado a los cinco roles fijos.

Un `Cargo` sí se aplica: se apoya en un rol del sistema (que decide lo que la
API permite) y elige qué módulos de ese rol usa. Ver usuarios/permisos_por_rol.py.
"""
from django.core.exceptions import ValidationError
from django.db import models

from usuarios.permisos_por_rol import NOMBRES_MODULO, modulos_del_cargo, validar_cargo

ROLES_BASE = [
    ("medico", "Médico"),
    ("enfermera", "Enfermería"),
    ("laboratorista", "Laboratorio"),
    ("recepcion", "Recepción"),
]


class Cargo(models.Model):
    """Un cargo (obstetriz, nutricionista…) sobre uno de los roles del sistema."""

    nombre = models.CharField(max_length=80, unique=True, verbose_name="Nombre del cargo")
    descripcion = models.TextField(blank=True, default="", verbose_name="Descripción")
    rol_base = models.CharField(max_length=20, choices=ROLES_BASE, verbose_name="Rol en que se basa")
    modulos = models.JSONField(default=list, blank=True, verbose_name="Módulos que usa")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cargos"
        verbose_name = "Cargo"
        verbose_name_plural = "Cargos"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    def clean(self):
        errores = validar_cargo(self.rol_base, self.modulos)
        if errores:
            raise ValidationError(errores)
        self.modulos = modulos_del_cargo(self.rol_base, self.modulos)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def nombres_modulos(self) -> list[str]:
        return [NOMBRES_MODULO.get(m, m) for m in self.modulos]
