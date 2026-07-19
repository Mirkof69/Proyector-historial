"""Aislamiento entre clínicas (multi-tenant). EL test que faltaba.

Por qué existe
--------------
La suite normal corre sobre SQLite y con `django_tenants` DESACTIVADO (ver
settings.py). O sea que la separación por esquemas —lo que garantiza que una
clínica no pueda ver los datos de otra, que es la columna vertebral del
sistema y su principal requisito legal— no la ejercitaba **ningún** test.

No es una preocupación teórica: el bug que apagó el log de auditoría clínica
entero venía exactamente de ahí. `connection.introspection.table_names()`
devuelve solo las tablas del esquema del tenant y no ve `auditoria_registros`,
que vive en `public`; la comprobación daba False siempre y la auditoría se
apagaba en silencio. Era estructuralmente imposible de detectar con la suite
corriendo sin tenants.

Cómo se corre
-------------
Necesita PostgreSQL levantado (no funciona sobre SQLite, que no tiene
esquemas):

    TEST_CON_TENANTS=true python -m pytest tests/test_aislamiento_tenants.py

Si django_tenants no está activo o el motor no es PostgreSQL, los tests se
SALTAN con un motivo explícito, en vez de pasar en falso.
"""
import datetime

import pytest
from django.apps import apps
from django.db import connection
from django.test import TransactionTestCase

TENANTS_ACTIVO = apps.is_installed("django_tenants")
ES_POSTGRES = connection.vendor == "postgresql"

RAZON = (
    "Requiere PostgreSQL con django_tenants activo. "
    "Correr con: TEST_CON_TENANTS=true python -m pytest "
    "tests/test_aislamiento_tenants.py"
)

pytestmark = pytest.mark.skipif(not (TENANTS_ACTIVO and ES_POSTGRES), reason=RAZON)


@pytest.mark.django_db
class AislamientoEntreClinicasTest(TransactionTestCase):
    """Dos clínicas distintas no pueden verse los datos entre sí."""

    # Los esquemas se crean/destruyen de verdad: hace falta transacción real.
    databases = "__all__"

    def setUp(self):
        from clientes.models import Client, Domain

        self.clinica_a = Client(schema_name="test_clinica_a", name="Clínica A")
        self.clinica_a.save()
        Domain.objects.create(
            domain="clinica-a.test.local", tenant=self.clinica_a, is_primary=True,
        )

        self.clinica_b = Client(schema_name="test_clinica_b", name="Clínica B")
        self.clinica_b.save()
        Domain.objects.create(
            domain="clinica-b.test.local", tenant=self.clinica_b, is_primary=True,
        )

    def tearDown(self):
        for clinica in (self.clinica_a, self.clinica_b):
            try:
                clinica.delete(force_drop=True)
            except Exception:
                pass

    def _crear_paciente(self, schema, nombre, ci):
        from django_tenants.utils import schema_context

        from pacientes.models import Paciente

        with schema_context(schema):
            return Paciente.objects.create(
                id_clinico=f"PAC-{ci}", nombre=nombre, apellido_paterno="Aislada",
                fecha_nacimiento=datetime.date(1990, 1, 1), genero="femenino", ci=ci,
            )

    def test_una_clinica_no_ve_las_pacientes_de_la_otra(self):
        """El requisito central: los datos clínicos no cruzan de esquema."""
        from django_tenants.utils import schema_context

        from pacientes.models import Paciente

        self._crear_paciente("test_clinica_a", "AnaDeLaA", "70000001")
        self._crear_paciente("test_clinica_b", "BeaDeLaB", "70000002")

        with schema_context("test_clinica_a"):
            nombres_a = set(Paciente.objects.values_list("nombre", flat=True))
        with schema_context("test_clinica_b"):
            nombres_b = set(Paciente.objects.values_list("nombre", flat=True))

        self.assertIn("AnaDeLaA", nombres_a)
        self.assertNotIn(
            "BeaDeLaB", nombres_a,
            "la Clínica A está viendo una paciente de la Clínica B",
        )
        self.assertIn("BeaDeLaB", nombres_b)
        self.assertNotIn(
            "AnaDeLaA", nombres_b,
            "la Clínica B está viendo una paciente de la Clínica A",
        )

    def test_la_misma_cedula_puede_existir_en_dos_clinicas(self):
        """Una paciente puede atenderse en dos clínicas: el UNIQUE de ci_hash
        es por esquema, no global. Si esto falla, el aislamiento está roto o
        la tabla quedó compartida sin querer."""
        self._crear_paciente("test_clinica_a", "Misma", "70000009")
        try:
            self._crear_paciente("test_clinica_b", "Misma", "70000009")
        except Exception as exc:  # pragma: no cover
            self.fail(f"La misma CI debería poder existir en otra clínica: {exc}")

    def test_la_auditoria_es_accesible_desde_el_esquema_de_un_tenant(self):
        """Regresión directa del bug que apagó la auditoría clínica.

        `auditoria_registros` vive en `public` (app compartida). Desde el
        esquema de un tenant el search_path es "<tenant>, public", así que la
        tabla SÍ es accesible con el ORM aunque `table_names()` no la liste.
        """
        from django_tenants.utils import schema_context

        from auditoria.models import RegistroAuditoria
        from auditoria.signals import verificar_tabla_auditoria_existe

        with schema_context("test_clinica_a"):
            self.assertTrue(
                verificar_tabla_auditoria_existe(),
                "la auditoría se cree inaccesible desde el tenant y se apaga sola",
            )
            RegistroAuditoria.objects.exists()  # no debe lanzar

    def test_crear_una_paciente_en_un_tenant_queda_auditado(self):
        """La trazabilidad tiene que funcionar DENTRO del contexto de tenant,
        que es como corre el sistema real."""
        from django_tenants.utils import schema_context

        from auditoria.models import RegistroAuditoria

        with schema_context("test_clinica_a"):
            antes = RegistroAuditoria.objects.count()

        paciente = self._crear_paciente("test_clinica_a", "Auditada", "70000010")

        with schema_context("test_clinica_a"):
            registro = RegistroAuditoria.objects.filter(
                accion="crear", registro_id=str(paciente.id),
            ).first()
            self.assertIsNotNone(
                registro, "crear una paciente en un tenant debe auditarse",
            )
            self.assertGreater(RegistroAuditoria.objects.count(), antes)
