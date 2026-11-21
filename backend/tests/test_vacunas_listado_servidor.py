"""La pantalla de vacunas filtra y resume EN EL SERVIDOR.

Antes pedía `page_size=1000`, el servidor cortaba en 200 y la pantalla
calculaba cifras y gráficas sobre esos 200: con más registros, faltaban
vacunas y las cifras mentían sin avisar.
"""
import datetime

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from pacientes.models import Paciente
from usuarios.models import Usuario
from vacunas.models import RegistroVacuna, TipoVacuna


class ListadoVacunasServidorTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(email="vac.srv@test.bo", nombre="Vera", apellido_paterno="Vac",
                                                 password="clave-segura-123", rol="medico")
        p = Paciente.objects.create(nombre="Rosa", apellido_paterno="Quispe", apellido_materno="Mamani",
                                    fecha_nacimiento=datetime.date(1995, 5, 5), genero="femenino", ci="7811101")
        flu = TipoVacuna.objects.create(nombre="Influenza estacional", dosis_requeridas=1)
        hep = TipoVacuna.objects.create(nombre="Hepatitis B", dosis_requeridas=3, intervalo_dosis_dias=30)
        hoy = timezone.localdate()
        ahora = timezone.now()
        base = {"paciente": p, "numero_dosis": 1, "lote": "L1", "laboratorio": "X",
                "via_administracion": "intramuscular", "sitio_aplicacion": "deltoides_izquierdo",
                "aplicado_por": cls.medico}
        # 205 de influenza completas: más que el tope de 200 por página
        RegistroVacuna.objects.bulk_create([
            RegistroVacuna(tipo_vacuna=flu, fecha_aplicacion=ahora - datetime.timedelta(days=i % 60, minutes=i), **base)
            for i in range(205)
        ])
        RegistroVacuna.objects.create(tipo_vacuna=hep, fecha_aplicacion=ahora,
                                      proxima_dosis_fecha=hoy - datetime.timedelta(days=3), **base)
        RegistroVacuna.objects.create(tipo_vacuna=hep, fecha_aplicacion=ahora - datetime.timedelta(hours=1),
                                      proxima_dosis_fecha=hoy + datetime.timedelta(days=3), **base)

    def setUp(self):
        self.c = APIClient()
        self.c.force_authenticate(self.medico)

    def test_el_total_es_el_real_aunque_pase_de_200(self):
        r = self.c.get("/api/vacunas/registros/", {"page_size": 20})
        self.assertEqual(r.json()["count"], 207)
        self.assertEqual(len(r.json()["results"]), 20)

    def test_filtros_de_la_pantalla_en_el_servidor(self):
        contar = lambda **q: self.c.get("/api/vacunas/registros/", {"page_size": 1, **q}).json()["count"]  # noqa: E731
        self.assertEqual(contar(vacuna="hepatitis"), 2)
        self.assertEqual(contar(estado_dosis="vencidas"), 1)
        self.assertEqual(contar(estado_dosis="pendientes"), 2)
        self.assertEqual(contar(estado_dosis="completas"), 205)
        self.assertEqual(contar(search="quispe"), 207)

    def test_resumen_cuenta_todo_con_los_mismos_filtros(self):
        r = self.c.get("/api/vacunas/registros/resumen/").json()
        self.assertEqual(r["total"], 207)
        self.assertEqual(r["vencidas"], 1)
        self.assertEqual(r["proxima_semana"], 1)
        self.assertEqual({t["name"]: t["value"] for t in r["por_tipo"]},
                         {"Influenza estacional": 205, "Hepatitis B": 2})
        self.assertEqual(sum(m["cantidad"] for m in r["por_mes"]), 207)
        filtrado = self.c.get("/api/vacunas/registros/resumen/", {"vacuna": "hepatitis"}).json()
        self.assertEqual(filtrado["total"], 2)


class ProximaDosisTest(TestCase):
    """La próxima dosis: siempre posterior a la aplicación; «futura» solo al
    registrarla o cambiarla. Antes se exigía futura SIEMPRE: pasada la fecha,
    el registro quedaba inválido y no se podía corregir ni el lote."""

    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(email="vac.prox@test.bo", nombre="Pia", apellido_paterno="Prox",
                                                 password="clave-segura-123", rol="medico")
        cls.p = Paciente.objects.create(nombre="Ana", apellido_paterno="Dosis", apellido_materno="X",
                                        fecha_nacimiento=datetime.date(1990, 1, 1), genero="femenino", ci="7833301")
        cls.tipo = TipoVacuna.objects.create(nombre="dT", dosis_requeridas=3, intervalo_dosis_dias=30)

    def _vacuna(self, aplicada, proxima):
        return RegistroVacuna(paciente=self.p, tipo_vacuna=self.tipo, numero_dosis=1, lote="L1", laboratorio="X",
                              via_administracion="intramuscular", sitio_aplicacion="deltoides_izquierdo",
                              aplicado_por=self.medico, fecha_aplicacion=aplicada, proxima_dosis_fecha=proxima)

    def test_al_registrar_la_proxima_dosis_tiene_que_ser_futura(self):
        from django.core.exceptions import ValidationError

        hoy = timezone.localdate()
        with self.assertRaises(ValidationError):
            self._vacuna(timezone.now() - datetime.timedelta(days=60), hoy - datetime.timedelta(days=1)).full_clean()

    def test_un_registro_antiguo_se_puede_corregir(self):
        """ESPERADO: cambiar el lote de una vacuna cuya próxima dosis ya pasó es válido."""
        v = self._vacuna(timezone.now() - datetime.timedelta(days=200), timezone.localdate() + datetime.timedelta(days=5))
        v.save()
        RegistroVacuna.objects.filter(pk=v.pk).update(proxima_dosis_fecha=timezone.localdate() - datetime.timedelta(days=100))
        v.refresh_from_db()
        v.lote = "L2-corregido"
        v.full_clean()  # no debe lanzar

    def test_la_proxima_dosis_no_puede_ser_antes_de_la_aplicada(self):
        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            self._vacuna(timezone.now() + datetime.timedelta(days=30), timezone.localdate() + datetime.timedelta(days=10)).full_clean()
