"""SIGNALS: AUDITORÍA AUTOMÁTICA EN TIEMPO REAL
Captura automáticamente todos los cambios (crear, actualizar, eliminar)
en los modelos del sistema y los registra en RegistroAuditoria.
"""

import json
import logging
import threading

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import RegistroAuditoria

logger = logging.getLogger(__name__)

_thread_locals = threading.local()


def get_current_user():
    """Get current user"""
    return getattr(_thread_locals, "user", None)


def set_current_user(user):
    """Set current user"""
    _thread_locals.user = user


def get_client_ip(request):
    """Get client ip"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")


def _get_instance_cache():
    """Cache por hilo — evita race condition entre requests concurrentes."""
    if not hasattr(_thread_locals, "instance_cache"):
        _thread_locals.instance_cache = {}
    return _thread_locals.instance_cache


EXCLUIR_MODELOS = [
    "RegistroAuditoria",
    "AccessLog",
    "Session",
    "LogEntry",
    "ContentType",
    "Permission",
]

PII_FIELDS = {
    "nombre", "apellido_paterno", "apellido_materno",
    "ci", "telefono", "email", "direccion",
    "contacto_emergencia_nombre", "contacto_emergencia_telefono",
    "contacto_emergencia_relacion",
    "numero_seguro_social",
    "password", "mfa_secret", "token",
}


def redactar_pii(data: dict) -> dict:
    """Redacta campos PII en registros de auditoría."""
    if not isinstance(data, dict):
        return data
    return {
        k: "***REDACTADO***" if k.lower() in PII_FIELDS and v is not None else v
        for k, v in data.items()
    }

_tabla_cache: dict[str, bool | None] = {"existe": None}


def verificar_tabla_auditoria_existe():
    """¿Existe la tabla de auditoría? Usa la introspección de Django (portable a
    PostgreSQL, SQLite y cualquier backend), en vez de un query a
    information_schema que solo funciona en PostgreSQL (antes eso deshabilitaba
    la auditoría en SQLite/tests)."""
    if _tabla_cache["existe"] is not None:
        return _tabla_cache["existe"]
    try:
        from django.db import connection

        _tabla_cache["existe"] = (
            "auditoria_registros" in connection.introspection.table_names()
        )
    except Exception:
        _tabla_cache["existe"] = False
    return _tabla_cache["existe"]


def debe_auditar_modelo(sender):
    """Debe auditar modelo"""
    if not verificar_tabla_auditoria_existe():
        return False
    return sender.__name__ not in EXCLUIR_MODELOS


def serializar_instancia(instance):
    """Serializar instancia"""
    try:
        data = {}
        for field in instance._meta.fields:
            field_name = field.name
            field_value = getattr(instance, field_name, None)
            if field.get_internal_type() == "ForeignKey":
                data[field_name] = field_value.pk if field_value else None
                if field_value:
                    data[f"{field_name}_display"] = str(field_value)
            elif field_value is not None and hasattr(field_value, "isoformat"):
                data[field_name] = field_value.isoformat()
            else:
                try:
                    json.dumps(field_value)
                    data[field_name] = field_value
                except (TypeError, ValueError):
                    data[field_name] = (
                        str(field_value) if field_value is not None else None
                    )
        return data
    except Exception as e:
        logger.error("Error al serializar instancia: %s", e)
        return {}


@receiver(pre_save)
def cache_instance_before_update(sender, instance, **_kwargs):
    """Cache instance before update"""
    if not debe_auditar_modelo(sender):
        return
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            cache_key = f"{sender.__name__}_{instance.pk}"
            _get_instance_cache()[cache_key] = serializar_instancia(old_instance)
        except sender.DoesNotExist:
            pass


@receiver(post_save)
def auditar_creacion_actualizacion(sender, instance, created, **_kwargs):
    """Auditar creacion actualizacion"""
    if not debe_auditar_modelo(sender):
        return
    try:
        modulo = sender.__name__.lower()
        usuario = get_current_user()
        if created:
            RegistroAuditoria.objects.create(
                modulo=modulo,
                accion="crear",
                registro_id=str(instance.pk),
                usuario=usuario,
                datos_nuevos=redactar_pii(serializar_instancia(instance)),
            )
        else:
            cache = _get_instance_cache()
            cache_key = f"{sender.__name__}_{instance.pk}"
            datos_anteriores = redactar_pii(cache.get(cache_key) or {})
            datos_nuevos = redactar_pii(serializar_instancia(instance))
            if datos_anteriores and datos_anteriores != datos_nuevos:
                RegistroAuditoria.objects.create(
                    modulo=modulo,
                    accion="actualizar",
                    registro_id=str(instance.pk),
                    usuario=usuario,
                    datos_anteriores=datos_anteriores,
                    datos_nuevos=datos_nuevos,
                )
            cache.pop(cache_key, None)
    except Exception as e:
        logger.error("Error en auditoría (post_save): %s", e)


@receiver(post_delete)
def auditar_eliminacion(sender, instance, **_kwargs):
    """Auditar eliminacion"""
    if not debe_auditar_modelo(sender):
        return
    try:
        RegistroAuditoria.objects.create(
            modulo=sender.__name__.lower(),
            accion="eliminar",
            registro_id=str(instance.pk),
            usuario=get_current_user(),
            datos_anteriores=redactar_pii(serializar_instancia(instance)),
        )
    except Exception as e:
        logger.error("Error en auditoría (post_delete): %s", e)
