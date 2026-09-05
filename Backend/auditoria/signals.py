"""SIGNALS: AUDITORÍA AUTOMÁTICA EN TIEMPO REAL
Captura automáticamente todos los cambios (crear, actualizar, eliminar)
en los modelos del sistema y los registra en RegistroAuditoria.
"""

import json
import logging
import threading

from django.db import transaction
from django.db.models.signals import (
    post_delete,
    post_migrate,
    post_save,
    pre_migrate,
    pre_save,
)
from django.dispatch import receiver

from .acciones import canonica
from .models import RegistroAuditoria

logger = logging.getLogger(__name__)

_thread_locals = threading.local()

# Durante `migrate` la tabla de auditoría puede no existir todavía, y el
# SELECT de comprobación —lanzado desde un signal dentro del schema editor—
# abortaba la transacción de la migración ("You can't execute queries until
# the end of the 'atomic' block"), tumbando hasta la creación de la BD de
# tests. Migrar no es una acción clínica: durante la migración no se audita.
_migrando = {"activo": False}


@receiver(pre_migrate)
def _marcar_inicio_migracion(**_kwargs):
    _migrando["activo"] = True


@receiver(post_migrate)
def _marcar_fin_migracion(**_kwargs):
    _migrando["activo"] = False


def set_current_request(request):
    """Guarda el request del hilo actual (lo llama AuditoriaMiddleware)."""
    _thread_locals.request = request


def get_current_user():
    """Usuario autenticado del request en curso, resuelto AL VUELO.

    Se resuelve aquí y no en el middleware porque con autenticación DRF por
    JWT/cookie el usuario recién queda disponible cuando la vista se ejecuta;
    en el middleware `request.user` todavía es AnonymousUser y la auditoría
    guardaba el "quién" vacío.
    """
    # set_current_user() explícito (comandos, tareas) tiene prioridad
    usuario = getattr(_thread_locals, "user", None)
    if usuario is not None:
        return usuario
    request = getattr(_thread_locals, "request", None)
    if request is None:
        return None
    try:
        candidato = getattr(request, "user", None)
        if candidato is not None and getattr(candidato, "is_authenticated", False):
            return candidato
    except Exception:  # request ya cerrado / usuario no resoluble
        return None
    return None


def set_current_user(user):
    """Set current user (uso explícito fuera de un request HTTP)."""
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


#: Modelos que NO se auditan automáticamente.
#:
#: La auditoría existe para responder «¿quién tocó los datos de esta paciente?».
#: Todo lo que no ayude a responder eso solo hace la tabla más grande y las
#: consultas más lentas.
#:
#: Medido sobre la base real el 5 de septiembre de 2026, con 41.367 registros
#: ocupando 36 MB:
#:
#:     notificaciones   17.929   43,3%
#:     paciente          9.046   21,9%
#:     notificacion      8.835   21,4%
#:     ...
#:
#: **El 64,7% de la auditoría era "se creó una notificación".** El sistema
#: auditaba sus propios avisos, y como los avisos se generan solos —una alerta
#: por cada control, por cada paciente registrada— la tabla crecía en círculo:
#: más notificaciones, más auditoría de notificaciones.
#:
#: Que el sistema se mande un aviso a sí mismo no es un hecho que un hospital
#: necesite poder reconstruir. Que alguien abriera una historia clínica, sí.
EXCLUIR_MODELOS = [
    "RegistroAuditoria",
    "AccessLog",
    "Session",
    "LogEntry",
    "ContentType",
    "Permission",
    # Avisos del propio sistema: 64,7% de la tabla y cero valor clínico.
    # Las acciones clínicas que los originan (crear paciente, registrar un
    # control) se siguen auditando en su propio módulo, que es donde importan.
    "Notificacion",
    "HistorialNotificaciones",
    "ConfiguracionNotificaciones",
    # Tokens JWT: se crean y rotan en cada login. El login ya se audita como
    # LOGIN, con usuario, IP y fecha; el token es un detalle de implementación.
    "OutstandingToken",
    "BlacklistedToken",
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
    """¿La tabla de auditoría es accesible desde el contexto actual?

    Se comprueba con una consulta real del ORM en vez de introspección de
    esquema. Motivo (bug encontrado en pruebas de carga): con django_tenants
    el search_path es "<tenant>, public" y
    `connection.introspection.table_names()` devuelve SOLO las tablas del
    esquema del tenant. Como `auditoria_registros` vive en `public` (app
    compartida), la comprobación daba False SIEMPRE y `debe_auditar_modelo()`
    apagaba en silencio la auditoría de TODOS los modelos clínicos: no se
    registraba ni una creación, edición o borrado de pacientes, embarazos,
    controles ni partos.

    Un SELECT del propio modelo respeta el search_path completo y es portable
    a cualquier backend (PostgreSQL, SQLite en tests).

    SOLO se memoriza el resultado POSITIVO. Antes también se cacheaba el
    negativo y eso envenenaba el proceso entero: si la primera comprobación
    ocurría sin contexto de tenant (arranque, comando, worker), ese False
    quedaba fijo y la auditoría seguía apagada, en silencio, durante TODA la
    vida del proceso. Reintentar cuesta un `SELECT 1 LIMIT 1`.

    La comprobación va dentro de un SAVEPOINT propio. Sin él, cuando la
    primera llamada caía dentro de un signal (o sea, dentro de la transacción
    del save que la disparó) y la consulta fallaba, la transacción entera
    quedaba abortada. El middleware hacía un "warm-up" para que la primera vez
    ocurriera en un momento limpio, pero eso solo cubre lo que pasa por un
    request: los saves del ORM en comandos, workers o tests —donde no hay
    middleware— seguían sin auditarse. Con el savepoint, un fallo se contiene
    y se reintenta en la siguiente llamada.
    """
    if _tabla_cache["existe"]:
        return True
    try:
        with transaction.atomic():
            RegistroAuditoria.objects.exists()
        _tabla_cache["existe"] = True
    except Exception:
        return False
    return True


def debe_auditar_modelo(sender):
    """Debe auditar modelo"""
    if _migrando["activo"]:
        return False
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
            # `canonica()` porque este signal escribe con `objects.create()`,
            # que NO pasa por `RegistroAuditoria.registrar()` -- el sitio donde
            # se normalizan los nombres. Sin esto seguia guardando 'crear' en
            # minusculas mientras el resto del sistema guarda 'CREAR', y quien
            # filtrara por el nombre canonico no encontraba estos registros.
            # Verificado sobre la base real: convivian 12.068 'CREAR' con
            # 5.199 'crear' para el mismo hecho.
            RegistroAuditoria.objects.create(
                modulo=modulo,
                accion=canonica("crear"),
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
                    # 'actualizar' -> 'EDITAR'. Este era el peor de los dos:
                    # habia 884 ediciones guardadas como 'actualizar' y cero
                    # como 'EDITAR', asi que filtrar por EDITAR devolvia nada
                    # y parecia que nunca se hubiera modificado ningun dato.
                    accion=canonica("actualizar"),
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
            # 'eliminar' -> 'DESACTIVAR', igual que en post_save. Habia 3.390
            # registros con el nombre legado; dar de baja una paciente se
            # guardaba unas veces como 'eliminar' y otras como
            # 'DESACTIVAR_PACIENTE', asi que ninguna consulta las encontraba
            # todas.
            accion=canonica("eliminar"),
            registro_id=str(instance.pk),
            usuario=get_current_user(),
            datos_anteriores=redactar_pii(serializar_instancia(instance)),
        )
    except Exception as e:
        logger.error("Error en auditoría (post_delete): %s", e)
