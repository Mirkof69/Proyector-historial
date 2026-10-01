"""Unifica «Evolución del embarazo» dentro de «Notas de evolución».

Había dos módulos para lo mismo a ojos de quien usa el sistema. La
«evolución» era una línea de tiempo escrita A MANO («hubo un control», «hubo
una ecografía») que duplicaba los registros reales —y podía contradecirlos—;
la línea de tiempo del embarazo ya se arma sola con controles, ecografías,
citas y laboratorios. Lo que una evolución sí aportaba era texto clínico libre,
que es exactamente una nota de evolución.

Se copia cada evolución a una nota (no se borra nada: la tabla vieja queda de
solo lectura). Es idempotente: una evolución ya importada no se duplica.
"""
from datetime import datetime, time

from django.db import migrations
from django.utils import timezone

TIPO = {"control": "control_prenatal", "urgencia": "urgencia"}
MARCA = "[Importado de Evolución del embarazo #{}]"
# La evolución vieja no tenía estos campos; vacíos, la nota no se podría
# volver a guardar desde el formulario (son obligatorios).
NO_REGISTRADO = "No registrado en el registro original."


def importar(apps, schema_editor):
    Evolucion = apps.get_model("evoluciones", "EvolucionEmbarazo")
    Nota = apps.get_model("notas_evolucion", "NotaEvolucion")
    Usuario = apps.get_model("usuarios", "Usuario")
    respaldo = (Usuario.objects.filter(rol="administrador", activo=True).order_by("id").first()
                or Usuario.objects.filter(is_superuser=True).order_by("id").first())
    for ev in Evolucion.objects.all().order_by("id"):
        marca = MARCA.format(ev.pk)
        if Nota.objects.filter(observaciones__startswith=marca).exists():
            continue
        medico = ev.medico or respaldo
        if medico is None:
            continue  # sin ningún usuario no hay a quién atribuir la nota
        observaciones = f"{marca} Tipo de evento original: {ev.get_tipo_evento_display() if hasattr(ev, 'get_tipo_evento_display') else ev.tipo_evento}."
        if ev.medico is None:
            observaciones += " Sin médico en el registro original: atribuida al administrador."
        Nota.objects.create(
            paciente_id=ev.paciente_id,
            embarazo_id=ev.embarazo_id,
            medico=medico,
            fecha_consulta=timezone.make_aware(datetime.combine(ev.fecha_evento, time(12, 0))),
            tipo_consulta=TIPO.get(ev.tipo_evento, "seguimiento"),
            motivo_consulta=ev.descripcion or "(sin descripción)",
            examen_fisico=NO_REGISTRADO,
            diagnosticos=NO_REGISTRADO,
            plan_tratamiento=NO_REGISTRADO,
            observaciones=observaciones,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("notas_evolucion", "0003_historia_clinica_protegida"),
        ("evoluciones", "0001_initial"),
        ("usuarios", "__first__"),
    ]

    operations = [migrations.RunPython(importar, migrations.RunPython.noop)]
