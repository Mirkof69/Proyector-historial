"""Tests de rendimiento: el listado de pacientes no debe hacer N+1.

Por que existe este archivo
---------------------------
`PacienteListSerializer` expone 8 campos calculados que tocan las relaciones
`embarazos`, `controles_prenatales` y `partos`. Sin precarga, cada paciente
dispara ~8 consultas: serializar 200 pacientes costaba 1601 consultas y
1717 ms, y bajo 100 usuarios concurrentes el endpoint llegaba a 42 segundos
de mediana.

El `prefetch_related` del ViewSet existia, pero estaba aplicado SOLO en
`action == "retrieve"` (el detalle de una paciente), que es justo el caso que
no lo necesita. El listado no llevaba ninguno.

Estos tests fijan el contrato: el numero de consultas NO puede crecer con la
cantidad de pacientes. Son tests de comportamiento, no de humo: si alguien
vuelve a poner un `.filter()` o un `.order_by()` sobre una relacion precargada
—que anula la cache del prefetch— estos tests fallan.
"""

import datetime

from django.test import TestCase

from embarazos.models import Embarazo
from pacientes.models import Paciente
from pacientes.serializers import PacienteListSerializer
from pacientes.views import PacienteViewSet
from usuarios.models import Usuario


def _crear_pacientes(cantidad, con_embarazo=True):
    """Crea `cantidad` pacientes, cada una con un embarazo si se pide."""
    creadas = []
    # Desplazamiento por los ya existentes: la CI es unica (ci_hash), asi que
    # dos tandas seguidas colisionarian empezando ambas en cero.
    inicio = Paciente.objects.count()
    for i in range(inicio, inicio + cantidad):
        paciente = Paciente.objects.create(
            nombre=f"Paciente{i}",
            apellido_paterno="Mamani",
            apellido_materno="Choque",
            fecha_nacimiento=datetime.date(1990, 5, 15),
            genero="femenino",
            ci=f"9{i:07d}",
        )
        if con_embarazo:
            Embarazo.objects.create(
                paciente=paciente,
                fecha_ultima_menstruacion=datetime.date(2026, 1, 10),
                estado="activo",
                numero_gesta=1,
                numero_para=0,
                numero_abortos=0,
                numero_cesareas=0,
            )
        creadas.append(paciente)
    return creadas


class ListadoPacientesSinNMasUnoTest(TestCase):
    """El costo en consultas del listado debe ser constante, no lineal."""

    @classmethod
    def setUpTestData(cls):
        """Un usuario para las relaciones de auditoria y nada mas."""
        cls.admin = Usuario.objects.create_superuser(
            email="admin@rendimiento.test",
            nombre="Admin",
            apellido_paterno="Rendimiento",
            password="adminpass123",
        )

    def _queryset_del_viewset(self):
        """El mismo queryset optimizado que usa el ViewSet para listar."""
        return PacienteViewSet.optimizar_para_listado(Paciente.objects.all())

    def test_consultas_no_crecen_con_el_numero_de_pacientes(self):
        """5 pacientes y 20 pacientes deben costar el MISMO numero de consultas.

        Es la definicion exacta de "no hay N+1": si el costo depende de la
        cantidad de filas, el prefetch no esta funcionando.
        """
        _crear_pacientes(5)
        with self.assertNumQueries(4):
            PacienteListSerializer(self._queryset_del_viewset(), many=True).data

        _crear_pacientes(15)  # ahora son 20
        with self.assertNumQueries(4):
            PacienteListSerializer(self._queryset_del_viewset(), many=True).data

    def test_el_listado_de_200_pacientes_cuesta_pocas_consultas(self):
        """El caso real que rompia: 200 pacientes (PAGE_SIZE por defecto).

        Antes: 1601 consultas. El limite de 10 deja margen para cambios
        razonables sin volver a permitir un N+1.
        """
        _crear_pacientes(200)
        queryset = self._queryset_del_viewset()
        with self.assertNumQueries(4):
            datos = PacienteListSerializer(queryset, many=True).data
        assert len(datos) == 200

    def test_los_datos_obstetricos_siguen_siendo_correctos(self):
        """La optimizacion no puede cambiar lo que se muestra en pantalla.

        Se verifica contra un embarazo real: si el filtrado en Python sobre la
        cache del prefetch estuviera mal, estos campos saldrian vacios y el
        test de consultas pasaria igual.
        """
        paciente = _crear_pacientes(1, con_embarazo=False)[0]
        Embarazo.objects.create(
            paciente=paciente,
            fecha_ultima_menstruacion=datetime.date(2026, 2, 1),
            estado="activo",
            numero_gesta=3,
            numero_para=2,
            numero_abortos=1,
            numero_cesareas=1,
        )
        fila = PacienteListSerializer(self._queryset_del_viewset(), many=True).data[0]

        assert fila["embarazos_activos"] is True
        assert fila["numero_gesta"] == 3
        assert fila["numero_para"] == 2
        assert fila["numero_abortos"] == 1
        assert fila["numero_cesareas"] == 1
        assert fila["ultimo_estado_obstetrico"] == "GESTANDO"

    def test_paciente_sin_embarazos_no_rompe(self):
        """Sin relaciones, los campos obstetricos deben ser neutros, no error."""
        _crear_pacientes(1, con_embarazo=False)
        fila = PacienteListSerializer(self._queryset_del_viewset(), many=True).data[0]

        assert fila["embarazos_activos"] is False
        assert fila["numero_gesta"] == 0
        assert fila["ultimo_estado_obstetrico"] is None
        assert fila["fecha_ultimo_evento"] is None
