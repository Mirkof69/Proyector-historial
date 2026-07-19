"""=============================================================================
TAREAS CELERY PARA NOTIFICACIONES AUTOMÁTICAS
=============================================================================
Tareas asíncronas para:
    pass
- Recordatorios automáticos de citas
- Alertas de exámenes pendientes
- Notificaciones de backups
- Limpieza de notificaciones antiguas
=============================================================================
"""

# from citas.models import Cita  # Deferred
# from laboratorio.models import ExamenLaboratorio  # Deferred
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from controles.models import ControlPrenatal
from embarazos.models import Embarazo

from .models import Notificacion, PrioridadNotificacion, TipoNotificacion

logger = logging.getLogger(__name__)
from .services import crear_notificacion_clinica


def _momento_de_la_cita(cita):
    """Fecha y hora de la cita como datetime con zona horaria.

    El modelo guarda `fecha_cita` y `hora_cita` en columnas separadas; esta
    función las combina para poder comparar contra "ahora".
    """
    from datetime import datetime, time

    hora = getattr(cita, "hora_cita", None) or time(0, 0)
    combinado = datetime.combine(cita.fecha_cita, hora)
    if timezone.is_naive(combinado):
        combinado = timezone.make_aware(combinado, timezone.get_current_timezone())
    return combinado


@shared_task(name="notificaciones.recordatorios_citas")
def enviar_recordatorios_citas():
    """Enviar recordatorios de citas próximas

    Se ejecuta cada hora y notifica citas que ocurran en las próximas 24 horas
    """
    from citas.models import Cita

    logger.info(" Iniciando envío de recordatorios de citas")

    ahora = timezone.now()
    ventana_inicio = ahora
    ventana_fin = ahora + timedelta(hours=24)

    # Cita NO tiene un campo `fecha_hora`: guarda `fecha_cita` (date) y
    # `hora_cita` (time) por separado. Filtrar por fecha_hora lanzaba
    # FieldError, o sea que esta tarea fallaba SIEMPRE y no se envió jamás un
    # recordatorio de cita. Se filtra por rango de fechas y luego se afina la
    # hora en Python, que es exacto y no depende del motor de base de datos.
    citas_proximas = [
        cita
        for cita in Cita.objects.filter(
            fecha_cita__gte=ventana_inicio.date(),
            fecha_cita__lte=ventana_fin.date(),
            estado__in=["agendada", "confirmada"],
        ).select_related("paciente", "medico")
        if ventana_inicio <= _momento_de_la_cita(cita) <= ventana_fin
    ]

    notificaciones_enviadas = 0

    for cita in citas_proximas:
        # Verificar si ya existe notificación para esta cita
        ya_notificado = Notificacion.objects.filter(
            entidad_tipo="cita",
            entidad_id=getattr(cita, 'id', None),
            tipo=TipoNotificacion.CITA_PROXIMA,
            fecha_creacion__gte=ahora - timedelta(hours=12),  # No duplicar en 12h
        ).exists()

        if ya_notificado:
            continue

        # Calcular tiempo hasta la cita
        tiempo_hasta = _momento_de_la_cita(cita) - ahora
        horas_hasta = int(tiempo_hasta.total_seconds() / 3600)

        # Determinar prioridad
        if horas_hasta <= 2:
            prioridad = PrioridadNotificacion.URGENTE
            mensaje_tiempo = "en menos de 2 horas"
        elif horas_hasta <= 6:
            prioridad = PrioridadNotificacion.ALTA
            mensaje_tiempo = f"en {horas_hasta} horas"
        else:
            prioridad = PrioridadNotificacion.NORMAL
            mensaje_tiempo = f"mañana a las {_momento_de_la_cita(cita).strftime('%H:%M')}"

        # Crear notificación
        try:
            # Antes: `if hasattr(cita.paciente, "usuario")`. Paciente NO tiene
            # relación `usuario` (el sistema no da cuentas a las pacientes),
            # así que la condición era SIEMPRE falsa y este recordatorio nunca
            # se emitía. Se avisa a quien puede actuar: el médico de la cita,
            # con fallback a administradores si no hay médico asignado.
            creadas = crear_notificacion_clinica(
                destinatario_preferido=cita.medico,
                tipo=TipoNotificacion.CITA_PROXIMA,
                prioridad=prioridad,
                titulo="Recordatorio de Cita",
                mensaje=f"{cita.paciente.nombre_completo} tiene una cita {mensaje_tiempo}. "
                f"Tipo: {getattr(cita, 'get_tipo_cita_display')()}",
                url=f"/dashboard/citas/{getattr(cita, 'id', None)}",
                entidad_tipo="cita",
                entidad_id=getattr(cita, 'id', None),
                metadata={
                    "cita_id": getattr(cita, 'id', None),
                    "fecha_cita": _momento_de_la_cita(cita).isoformat(),
                    "tipo": getattr(cita, 'tipo_cita', ''),
                    "horas_hasta": horas_hasta,
                },
            )
            notificaciones_enviadas += len(creadas)
        except Exception as e:
            logger.error("Error creando notificación para cita %s: %s", getattr(cita, 'id', None), e)

    logger.info("Recordatorios de citas enviados: %s", notificaciones_enviadas)
    return {"enviadas": notificaciones_enviadas}


