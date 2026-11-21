"""Borra los avisos «RESULTADO CRÍTICO» que el fallo del 29/10 generó de más.

    python manage.py quitar_avisos_criticos_falsos            # solo cuenta
    python manage.py quitar_avisos_criticos_falsos --borrar   # los borra

El aviso comparaba cada resultado con el PRIMER parámetro de su tipo de
examen (una hemoglobina de 11,9 contra los basófilos 0-1 %), así que casi todo
hemograma llegaba al médico como «Requiere atención inmediata». Con la regla
corregida se revisa cada aviso: se borra si su resultado NO es crítico o ya no
existe. Los críticos de verdad se quedan. El resultado y su interpretación no
se tocan (`es_critico` siempre se calculó bien); tampoco la auditoría.
"""
from django.core.management.base import BaseCommand
from django_tenants.utils import get_tenant_model, schema_context

from laboratorio.models import ResultadoLaboratorio
from laboratorio.signals import verificar_resultado_critico
from notificaciones.models import Notificacion, TipoNotificacion


class Command(BaseCommand):
    help = "Cuenta (o borra con --borrar) los avisos de resultado crítico que no lo eran"

    def add_arguments(self, parser):
        parser.add_argument("--borrar", action="store_true", help="Borrarlos; sin esto solo se cuentan")
        parser.add_argument("--tenant", help="Esquema de una sola clínica (por defecto, todas)")

    def handle(self, *args, **opciones):
        esquemas = [opciones["tenant"]] if opciones["tenant"] else list(
            get_tenant_model().objects.exclude(schema_name="public").values_list("schema_name", flat=True))
        for esquema in esquemas:
            with schema_context(esquema):
                avisos = Notificacion.objects.filter(tipo=TipoNotificacion.EXAMEN_CRITICO,
                                                     entidad_tipo="resultado_laboratorio")
                ids = set(avisos.values_list("entidad_id", flat=True))
                resultados = ResultadoLaboratorio.objects.filter(pk__in=ids).select_related("valor_referencia")
                criticos = {r.pk for r in resultados if verificar_resultado_critico(r)}
                falsos = avisos.exclude(entidad_id__in=criticos)
                cuantos = falsos.count()
                if opciones["borrar"]:
                    falsos.delete()
                verbo = "borrados" if opciones["borrar"] else "a borrar (use --borrar)"
                self.stdout.write(f"{esquema}: {cuantos} avisos {verbo}; se quedan {avisos.count() if opciones['borrar'] else len(criticos)} críticos reales")
