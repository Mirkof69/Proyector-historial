"""Tests de la Historia Clínica Integrada.

Por qué existe este archivo
---------------------------
La historia clínica es el documento donde el médico ve TODO lo de una paciente.
Si un dato falta, sobra o está duplicado, la decisión clínica se toma sobre
información falsa. Estos tests fijan tres cosas:

  1. Cada estudio de laboratorio aparece UNA sola vez, sin importar cuántos
     embarazos tenga la paciente.
  2. Los contadores del resumen coinciden con lo que realmente hay en la base.
  3. Una paciente sin datos no rompe el informe: dice que no tiene, en cero.

El bug que motivó el punto 1: la consulta de laboratorios se hacía DENTRO del
bucle de embarazos con `Q(control_prenatal__embarazo=embarazo) | Q(paciente=
paciente)`. La segunda mitad de ese OR trae todos los laboratorios de la
paciente, así que con 3 embarazos cada análisis se contaba y se listaba 3
veces. El mismo error estaba en el contador `total_laboratorios`.
"""

import datetime

from django.test import TestCase

from controles.models import ControlPrenatal
from embarazos.models import Embarazo
from laboratorio.models import ExamenLaboratorio, TipoExamen
from pacientes.models import Paciente
from pacientes.views import construir_historia_clinica
from usuarios.models import Usuario


class HistoriaClinicaIntegradaTest(TestCase):
    """La historia clínica debe reflejar exactamente lo que hay en la base."""

    @classmethod
    def setUpTestData(cls):
        """Una paciente con 3 embarazos y 2 laboratorios: el caso del bug."""
        cls.medica = Usuario.objects.create_user(
            email="medica@historia.test",
            nombre="Rosa",
            apellido_paterno="Condori",
            password="clave-de-prueba-123",
        )
        cls.paciente = Paciente.objects.create(
            nombre="Teresa",
            apellido_paterno="Mamani",
            apellido_materno="Huanca",
            fecha_nacimiento=datetime.date(1990, 3, 20),
            genero="femenino",
            ci="8811223",
        )
        cls.embarazos = [
            Embarazo.objects.create(
                paciente=cls.paciente,
                fecha_ultima_menstruacion=datetime.date(2020 + i, 1, 10),
                estado="finalizado" if i < 2 else "activo",
                numero_gesta=i + 1,
                numero_para=0,
                numero_abortos=0,
                numero_cesareas=0,
            )
            for i in range(3)
        ]
        cls.tipo = TipoExamen.objects.create(
            nombre="Hemograma Completo",
            codigo="HEM-001",
            categoria="hematologia",
        )
        # Dos laboratorios de la paciente, NO atados a un control concreto:
        # es el caso que el `| Q(paciente=paciente)` multiplicaba.
        cls.laboratorios = [
            ExamenLaboratorio.objects.create(
                paciente=cls.paciente,
                tipo_examen=cls.tipo,
                fecha_solicitud=datetime.date(2026, 3, 1 + i),
            )
            for i in range(2)
        ]

    def test_cada_laboratorio_aparece_una_sola_vez(self):
        """ESPERADO: 2 laboratorios en el timeline. OBTENIDO antes del arreglo: 6."""
        timeline, _ = construir_historia_clinica(self.paciente)

        labs = [e for e in timeline if e.get("tipo_evento") == "laboratorio"]
        ids = [e.get("id") for e in labs]

        assert len(labs) == 2, (
            f"Esperado 2 laboratorios, obtenido {len(labs)}. "
            f"Con 3 embarazos, el bug los multiplicaba a 6."
        )
        assert len(set(ids)) == len(ids), f"Hay laboratorios repetidos: {ids}"

    def test_el_contador_de_laboratorios_coincide_con_la_base(self):
        """ESPERADO: total_laboratorios == 2, igual que en la base de datos."""
        _, estadisticas = construir_historia_clinica(self.paciente)

        real = ExamenLaboratorio.objects.filter(paciente=self.paciente).count()
        assert estadisticas["total_laboratorios"] == real == 2, (
            f"El resumen dice {estadisticas['total_laboratorios']} laboratorios "
            f"pero en la base hay {real}."
        )

    def test_los_contadores_reflejan_lo_que_hay(self):
        """ESPERADO: los contadores del resumen cuadran uno a uno con la base."""
        ControlPrenatal.objects.create(
            paciente=self.paciente,
            embarazo=self.embarazos[0],
            fecha_control=datetime.date(2026, 4, 5),
            numero_control=1,
            semanas_gestacion=28,
            peso_actual=62.5,
            talla=158,
            presion_arterial_sistolica=110,
            presion_arterial_diastolica=70,
        )
        _, est = construir_historia_clinica(self.paciente)

        assert est["total_embarazos"] == 3
        assert est["embarazos_activos"] == 1
        assert est["total_controles"] == 1
        assert est["total_ecografias"] == 0
        assert est["total_partos"] == 0

    def test_el_total_de_eventos_es_la_suma_real(self):
        """ESPERADO: total_eventos == largo del timeline, sin inflar."""
        timeline, est = construir_historia_clinica(self.paciente)

        assert est["total_eventos"] == len(timeline)
        # 3 embarazos + 2 laboratorios, nada más sembrado.
        assert est["total_eventos"] == 5, (
            f"Esperado 5 eventos (3 embarazos + 2 laboratorios), "
            f"obtenido {est['total_eventos']}."
        )

    def test_paciente_sin_datos_dice_que_no_tiene(self):
        """ESPERADO: ceros y timeline vacío, no un error ni datos ajenos.

        El médico tiene que poder distinguir "no tiene estudios" de "falló la
        consulta". Ambos casos se veían igual si esto reventaba.
        """
        sola = Paciente.objects.create(
            nombre="Ana",
            apellido_paterno="Quispe",
            apellido_materno="Poma",
            fecha_nacimiento=datetime.date(1995, 8, 8),
            genero="femenino",
            ci="7700111",
        )
        timeline, est = construir_historia_clinica(sola)

        assert timeline == []
        assert est["total_embarazos"] == 0
        assert est["total_controles"] == 0
        assert est["total_laboratorios"] == 0
        assert est["total_eventos"] == 0

    def test_no_se_mezclan_datos_de_otras_pacientes(self):
        """ESPERADO: la historia de una paciente no incluye nada de otra.

        Es el equivalente, dentro de una misma clínica, del aislamiento entre
        tenants: la historia clínica de Teresa no puede mostrar los análisis
        de Ana.
        """
        otra = Paciente.objects.create(
            nombre="Ana",
            apellido_paterno="Flores",
            apellido_materno="Yujra",
            fecha_nacimiento=datetime.date(1992, 2, 2),
            genero="femenino",
            ci="7700222",
        )
        ExamenLaboratorio.objects.create(
            paciente=otra, tipo_examen=self.tipo,
            fecha_solicitud=datetime.date(2026, 5, 5),
        )

        timeline, est = construir_historia_clinica(self.paciente)
        labs = [e for e in timeline if e.get("tipo_evento") == "laboratorio"]

        assert len(labs) == 2, "Se coló un laboratorio de otra paciente."
        assert est["total_laboratorios"] == 2
