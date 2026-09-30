"""Auditar las acciones masivas del admin de Django.

Las acciones masivas («marcar como…», «activar», etc.) suelen hacer
queryset.update(), que no dispara señales: cambiaban cientos de registros
sin dejar rastro en la auditoría. Todas pasan por ModelAdmin.response_action,
así que se envuelve ese único punto en lugar de tocar cada admin.py.
"""
import functools
import logging

logger = logging.getLogger(__name__)

MAX_IDS_EN_DETALLE = 50


def instalar():
    from django.contrib.admin import helpers
    from django.contrib.admin.options import ModelAdmin

    if getattr(ModelAdmin.response_action, "_auditado", False):
        return
    original = ModelAdmin.response_action

    @functools.wraps(original)
    def response_action(self, request, queryset):
        accion = request.POST.get("action", "")
        seleccion = request.POST.getlist(helpers.ACTION_CHECKBOX_NAME)
        todos = request.POST.get("select_across") == "1"
        respuesta = original(self, request, queryset)
        # delete_selected primero pide confirmación: solo se ejecuta con «post».
        ejecutada = accion and (seleccion or todos) and (accion != "delete_selected" or request.POST.get("post"))
        if ejecutada:
            try:
                from .models import RegistroAuditoria

                ids = ", ".join(seleccion[:MAX_IDS_EN_DETALLE]) + ("…" if len(seleccion) > MAX_IDS_EN_DETALLE else "")
                RegistroAuditoria.registrar(
                    usuario=request.user, accion="ACCION_MASIVA_ADMIN",
                    modulo=self.model._meta.model_name,
                    detalle=f"Acción «{accion}» sobre "
                            + ("TODOS los registros filtrados" if todos else f"{len(seleccion)} registros: {ids}"),
                    request=request,
                )
            except Exception:
                logger.exception("No se pudo auditar la acción masiva %s", accion)
        return respuesta

    response_action._auditado = True
    ModelAdmin.response_action = response_action
