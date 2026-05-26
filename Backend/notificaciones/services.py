"""=============================================================================
MÓDULO: NOTIFICACIONES - SERVICES
=============================================================================
Servicio completo de notificaciones adaptado de cocineros-sistema
Proporciona métodos para crear, gestionar y consultar notificaciones
=============================================================================
"""

import logging
from datetime import timedelta
from typing import Any

from django.utils import timezone

from .models import Notificacion, PrioridadNotificacion, TipoNotificacion

logger = logging.getLogger(__name__)


class NotificacionService:
    """Servicio centralizado para la gestión de notificaciones

    Adaptado del NotificacionService de cocineros-sistema (Laravel)
    a Django siguiendo las mismas funcionalidades y estructura.
    """

    # ========== CONSTANTES DE TIPOS ==========
    # (Ya definidas en TipoNotificacion, pero se replican para compatibilidad)
    TIPO_CITA_PROXIMA = TipoNotificacion.CITA_PROXIMA
    TIPO_CITA_CONFIRMADA = TipoNotificacion.CITA_CONFIRMADA
    TIPO_CITA_CANCELADA = TipoNotificacion.CITA_CANCELADA
    TIPO_CITA_REAGENDADA = TipoNotificacion.CITA_REAGENDADA

    TIPO_EXAMEN_LISTO = TipoNotificacion.EXAMEN_LISTO
    TIPO_EXAMEN_CRITICO = TipoNotificacion.EXAMEN_CRITICO
    TIPO_EXAMEN_SOLICITADO = TipoNotificacion.EXAMEN_SOLICITADO

    TIPO_ALERTA_CRITICA = TipoNotificacion.ALERTA_CRITICA
    TIPO_ALERTA_ADVERTENCIA = TipoNotificacion.ALERTA_ADVERTENCIA
    TIPO_ALERTA_INFORMACION = TipoNotificacion.ALERTA_INFORMACION

    TIPO_RECORDATORIO = TipoNotificacion.RECORDATORIO
    TIPO_RECORDATORIO_MEDICACION = TipoNotificacion.RECORDATORIO_MEDICACION
    TIPO_RECORDATORIO_CONTROL = TipoNotificacion.RECORDATORIO_CONTROL

    TIPO_DOCUMENTO_LISTO = TipoNotificacion.DOCUMENTO_LISTO
    TIPO_MENSAJE_MEDICO = TipoNotificacion.MENSAJE_MEDICO

    @staticmethod
    def crear(
        usuario_id: int,
        tipo: str,
        titulo: str,
        mensaje: str,
        datos: dict[str, Any] | None = None,
        prioridad: str = PrioridadNotificacion.NORMAL,
        url: str = "",
        url_texto: str = "",
        entidad_tipo: str = "",
        entidad_id: int | None = None,
        fecha_expiracion: timezone.datetime | None = None,
    ) -> Notificacion | None:
        """Crear una notificación

        Args:
            usuario_id: ID del usuario destinatario
            tipo: Tipo de notificación (TipoNotificacion)
            titulo: Título de la notificación
            mensaje: Mensaje detallado
            datos: Datos adicionales en formato dict
            prioridad: Prioridad de la notificación
            url: URL de acción (ruta del frontend)
            url_texto: Texto del botón de acción
            entidad_tipo: Tipo de entidad relacionada
            entidad_id: ID de la entidad relacionada
            fecha_expiracion: Fecha de expiración

        Returns:
            Notificacion creada o None si hay error

        """
        try:
            notificacion = Notificacion.objects.create(
                usuario_id=usuario_id,
                tipo=tipo,
                prioridad=prioridad,
                titulo=titulo,
                mensaje=mensaje,
                metadata=datos or {},
                url=url,
                url_texto=url_texto,
                entidad_tipo=entidad_tipo,
                entidad_id=entidad_id,
                fecha_expiracion=fecha_expiracion,
                leida=False,
            )

            logger.info(
                "Notificación creada: %s para usuario %s",
                notificacion.id,
                usuario_id,
            )

            # Broadcast via WebSocket for real-time delivery
            try:
                from notifications_websocket.bridge import broadcast_notification

                broadcast_notification(notificacion)
            except Exception:
                # Don't break notification creation if WebSocket is unavailable
                pass

            return notificacion

        except Exception as e:
            logger.error("Error al crear notificación: %s", str(e))
            return None

    @staticmethod
    def notificar_nueva_cita(cita) -> Notificacion | None:
        """Notificar cuando se crea una nueva cita

        Args:
            cita: Instancia del modelo Cita

        Returns:
            Notificacion creada

        """
        if not hasattr(cita.paciente, "usuario"):
            return None

        medico_nombre = (
            cita.medico.nombre_completo if cita.medico else "pendiente de asignar"
        )
        mensaje = f"Se ha confirmado su cita para el {cita.fecha_hora.strftime('%d/%m/%Y a las %H:%M')} con Dr./Dra. {medico_nombre}"

        return NotificacionService.crear(
            usuario_id=cita.paciente.usuario.id,
            tipo=TipoNotificacion.CITA_CONFIRMADA,
            prioridad=PrioridadNotificacion.ALTA,
            titulo="Cita Confirmada",
            mensaje=mensaje,
            url=f"/citas/{cita.id}",
            url_texto="Ver Detalle de Cita",
            entidad_tipo="cita",
            entidad_id=cita.id,
            datos={
                "cita_id": cita.id,
                "fecha_cita": cita.fecha_hora.isoformat(),
                "medico": medico_nombre,
                "tipo_cita": cita.tipo_cita,
            },
        )

    @staticmethod
    def notificar_cancelacion_cita(cita, motivo: str = "") -> Notificacion | None:
        """Notificar cuando se cancela una cita

        Args:
            cita: Instancia del modelo Cita
            motivo: Motivo de cancelación

        Returns:
            Notificacion creada

        """
        if not hasattr(cita.paciente, "usuario"):
            return None

        mensaje = f"Su cita del {cita.fecha_hora.strftime('%d/%m/%Y a las %H:%M')} ha sido cancelada."
        if motivo:
            mensaje += f" Motivo: {motivo}"

        return NotificacionService.crear(
            usuario_id=cita.paciente.usuario.id,
            tipo=TipoNotificacion.CITA_CANCELADA,
            prioridad=PrioridadNotificacion.ALTA,
            titulo="Cita Cancelada",
            mensaje=mensaje,
            url="/citas",
            url_texto="Agendar Nueva Cita",
            entidad_tipo="cita",
            entidad_id=cita.id,
            datos={"cita_id": cita.id, "motivo": motivo},
        )

    @staticmethod
    def notificar_resultado_examen(examen) -> Notificacion | None:
        """Notificar cuando un examen de laboratorio está listo

        Args:
            examen: Instancia del modelo ExamenLaboratorio

        Returns:
            Notificacion creada

        """
        if not hasattr(examen.paciente, "usuario"):
            return None

        # Verificar si hay resultados críticos
        tiene_criticos = False
        if hasattr(examen, "resultados"):
            tiene_criticos = examen.resultados.filter(es_critico=True).exists()

        if tiene_criticos:
            tipo = TipoNotificacion.EXAMEN_CRITICO
            prioridad = PrioridadNotificacion.CRITICA
            titulo = "⚠️ RESULTADOS CRÍTICOS"
            mensaje = f"Los resultados de {examen.tipo_examen} están listos. ATENCIÓN: Se encontraron valores críticos que requieren atención médica inmediata."
        else:
            tipo = TipoNotificacion.EXAMEN_LISTO
            prioridad = PrioridadNotificacion.ALTA
            titulo = "Resultados de Examen Listos"
            mensaje = f"Los resultados de {examen.tipo_examen} ya están disponibles."

        return NotificacionService.crear(
            usuario_id=examen.paciente.usuario.id,
            tipo=tipo,
            prioridad=prioridad,
            titulo=titulo,
            mensaje=mensaje,
            url=f"/laboratorio/{examen.id}",
            url_texto="Ver Resultados",
            entidad_tipo="examen",
            entidad_id=examen.id,
            datos={
                "examen_id": examen.id,
                "tipo_examen": str(examen.tipo_examen),
                "tiene_criticos": tiene_criticos,
            },
        )

    @staticmethod
    def notificar_documento_listo(documento, paciente) -> Notificacion | None:
        """Notificar cuando un documento médico está listo

        Args:
            documento: Nombre/tipo del documento
            paciente: Instancia del modelo Paciente

        Returns:
            Notificacion creada

        """
        if not hasattr(paciente, "usuario"):
            return None

        return NotificacionService.crear(
            usuario_id=paciente.usuario.id,
            tipo=TipoNotificacion.DOCUMENTO_LISTO,
            prioridad=PrioridadNotificacion.NORMAL,
            titulo="Documento Médico Listo",
            mensaje=f"Su {documento} está listo para descarga.",
            url="/documentos",
            url_texto="Ver Documentos",
            entidad_tipo="paciente",
            entidad_id=paciente.id,
            datos={"documento": documento, "paciente_id": paciente.id},
        )

    @staticmethod
    def crear_alerta_medica(
        paciente,
        titulo: str,
        mensaje: str,
        prioridad: str = PrioridadNotificacion.ALTA,
        metadata: dict | None = None,
    ) -> Notificacion | None:
        """Crear una alerta médica genérica

        Args:
            paciente: Instancia del modelo Paciente
            titulo: Título de la alerta
            mensaje: Mensaje detallado
            prioridad: Prioridad de la alerta
            metadata: Datos adicionales

        Returns:
            Notificacion creada

        """
        if not hasattr(paciente, "usuario"):
            return None

        tipo = (
            TipoNotificacion.ALERTA_CRITICA
            if prioridad == PrioridadNotificacion.CRITICA
            else TipoNotificacion.ALERTA_ADVERTENCIA
        )

        return NotificacionService.crear(
            usuario_id=paciente.usuario.id,
            tipo=tipo,
            prioridad=prioridad,
            titulo=titulo,
            mensaje=mensaje,
            url=f"/pacientes/{paciente.id}",
            url_texto="Ver Historia Clínica",
            entidad_tipo="paciente",
            entidad_id=paciente.id,
            datos=metadata or {},
        )

    @staticmethod
    def obtener_no_leidas(usuario_id: int, limite: int = 10) -> list[Notificacion]:
        """Obtener notificaciones no leídas de un usuario

        Args:
            usuario_id: ID del usuario
            limite: Número máximo de notificaciones

        Returns:
            Lista de notificaciones no leídas

        """
        return list(
            Notificacion.objects.filter(
                usuario_id=usuario_id, leida=False, archivada=False,
            ).order_by("-fecha_creacion")[:limite],
        )

    @staticmethod
    def obtener_todas(usuario_id: int, limite: int = 50) -> list[Notificacion]:
        """Obtener todas las notificaciones de un usuario

        Args:
            usuario_id: ID del usuario
            limite: Número máximo de notificaciones

        Returns:
            Lista de notificaciones

        """
        return list(
            Notificacion.objects.filter(
                usuario_id=usuario_id, archivada=False,
            ).order_by("-fecha_creacion")[:limite],
        )

    @staticmethod
    def marcar_como_leida(notificacion_id: int) -> bool:
        """Marcar una notificación como leída

        Args:
            notificacion_id: ID de la notificación

        Returns:
            True si se marcó correctamente, False en caso contrario

        """
        try:
            notificacion = Notificacion.objects.get(id=notificacion_id)
            notificacion.marcar_como_leida()
            return True
        except Notificacion.DoesNotExist:
            logger.warning("Notificación %s no encontrada", notificacion_id)
            return False
        except Exception as e:
            logger.error("Error al marcar notificación como leída: %s", str(e))
            return False

    @staticmethod
    def marcar_todas_leidas(usuario_id: int) -> int:
        """Marcar todas las notificaciones de un usuario como leídas

        Args:
            usuario_id: ID del usuario

        Returns:
            Número de notificaciones marcadas

        """
        ahora = timezone.now()
        actualizadas = Notificacion.objects.filter(
            usuario_id=usuario_id, leida=False, archivada=False,
        ).update(leida=True, fecha_leida=ahora)

        logger.info(
            "Marcadas %s notificaciones como leídas para usuario %s",
            actualizadas,
            usuario_id,
        )
        return actualizadas

    @staticmethod
    def contar_no_leidas(usuario_id: int) -> int:
        """Contar notificaciones no leídas de un usuario

        Args:
            usuario_id: ID del usuario

        Returns:
            Número de notificaciones no leídas

        """
        return Notificacion.objects.filter(
            usuario_id=usuario_id, leida=False, archivada=False,
        ).count()

    @staticmethod
    def limpiar_antiguas(dias_antiguedad: int = 30) -> int:
        """Eliminar notificaciones antiguas ya leídas

        Args:
            dias_antiguedad: Días de antigüedad para considerar eliminación

        Returns:
            Número de notificaciones eliminadas

        """
        fecha_corte = timezone.now() - timedelta(days=dias_antiguedad)

        eliminadas, _ = Notificacion.objects.filter(
            fecha_creacion__lt=fecha_corte, leida=True,
        ).delete()

        logger.info("Eliminadas %s notificaciones antiguas", eliminadas)
        return eliminadas

    @staticmethod
    def obtener_estadisticas(usuario_id: int) -> dict[str, Any]:
        """Obtener estadísticas de notificaciones de un usuario

        Args:
            usuario_id: ID del usuario

        Returns:
            Diccionario con estadísticas

        """
        total = Notificacion.objects.filter(
            usuario_id=usuario_id, archivada=False,
        ).count()
        no_leidas = Notificacion.objects.filter(
            usuario_id=usuario_id, leida=False, archivada=False,
        ).count()
        leidas = Notificacion.objects.filter(
            usuario_id=usuario_id, leida=True, archivada=False,
        ).count()
        archivadas = Notificacion.objects.filter(
            usuario_id=usuario_id, archivada=True,
        ).count()

        # Estadísticas por tipo
        por_tipo = {}
        for tipo, _ in TipoNotificacion.choices:
            count = Notificacion.objects.filter(
                usuario_id=usuario_id, tipo=tipo, archivada=False,
            ).count()
            if count > 0:
                por_tipo[tipo] = count

        # Estadísticas por prioridad
        por_prioridad = {}
        for prioridad, _ in PrioridadNotificacion.choices:
            count = Notificacion.objects.filter(
                usuario_id=usuario_id, prioridad=prioridad, leida=False, archivada=False,
            ).count()
            if count > 0:
                por_prioridad[prioridad] = count

        # Notificaciones recientes (últimas 24 horas)
        hace_24h = timezone.now() - timedelta(hours=24)
        recientes_24h = Notificacion.objects.filter(
            usuario_id=usuario_id, fecha_creacion__gte=hace_24h, archivada=False,
        ).count()

        return {
            "total_notificaciones": total,
            "no_leidas": no_leidas,
            "leidas": leidas,
            "archivadas": archivadas,
            "por_tipo": por_tipo,
            "por_prioridad": por_prioridad,
            "recientes_24h": recientes_24h,
        }

    @staticmethod
    def agrupar_por_tipo(
        usuario_id: int, solo_no_leidas: bool = False,
    ) -> dict[str, list[Notificacion]]:
        """Agrupar notificaciones por tipo para un usuario

        Args:
            usuario_id: ID del usuario
            solo_no_leidas: Si True, solo incluye no leídas

        Returns:
            Diccionario con tipos como claves y listas de notificaciones

        """
        queryset = Notificacion.objects.filter(usuario_id=usuario_id, archivada=False)

        if solo_no_leidas:
            queryset = queryset.filter(leida=False)

        agrupadas = {}
        for notif in queryset.order_by("-fecha_creacion"):
            tipo = notif.tipo
            if tipo not in agrupadas:
                agrupadas[tipo] = []
            agrupadas[tipo].append(notif)

        return agrupadas

    @staticmethod
    def eliminar_notificacion(notificacion_id: int, usuario_id: int) -> bool:
        """Eliminar una notificación específica

        Args:
            notificacion_id: ID de la notificación
            usuario_id: ID del usuario (para verificación de permisos)

        Returns:
            True si se eliminó correctamente, False en caso contrario

        """
        try:
            notificacion = Notificacion.objects.get(
                id=notificacion_id, usuario_id=usuario_id,
            )
            notificacion.delete()
            logger.info("Notificación %s eliminada", notificacion_id)
            return True
        except Notificacion.DoesNotExist:
            logger.warning(
                "Notificación %s no encontrada para usuario %s", notificacion_id, usuario_id,
            )
            return False
        except Exception as e:
            logger.error("Error al eliminar notificación: %s", str(e))
            return False
