"""La campana tiene que avisar, y la tabla no puede crecer sin freno.

Por qué existe este archivo
---------------------------
El sistema creaba las notificaciones bien —alertas médicas, pacientes
registradas, recordatorios— y aun así **no avisaba de ninguna**. Medido sobre
el tenant real el 5 de septiembre de 2026:

  - 15.698 notificaciones acumuladas, 15.694 sin leer, **849 urgentes o
    críticas que nadie había visto**.
  - La campana del encabezado cargaba la lista SOLO al abrir el desplegable y
    contaba sobre esa lista. Como empezaba vacía, **el badge mostraba 0**
    hasta que alguien hacía clic. Había que abrir la campana para enterarse de
    que había algo que mirar.
  - El contexto que sí vigilaba en tiempo real no lo usaba ningún componente.
  - Y cuando se refrescaba, pedía `GET /notificaciones/`: 55.888 bytes y 2,2
    segundos, cada 30 segundos, por cada usuaria. Con cien personas eso son
    unas siete peticiones ocupadas de forma permanente en pintar un número.
  - Ese número además salía mal: la lista viene paginada de 200 en 200, así que
    el contador **no podía pasar de 200** aunque hubiera 7.135 pendientes.

Y las tres rutinas de mantenimiento archivaban o borraban **cero filas,
siempre**, por condiciones que no se cumplían nunca.

Cada test declara el resultado ESPERADO y lo compara con el OBTENIDO.
"""

import datetime

from django.utils import timezone
from rest_framework.test import APITestCase

from notificaciones.mantenimiento import (
    DIAS_PARA_ARCHIVAR,
    archivar_por_antiguedad,
    borrar_archivadas_antiguas,
    estado_actual,
)
from notificaciones.models import Notificacion, PrioridadNotificacion, TipoNotificacion
from usuarios.models import Usuario

CLAVE = "clave-de-prueba-123"


def _envejecer(notificacion, dias):
    """Mueve la fecha de creación hacia atrás.

    Hace falta porque `fecha_creacion` es `auto_now_add`: se fija al crear y no
    se puede pasar por el constructor. Sin esto no hay forma de probar nada que
    dependa de la antigüedad.
    """
    Notificacion.objects.filter(pk=notificacion.pk).update(
        fecha_creacion=timezone.now() - datetime.timedelta(days=dias),
    )
    notificacion.refresh_from_db()
    return notificacion