@shared_task(name="notificaciones.alertas_examenes_pendientes")
def alertar_examenes_pendientes():
    """Alertar sobre exámenes de laboratorio pendientes hace más de 48 horas
    """
    from laboratorio.models import ExamenLaboratorio

    logger.info(" Revisando exámenes pendientes")

    fecha_corte = timezone.now() - timedelta(hours=48)

    # Buscar exámenes solicitados hace más de 48h que no tienen resultados
    examenes_pendientes = ExamenLaboratorio.objects.filter(
        fecha_solicitud__lte=fecha_corte,
        fecha_resultado__isnull=True,
        estado__in=["solicitado", "en_proceso"],
    ).select_related("paciente")

    notificaciones_enviadas = 0

    for examen in examenes_pendientes:
        # Verificar si ya se notificó recientemente
        ya_notificado = Notificacion.objects.filter(
            entidad_tipo="examen",
            entidad_id=getattr(examen, 'id', None),
            tipo=TipoNotificacion.RECORDATORIO,
            fecha_creacion__gte=timezone.now() - timedelta(days=7),
        ).exists()

        if ya_notificado:
            continue

        dias_pendiente = (timezone.now() - examen.fecha_solicitud).days

        try:
            # Igual que en las citas: la condición sobre `paciente.usuario`
            # era siempre falsa y la alerta nunca se emitía. Se avisa al
            # médico solicitante, que es quien puede reclamar el resultado.
            creadas = crear_notificacion_clinica(
                destinatario_preferido=getattr(examen, "medico_solicitante", None),
                tipo=TipoNotificacion.RECORDATORIO,
                prioridad=PrioridadNotificacion.ALTA,
                titulo="Examen de Laboratorio Pendiente",
                mensaje=f"{examen.paciente.nombre_completo} tiene un examen pendiente "
                f"desde hace {dias_pendiente} días. "
                f"Tipo: {examen.tipo_examen.nombre if hasattr(examen, 'tipo_examen') else 'Examen de laboratorio'}.",
                url=f"/dashboard/laboratorio/{getattr(examen, 'id', None)}",
                entidad_tipo="examen",
                entidad_id=getattr(examen, 'id', None),
                metadata={
                    "examen_id": getattr(examen, 'id', None),
                    "dias_pendiente": dias_pendiente,
                    "fecha_solicitud": examen.fecha_solicitud.isoformat(),
                },
            )
            notificaciones_enviadas += len(creadas)
        except Exception as e:
            logger.error("Error creando alerta para examen %s: %s", getattr(examen, 'id', None), e)

    logger.info(
        "✅ Alertas de exámenes pendientes enviadas: %s",
        notificaciones_enviadas,
    )
    return {"enviadas": notificaciones_enviadas}


@shared_task(name="notificaciones.notificar_backup_completado")
def notificar_backup_completado(backup_metadata):
    """Notificar a administradores que se completó un backup

    Args:
        backup_metadata: Diccionario con información del backup

    """
    from usuarios.models import Usuario

    logger.info(" Notificando backup completado")

    # Obtener usuarios administradores
    administradores = Usuario.objects.filter(rol__in=["administrador", "director"])

    if not administradores.exists():
        logger.warning("No hay administradores para notificar")
        return {"enviadas": 0}

    backup_type = backup_metadata.get("type", "manual")
    backup_size = backup_metadata.get("size_mb", 0)
    backup_file = backup_metadata.get("filename", "backup.sql.gz")

    tipo_emoji = {"daily": "", "weekly": "", "monthly": "️", "manual": ""}

    notificaciones_enviadas = 0

    for admin in administradores:
        try:
            Notificacion.objects.create(
                usuario=admin,
                tipo=TipoNotificacion.NOVEDAD_SISTEMA,
                prioridad=PrioridadNotificacion.BAJA,
                titulo=f"{tipo_emoji.get(backup_type, '')} Backup Completado",
                mensaje=f"Se realizó exitosamente un backup {backup_type} de la base de datos. "
                f"Tamaño: {backup_size} MB. "
                f"Archivo: {backup_file}",
                url="/dashboard/backups",
                url_texto="Ver Backups",
                entidad_tipo="backup",
                metadata=backup_metadata,
            )
            notificaciones_enviadas += 1
        except Exception as e:
            logger.error("Error notificando backup a %s: %s", admin.username, e)

    logger.info("Notificaciones de backup enviadas: %s", notificaciones_enviadas)
    return {"enviadas": notificaciones_enviadas}


@shared_task(name="notificaciones.limpiar_notificaciones_antiguas")
def limpiar_notificaciones_antiguas(dias=90):
    """Eliminar notificaciones leídas más antiguas que X días

    Args:
        dias: Número de días de retención (default: 90)

    """
    logger.info("Limpiando notificaciones antiguas (%s días)", dias)

    fecha_corte = timezone.now() - timedelta(days=dias)

    # Eliminar notificaciones leídas y archivadas antiguas
    notificaciones_eliminadas = Notificacion.objects.filter(
        leida=True, archivada=True, fecha_creacion__lte=fecha_corte,
    ).delete()[0]

    logger.info("Notificaciones eliminadas: %s", notificaciones_eliminadas)
    return {"eliminadas": notificaciones_eliminadas}


