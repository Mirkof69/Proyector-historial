"""Búsqueda de pacientes en TODOS los módulos que la ofrecen.

Regresión de un bug que estaba en 12 viewsets a la vez: los datos
identificatorios de Paciente están cifrados, y `SearchFilter` de DRF hace
`icontains` en SQL, o sea LIKE contra texto cifrado. Buscar una paciente por
apellido devolvía 0 resultados en embarazos, controles, ecografías, partos,
laboratorio, vacunas, citas, triaje, antecedentes y notas de evolución.

Estos tests fallan contra el código anterior a `core/filtros.py`.
"""
import datetime

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from embarazos.models import Embarazo
from pacientes.busqueda import ids_pacientes_que_coinciden, normalizar
from pacientes.models import Paciente
from usuarios.models import Usuario


class BusquedaPacienteHelperTest(TestCase):
    """El buscador canónico que comparten todas las vistas."""

    def setUp(self):
        self.lopez = Paciente.objects.create(
            nombre="Modesta", apellido_paterno="López", apellido_materno="Choque",
            fecha_nacimiento=datetime.date(1992, 5, 4), genero="femenino", ci="80011223",
        )
        self.vargas = Paciente.objects.create(
            nombre="Fernanda", apellido_paterno="Vargas", apellido_materno="Suárez",
            fecha_nacimiento=datetime.date(1988, 3, 9), genero="femenino", ci="80044556",
        )

    def test_normalizar_quita_tildes_y_mayusculas(self):
        self.assertEqual(normalizar("LÓPEZ"), "lopez")
        self.assertEqual(normalizar("Suárez"), "suarez")
        self.assertEqual(normalizar(None), "")

    def test_encuentra_por_apellido(self):
        self.assertEqual(ids_pacientes_que_coinciden("Vargas"), [self.vargas.pk])

    def test_encuentra_sin_tildes(self):
        """"lopez" debe encontrar a "López": en Bolivia se escribe de ambas formas."""
        for termino in ("lopez", "LÓPEZ", "López", "lópez"):
            self.assertIn(
                self.lopez.pk, ids_pacientes_que_coinciden(termino), f"buscando {termino!r}",
            )

    def test_encuentra_por_nombre_de_pila(self):
        self.assertEqual(ids_pacientes_que_coinciden("Fernanda"), [self.vargas.pk])

    def test_encuentra_por_cedula_exacta(self):
        """La CI está cifrada: se resuelve por ci_hash, no por LIKE."""
        self.assertEqual(ids_pacientes_que_coinciden("80011223"), [self.lopez.pk])

    def test_cedula_parcial_no_devuelve_a_otra_paciente(self):
        """Media cédula no puede traer a la paciente equivocada."""
        self.assertNotIn(self.lopez.pk, ids_pacientes_que_coinciden("8001"))

    def test_sin_coincidencias_devuelve_vacio(self):
        """Nunca "todos": devolver la lista entera sería peor que no encontrar."""
        self.assertEqual(ids_pacientes_que_coinciden("zzzznoexiste"), [])

    def test_termino_vacio_devuelve_vacio(self):
        self.assertEqual(ids_pacientes_que_coinciden("   "), [])


class BusquedaEnModulosClinicosTest(TestCase):
    """La misma búsqueda tiene que funcionar en las listas clínicas."""

    def setUp(self):
        self.usuario = Usuario.objects.create_superuser(
            email="busca@test.bo", nombre="Busca", apellido_paterno="Dor",
            password="clave12345",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.usuario)

        self.lopez = Paciente.objects.create(
            nombre="Modesta", apellido_paterno="López",
            fecha_nacimiento=datetime.date(1992, 5, 4), genero="femenino", ci="80011223",
        )
        self.vargas = Paciente.objects.create(
            nombre="Fernanda", apellido_paterno="Vargas",
            fecha_nacimiento=datetime.date(1988, 3, 9), genero="femenino", ci="80044556",
        )
        hoy = datetime.date.today()
        for paciente in (self.lopez, self.vargas):
            Embarazo.objects.create(
                paciente=paciente,
                numero_gesta=1,
                fecha_ultima_menstruacion=hoy - datetime.timedelta(weeks=20),
                fecha_probable_parto=hoy + datetime.timedelta(weeks=20),
                estado="activo",
            )

    def test_embarazos_se_filtran_por_apellido_de_la_paciente(self):
        url = reverse("embarazo-list")
        respuesta = self.client.get(url, {"search": "Vargas"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data["count"], 1)

    def test_embarazos_sin_coincidencia_no_devuelven_todo(self):
        """Si el filtro se rompe, el síntoma típico es "devuelve la lista entera"."""
        url = reverse("embarazo-list")
        respuesta = self.client.get(url, {"search": "zzzznoexiste"})
        self.assertEqual(respuesta.data["count"], 0)

    def test_embarazos_sin_termino_devuelven_todo(self):
        url = reverse("embarazo-list")
        respuesta = self.client.get(url)
        self.assertEqual(respuesta.data["count"], 2)
