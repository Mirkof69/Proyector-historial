import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from django_tenants.utils import get_tenant_model, tenant_context

from ecografias.models import AnatomiaFetal, AnexosFetales, BiometriaFetal, Ecografia
from embarazos.models import Embarazo
from pacientes.models import Paciente

User = get_user_model()

TIPOS_ECO = ["obstetrica", "transvaginal", "doppler"]
INDICACIONES = [
    "Control rutinario de embarazo",
    "Sospecha RCIU",
    "Control de placenta previa",
    "Sospecha de anomalia fetal",
    "Control de embarazo gemelar",
    "Evaluacion de bienestar fetal",
    "Sospecha de oligohidramnios",
    "Control postermino",
    "Evaluacion de crecimiento fetal",
    "Control embarazo alto riesgo"
]
DIAGNOSTICOS = [
    "Embarazo intrauterino unico activo",
    "Embarazo intrauterino unico con crecimiento adecuado para edad gestacional",
    "Embarazo intrauterino unico con RCIU tipo I",
    "Embarazo intrauterino gemelar bicorial biamniotico",
    "Placenta previa oclusiva total",
    "Oligohidramnios moderado",
    "Polihidramnios leve",
    "Embarazo de curso normal"
]


class Command(BaseCommand):
    help = "Genera datos de prueba para ecografias"

    def add_arguments(self, parser):
        parser.add_argument("--cantidad", type=int, default=20, help="Numero de ecografias a crear")

    def handle(self, *args, **options):
        cantidad = options["cantidad"]

        TenantModel = get_tenant_model()
        tenants = TenantModel.objects.filter(schema_name="clinica_demo")
        if not tenants.exists():
            self.stdout.write(self.style.ERROR("No se encontro tenant clinica_demo"))
            return
        tenant = tenants.first()

        with tenant_context(tenant):
            medicos = list(User.objects.filter(is_staff=True)[:3])
            pacientes = list(Paciente.objects.all())

            if not medicos:
                medicos = list(User.objects.all()[:3])

            creadas = 0
            for i in range(cantidad):
                paciente = random.choice(pacientes) if pacientes else None
                if not paciente:
                    continue

                embarazos = list(Embarazo.objects.filter(paciente=paciente))
                embarazo = random.choice(embarazos) if embarazos else None

                medico = random.choice(medicos) if medicos else None
                if not medico:
                    continue

                eg_semanas = random.randint(8, 40)
                eg_dias = random.randint(0, 6)
                fecha_eco = timezone.now().date() - timedelta(days=random.randint(0, 90))

                eco = Ecografia.objects.create(
                    embarazo=embarazo,
                    paciente=paciente,
                    medico=medico,
                    fecha_ecografia=fecha_eco,
                    tipo_ecografia=random.choice(TIPOS_ECO),
                    indicacion=random.choice(INDICACIONES),
                    edad_gestacional_semanas=eg_semanas,
                    edad_gestacional_dias=eg_dias,
                    numero_fetos=1,
                    vitalidad_fetal=True,
                    frecuencia_cardiaca_fetal=random.randint(120, 160),
                    indice_liquido_amniotico=round(random.uniform(5, 25), 1),
                    localizacion_placenta=random.choice(
                        ["anterior", "posterior", "fundica", "lateral_derecha", "lateral_izquierda", "previa"]
                    ),
                    grado_madurez_placenta=random.randint(0, 3),
                    calidad_estudio="buena",
                    limitaciones_tecnicas="",
                    diagnostico=random.choice(DIAGNOSTICOS),
                    observaciones="Estudio de control sin alteraciones",
                    requiere_seguimiento=random.choice([True, False]),
                    created_by=medico,
                    updated_by=medico,
                )

                BiometriaFetal.objects.create(
                    ecografia=eco,
                    diametro_biparietal=round(random.uniform(20, 95), 1),
                    circunferencia_cefalica=round(random.uniform(80, 350), 1),
                    circunferencia_abdominal=round(random.uniform(60, 360), 1),
                    longitud_femur=round(random.uniform(10, 78), 1),
                    peso_fetal_estimado=round(random.uniform(150, 3800), 0),
                    percentil_peso=random.randint(3, 97),
                )

                AnatomiaFetal.objects.create(
                    ecografia=eco,
                    craneo_normal=True,
                    cerebro_normal=True,
                    corazon_normal=True,
                    pulmones_normales=True,
                    columna_normal=True,
                )

                AnexosFetales.objects.create(
                    ecografia=eco,
                    placenta_localizacion=random.choice(
                        ["anterior", "posterior", "fundica", "lateral_derecha", "lateral_izquierda"]
                    ),
                    liquido_amniotico_normal=True,
                    longitud_cervical=round(random.uniform(25, 45), 1),
                )

                creadas += 1

            self.stdout.write(
                self.style.SUCCESS(f"Se crearon {creadas} ecografias de prueba exitosamente")
            )
