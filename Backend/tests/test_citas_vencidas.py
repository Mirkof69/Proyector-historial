"""Citas de días pasados y turnos libres en la agenda de la demo.

Nada cerraba las citas agendadas cuyo día ya había pasado (75 en la demo
seguían «pendientes» semanas después) y completar_demo llenaba los 16 turnos
diarios de los tres médicos hasta fin de año: no se podía agendar ninguna cita.
Ver citas/vencimiento.py y pacientes/management/commands/completar_demo.py.
"""
import datetime

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from citas.models import Cita, HistorialCita
from citas.vencimiento import cerrar_citas_vencidas
from embarazos.models import Embarazo
from pacientes.management.commands import completar_demo
from pacientes.models import Paciente
from usuarios.models import Usuario


def _paciente(n):
    return Paciente.objects.create(
        nombre=f"Paciente{n}", apellido_paterno="Vence", apellido_materno="Cita",
        fecha_nacimiento=datetime.date(1993, 3, 3), genero="femenino", ci=f"79{n:05d}")


class CitasVencidasTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(
            email="medico.vence@hospital.bo", nombre="M", apellido_paterno="V",
            password="clave-segura-123", rol="medico")
        cls.hoy = timezone.localdate()
        ayer = cls.hoy - datetime.timedelta(days=1)
        datos = [("agendada", ayer), ("confirmada", ayer - datetime.timedelta(days=9)),
                 ("completada", ayer), ("agendada", cls.hoy)]
        # bulk_create: Cita.save() no deja guardar citas en el pasado.
        Cita.objects.bulk_create([
            Cita(paciente=_paciente(i), medico=cls.medico, fecha_cita=fecha, hora_cita=datetime.time(8, 0),
                 tipo_cita="control", estado=estado, motivo="Control")
            for i, (estado, fecha) in enumerate(datos)])

    def setUp(self):
        cache.clear()

    def test_las_pendientes_de_dias_pasados_quedan_como_no_asistio(self):
        # ESPERADO: 2 (la agendada de ayer y la confirmada de hace 10 días).
        self.assertEqual(cerrar_citas_vencidas(), 2)
        estados = Cita.objects.values_list("estado", flat=True)
        self.assertEqual(sorted(estados), ["agendada", "completada", "no_asistio", "no_asistio"])
        # La de hoy sigue agendada aunque su hora haya pasado: puede llegar tarde.
        self.assertEqual(Cita.objects.get(fecha_cita=self.hoy).estado, "agendada")
        historial = HistorialCita.objects.filter(estado_nuevo="no_asistio")
        self.assertEqual(sorted(historial.values_list("estado_anterior", flat=True)), ["agendada", "confirmada"])
        self.assertEqual(cerrar_citas_vencidas(), 0)

    def test_abrir_la_agenda_las_cierra(self):
        cliente = APIClient()
        cliente.force_authenticate(self.medico)
        r = cliente.get("/api/citas/citas/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Cita.objects.filter(estado="no_asistio").count(), 2)


class TurnosLibresDeLaDemoTest(TestCase):
    def setUp(self):
        self.medico = Usuario.objects.create_user(
            email="medica.demo@hospital.bo", nombre="D", apellido_paterno="Demo",
            password="clave-segura-123", rol="medico")
        # 40 embarazos activos sin controles: todas piden cita desde hoy, más de
        # lo que cabe en un día (16 turnos).
        for i in range(40):
            Embarazo.objects.create(paciente=_paciente(100 + i), numero_gesta=1, estado="activo",
                                    fecha_ultima_menstruacion=timezone.localdate() - datetime.timedelta(weeks=20))

    def test_las_proximas_generadas_dejan_libres_los_turnos_reservados(self):
        r = completar_demo.Command()._citas()
        self.assertEqual(r["citas_proximas"], 40)
        horas = set(Cita.objects.values_list("hora_cita", flat=True))
        # ESPERADO: ninguna cita generada en los turnos libres (antes: los 16 llenos).
        self.assertFalse(horas & completar_demo.TURNOS_LIBRES)

    def test_corre_las_citas_que_ya_ocupaban_un_turno_libre(self):
        manana = completar_demo._habil(timezone.localdate() + datetime.timedelta(days=2))
        generada, manual = _paciente(500), _paciente(501)
        Cita.objects.bulk_create([
            Cita(paciente=generada, medico=self.medico, fecha_cita=manana, hora_cita=datetime.time(9, 30),
                 tipo_cita="control", estado="agendada", motivo=completar_demo.MOTIVO_PROXIMA),
            # Una cita agendada por una persona no se mueve aunque esté en un turno libre.
            Cita(paciente=manual, medico=self.medico, fecha_cita=manana, hora_cita=datetime.time(11, 30),
                 tipo_cita="control", estado="agendada", motivo="Dolor pélvico")])
        self.assertEqual(completar_demo.Command()._liberar_turnos(), 1)
        movida = Cita.objects.get(paciente=generada)
        self.assertEqual((movida.fecha_cita, movida.hora_cita), (manana, datetime.time(8, 0)))
        self.assertEqual(Cita.objects.get(paciente=manual).hora_cita, datetime.time(11, 30))

    def test_si_su_medica_no_tiene_lugar_pasa_a_otro_medico(self):
        from unittest.mock import patch

        otro = Usuario.objects.create_user(
            email="medico.libre@hospital.bo", nombre="L", apellido_paterno="Libre",
            password="clave-segura-123", rol="medico")
        dia = completar_demo._habil(timezone.localdate() + datetime.timedelta(days=2))
        llenas = [h for h in completar_demo.FRANJAS if h not in completar_demo.TURNOS_LIBRES]
        Cita.objects.bulk_create(
            [Cita(paciente=_paciente(600 + i), medico=self.medico, fecha_cita=dia, hora_cita=h,
                  tipo_cita="control", estado="agendada", motivo="Control") for i, h in enumerate(llenas)]
            + [Cita(paciente=_paciente(700), medico=self.medico, fecha_cita=dia, hora_cita=datetime.time(15, 0),
                    tipo_cita="control", estado="agendada", motivo=completar_demo.MOTIVO_PROXIMA)])
        with patch.object(completar_demo, "HORIZONTE_DIAS", (dia - timezone.localdate()).days):
            self.assertEqual(completar_demo.Command()._liberar_turnos(), 1)
        movida = Cita.objects.get(motivo=completar_demo.MOTIVO_PROXIMA)
        self.assertEqual((movida.medico, movida.fecha_cita, movida.hora_cita), (otro, dia, datetime.time(8, 0)))


class PartosDeLaCargaTest(TestCase):
    def test_los_partos_ya_ocurridos_quedan_finalizados(self):
        from partos.models import Parto, RecienNacido

        paciente = _paciente(900)
        embarazo = Embarazo.objects.create(paciente=paciente, numero_gesta=1, estado="finalizado",
                                           fecha_ultima_menstruacion=timezone.localdate() - datetime.timedelta(weeks=60))
        hace_meses = timezone.now() - datetime.timedelta(days=120)
        viejo = Parto.objects.create(paciente=paciente, embarazo=embarazo, fecha_parto=hace_meses,
                                     edad_gestacional_parto="39+1", tipo_parto="vaginal_espontaneo")
        RecienNacido.objects.create(parto=viejo, fecha_nacimiento=hace_meses, sexo="femenino",
                                    peso_nacimiento=3200, talla_nacimiento=49, apgar_1_minuto=8, apgar_5_minutos=9)
        en_curso = Parto.objects.create(paciente=_paciente(901), fecha_parto=timezone.now(),
                                        edad_gestacional_parto="39", tipo_parto="vaginal_espontaneo")
        # ESPERADO: solo el de hace 4 meses con su recién nacido.
        self.assertEqual(completar_demo.Command()._partos_terminados(), 1)
        viejo.refresh_from_db()
        en_curso.refresh_from_db()
        self.assertTrue(viejo.parto_finalizado)
        self.assertFalse(en_curso.parto_finalizado)
