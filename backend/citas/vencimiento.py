"""Cierre de las citas cuyo día ya pasó sin que se registrara la atención.

Una cita «agendada» o «confirmada» de ayer o antes ya no va a ocurrir: si la
paciente hubiera venido, recepción la habría marcado presente y el médico la
habría completado. Nada las cerraba, así que la agenda seguía mostrando como
pendientes citas vencidas hace semanas y los reportes las contaban como por
atender. Quedan como «No asistió», con su línea en el historial de la cita.

Las del día en curso no se tocan aunque su hora haya pasado: la paciente puede
llegar tarde y recepción todavía la puede atender.
"""
from django.core.cache import cache
from django.db import connection, transaction
from django.utils import timezone

from .models import Cita, HistorialCita

PENDIENTES = ("agendada", "confirmada")
MOTIVO = "Cierre automático: el día de la cita pasó sin que se registrara la atención."


def cerrar_citas_vencidas(hoy=None) -> int:
    """Pasa a «No asistió» las citas pendientes de días anteriores a `hoy`."""
    hoy = hoy or timezone.localdate()
    with transaction.atomic():
        vencidas = list(
            Cita.objects.select_for_update()
            .filter(fecha_cita__lt=hoy, estado__in=PENDIENTES)
            .values_list("id", "estado"),
        )
        if not vencidas:
            return 0
        # update() y bulk_create(): sin señales, para no mandar al médico una
        # notificación por cada cita vieja que se cierra.
        Cita.objects.filter(pk__in=[pk for pk, _ in vencidas]).update(
            estado="no_asistio", fecha_actualizacion=timezone.now(),
        )
        HistorialCita.objects.bulk_create(
            [HistorialCita(cita_id=pk, estado_anterior=estado, estado_nuevo="no_asistio",
                           motivo_cambio=MOTIVO) for pk, estado in vencidas],
            batch_size=1000,
        )
    return len(vencidas)


def cerrar_citas_vencidas_hoy() -> int:
    """Lo mismo, a lo sumo una vez por día y por clínica.

    El sistema no tiene un `celery beat` permanente: el cierre corre al abrir
    cualquier pantalla de citas (y al arrancar, desde INICIAR.bat). La marca en
    caché evita repetir la consulta en cada petición del día.
    """
    hoy = timezone.localdate()
    clave = f"citas-vencidas:{getattr(connection, 'schema_name', 'public')}:{hoy.isoformat()}"
    if not cache.add(clave, 1, timeout=60 * 60 * 26):
        return 0
    return cerrar_citas_vencidas(hoy)
