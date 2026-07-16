"""Tests para ecografias_archivos (adjuntos de ecografías)."""
from datetime import date, timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from ecografias.models import Ecografia
from embarazos.models import Embarazo
from pacientes.models import Paciente

from .models import EcografiaArchivo


class EcografiaArchivoTest(TestCase):
    def setUp(self):
        paciente = Paciente.objects.create(
            id_clinico="PAC-EA-1", nombre="Nora", apellido_paterno="Sosa",
            fecha_nacimiento=date(1990, 6, 6), genero="femenino", ci="2000001",
        )
        embarazo = Embarazo.objects.create(
            paciente=paciente, numero_gesta=1,
            fecha_ultima_menstruacion=date.today() - timedelta(weeks=18),
        )
        self.eco = Ecografia.objects.create(
            embarazo=embarazo, paciente=paciente, fecha_ecografia=date.today(),
            tipo_ecografia="primer_trimestre", edad_gestacional_semanas=12,
            diagnostico="Normal",
        )

    def test_crear_archivo_adjunto(self):
        archivo = SimpleUploadedFile("eco.jpg", b"contenido-fake", content_type="image/jpeg")
        a = EcografiaArchivo.objects.create(
            ecografia=self.eco, archivo=archivo, tipo_archivo="imagen",
            nombre_archivo="eco.jpg",
        )
        self.assertEqual(a.ecografia, self.eco)
        self.assertEqual(a.nombre_archivo, "eco.jpg")

    def tearDown(self):
        for a in EcografiaArchivo.objects.all():
            a.archivo.delete(save=False)
