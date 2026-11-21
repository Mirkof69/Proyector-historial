"""Las acciones masivas del admin quedan en la auditoría.

Fallo que previene: hacían queryset.update(), que no dispara señales, y
cambiaban muchos registros sin dejar rastro.
"""
from django.contrib.admin import helpers
from django.test import TestCase

from auditoria.models import RegistroAuditoria
from usuarios.models import Usuario


class AccionMasivaAdminTest(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser(email="su.masivo@test.bo", password="clave-segura-123",
                                                      nombre="Su", apellido_paterno="Masivo")
        self.client.force_login(self.admin)
        self.victimas = [Usuario.objects.create_user(email=f"u{i}.masivo@test.bo", nombre="U", apellido_paterno=str(i),
                                                     password="clave-segura-123", rol="enfermera") for i in range(3)]

    def test_la_accion_masiva_se_audita(self):
        r = self.client.post("/admin/usuarios/usuario/", {
            "action": "hacer_staff",
            helpers.ACTION_CHECKBOX_NAME: [str(u.pk) for u in self.victimas],
        })
        self.assertIn(r.status_code, (200, 302))
        registro = RegistroAuditoria.objects.get(accion="ACCION_MASIVA_ADMIN")
        self.assertEqual(registro.modulo, "usuario")
        self.assertIn("hacer_staff", registro.detalle)
        self.assertIn("3 registros", registro.detalle)

    def test_la_pantalla_de_confirmacion_del_borrado_no_se_audita(self):
        self.client.post("/admin/usuarios/usuario/", {
            "action": "delete_selected", helpers.ACTION_CHECKBOX_NAME: [str(self.victimas[0].pk)],
        })
        self.assertFalse(RegistroAuditoria.objects.filter(accion="ACCION_MASIVA_ADMIN").exists())