@shared_task(name="notificaciones.archivar_notificaciones_expiradas")
def archivar_notificaciones_expiradas():
    """Archivar automáticamente notificaciones que han expirado
    """
    logger.info(" Archivando notificaciones expiradas")

    ahora = timezone.now()

    # Archivar notificaciones expiradas que no están archivadas
    notificaciones_archivadas = Notificacion.objects.filter(
        archivada=False, fecha_expiracion__lte=ahora,
    ).update(archivada=True)

    logger.info("Notificaciones archivadas: %s", notificaciones_archivadas)
    return {"archivadas": notificaciones_archivadas}


@shared_task(name="notificaciones.recordatorios_controles_prenatales")
def recordatorios_controles_prenatales():
    """Enviar recordatorios para controles prenatales próximos o atrasados
    """
    logger.info(" Enviando recordatorios de controles prenatales")

    ahora = timezone.now()
    notificaciones_enviadas = 0

    # Buscar embarazos activos
    embarazos_activos = Embarazo.objects.filter(estado="activo").select_related(
        "paciente",
    )

    for embarazo in embarazos_activos:
        # Obtener último control
        ultimo_control = (
            ControlPrenatal.objects.filter(embarazo=embarazo)
            .order_by("-fecha_control")
            .first()
        )

        # Calcular si necesita control
        if ultimo_control:
            dias_desde_ultimo = (ahora.date() - ultimo_control.fecha_control).days
            # Controles cada 4 semanas (28 días) aproximadamente
            if dias_desde_ultimo >= 28:
                prioridad = (
                    PrioridadNotificacion.ALTA
                    if dias_desde_ultimo >= 35
                    else PrioridadNotificacion.NORMAL
                )

                try:
                    # `paciente.usuario` no existe: esta alerta de control
                    # atrasado nunca se emitía. Va al médico responsable.
                    creadas = crear_notificacion_clinica(
                        destinatario_preferido=embarazo.medico_responsable,
                        tipo=TipoNotificacion.RECORDATORIO_CONTROL,
                        prioridad=prioridad,
                        titulo="Recordatorio: Control Prenatal",
                        mensaje=f"{embarazo.paciente.nombre_completo}: han pasado "
                        f"{dias_desde_ultimo} días desde su último control prenatal.",
                        url=f"/dashboard/controles?embarazo={getattr(embarazo, 'id', None)}",
                        entidad_tipo="embarazo",
                        entidad_id=getattr(embarazo, 'id', None),
                        metadata={
                            "embarazo_id": getattr(embarazo, 'id', None),
                            "dias_desde_ultimo_control": dias_desde_ultimo,
                        },
                    )
                    notificaciones_enviadas += len(creadas)
                except Exception as e:
                    logger.error(
                        "Error creando recordatorio para embarazo %s: %s",
                        getattr(embarazo, 'id', None),
                        e,
                    )
        else:
            # Primer control
            semanas_embarazo = getattr(embarazo, 'edad_gestacional_semanas', 0) or 0
            if semanas_embarazo > 4:  # Después de 4 semanas sin controles
                try:
                    creadas = crear_notificacion_clinica(
                        destinatario_preferido=embarazo.medico_responsable,
                        tipo=TipoNotificacion.RECORDATORIO_CONTROL,
                        prioridad=PrioridadNotificacion.ALTA,
                        titulo="Importante: Primer Control Prenatal",
                        mensaje=f"{embarazo.paciente.nombre_completo} aún no tiene "
                        "su primer control prenatal registrado.",
                        url=f"/dashboard/controles?embarazo={getattr(embarazo, 'id', None)}",
                        entidad_tipo="embarazo",
                        entidad_id=getattr(embarazo, 'id', None),
                        metadata={
                            "embarazo_id": getattr(embarazo, 'id', None),
                            "primer_control": True,
                        },
                    )
                    notificaciones_enviadas += len(creadas)
                except Exception as e:
                    logger.error(
                        "Error creando recordatorio para embarazo %s: %s",
                        getattr(embarazo, 'id', None),
                        e,
                    )

    logger.info("Recordatorios de controles enviados: %s", notificaciones_enviadas)
    return {"enviadas": notificaciones_enviadas}


@shared_task(name="notificaciones.tasks.escalar_notificaciones_criticas")
def escalar_notificaciones_criticas():
    """Escala las alertas CRÍTICAS que siguen sin leerse según los umbrales de
    settings (nivel 2 → jefe de guardia; nivel 3 → coordinación médica). Corre
    periódicamente vía Celery beat (ver CELERY_BEAT_SCHEDULE). Cada escalamiento
    deja su registro de auditoría con motivo timeout."""
    from .services import escalar_notificaciones_criticas as _escalar

    escaladas = _escalar()
    logger.info("Escalamiento crítico: %s alerta(s) escaladas.", escaladas)
    return {"escaladas": escaladas}
