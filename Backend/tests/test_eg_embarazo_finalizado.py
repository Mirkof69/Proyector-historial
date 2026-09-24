"""La edad gestacional de un embarazo terminado se cuenta hasta el parto.

Fallo que previene: se contaba siempre hasta hoy; un embarazo que terminó
hace un año mostraba «85+3 semanas» y tercer trimestre.
"""
import datetime

from django.test import TestCase
from django.utils import timezone

from embarazos.models import Embarazo
from embarazos.serializers import EmbarazoListSerializer, EmbarazoSerializer
from pacientes.models import Paciente
from partos.models import Parto
from usuarios.models import Usuario


class EdadGestacionalTerminadoTest(TestCase):
    def setUp(self):
        self.medico = Usuario.objects.create_user(email="med.eg@test.bo", nombre="M", apellido_paterno="E",
                                                  password="clave-segura-123", rol="medico")
        self.paciente = Paciente.objects.create(nombre="Ana", apellido_paterno="Eg", apellido_materno="Fin",
                                                fecha_nacimiento=datetime.date(1990, 1, 1), genero="femenino",
                                                ci="7966001")

    def test_embarazo_terminado_hace_un_anio_muestra_la_eg_del_parto(self):
        fum = timezone.localdate() - datetime.timedelta(days=365 + 39 * 7 + 2)
        embarazo = Embarazo.objects.create(paciente=self.paciente, numero_gesta=1, fecha_ultima_menstruacion=fum)
        Parto.objects.create(paciente=self.paciente, embarazo=embarazo, medico_responsable=self.medico,
                             numero_parto="P-EG-1", edad_gestacional_parto="39+2", parto_finalizado=True,
                             fecha_parto=timezone.make_aware(datetime.datetime.combine(
                                 fum + datetime.timedelta(days=39 * 7 + 2), datetime.time(10, 0))))
        embarazo.refresh_from_db()
        self.assertEqual(embarazo.estado, "finalizado")
        self.assertEqual(EmbarazoSerializer(embarazo).data["semanas_gestacion"], "39+2")
        self.assertEqual(EmbarazoListSerializer(embarazo).data["semanas_gestacion"], "39+2")

    def test_terminado_sin_parto_no_inventa_semanas(self):
        embarazo = Embarazo.objects.create(paciente=self.paciente, numero_gesta=1, estado="perdida",
                                           fecha_ultima_menstruacion=timezone.localdate() - datetime.timedelta(weeks=60))
        self.assertIsNone(EmbarazoListSerializer(embarazo).data["semanas_gestacion"])

    def test_activo_se_cuenta_hasta_hoy(self):
        embarazo = Embarazo.objects.create(paciente=self.paciente, numero_gesta=1,
                                           fecha_ultima_menstruacion=timezone.localdate() - datetime.timedelta(days=20 * 7 + 3))
        self.assertEqual(EmbarazoListSerializer(embarazo).data["semanas_gestacion"], "20+3")


class UnEmbarazoActivoTest(TestCase):
    """Dos peticiones simultáneas podían crear dos embarazos activos; ahora lo impide la base."""

    def test_la_base_rechaza_un_segundo_embarazo_activo(self):
        from django.db import IntegrityError, transaction

        p = Paciente.objects.create(nombre="Ana", apellido_paterno="Dos", apellido_materno="Activos",
                                    fecha_nacimiento=datetime.date(1990, 1, 1), genero="femenino", ci="7966002")
        fum = timezone.localdate() - datetime.timedelta(weeks=10)
        Embarazo.objects.create(paciente=p, numero_gesta=1, fecha_ultima_menstruacion=fum)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Embarazo.objects.create(paciente=p, numero_gesta=2, fecha_ultima_menstruacion=fum)

    def test_varios_embarazos_terminados_si_se_permiten(self):
        p = Paciente.objects.create(nombre="Ana", apellido_paterno="Varios", apellido_materno="Fin",
                                    fecha_nacimiento=datetime.date(1990, 1, 1), genero="femenino", ci="7966003")
        fum = timezone.localdate() - datetime.timedelta(weeks=100)
        Embarazo.objects.create(paciente=p, numero_gesta=1, fecha_ultima_menstruacion=fum, estado="finalizado")
        Embarazo.objects.create(paciente=p, numero_gesta=2, fecha_ultima_menstruacion=fum, estado="finalizado")
        Embarazo.objects.create(paciente=p, numero_gesta=3, fecha_ultima_menstruacion=timezone.localdate())
        self.assertEqual(Embarazo.objects.filter(paciente=p).count(), 3)
