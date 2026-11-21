"""Tests para el módulo de Monitoring (health check).

Incluye el endpoint /api/health/ que verifica BD/Redis/IA — el mismo que antes
crasheaba por el `import os` faltante (ahora corregido).
"""
from django.test import TestCase

from . import views


class MonitoringInternoTest(TestCase):
    def test_get_version_devuelve_string(self):
        self.assertIsInstance(views._get_version(), str)

    def test_get_uptime_no_crashea(self):
        self.assertIsNotNone(views._get_uptime())

    def test_check_database_saludable_en_tests(self):
        # En tests la BD está disponible → healthy
        estado = views._check_database()
        self.assertEqual(estado["status"], "healthy")

    def test_check_ai_service_no_crashea(self):
        # Antes fallaba por 'import os' faltante; ahora debe devolver dict con status
        estado = views._check_ai_service()
        self.assertIn("status", estado)


class HealthEndpointTest(TestCase):
    def test_health_endpoint_responde(self):
        resp = self.client.get("/api/health/")
        # BD sana en tests → 200; nunca debe crashear (500)
        self.assertIn(resp.status_code, (200, 503))
        data = resp.json()
        self.assertIn("status", data)
