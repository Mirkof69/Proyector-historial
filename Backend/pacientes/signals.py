"""Signals para módulo de Pacientes"""

from datetime import date

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from notificaciones.models import Notificacion

from .models import Paciente


@receiver(post_save, sender=Paciente)
def paciente_creado_o_actualizado(_sender, instance, created, **_kwargs):
    """Signal cuando se crea o actualiza un paciente
    """
    if created:
        # Nuevo paciente registrado
        Notificacion.objects.create(
            titulo="Nueva Paciente Registrada",
            mensaje=f"Se ha registrado a {instance.nombre_completo} en el sistema",
            tipo="alerta_informacion",
            entidad_tipo="paciente",
            entidad_id=instance.id,
            prioridad="baja",
        )

        # Verificar si es paciente de alto riesgo
        verificar_paciente_alto_riesgo(instance)


@receiver(pre_save, sender=Paciente)
def calcular_datos_paciente(_sender, instance, **_kwargs):
    """Calcular datos automáticos antes de guardar
    """
    # Calcular edad actual si no está definida
    if instance.fecha_nacimiento and not instance.edad:
        hoy = date.today()
        instance.edad = (
            hoy.year
            - instance.fecha_nacimiento.year
            - (
                (hoy.month, hoy.day)
                < (instance.fecha_nacimiento.month, instance.fecha_nacimiento.day)
            )
        )

    # Generar nombre completo
    if not instance.nombre_completo:
        partes = [instance.nombre]
        if hasattr(instance, "apellido_paterno") and instance.apellido_paterno:
            partes.append(instance.apellido_paterno)
        if hasattr(instance, "apellido_materno") and instance.apellido_materno:
            partes.append(instance.apellido_materno)
        instance.nombre_completo = " ".join(partes)


@receiver(post_save, sender=Paciente)
def verificar_cumpleanos_proximo(_sender, instance, _created, **_kwargs):
    """Notificar cumpleaños próximos
    """
    if instance.fecha_nacimiento:
        hoy = date.today()
        proximo_cumple = date(
            hoy.year, instance.fecha_nacimiento.month, instance.fecha_nacimiento.day,
        )

        if proximo_cumple < hoy:
            proximo_cumple = date(
                hoy.year + 1,
                instance.fecha_nacimiento.month,
                instance.fecha_nacimiento.day,
            )

        dias_para_cumple = (proximo_cumple - hoy).days

        if 0 <= dias_para_cumple <= 7:
            Notificacion.objects.create(
                titulo=" Cumpleaños Próximo",
                mensaje=f"El cumpleaños de {instance.nombre_completo} es en {dias_para_cumple} día(s)",
                tipo="recordatorio",
                entidad_tipo="paciente",
                entidad_id=instance.id,
                prioridad="baja",
            )


def verificar_paciente_alto_riesgo(paciente):
    """Verificar si la paciente tiene factores de alto riesgo
    """
    factores_riesgo = []

    # Edad materna avanzada
    if paciente.edad and paciente.edad >= 35:
        factores_riesgo.append("Edad materna avanzada (≥35 años)")

    # Edad materna muy joven
    if paciente.edad and paciente.edad < 18:
        factores_riesgo.append("Edad materna muy joven (<18 años)")

    # Si hay factores de riesgo, notificar
    if factores_riesgo:
        mensaje = (
            f"Factores de riesgo detectados para {paciente.nombre_completo}:\n"
            + "\n".join(f"- {f}" for f in factores_riesgo)
        )

        Notificacion.objects.create(
            titulo="ALERTA: Factores de Riesgo Detectados",
            mensaje=mensaje,
            tipo="alerta_advertencia",
            entidad_tipo="paciente",
            entidad_id=paciente.id,
            prioridad="normal",
        )


@receiver(post_save, sender=Paciente)
def actualizar_historia_clinica(_sender, _instance, created, **_kwargs):
    """Inicializar historia clínica al crear paciente
    """
    if created:
        # Aquí podrías crear registro inicial de historia clínica
        # o realizar otras inicializaciones necesarias
        pass
