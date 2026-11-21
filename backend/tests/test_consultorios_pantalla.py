"""El formulario de consultorios guarda lo que la pantalla envía.

La pantalla usaba `tipo`, `area`, `estado` y varios equipos que el modelo no
tenía: la tabla mostraba «—» y todos los consultorios como inactivos, y crear
uno desde la pantalla fallaba (consultorios/serializers.py).
"""
from django.test import TestCase
from rest_framework.test import APIClient

from consultorios.models import Consultorio
from usuarios.models import Usuario

URL = "/api/consultorios/"


class ConsultorioDesdeLaPantallaTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Usuario.objects.create_user(email="adm.cons@test.bo", nombre="Ana", apellido_paterno="Cons",
                                                password="clave-segura-123", rol="administrador")

    def setUp(self):
        self.cliente = APIClient()
        self.cliente.force_authenticate(self.admin)

    def test_crear_con_los_campos_de_la_pantalla(self):
        r = self.cliente.post(URL, {
            "codigo": "CON-09", "nombre": "Consultorio 9", "tipo": "ginecologia", "estado": "disponible",
            "area": "Bloque B", "piso": 2, "capacidad_personas": 3, "equipamiento": "intermedio",
            "tiene_camilla": True, "tiene_oxigeno": True, "tiene_computadora": True, "activo": True,
            "descripcion": "Consulta de alto riesgo", "ubicacion": "Bloque B, piso 2",
        }, format="json")
        self.assertEqual(r.status_code, 201, r.content[:400])
        c = Consultorio.objects.get(codigo="CON-09")
        self.assertEqual((c.tipo_consultorio, c.edificio, c.nivel_equipamiento, c.tiene_oxigeno, c.descripcion),
                         ("ginecologia", "Bloque B", "intermedio", True, "Consulta de alto riesgo"))
        self.assertEqual((r.json()["estado"], r.json()["tipo"], r.json()["area"]), ("disponible", "ginecologia", "Bloque B"))

    def test_estado_se_guarda_en_los_booleanos(self):
        c = Consultorio.objects.create(codigo="CON-10", nombre="Consultorio 10", tipo_consultorio="general",
                                       ubicacion="Bloque A")
        r = self.cliente.patch(f"{URL}{c.pk}/", {"estado": "mantenimiento"}, format="json")
        self.assertEqual(r.status_code, 200, r.content[:400])
        self.assertEqual(r.json()["estado"], "mantenimiento")
        r = self.cliente.patch(f"{URL}{c.pk}/", {"estado": "inactivo"}, format="json")
        self.assertEqual(r.json()["estado"], "inactivo")


class ConsultoriosEnfermeriaTest(TestCase):
    """Enfermería ve los consultorios (su menú los ofrece) pero no los modifica."""

    def test_enfermera_lee_pero_no_crea(self):
        enfermera = Usuario.objects.create_user(email="enf.cons@test.bo", nombre="Eva", apellido_paterno="Cons",
                                                password="clave-segura-123", rol="enfermera")
        c = APIClient()
        c.force_authenticate(enfermera)
        self.assertEqual(c.get(URL).status_code, 200)
        self.assertEqual(c.post(URL, {"codigo": "X-1", "nombre": "X", "tipo": "general"}, format="json").status_code, 403)

    def test_recepcion_lee_pero_no_crea(self):
        recepcion = Usuario.objects.create_user(email="rec.cons@test.bo", nombre="Rita", apellido_paterno="Cons",
                                                password="clave-segura-123", rol="recepcion")
        c = APIClient()
        c.force_authenticate(recepcion)
        self.assertEqual(c.get(URL).status_code, 200)
        self.assertEqual(c.post(URL, {"codigo": "X-2", "nombre": "X", "tipo": "general"}, format="json").status_code, 403)
