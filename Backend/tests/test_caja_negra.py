"""Pruebas de CAJA NEGRA.

Qué significa aquí
------------------
Se prueba el sistema **por fuera**, como lo usa una persona: se manda una
petición HTTP y se mira la respuesta. Este archivo no importa ningún módulo
interno del proyecto salvo los modelos imprescindibles para dejar datos
preparados; no sabe cuántas consultas SQL se hacen, ni qué función corre, ni
cómo está montado por dentro.

La pregunta que responde es: **¿el sistema hace lo que promete?**

Sirve para detectar lo que un test interno no ve: que la URL sea la que es, que
el código de estado sea el correcto, que el JSON traiga los campos con los
nombres que el frontend espera. Los fallos de contrato viven aquí.

La técnica de diseño es **partición de equivalencia y valores límite**: para
cada entrada se prueba un caso válido representativo, uno inválido, y los
bordes (vacío, cero, el máximo, uno más del máximo).

Cada test declara el resultado ESPERADO y lo compara con el OBTENIDO.
"""

import datetime

from rest_framework.test import APIClient, APITestCase

from pacientes.models import Paciente
from usuarios.models import Usuario

CLAVE = "clave-de-prueba-123"


class _ApiComoUsuaria(APITestCase):
    """Cliente autenticado. A partir de aquí, solo HTTP."""

    @classmethod
    def setUpTestData(cls):
        cls.medica = Usuario.objects.create_user(
            email="dra.negra@test.bo", nombre="Elena",
            apellido_paterno="Choque", password=CLAVE, rol="medico",
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.medica)


class ContratoDeLaApiDePacientesTest(_ApiComoUsuaria):
    """Lo que el frontend da por hecho que va a recibir."""

    def test_el_listado_responde_con_la_forma_paginada_de_siempre(self):
        """ESPERADO: count, next, previous, results.

        El frontend lee `results` y `count`. Si un día el listado devolviera
        una lista pelada, todas las pantallas se quedarían en blanco sin dar
        ningún error de servidor.
        """
        respuesta = self.client.get("/api/pacientes/")

        assert respuesta.status_code == 200
        for campo in ("count", "next", "previous", "results"):
            assert campo in respuesta.data, f"Falta '{campo}' en la respuesta."

    def test_crear_una_paciente_devuelve_201_y_su_id(self):
        """ESPERADO: 201 con `id`, no 200.

        El frontend usa ese id para navegar a la ficha recién creada.
        """
        respuesta = self.client.post("/api/pacientes/", {
            "nombre": "Fernanda", "apellido_paterno": "Mamani",
            "apellido_materno": "Choque", "fecha_nacimiento": "1995-06-12",
            "genero": "femenino", "ci": "4455661",
        }, format="json")

        assert respuesta.status_code == 201, respuesta.data
        assert "id" in respuesta.data

    def test_una_fecha_de_nacimiento_imposible_se_rechaza_con_400(self):
        """ESPERADO: 400, no 500 ni un 201 silencioso.

        Valor límite: una fecha en el futuro. Guardarla dejaría una paciente
        con edad negativa, y la edad gestacional se calcula a partir de ahí.
        """
        respuesta = self.client.post("/api/pacientes/", {
            "nombre": "Imposible", "apellido_paterno": "Fecha",
            "apellido_materno": "Futura", "fecha_nacimiento": "2099-01-01",
            "genero": "femenino", "ci": "4455662",
        }, format="json")

        assert respuesta.status_code == 400, (
            f"Aceptó una fecha de nacimiento en 2099 con {respuesta.status_code}."
        )

    def test_faltar_un_campo_obligatorio_da_400_y_dice_cual(self):
        """ESPERADO: 400 y el nombre del campo en el cuerpo.

        Un 400 sin decir qué falta obliga a adivinar; el formulario no puede
        marcar el campo en rojo.
        """
        respuesta = self.client.post("/api/pacientes/", {
            "apellido_paterno": "SinNombre",
        }, format="json")

        assert respuesta.status_code == 400
        assert "nombre" in respuesta.data, (
            f"El error no menciona el campo que falta: {respuesta.data}"
        )

    def test_pedir_una_paciente_que_no_existe_da_404(self):
        """ESPERADO: 404, no 500."""
        assert self.client.get("/api/pacientes/999999/").status_code == 404


