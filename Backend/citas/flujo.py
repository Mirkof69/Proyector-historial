"""La cita del día sigue a la paciente por el resto del flujo.

Antes la cita quedaba aislada: el triaje no la tomaba (la paciente pasaba por
enfermería y su cita seguía «agendada») y el control prenatal tampoco la
cerraba, así que al día siguiente la atendida figuraba como «No asistió».
- Triaje de una paciente citada hoy → la cita se vincula al triaje y pasa a
  «En sala de espera» (la llegada quedó registrada en enfermería).
- Control prenatal con fecha de hoy → la cita de hoy pasa a «Completada».
Cada cambio deja su línea en el historial de la cita, con quién lo hizo.
"""
from django.utils import timezone

from .models import Cita, HistorialCita


def _cambiar(cita, estado, motivo, usuario):
    anterior = cita.estado
    cita.estado = estado
    cita.save(update_fields=["estado", "fecha_actualizacion"])
    HistorialCita.objects.create(cita=cita, estado_anterior=anterior, estado_nuevo=estado,
                                 motivo_cambio=motivo, usuario=usuario)


def _de_hoy(paciente_id):
    return (Cita.objects.filter(paciente_id=paciente_id, fecha_cita=timezone.localdate(),
                                estado__in=Cita.OCUPAN_TURNO).order_by("hora_cita"))


def llegada_por_triaje(triaje, usuario) -> Cita | None:
    """Vincula el triaje con la cita de hoy de la paciente y la pone en espera."""
    cita = triaje.cita
    if cita is None:
        cita = _de_hoy(triaje.paciente_id).filter(triaje__isnull=True).first()
        if cita is None:
            return None
        triaje.cita = cita
        triaje.save(update_fields=["cita"])
    if cita.estado in ("agendada", "confirmada"):
        _cambiar(cita, "en_espera", "Llegada registrada en el triaje", usuario)
    return cita


def atendida_por_control(control, usuario) -> Cita | None:
    """El control prenatal de hoy cierra la cita de hoy de la paciente."""
    if control.fecha_control != timezone.localdate():
        return None
    cita = _de_hoy(control.paciente_id).first()
    if cita is not None:
        _cambiar(cita, "completada", f"Atendida: control prenatal n.º {control.numero_control}", usuario)
    return cita
