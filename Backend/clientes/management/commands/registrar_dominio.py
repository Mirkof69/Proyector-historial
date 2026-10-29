"""Registra la dirección por la que se va a entrar al sistema.

    python manage.py registrar_dominio 192.168.0.6 --tenant clinica
    python manage.py registrar_dominio --detectar-ip --tenant clinica
    python manage.py registrar_dominio --listar

Por qué hace falta
------------------
El sistema es multi-tenant: cada clínica vive en su propio esquema de base de
datos, y django-tenants decide a cuál entrar **mirando la dirección por la que
llegó la petición**. Esa correspondencia vive en una tabla, y si la dirección
no está ahí, la petición no llega a ninguna clínica.

Comprobado el 5 de septiembre de 2026: solo estaban registrados `localhost` y
`127.0.0.1`. Es decir, el sistema funcionaba **únicamente desde el ordenador
donde corre**. Desde cualquier otro equipo de la clínica —el de recepción, el
del consultorio— entrar por `http://192.168.0.6:8000` devolvía **404 siempre**,
sin ningún mensaje que explicara por qué.

Y un 404 es la peor forma de fallar aquí, porque parece que la dirección está
mal escrita en vez de que falte una fila en una tabla.

Aparte de esto hay que añadir la misma dirección a `ALLOWED_HOSTS` en el
`.env`; si no, Django la rechaza antes de llegar al enrutador de tenants. El
comando lo recuerda al terminar.
"""
import socket

from django.core.management.base import BaseCommand, CommandError
from django_tenants.utils import get_tenant_domain_model, get_tenant_model


def ip_de_esta_maquina() -> str:
    """La IP con la que este equipo se ve desde la red local.

    Se abre un socket UDP hacia una dirección externa —sin mandar nada— solo
    para que el sistema operativo elija la interfaz de salida y diga qué IP
    usaría. Es más fiable que `gethostbyname(gethostname())`, que en Windows
    con varias tarjetas de red suele devolver 127.0.0.1 o la del adaptador
    equivocado.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


class Command(BaseCommand):
    help = "Registra una dirección (IP o nombre) para que apunte a una clínica."

    def add_arguments(self, parser):
        parser.add_argument(
            "dominio", nargs="?", default=None,
            help="IP o nombre, sin http:// y sin puerto. Ej: 192.168.0.6",
        )
        parser.add_argument(
            "--tenant", default=None,
            help="Esquema de la clínica. Ej: clinica",
        )
        parser.add_argument(
            "--detectar-ip", action="store_true",
            help="Usa la IP de este equipo en la red local.",
        )
        parser.add_argument(
            "--listar", action="store_true",
            help="Muestra lo que hay registrado y termina.",
        )

    def handle(self, *args, **options):
        Dominio = get_tenant_domain_model()
        Tenant = get_tenant_model()

        if options["listar"]:
            self._listar(Dominio)
            return

        dominio = options["dominio"]
        if options["detectar_ip"]:
            dominio = ip_de_esta_maquina()
            self.stdout.write(f"IP detectada en la red local: {dominio}")

        if not dominio:
            raise CommandError(
                "Falta la dirección. Pásala como argumento o usa --detectar-ip.",
            )

        # Errores tipicos al copiar y pegar de la barra del navegador.
        if "://" in dominio or "/" in dominio:
            raise CommandError(
                f"'{dominio}' lleva protocolo o ruta. Se registra solo el "
                f"nombre o la IP: 192.168.0.6",
            )
        if ":" in dominio:
            raise CommandError(
                f"'{dominio}' lleva puerto. El puerto no forma parte del "
                f"dominio: usa '{dominio.split(':')[0]}'.",
            )

        esquema = options["tenant"]
        if not esquema:
            raise CommandError(
                "Falta --tenant. Las clínicas disponibles son: "
                + ", ".join(
                    t.schema_name
                    for t in Tenant.objects.exclude(schema_name="public")
                ),
            )

        try:
            tenant = Tenant.objects.get(schema_name=esquema)
        except Tenant.DoesNotExist:
            raise CommandError(f"No existe ninguna clínica con el esquema '{esquema}'.")

        ya = Dominio.objects.filter(domain=dominio).first()
        if ya:
            if ya.tenant_id == tenant.id:
                self.stdout.write(
                    self.style.WARNING(f"'{dominio}' ya apuntaba a {esquema}. Sin cambios."),
                )
            else:
                raise CommandError(
                    f"'{dominio}' ya está registrado y apunta a "
                    f"'{ya.tenant.schema_name}'. Dos clínicas no pueden "
                    f"compartir dirección: las peticiones irían al esquema "
                    f"equivocado y una clínica vería los datos de la otra.",
                )
        else:
            # `is_primary=False`: el principal ya existe y solo puede haber uno.
            Dominio.objects.create(domain=dominio, tenant=tenant, is_primary=False)
            self.stdout.write(self.style.SUCCESS(f"'{dominio}' registrado en {esquema}."))

        self._listar(Dominio)
        self.stdout.write(
            self.style.MIGRATE_HEADING("\nFalta un paso, en el archivo .env:"),
        )
        self.stdout.write(
            f"  Añadir '{dominio}' a ALLOWED_HOSTS y, si el frontend se sirve\n"
            f"  desde otra máquina, 'http://{dominio}:3000' a CORS_ALLOWED_ORIGINS\n"
            f"  y a CSRF_TRUSTED_ORIGINS. Sin eso Django rechaza la petición\n"
            f"  antes de llegar aquí. Después hay que reiniciar el servidor.",
        )

    def _listar(self, Dominio):
        self.stdout.write(self.style.MIGRATE_HEADING("\nDirecciones registradas:"))
        for d in Dominio.objects.select_related("tenant").order_by("domain"):
            marca = " (principal)" if d.is_primary else ""
            self.stdout.write(f"  {d.domain:32s} -> {d.tenant.schema_name}{marca}")