class ValoresLimiteDelListadoTest(_ApiComoUsuaria):
    """Los bordes del parámetro de paginación."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        for i in range(30):
            Paciente.objects.create(
                nombre=f"Paciente{i}", apellido_paterno="Limite",
                apellido_materno="Prueba", fecha_nacimiento=datetime.date(1990, 1, 1),
                genero="femenino", ci=f"77{i:05d}",
            )

    def test_page_size_uno_devuelve_una(self):
        """ESPERADO: 1. Borde inferior."""
        respuesta = self.client.get("/api/pacientes/?page_size=1")
        assert len(respuesta.data["results"]) == 1

    def test_page_size_enorme_se_corta_en_el_tope(self):
        """ESPERADO: no más de 200. Borde superior.

        Sin tope, cualquiera puede pedir la tabla entera en una petición.
        """
        respuesta = self.client.get("/api/pacientes/?page_size=999999")
        assert len(respuesta.data["results"]) <= 200

    def test_page_size_con_texto_no_revienta(self):
        """ESPERADO: 200 con el tamaño por defecto, no un 500.

        Entrada inválida: alguien edita la URL a mano.
        """
        respuesta = self.client.get("/api/pacientes/?page_size=muchos")
        assert respuesta.status_code == 200

    def test_una_pagina_que_no_existe_da_404_no_una_lista_vacia(self):
        """ESPERADO: 404.

        Una lista vacía haría creer que no hay pacientes.
        """
        assert self.client.get("/api/pacientes/?page=9999").status_code == 404


class BusquedaVistaDesdeFueraTest(_ApiComoUsuaria):
    """Buscar sin saber cómo está implementada la búsqueda."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.paciente = Paciente.objects.create(
            nombre="Fernanda", apellido_paterno="Mamani",
            apellido_materno="Choque", fecha_nacimiento=datetime.date(1995, 6, 12),
            genero="femenino", ci="8899001",
        )

    def _ids(self, termino):
        r = self.client.get(f"/api/pacientes/?search={termino}")
        return [p["id"] for p in r.data["results"]]

    def test_se_encuentra_por_apellido_exacto(self):
        """ESPERADO: aparece."""
        assert self.paciente.id in self._ids("Mamani")

    def test_se_encuentra_escribiendolo_como_suena(self):
        """ESPERADO: aparece buscando 'Mamany'.

        Es el caso de recepción: quien dicta y quien escribe no coinciden.
        """
        assert self.paciente.id in self._ids("Mamany")

    def test_buscar_algo_que_no_esta_devuelve_lista_vacia_no_error(self):
        """ESPERADO: 200 con results vacío."""
        r = self.client.get("/api/pacientes/?search=Zzzyxwv")
        assert r.status_code == 200
        assert r.data["results"] == []

    def test_buscar_cadena_vacia_devuelve_el_listado_completo(self):
        """ESPERADO: 200 y al menos la paciente creada."""
        assert self.paciente.id in self._ids("")


class SinCredencialesNoSePasaTest(APITestCase):
    """Caja negra sobre la puerta de entrada, sin autenticar."""

    def test_pedir_pacientes_sin_sesion_da_401(self):
        """ESPERADO: 401, y sin filtrar ningún dato en el cuerpo."""
        respuesta = APIClient().get("/api/pacientes/")

        assert respuesta.status_code == 401
        cuerpo = str(respuesta.data).lower()
        assert "mamani" not in cuerpo and "paciente" not in cuerpo.replace("pacientes", "")

    def test_login_con_contrasena_mala_da_401_y_no_dice_si_el_email_existe(self):
        """ESPERADO: el mismo mensaje exista o no el email.

        Si el mensaje cambiara, cualquiera podría averiguar qué correos están
        dados de alta probándolos uno a uno.
        """
        Usuario.objects.create_user(
            email="existe@test.bo", nombre="Ana", apellido_paterno="Real",
            password=CLAVE, rol="medico",
        )
        cliente = APIClient()

        con_email_real = cliente.post("/api/usuarios/login/", {
            "email": "existe@test.bo", "password": "claveEquivocada",
        }, format="json")
        con_email_falso = cliente.post("/api/usuarios/login/", {
            "email": "noexiste@test.bo", "password": "claveEquivocada",
        }, format="json")

        assert con_email_real.status_code == con_email_falso.status_code == 401
        assert str(con_email_real.data) == str(con_email_falso.data), (
            "El mensaje delata si el email está registrado: "
            f"{con_email_real.data} vs {con_email_falso.data}"
        )