class _ConMedica(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medica = Usuario.objects.create_user(
            email="dra.campana@test.bo", nombre="Elena",
            apellido_paterno="Choque", password=CLAVE, rol="medico",
        )

    def setUp(self):
        self.client.force_authenticate(user=self.medica)

    def _notificar(self, titulo, prioridad=PrioridadNotificacion.NORMAL, dias=0):
        n = Notificacion.objects.create(
            usuario=self.medica,
            tipo=TipoNotificacion.ALERTA_ADVERTENCIA,
            titulo=titulo,
            mensaje="Cuerpo del aviso",
            prioridad=prioridad,
        )
        return _envejecer(n, dias) if dias else n


class LaCampanaAvisaSinAbrirlaTest(_ConMedica):
    """El resumen tiene que dar el número correcto de una sola llamada."""

    def test_el_resumen_cuenta_TODAS_las_pendientes_no_solo_una_pagina(self):
        """ESPERADO: 250, no 200.

        Es el fallo exacto que había: la lista viene paginada de 200 en 200 y
        el contador se calculaba sobre lo recibido, así que topaba en 200.
        Se crean 250 a propósito para cruzar ese tope.
        """
        for i in range(250):
            self._notificar(f"Aviso {i}")

        respuesta = self.client.get("/api/notificaciones/resumen/")

        assert respuesta.status_code == 200
        assert respuesta.data["pendientes"] == 250, (
            f"El resumen dice {respuesta.data['pendientes']} pendientes de 250. "
            f"Si dice 200, el contador volvió a calcularse sobre una página."
        )

    def test_el_resumen_no_manda_las_250_notificaciones(self):
        """ESPERADO: como mucho 8 en `ultimas`.

        La campana necesita un número y unas pocas líneas, no la tabla entera.
        Mandarla completa costaba 55 KB por refresco.
        """
        for i in range(250):
            self._notificar(f"Aviso {i}")

        respuesta = self.client.get("/api/notificaciones/resumen/")

        assert len(respuesta.data["ultimas"]) <= 8, (
            f"El resumen manda {len(respuesta.data['ultimas'])} notificaciones. "
            f"Es el endpoint de la campana: tiene que ser pequeño."
        )

    def test_las_criticas_se_cuentan_aparte(self):
        """ESPERADO: 3 urgentes de 5 pendientes.

        El color del badge depende de esto. Si las críticas no se distinguen,
        una alerta que hay que mirar ahora se ve igual que un recordatorio.
        """
        self._notificar("Rutina 1")
        self._notificar("Rutina 2")
        self._notificar("Grave 1", PrioridadNotificacion.CRITICA)
        self._notificar("Grave 2", PrioridadNotificacion.CRITICA)
        self._notificar("Grave 3", PrioridadNotificacion.URGENTE)

        respuesta = self.client.get("/api/notificaciones/resumen/")

        assert respuesta.data["pendientes"] == 5
        assert respuesta.data["urgentes"] == 3, (
            "Las críticas no se están contando junto a las urgentes: el badge "
            "no se pondría rojo con una alerta crítica esperando."
        )

    def test_las_leidas_no_cuentan(self):
        """ESPERADO: 1 pendiente de 3 creadas."""
        a = self._notificar("Vista 1")
        b = self._notificar("Vista 2")
        self._notificar("Sin ver")
        a.marcar_como_leida()
        b.marcar_como_leida()

        respuesta = self.client.get("/api/notificaciones/resumen/")

        assert respuesta.data["pendientes"] == 1

    def test_las_archivadas_no_cuentan(self):
        """ESPERADO: 1 pendiente.

        Archivar es lo que hace el mantenimiento con lo viejo. Si lo archivado
        siguiera contando, el mantenimiento no serviría de nada.
        """
        vieja = self._notificar("Vieja")
        self._notificar("Reciente")
        vieja.archivada = True
        vieja.save(update_fields=["archivada"])

        respuesta = self.client.get("/api/notificaciones/resumen/")

        assert respuesta.data["pendientes"] == 1

    def test_sin_notificaciones_devuelve_cero_y_no_falla(self):
        """ESPERADO: 0 y lista vacía, no un error."""
        respuesta = self.client.get("/api/notificaciones/resumen/")

        assert respuesta.status_code == 200
        assert respuesta.data["pendientes"] == 0
        assert respuesta.data["urgentes"] == 0
        assert respuesta.data["ultimas"] == []


class ElListadoDeNoLeidasVaPaginadoTest(_ConMedica):
    """`no_leidas` serializaba todas de golpe."""

    def test_no_devuelve_las_500_de_una_vez(self):
        """ESPERADO: como mucho 200 por página.

        Sin paginar, con las 7.135 pendientes que había en el tenant real,
        esta respuesta eran varios megabytes en una sola petición.
        """
        for i in range(500):
            self._notificar(f"Aviso {i}")

        respuesta = self.client.get("/api/notificaciones/no_leidas/")

        assert respuesta.status_code == 200
        assert len(respuesta.data["results"]) <= 200, (
            f"Devolvió {len(respuesta.data['results'])} de golpe: volvió a "
            f"serializar todas las pendientes sin paginar."
        )
        assert respuesta.data["count"] == 500, "El total sigue siendo correcto."


class ElMantenimientoArchivaDeVerdadTest(_ConMedica):
    """Las tres rutinas anteriores archivaban y borraban cero. Siempre."""

    def test_archiva_lo_rutinario_pasada_su_ventana(self):
        """ESPERADO: se archiva la de 70 días, no la de 10.

        La ventana de prioridad normal son 60 días.
        """
        vieja = self._notificar("De hace tiempo", dias=70)
        nueva = self._notificar("De ayer", dias=10)

        archivar_por_antiguedad()

        vieja.refresh_from_db()
        nueva.refresh_from_db()
        assert vieja.archivada is True, "No archivó una de 70 días con ventana de 60."
        assert nueva.archivada is False, "Archivó una de 10 días: la ventana se ignoró."

    def test_las_criticas_aguantan_mucho_mas_que_las_rutinarias(self):
        """ESPERADO: a los 70 días la normal se archiva y la crítica no.

        Es la razón de que las ventanas dependan de la prioridad. Una alerta
        crítica sin ver tiene que seguir molestando en la campana bastante más
        que un recordatorio de control.
        """
        rutinaria = self._notificar("Recordatorio", PrioridadNotificacion.NORMAL, dias=70)
        critica = self._notificar("Riesgo alto", PrioridadNotificacion.CRITICA, dias=70)

        archivar_por_antiguedad()

        rutinaria.refresh_from_db()
        critica.refresh_from_db()
        assert rutinaria.archivada is True
        assert critica.archivada is False, (
            "Se archivó una alerta crítica a los 70 días. Su ventana son "
            f"{DIAS_PARA_ARCHIVAR[PrioridadNotificacion.CRITICA]} días."
        )

    def test_archivar_baja_el_contador_de_la_campana(self):
        """ESPERADO: de 3 pendientes a 1.

        Es el punto de todo esto: que el número de la campana vuelva a
        significar algo en vez de crecer para siempre.
        """
        self._notificar("Vieja 1", dias=70)
        self._notificar("Vieja 2", dias=80)
        self._notificar("Reciente", dias=5)

        assert estado_actual()["pendientes"] == 3
        archivar_por_antiguedad()

        assert estado_actual()["pendientes"] == 1

    def test_simular_no_toca_nada(self):
        """ESPERADO: cuenta 1 pero la deja sin archivar.

        Sirve para poder ver el efecto sobre una base real antes de aplicarlo:
        la primera pasada tras meses sin mantenimiento archiva miles de golpe.
        """
        vieja = self._notificar("De hace tiempo", dias=70)

        resultado = archivar_por_antiguedad(simular=True)

        vieja.refresh_from_db()
        assert resultado["total"] == 1, "No contó la que archivaría."
        assert vieja.archivada is False, "Con --simular modificó la base."


class NoSeBorranLasAlertasClinicasTest(_ConMedica):
    """Archivar es reversible; borrar no. Las críticas no se borran solas."""

    def test_borra_lo_rutinario_ya_archivado_y_leido(self):
        """ESPERADO: desaparece."""
        n = self._notificar("Recordatorio viejo", PrioridadNotificacion.BAJA, dias=200)
        n.archivada = True
        n.leida = True
        n.save(update_fields=["archivada", "leida"])

        borradas = borrar_archivadas_antiguas()

        assert borradas == 1
        assert not Notificacion.objects.filter(pk=n.pk).exists()

    def test_NO_borra_una_alerta_critica_por_vieja_que_sea(self):
        """ESPERADO: sigue existiendo tras 400 días.

        Una alerta crítica es la prueba de que el sistema avisó. Que la borre
        una tarea automática es justo lo que no puede pasar en un expediente
        clínico.
        """
        n = self._notificar("Riesgo grave", PrioridadNotificacion.CRITICA, dias=400)
        n.archivada = True
        n.leida = True
        n.save(update_fields=["archivada", "leida"])

        borrar_archivadas_antiguas()

        assert Notificacion.objects.filter(pk=n.pk).exists(), (
            "Se borró automáticamente una alerta crítica. Se archivan, no se "
            "borran: la decisión de eliminarlas no la toma una tarea de cron."
        )

    def test_NO_borra_lo_que_todavia_no_se_ha_leido(self):
        """ESPERADO: sigue ahí.

        Borrar algo que nadie llegó a ver es perder el aviso sin dejar rastro.
        """
        n = self._notificar("Sin leer", PrioridadNotificacion.BAJA, dias=300)
        n.archivada = True
        n.save(update_fields=["archivada"])

        borrar_archivadas_antiguas()

        assert Notificacion.objects.filter(pk=n.pk).exists()
