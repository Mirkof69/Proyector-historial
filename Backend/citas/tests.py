"""Tests para el módulo de Citas Médicas"""

from datetime import date, time, timedelta
from typing import cast

from django.test import TestCase
from django.utils import timezone

from consultorios.models import Consultorio
from pacientes.models import Paciente
from usuarios.models import Usuario

from .models import Cita, Disponibilidad


class CitaModelTestCase(TestCase):
    """Citamodeltestcase"""
    def setUp(self):
        """Setup"""
        self.medico = Usuario.objects.create_user(
            email="medico_test@clinica.com",
            password="password123",
            rol="medico",
            nombre="Dr. Test",
            apellido_paterno="Medico",
        )
        self.paciente = Paciente.objects.create(
            nombre="Paciente",
            apellido_paterno="Test",
            fecha_nacimiento=date(1990, 1, 1),
            genero="F",
            ci="1234567",
        )
        self.consultorio = Consultorio.objects.create(
            nombre="Consultorio 1", ubicacion="Piso 1",
        )

    def test_crear_cita_valida(self):
        """Test crear una cita en el futuro"""
        fecha_futura = timezone.now().date() + timedelta(days=5)
        cita = cast(Cita, Cita.objects.create(
            paciente=self.paciente,
            medico=self.medico,
            consultorio=self.consultorio,
            fecha_cita=fecha_futura,
            hora_cita=time(10, 0),
            motivo="Consulta general",
        ))
        self.assertIsNotNone(cita.id)
        self.assertEqual(cita.estado, "agendada")

    def test_validacion_fecha_pasada(self):
        """No se deben permitir citas en el pasado"""
        fecha_pasada = timezone.now().date() - timedelta(days=1)
        cita = Cita(
            paciente=self.paciente,
            medico=self.medico,
            fecha_cita=fecha_pasada,
            hora_cita=time(10, 0),
            motivo="Intento pasado",
        )
        with self.assertRaises(Exception):  # ValidationError
            cita.full_clean()
            cita.save()

    def test_conflicto_horario_medico(self):
        """No se pueden agendar dos citas al mismo tiempo para el mismo médico"""
        fecha = timezone.now().date() + timedelta(days=5)
        hora = time(11, 0)

        Cita.objects.create(
            paciente=self.paciente,
            medico=self.medico,
            fecha_cita=fecha,
            hora_cita=hora,
            motivo="Cita 1",
        )

        cita2 = Cita(
            paciente=self.paciente,
            medico=self.medico,
            fecha_cita=fecha,
            hora_cita=hora,
            motivo="Cita 2 (Conflicto)",
        )

        with self.assertRaises(Exception):
            cita2.full_clean()
            cita2.save()

    def test_flujo_estados(self):
        """Test transitions de estados"""
        cita = Cita.objects.create(
            paciente=self.paciente,
            medico=self.medico,
            fecha_cita=timezone.now().date() + timedelta(days=2),
            hora_cita=time(9, 0),
            motivo="Flujo",
        )

        cita.confirmar(self.medico)
        self.assertEqual(cita.estado, "confirmada")
        self.assertIsNotNone(cita.fecha_confirmacion)

        cita.completar()
        self.assertEqual(cita.estado, "completada")


class DisponibilidadTestCase(TestCase):
    """Disponibilidadtestcase"""
    def setUp(self):
        """Setup"""
        self.medico = Usuario.objects.create_user(
            email="medico_disp@clinica.com",
            nombre="Medico",
            apellido_paterno="Disp",
            password="password123",
            rol="medico",
        )

    def test_crear_disponibilidad(self):
        """Test crear disponibilidad"""
        disp = Disponibilidad.objects.create(
            medico=self.medico,
            dia_semana=0,  # Lunes
            hora_inicio=time(8, 0),
            hora_fin=time(12, 0),
        )
        self.assertEqual(
            len(disp.horas_disponibles), 8,
        )  # 8 slots de 30 mins en 4 horas
