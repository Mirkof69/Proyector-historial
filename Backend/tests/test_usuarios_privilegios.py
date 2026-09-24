"""Nadie que no sea administrador puede darse privilegios ni tocar a otros usuarios.

Fallo que previene: `UsuarioViewSet` solo exigía sesión y su serializer dejaba
escribir `rol`, `is_staff`, `is_superuser` y `password`. Recepción podía
hacerse superusuaria con un PATCH, cambiar la contraseña de otra persona,
crear usuarios o desactivar al administrador.
"""
from django.test import TestCase
from rest_framework.test import APIClient

from usuarios.models import Usuario


class PrivilegiosDeUsuariosTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Usuario.objects.create_user(
            email="admin.priv@test.bo", nombre="Ada", apellido_paterno="Admin",
            password="clave-segura-123", rol="administrador")
        cls.recepcion = Usuario.objects.create_user(
            email="recep.priv@test.bo", nombre="Rosa", apellido_paterno="Recepcion",
            password="clave-segura-123", rol="recepcion")
        cls.medico = Usuario.objects.create_user(
            email="medico.priv@test.bo", nombre="Mario", apellido_paterno="Medico",
            password="clave-segura-123", rol="medico")

    def _cliente(self, usuario):
        c = APIClient()
        c.force_authenticate(usuario)
        return c

    def test_recepcion_no_puede_hacerse_superusuaria(self):
        """ESPERADO: la petición se acepta (es su perfil), pero los privilegios no cambian."""
        r = self._cliente(self.recepcion).patch(
            f"/api/usuarios/{self.recepcion.pk}/",
            {"is_superuser": True, "is_staff": True, "rol": "administrador", "nombre": "Rosa María"},
            format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.recepcion.refresh_from_db()
        self.assertFalse(self.recepcion.is_superuser)
        self.assertFalse(self.recepcion.is_staff)
        self.assertEqual(self.recepcion.rol, "recepcion")
        self.assertEqual(self.recepcion.nombre, "Rosa María")   # el perfil sí se edita

    def test_no_puede_cambiar_la_contrasena_por_el_perfil(self):
        self._cliente(self.recepcion).patch(
            f"/api/usuarios/{self.recepcion.pk}/",
            {"password": "otra-clave-999", "password_confirm": "otra-clave-999"}, format="json")
        self.recepcion.refresh_from_db()
        self.assertTrue(self.recepcion.check_password("clave-segura-123"))

    def test_no_puede_editar_a_otro_usuario(self):
        r = self._cliente(self.recepcion).patch(
            f"/api/usuarios/{self.medico.pk}/", {"nombre": "Hackeado"}, format="json")
        self.assertEqual(r.status_code, 403)
        self.medico.refresh_from_db()
        self.assertEqual(self.medico.nombre, "Mario")

    def test_no_puede_crear_usuarios(self):
        r = self._cliente(self.medico).post("/api/usuarios/", {
            "email": "nuevo@test.bo", "nombre": "N", "apellido_paterno": "N",
            "password": "clave-segura-123", "password_confirm": "clave-segura-123", "rol": "administrador",
        }, format="json")
        self.assertEqual(r.status_code, 403)
        self.assertFalse(Usuario.objects.filter(email="nuevo@test.bo").exists())

    def test_no_puede_desactivar_ni_borrar_al_administrador(self):
        c = self._cliente(self.medico)
        self.assertEqual(c.post(f"/api/usuarios/{self.admin.pk}/desactivar/").status_code, 403)
        self.assertEqual(c.delete(f"/api/usuarios/{self.admin.pk}/").status_code, 403)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.activo)

    def test_el_administrador_si_puede_cambiar_roles(self):
        r = self._cliente(self.admin).patch(
            f"/api/usuarios/{self.medico.pk}/", {"rol": "enfermera"}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.medico.refresh_from_db()
        self.assertEqual(self.medico.rol, "enfermera")

    def test_sin_sesion_es_401(self):
        self.assertEqual(APIClient().post("/api/usuarios/", {}, format="json").status_code, 401)
