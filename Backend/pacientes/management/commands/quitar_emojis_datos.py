"""Quita los emojis que quedaron guardados en textos de la base.

    python manage.py quitar_emojis_datos --schema=clinica

Los mensajes del sistema (títulos de notificaciones, alertas, recomendaciones)
se generaban con emojis («⚠️ RESULTADO CRÍTICO»). El código ya no los pone; este
comando limpia lo que ya estaba guardado para que la interfaz use solo íconos.

No toca la auditoría (es inmutable por ley) ni los campos cifrados. Usa
update(): es una corrección de formato, no una edición clínica.
"""
import re

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import models
from django_tenants.utils import schema_context

from clientes.constantes import ESQUEMA_PRINCIPAL

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⬀-⯿⌀-⏿]️?[ \t]?")
EMOJI_SQL = "[\\U0001F300-\\U0001FAFF\\u2600-\\u27BF\\u2B00-\\u2BFF\\u2300-\\u23FF]"
APPS_EXCLUIDAS = {"auditoria", "admin", "auth", "contenttypes", "sessions", "django_tenants", "clientes"}


def limpiar(texto: str) -> str:
    return EMOJI.sub("", texto).replace("️", "").strip()


class Command(BaseCommand):
    help = "Quita emojis de los textos guardados (sin tocar la auditoría)"

    def add_arguments(self, parser):
        parser.add_argument("--schema", default=ESQUEMA_PRINCIPAL)

    def handle(self, *args, **opciones):
        total = {}
        with schema_context(opciones["schema"]):
            for modelo in apps.get_models():
                if modelo._meta.app_label in APPS_EXCLUIDAS or modelo._meta.proxy or not modelo._meta.managed:
                    continue
                campos = [f.name for f in modelo._meta.concrete_fields
                          if type(f) in (models.CharField, models.TextField)]
                for campo in campos:
                    try:
                        filas = list(modelo.objects.filter(**{f"{campo}__regex": EMOJI_SQL}).values_list("pk", campo))
                    except Exception:  # noqa: BLE001 — tabla de otro esquema o no creada
                        continue
                    for pk, texto in filas:
                        modelo.objects.filter(pk=pk).update(**{campo: limpiar(texto)})
                    if filas:
                        total[f"{modelo._meta.label}.{campo}"] = len(filas)
        self.stdout.write(self.style.SUCCESS(f"Textos limpiados: {total or 'ninguno'}"))
