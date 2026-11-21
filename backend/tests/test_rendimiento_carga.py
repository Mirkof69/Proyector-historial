"""Lo que la prueba de carga del 29/10/2026 encontró, para que no vuelva.

Con 50-100 usuarios a la vez (quality-assurance/prueba_carga_roles.py) las
rutas más lentas no lo eran por la base de datos sino por consultas repetidas
fila por fila y por cálculos que se rehacían en cada Panel:

  - `alertas-medicas/activas/`: una consulta por alerta para leer la paciente
    (202 por página).
  - `notificaciones/no_leidas/`: el enlace de cada notificación comprobaba en
    la base si el registro existía (202 por página).
  - Ficha e historia clínica de la paciente: la precarga se descartaba al
    reordenar en el serializer (84 consultas).
  - `laboratorios/tipos-examenes/`: un COUNT por tipo de examen.
  - `estadisticas-generales/`: cargaba las 1.300 pacientes enteras y
    descifraba 9.100 campos solo para una edad promedio.

Cada test fija que el número de consultas NO crece con los datos y que el
resultado es el mismo que el del camino sin optimizar.
"""

import datetime
from decimal import Decimal

from django.core.cache import cache
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from controles.models import ControlPrenatal
from core.cache_estadisticas import valor_cacheado
from embarazos.models import Embarazo
from laboratorio.models import ExamenLaboratorio, TipoExamen
from notificaciones.models import Notificacion, TipoNotificacion
from notificaciones.serializers import enlace_de, entidades_existentes
from pacientes.models import Paciente
from usuarios.models import Usuario

_ci = iter(range(7_810_000, 7_899_999))


def _paciente(nacimiento=datetime.date(1994, 6, 15)):
    return Paciente.objects.create(nombre="Carga", apellido_paterno="Prueba", ci=str(next(_ci)),
                                   fecha_nacimiento=nacimiento, genero="femenino")


def _embarazo(paciente, semanas=20, estado="activo"):
    return Embarazo.objects.create(paciente=paciente, numero_gesta=1, numero_para=0, tipo_embarazo="simple",
                                   estado=estado,
                                   fecha_ultima_menstruacion=timezone.localdate() - datetime.timedelta(weeks=semanas))


