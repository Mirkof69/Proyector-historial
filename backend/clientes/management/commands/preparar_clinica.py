"""Deja lista la clínica real con todos sus catálogos, sin un solo dato ficticio.

    python manage.py preparar_clinica
    python manage.py preparar_clinica --nombre "Fetal Medical Bolivia" --dominio 192.168.1.11

Idempotente: se puede correr de nuevo y solo agrega lo que falte. Crea:
- la clínica `clinica` (si no existe) con sus dominios: localhost, 127.0.0.1,
  la IP de este equipo y los que se pasen con --dominio;
- el catálogo de laboratorio (tipos de examen y rangos de referencia para la
  altura de La Paz), las vacunas del embarazo y los horarios de atención;
- el nombre de la clínica en la configuración del sistema.

Los tipos de reporte y los grupos de permisos por rol llegan con las
migraciones. Las cuentas del personal, consultorios y agendas se crean desde
la aplicación: dependen del hospital.
"""
from datetime import time
from io import StringIO

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django_tenants.utils import get_tenant_domain_model, get_tenant_model, schema_context

from clientes.constantes import ESQUEMA_PRINCIPAL


class Command(BaseCommand):
    help = "Crea o completa la clínica real con sus catálogos (sin datos de demostración)"

    def add_arguments(self, parser):
        parser.add_argument("--nombre", default="Fetal Medical Bolivia", help="Nombre de la clínica")
        parser.add_argument("--dominio", action="append", default=[],
                            help="Dominio o IP adicional (se puede repetir)")

    def handle(self, *args, **opciones):
        Clinica, Dominio = get_tenant_model(), get_tenant_domain_model()
        clinica = Clinica.objects.filter(schema_name=ESQUEMA_PRINCIPAL).first()
        if clinica is None:
            self.stdout.write(f"Creando la clínica «{ESQUEMA_PRINCIPAL}» (migra su esquema, tarda un poco)…")
            clinica = Clinica(schema_name=ESQUEMA_PRINCIPAL, name=opciones["nombre"])
            clinica.save()
        dominios = ["localhost", "127.0.0.1", *opciones["dominio"]]
        for i, dominio in enumerate(dominios):
            Dominio.objects.get_or_create(domain=dominio, defaults={"tenant": clinica, "is_primary": i == 0})
        call_command("registrar_dominio", "--detectar-ip", "--tenant", ESQUEMA_PRINCIPAL, stdout=StringIO())

        with schema_context(ESQUEMA_PRINCIPAL):
            from laboratorio.models import TipoExamen, ValorReferencia
            from reportes.models import TipoReporte
            from reportes.models_config import HorarioAtencion, SistemaConfiguracion
            from vacunas.catalogo import asegurar_vacunas

            call_command("poblar_valores_referencia", stdout=StringIO())
            vacunas = asegurar_vacunas()
            for dia, _ in HorarioAtencion.DIAS_SEMANA:
                laborable = dia not in ("sabado", "domingo")
                HorarioAtencion.objects.get_or_create(dia=dia, defaults={
                    "activo": laborable, "hora_inicio": time(8, 0), "hora_fin": time(18, 0) if laborable else time(12, 0),
                })
            config = SistemaConfiguracion.get_configuracion()
            if config.nombre_clinica in ("", "Centro Médico"):
                config.nombre_clinica = opciones["nombre"]
                config.save(update_fields=["nombre_clinica"])

            resumen = {
                "tipos de examen": TipoExamen.objects.count(),
                "rangos de referencia": ValorReferencia.objects.count(),
                "vacunas": f"{vacunas} nuevas",
                "tipos de reporte": TipoReporte.objects.count(),
                "horarios": HorarioAtencion.objects.count(),
            }
        self.stdout.write(self.style.SUCCESS(
            f"Clínica «{clinica.name}» lista. Dominios: "
            f"{', '.join(Dominio.objects.filter(tenant=clinica).values_list('domain', flat=True))}. {resumen}",
        ))
