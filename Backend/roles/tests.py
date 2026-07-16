"""Tests para el módulo de Roles (catálogo)."""
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import CatRol


class CatRolTest(TestCase):
    def test_crear_rol_y_str(self):
        rol = CatRol.objects.create(nombre="rol_qa_prueba", descripcion="Rol de prueba QA")
        self.assertIn("rol_qa_prueba", str(rol).lower())

    def test_nombre_unico(self):
        CatRol.objects.create(nombre="rol_qa_unico", descripcion="d")
        with self.assertRaises(IntegrityError), transaction.atomic():
            CatRol.objects.create(nombre="rol_qa_unico", descripcion="otra")
