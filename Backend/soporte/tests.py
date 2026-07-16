"""Tests para el módulo de Soporte técnico (tickets)."""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import TicketSoporte

Usuario = get_user_model()


class TicketSoporteModelTest(APITestCase):
    """Tests del modelo TicketSoporte."""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email="medico@test.bo", nombre="Ana", apellido_paterno="Vargas", password="x",
        )

    def test_str_incluye_asunto(self):
        ticket = TicketSoporte.objects.create(
            usuario=self.usuario, asunto="No carga el listado", modulo="pacientes",
            descripcion="Se queda cargando",
        )
        self.assertIn("No carga el listado", str(ticket))

    def test_estado_por_defecto_abierto(self):
        ticket = TicketSoporte.objects.create(
            usuario=self.usuario, asunto="Duda", modulo="otro", descripcion="d",
        )
        self.assertEqual(ticket.estado, "abierto")
        self.assertEqual(ticket.prioridad, "media")


class TicketSoporteApiTest(APITestCase):
    """Tests de la API de tickets: permisos y aislamiento por usuario."""

    def setUp(self):
        self.user_a = Usuario.objects.create_user(
            email="a@test.bo", nombre="A", apellido_paterno="Uno", password="x",
        )
        self.user_b = Usuario.objects.create_user(
            email="b@test.bo", nombre="B", apellido_paterno="Dos", password="x",
        )
        self.admin = Usuario.objects.create_superuser(
            email="admin@test.bo", nombre="Admin", apellido_paterno="Sys", password="x",
        )
        self.url = "/api/soporte/tickets/"

    def test_crear_ticket_asigna_usuario_actual(self):
        self.client.force_authenticate(self.user_a)
        resp = self.client.post(self.url, {
            "asunto": "Error en reporte", "modulo": "reportes", "descripcion": "falla",
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        ticket = TicketSoporte.objects.get(id=resp.data["id"])
        self.assertEqual(ticket.usuario, self.user_a)
        # El estado es read-only: siempre arranca "abierto"
        self.assertEqual(ticket.estado, "abierto")

    def test_usuario_solo_ve_sus_tickets(self):
        TicketSoporte.objects.create(usuario=self.user_a, asunto="A1", modulo="otro", descripcion="d")
        TicketSoporte.objects.create(usuario=self.user_b, asunto="B1", modulo="otro", descripcion="d")

        self.client.force_authenticate(self.user_a)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        asuntos = [t["asunto"] for t in resp.data.get("results", resp.data)]
        self.assertIn("A1", asuntos)
        self.assertNotIn("B1", asuntos)

    def test_admin_ve_todos_los_tickets(self):
        TicketSoporte.objects.create(usuario=self.user_a, asunto="A1", modulo="otro", descripcion="d")
        TicketSoporte.objects.create(usuario=self.user_b, asunto="B1", modulo="otro", descripcion="d")

        self.client.force_authenticate(self.admin)
        resp = self.client.get(self.url)
        asuntos = [t["asunto"] for t in resp.data.get("results", resp.data)]
        self.assertIn("A1", asuntos)
        self.assertIn("B1", asuntos)

    def test_usuario_normal_no_puede_actualizar(self):
        ticket = TicketSoporte.objects.create(
            usuario=self.user_a, asunto="A1", modulo="otro", descripcion="d",
        )
        self.client.force_authenticate(self.user_a)
        resp = self.client.patch(f"{self.url}{ticket.id}/", {"estado": "resuelto"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonimo_no_accede(self):
        resp = self.client.get(self.url)
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