class _ConMedico(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(email="med.carga@test.bo", nombre="Ana", apellido_paterno="Carga",
                                                 password="clave-segura-123", rol="medico")

    def setUp(self):
        self.api = APIClient()
        self.api.force_authenticate(user=self.medico)

    def _consultas(self, ruta):
        with CaptureQueriesContext(connection) as cq:
            r = self.api.get(ruta)
        self.assertEqual(r.status_code, 200, r.content[:300])
        return len(cq.captured_queries), r.json()

    def _control(self, embarazo, sistolica=110, diastolica=70, numero=1):
        return ControlPrenatal.objects.create(
            embarazo=embarazo, paciente=embarazo.paciente, medico=self.medico, numero_control=numero,
            fecha_control=timezone.localdate(), semanas_gestacion=20, peso_actual=Decimal("65.00"),
            talla=Decimal("160.00"), presion_arterial_sistolica=sistolica, presion_arterial_diastolica=diastolica)


class NotificacionesSinConsultaPorFilaTest(_ConMedico):
    def _notificar(self, entidad_tipo, entidad_id):
        return Notificacion.objects.create(usuario=self.medico, tipo=TipoNotificacion.ALERTA_ADVERTENCIA,
                                           titulo="Aviso", mensaje="Cuerpo", entidad_tipo=entidad_tipo,
                                           entidad_id=entidad_id)

    def test_las_consultas_no_crecen_con_las_notificaciones(self):
        """ESPERADO: las mismas consultas con 4 que con 40 notificaciones enlazadas."""
        pacientes = [_paciente() for _ in range(4)]
        for p in pacientes:
            self._notificar("paciente", p.pk)
        self._consultas("/api/notificaciones/no_leidas/")  # la 1.ª carga permisos del usuario
        pocas, _ = self._consultas("/api/notificaciones/no_leidas/")
        for _ in range(9):
            for p in pacientes:
                self._notificar("paciente", p.pk)
        muchas, datos = self._consultas("/api/notificaciones/no_leidas/")
        self.assertEqual(len(datos["results"]), 40)
        self.assertEqual(muchas, pocas)

    def test_el_enlace_es_el_mismo_que_consultando_de_a_una(self):
        """ESPERADO: mismo enlace con la consulta agrupada que sin ella, también
        para un registro borrado (va a la bandeja) y para una paciente."""
        p = _paciente()
        e = _embarazo(p)
        notifs = [self._notificar("paciente", p.pk), self._notificar("embarazo", e.pk),
                  self._notificar("embarazo", 999_999), self._notificar("resultado_laboratorio", 999_998),
                  self._notificar("", None)]
        existentes = entidades_existentes(notifs)
        for n in notifs:
            self.assertEqual(enlace_de(n, self.medico, existentes), enlace_de(n, self.medico))
        self.assertEqual(enlace_de(notifs[2], self.medico, existentes), "/dashboard/notificaciones")


class FichaDePacienteSinConsultaPorFilaTest(_ConMedico):
    def test_las_consultas_no_crecen_con_la_historia(self):
        """ESPERADO: la misma cantidad de consultas para una historia corta y una larga."""
        corta = _paciente()
        self._control(_embarazo(corta))
        larga = _paciente()
        for i in range(3):
            emb = _embarazo(larga, semanas=10 + i, estado="activo" if i == 2 else "finalizado")
            for n in range(1, 4):
                self._control(emb, numero=n)
        self._consultas(f"/api/pacientes/{corta.pk}/")  # la 1.ª carga permisos del usuario
        for ruta in ("/api/pacientes/{}/", "/api/pacientes/{}/historial-completo/"):
            q_corta, _ = self._consultas(ruta.format(corta.pk))
            q_larga, datos = self._consultas(ruta.format(larga.pk))
            self.assertEqual(q_larga, q_corta, ruta)
        ficha = datos["paciente"]
        self.assertEqual((len(ficha["embarazos"]), len(ficha["controles_prenatales"]), ficha["embarazos_activos"]),
                         (3, 9, 1))

    def test_los_registros_del_mismo_dia_salen_siempre_en_el_mismo_orden(self):
        """ESPERADO: empates de fecha desempatados por id, del más nuevo al más viejo."""
        p = _paciente()
        emb = _embarazo(p)
        ids = [self._control(emb, numero=n).pk for n in range(1, 4)]  # misma fecha_control
        _, datos = self._consultas(f"/api/pacientes/{p.pk}/")
        self.assertEqual([c["id"] for c in datos["controles_prenatales"]], sorted(ids, reverse=True))


class AlertasActivasSinConsultaPorFilaTest(_ConMedico):
    def test_las_consultas_no_crecen_con_las_alertas(self):
        """Cada control con 160/110 crea una alerta activa con su paciente."""
        self._control(_embarazo(_paciente()), 160, 110)
        pocas, d1 = self._consultas("/api/reportes/alertas-medicas/activas/")
        for _ in range(5):
            self._control(_embarazo(_paciente()), 160, 110)
        muchas, d2 = self._consultas("/api/reportes/alertas-medicas/activas/")
        self.assertGreater(len(d2["results"]), len(d1["results"]))
        self.assertEqual(muchas, pocas)
        self.assertTrue(all(a["paciente_nombre"] == "Carga Prueba" for a in d2["results"]))


class TiposDeExamenContadosEnUnaConsultaTest(_ConMedico):
    def test_total_de_examenes_por_tipo(self):
        """ESPERADO: 2 y 0, y las mismas consultas con 2 tipos que con 6."""
        p = _paciente()
        tipos = [TipoExamen.objects.create(nombre=f"Tipo {i}", codigo=f"TCG{i}", categoria="hematologia",
                                           tiempo_resultado=1) for i in range(2)]
        for _ in range(2):
            ExamenLaboratorio.objects.create(paciente=p, tipo_examen=tipos[0], fecha_solicitud=timezone.now())
        pocas, datos = self._consultas("/api/laboratorios/tipos-examenes/?page_size=100")
        totales = {t["codigo"]: t["total_examenes"] for t in datos["results"]}
        self.assertEqual((totales["TCG0"], totales["TCG1"]), (2, 0))
        for i in range(2, 6):
            TipoExamen.objects.create(nombre=f"Tipo {i}", codigo=f"TCG{i}", categoria="hematologia",
                                      tiempo_resultado=1)
        muchas, _ = self._consultas("/api/laboratorios/tipos-examenes/?page_size=100")
        self.assertEqual(muchas, pocas)


class EdadPromedioDeEmbarazadasTest(TestCase):
    def test_una_paciente_con_dos_embarazos_cuenta_una_vez(self):
        """ESPERADO: (30 + 20) / 2 = 25, no (30 + 30 + 20) / 3."""
        from reportes.services.report_service import ReportService

        hoy = timezone.localdate()
        treinta = _paciente(hoy.replace(year=hoy.year - 30) - datetime.timedelta(days=1))
        veinte = _paciente(hoy.replace(year=hoy.year - 20) - datetime.timedelta(days=1))
        _embarazo(treinta, semanas=8)
        _embarazo(treinta, semanas=30, estado="finalizado")
        _embarazo(veinte, semanas=20)
        _paciente()  # sin embarazos: no entra
        stats = ReportService.get_embarazos_stats()
        self.assertEqual(stats["edad_promedio"], 25.0)
        self.assertEqual(stats["por_trimestre"], {"primer_trimestre": 1, "segundo_trimestre": 1,
                                                  "tercer_trimestre": 0})


class CacheDeEstadisticasTest(TestCase):
    def setUp(self):
        cache.clear()
        self.llamadas = 0

    def _calcular(self):
        self.llamadas += 1
        return {"n": self.llamadas}

    def test_apagada_en_los_tests_recalcula_siempre(self):
        valor_cacheado("prueba", self._calcular)
        valor_cacheado("prueba", self._calcular)
        self.assertEqual(self.llamadas, 2)

    @override_settings(ESTADISTICAS_CACHE_SEGUNDOS=60)
    def test_encendida_calcula_una_vez_por_parametros(self):
        self.assertEqual(valor_cacheado("prueba", self._calcular, {"desde": "2026-01-01"}), {"n": 1})
        self.assertEqual(valor_cacheado("prueba", self._calcular, {"desde": "2026-01-01"}), {"n": 1})
        self.assertEqual(valor_cacheado("prueba", self._calcular, {"desde": "2026-02-01"}), {"n": 2})
        self.assertEqual(self.llamadas, 2)

    @override_settings(ESTADISTICAS_CACHE_SEGUNDOS=60)
    def test_un_resultado_con_error_no_se_guarda(self):
        valor_cacheado("prueba", self._calcular, cacheable=lambda v: False)
        valor_cacheado("prueba", self._calcular, cacheable=lambda v: False)
        self.assertEqual(self.llamadas, 2)
