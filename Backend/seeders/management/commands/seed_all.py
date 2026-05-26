"""=============================================================================
SEED_ALL - Comprehensive Database Seeder for Fetal Medical System
=============================================================================
Creates realistic clinical test data for ALL 22 modules.

Usage:
    python manage.py seed_all
    python manage.py seed_all --flush    # Clear database first

Modules seeded:
    1.  Usuarios (Users with roles)
    2.  Roles (CatRoles)
    3.  Consultorios (Clinics/Offices)
    4.  Pacientes (Patients)
    5.  Antecedentes (Medical History)
    6.  Embarazos (Pregnancies)
    7.  Controles Prenatales (Prenatal Controls)
    8.  Ecografias (Ultrasounds with biometry)
    9.  Laboratorio (Lab Results)
    10. Citas (Appointments)
    11. Partos (Deliveries)
    12. Calculadoras (Risk Calculators)
    13. Triaje (Triage Assessments)
    14. Evoluciones (Pregnancy Evolutions)
    15. Notas Evolucion (Medical Notes)
    16. Vacunas (Vaccinations)
    17. Notificaciones (Notifications)
    18. IA Medica (AI Medical Analysis)
    19. Auditoria (Audit Records)
    20. Ecografias Archivos (Ultrasound Files)
    21. Calculadoras Avanzadas
    22. Reportes data (via other modules)
=============================================================================
"""

import random
from datetime import date, datetime, timedelta
from datetime import time as dtime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

# =============================================================================
# HELPER: CLINICALLY REALISTIC DATA GENERATORS
# =============================================================================

# Realistic Bolivian/Spanish names
NOMBRES_FEMENINOS = [
    "Maria",
    "Ana",
    "Carmen",
    "Rosa",
    "Lucia",
    "Elena",
    "Sofia",
    "Valentina",
    "Isabella",
    "Camila",
    "Daniela",
    "Andrea",
    "Patricia",
    "Gabriela",
    "Mariana",
    "Carolina",
    "Fernanda",
    "Alejandra",
    "Paula",
    "Laura",
    "Claudia",
    "Veronica",
    "Silvia",
    "Adriana",
    "Natalia",
    "Angela",
    "Teresa",
    "Gloria",
    "Pilar",
    "Lourdes",
    "Guadalupe",
    "Esperanza",
    "Mercedes",
    "Dolores",
    "Ines",
    "Beatriz",
    "Rocio",
    "Jimena",
    "Ximena",
    "Constanza",
    "Catalina",
    "Antonella",
    "Renata",
    "Regina",
    "Fatima",
    "Zaira",
    "Nadia",
    "Yolanda",
    "Miriam",
    "Sandra",
    "Lilian",
    "Gisela",
]

NOMBRES_MASCULINOS = [
    "Carlos",
    "Juan",
    "Jose",
    "Miguel",
    "Pedro",
    "Luis",
    "Jorge",
    "Roberto",
    "Fernando",
    "Eduardo",
    "Ricardo",
    "Alberto",
    "Diego",
    "Andres",
    "Francisco",
    "Antonio",
    "Javier",
    "Alejandro",
    "Daniel",
    "Rafael",
    "Manuel",
    "Gabriel",
    "Sergio",
    "Raul",
    "Arturo",
    "Alfredo",
    "Oscar",
    "Victor",
    "Mario",
    "Hector",
    "Felipe",
    "Agustin",
    "Mateo",
    "Santiago",
    "Nicolas",
    "Martin",
    "Gustavo",
    "Rodrigo",
    "Pablo",
    "Ignacio",
    "Enrique",
    "Ramon",
    "Guillermo",
    "Julio",
]

APELLIDOS = [
    "Condori",
    "Mamani",
    "Quispe",
    "Huanca",
    "Flores",
    "Torrez",
    "Rivera",
    "Vargas",
    "Gutierrez",
    "Rodriguez",
    "Lopez",
    "Martinez",
    "Garcia",
    "Fernandez",
    "Gonzalez",
    "Perez",
    "Sanchez",
    "Ramirez",
    "Cruz",
    "Diaz",
    "Morales",
    "Jimenez",
    "Reyes",
    "Torres",
    "Romero",
    "Chura",
    "Nina",
    "Apaza",
    "Choque",
    "Ticona",
    "Medina",
    "Castillo",
    "Herrera",
    "Vasquez",
    "Aguilar",
    "Soto",
    "Rojas",
    "Vega",
    "Castro",
    "Ortiz",
    "Delgado",
    "Pena",
    "Mendoza",
    "Serrano",
    "Camacho",
    "Paz",
]

CALLES_LA_PAZ = [
    "Av. 16 de Julio",
    "Av. Busch",
    "Av. Arce",
    "Av. 6 de Agosto",
    "Calle Comercio",
    "Calle Potosi",
    "Calle Junin",
    "Calle Loayza",
    "Av. Heroínas",
    "Calle Ingavi",
    "Calle Mercado",
    "Av. Montenegro",
    "Calle Belzu",
    "Calle Colon",
    "Av. Mariscal Santa Cruz",
    "Calle Yanacha",
    "Av. Villazon",
    "Calle Bueno",
    "Av. Peru",
    "Calle Ravelo",
]

CIUDADES_BOLIVIA = [
    "La Paz",
    "El Alto",
    "Cochabamba",
    "Santa Cruz",
    "Oruro",
    "Sucre",
    "Potosi",
    "Tarija",
    "Beni",
    "Viacha",
    "Achocalla",
    "Laja",
]

OBSERVACIONES_CONTROL = [
    "Paciente refiere buen estado general. Movimientos fetales presentes.",
    "Control sin novedades. Frecuencia cardiaca fetal normal.",
    "Paciente refiere molestias lumbares leves. Se indica reposo relativo.",
    "Control de rutina. Se solicita ecografia de control.",
    "Paciente con ganancia de peso adecuada. Se continua suplemento de hierro.",
    "Se detecta leve edema en miembros inferiores. Monitoreo de PA.",
    "Paciente refiere contracciones de Braxton Hicks ocasionales.",
    "Control normal. Se indica continuar con vitaminas prenatales.",
    "Paciente con leve anemia. Se aumenta dosis de suplemento ferroso.",
    "Se programa proxima ecografia para evaluacion de crecimiento.",
    "Paciente refiere mejoras en nauseas. Ganancia de peso dentro de rango.",
    "Control de seguimiento. Presion arterial dentro de limites normales.",
    "Se realiza perfil bi fisico fetal. Resultados dentro de normalidad.",
    "Paciente con signos de alarma explicados. Proxima cita en 2 semanas.",
    "Evaluacion de crecimiento fetal adecuada para edad gestacional.",
]

DIAGNOSTICOS_ULTRASONIDO = [
    "Feto unico, vivo, con biometria adecuada para edad gestacional.",
    "Embarazo unico, evolutivo, con parametros biometricos normales.",
    "Feto unico en presentacion cefalica. Biometria dentro de percentiles normales.",
    "Embarazo en curso con desarrollo fetal apropiado para edad gestacional.",
    "Feto unico, con adecuada relacion peso/edad gestacional.",
    "Biometria fetal compatible con edad gestacional por fecha de ultima menstruacion.",
    "Feto unico, vivo, con actividad cardiaca presente. Parametros normales.",
    "Embarazo evolutivo con biometria fetal dentro de rangos esperados.",
]


def random_date(start_date, end_date):
    """Generate a random date between two dates. Returns start_date if range is invalid."""
    delta = end_date - start_date
    if delta.days <= 0:
        return start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)


def random_decimal(min_val, max_val, decimals=1):
    """Generate a random Decimal within range."""
    val = round(random.uniform(float(min_val), float(max_val)), decimals)
    return Decimal(str(val))


def clamp(value, min_val, max_val):
    """Clamp a value between min and max."""
    return max(min_val, min(max_val, value))


# =============================================================================
# COMMAND CLASS
# =============================================================================


class Command(BaseCommand):
    """Command"""
    help = "Seed the database with realistic clinical test data for all 22 modules."

    def add_arguments(self, parser):
        """Add arguments"""
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Clear existing seeded data before inserting new data",
        )

    def __init__(self, *args, **kwargs):
        """Init"""
        super().__init__(*args, **kwargs)
        self.faker = None
        self.stats = {}
        self.users = {}
        self.pacientes = []
        self.embarazos = []
        self.controles = []
        self.ecografias = []
        self.consultorios = []
        self.tipos_examenes = []
        self.tipos_vacunas = []
        self.cat_roles = {}

    def log(self, msg):
        """Log"""
        self.stdout.write(self.style.SUCCESS(f"  {msg}"))

    def log_section(self, msg):
        """Log section"""
        self.stdout.write(self.style.NOTICE(f"\n{'=' * 60}"))
        self.stdout.write(self.style.NOTICE(f"  {msg}"))
        self.stdout.write(self.style.NOTICE(f"{'=' * 60}"))

    def log_warning(self, msg):
        """Log warning"""
        self.stdout.write(self.style.WARNING(f"  WARNING: {msg}"))

    def handle(self, *args, **options):
        """Handle"""
        self.log_section("FETAL MEDICAL SYSTEM - DATABASE SEEDER")

        if options["flush"]:
            self.log_section("FLUSHING EXISTING DATA")
            self._flush_data()

        self._seed_roles()
        self._seed_users()
        self._seed_consultorios()
        self._seed_pacientes()
        self._seed_antecedentes()
        self._seed_embarazos()
        self._seed_controles_prenatales()
        self._seed_ecografias()
        self._seed_tipos_examenes()
        self._seed_laboratorio()
        self._seed_citas()
        self._seed_partos()
        self._seed_calculadoras_riesgo()
        self._seed_triaje()
        self._seed_evoluciones()
        self._seed_notas_evolucion()
        self._seed_tipos_vacunas()
        self._seed_vacunas()
        self._seed_notificaciones()
        self._seed_ia_medica()
        self._seed_auditoria()

        self._print_summary()

    # =============================================================================
    # FLUSH
    # =============================================================================

    def _flush_data(self):
        """Clear existing data in reverse dependency order."""
        from django.apps import apps

        # Models to clear in order (dependents first)
        model_names = [
            "notificaciones.Notificacion",
            "notificaciones.HistorialNotificaciones",
            "notas_evolucion.NotaEvolucion",
            "vacunas.RegistroVacuna",
            "evoluciones.EvolucionEmbarazo",
            "triaje.TriajeEnfermeria",
            "partos.Parto",
            "citas.Cita",
            "citas.HistorialCita",
            "laboratorio.ResultadoLaboratorio",
            "laboratorio.ExamenLaboratorio",
            "laboratorio.ValorReferencia",
            "laboratorio.TipoExamen",
            "ecografias.ImagenEcografia",
            "ecografias.AnatomiaFetal",
            "ecografias.BiometriaFetal",
            "ecografias.AnexosFetales",
            "ecografias.Ecografia",
            "controles.ControlPrenatal",
            "calculadoras.BiomarcadorMOM",
            "calculadoras.MedicionEcografica",
            "calculadoras.CalculadoraRiesgo",
            "antecedentes.AntecedentePatologico",
            "antecedentes.AntecedenteGinecoObstetrico",
            "embarazos.Embarazo",
            "pacientes.Paciente",
            "consultorios.Consultorio",
            "usuarios.HorarioAtencion",
            "usuarios.Usuario",
            "roles.CatRol",
            "ia_medica.ConsultaIA",
            "ia_medica.AnalisisLaboratorioML",
            "ia_medica.DatasetEntrenamientoIA",
            "ia_medica.ConfiguracionModeloIA",
            "ia_medica.EstadisticasIA",
            "auditoria.RegistroAuditoria",
            "vacunas.TipoVacuna",
        ]

        count = 0
        for model_name in model_names:
            app_label, model = model_name.split(".")
            try:
                Model = apps.get_model(app_label, model)
                n = Model.objects.count()
                if n > 0:
                    Model.objects.all().delete()
                    count += n
            except LookupError:
                pass

        self.log(f"Deleted {count} existing records.")

    # =============================================================================
    # 1. ROLES
    # =============================================================================

    def _seed_roles(self):
        """Seed roles"""
        from roles.models import CatRol

        if CatRol.objects.exists():
            self.log("Roles already exist, skipping.")
            return

        self.log_section("1. SEEDING ROLES")

        roles_data = [
            (
                "medico",
                "Medico especialista en ginecologia y obstetricia",
                {
                    "crear_pacientes": True,
                    "ver_historial": True,
                    "recetar": True,
                    "agendar": True,
                },
            ),
            (
                "enfermera",
                "Enfermera de soporte y triaje",
                {"crear_pacientes": True, "triaje": True, "ver_historial": True},
            ),
            (
                "administrativo",
                "Personal administrativo de la clinica",
                {"agendar": True, "crear_pacientes": True, "ver_historial": False},
            ),
        ]

        for nombre, desc, perms in roles_data:
            rol, created = CatRol.objects.get_or_create(
                nombre=nombre,
                defaults={"descripcion": desc, "permisos": perms, "activo": True},
            )
            if created:
                self.log(f"  Created role: {nombre}")
                self.stats["roles"] = self.stats.get("roles", 0) + 1
            self.cat_roles[nombre] = rol

    # =============================================================================
    # 2. USERS
    # =============================================================================

    def _seed_users(self):
        """Seed users"""
        from usuarios.models import Usuario

        if Usuario.objects.filter(email__startswith="seed_").exists():
            self.log("Seed users already exist, skipping.")
            self.users = {
                u.email: u for u in Usuario.objects.filter(email__startswith="seed_")
            }
            return

        self.log_section("2. SEEDING USERS")

        users_config = [
            (
                "seed_admin@fetal.com",
                "admin",
                "Admin",
                "Sistema",
                "administrador",
                True,
                True,
                True,
            ),
            (
                "seed_dr.garcia@fetal.com",
                "dr.garcia",
                "Roberto",
                "Garcia Mendoza",
                "medico",
                True,
                False,
                True,
            ),
            (
                "seed_dr.mamani@fetal.com",
                "dr.mamani",
                "Fernando",
                "Mamani Quispe",
                "medico",
                True,
                False,
                True,
            ),
            (
                "seed_dr.lopez@fetal.com",
                "dr.lopez",
                "Carolina",
                "Lopez Rivera",
                "medico",
                True,
                False,
                True,
            ),
            (
                "seed_nurse.rosa@fetal.com",
                "nurse.rosa",
                "Rosa",
                "Condori Flores",
                "enfermero",
                True,
                False,
                False,
            ),
            (
                "seed_nurse.ana@fetal.com",
                "nurse.ana",
                "Ana",
                "Huanca Torrez",
                "enfermero",
                True,
                False,
                False,
            ),
        ]

        for (
            email,
            _username,
            nombre,
            apellido,
            rol,
            activo,
            is_staff,
            is_superuser,
        ) in users_config:
            apellido_p, _, apellido_m = apellido.partition(" ")
            user, created = Usuario.objects.get_or_create(
                email=email,
                defaults={
                    "nombre": nombre,
                    "apellido_paterno": apellido_p,
                    "apellido_materno": apellido_m or None,
                    "rol": rol,
                    "activo": activo,
                    "is_staff": is_staff,
                    "is_superuser": is_superuser,
                    "especialidad": "Ginecologia y Obstetricia"
                    if rol == "medico"
                    else None,
                    "telefono": f"+591{random.randint(70000000, 79999999)}",
                },
            )
            if created:
                user.set_password("admin123")
                user.save()
                self.log(f"  Created user: {email} ({rol})")
            self.users[email] = user
            self.stats["usuarios"] = self.stats.get("usuarios", 0) + 1

    # =============================================================================
    # 3. CONSULTORIOS
    # =============================================================================

    def _seed_consultorios(self):
        """Seed consultorios"""
        from consultorios.models import Consultorio

        if Consultorio.objects.exists():
            self.consultorios = list(Consultorio.objects.all())
            self.log(
                f"Consultorios already exist ({len(self.consultorios)}), using existing.",
            )
            return

        self.log_section("3. SEEDING CONSULTORIOS")

        consultorios_data = [
            (
                "Consultorio 1",
                "CONS-01",
                "Planta Baja, Edificio Principal",
                "Planta Baja",
                "Edificio Principal",
                "ginecologia",
                4,
                True,
                True,
                True,
            ),
            (
                "Consultorio 2",
                "CONS-02",
                "Piso 1, Edificio Principal",
                "Piso 1",
                "Edificio Principal",
                "ginecologia",
                3,
                True,
                True,
                False,
            ),
            (
                "Consultorio Ecografia",
                "ECO-01",
                "Piso 2, Edificio Principal",
                "Piso 2",
                "Edificio Principal",
                "ecografia",
                3,
                True,
                True,
                True,
            ),
            (
                "Consultorio Laboratorio",
                "LAB-01",
                "Planta Baja, Edificio Anexo",
                "Planta Baja",
                "Edificio Anexo",
                "laboratorio",
                5,
                True,
                False,
                False,
            ),
            (
                "Consultorio Urgencias",
                "URG-01",
                "Planta Baja, Emergencia",
                "Planta Baja",
                "Emergencia",
                "urgencias",
                6,
                True,
                True,
                False,
            ),
        ]

        admin_user = self.users.get("seed_admin@fetal.com")
        for (
            nombre,
            codigo,
            ubicacion,
            piso,
            edificio,
            tipo,
            capacidad,
            bano,
            camilla,
            ecografo,
        ) in consultorios_data:
            c, created = Consultorio.objects.get_or_create(
                nombre=nombre,
                defaults={
                    "codigo": codigo,
                    "ubicacion": ubicacion,
                    "piso": piso,
                    "edificio": edificio,
                    "tipo_consultorio": tipo,
                    "capacidad_personas": capacidad,
                    "tiene_bano": bano,
                    "tiene_camilla": camilla,
                    "tiene_ecografo": ecografo,
                    "activo": True,
                    "created_by": admin_user,
                },
            )
            if created:
                self.log(f"  Created consultorio: {nombre}")
            self.consultorios.append(c)
            self.stats["consultorios"] = self.stats.get("consultorios", 0) + 1

    # =============================================================================
    # 4. PACIENTES
    # =============================================================================

    def _seed_pacientes(self):
        """Seed pacientes"""
        from pacientes.models import Paciente

        existing = Paciente.objects.filter(id_clinico__startswith="SEED-").count()
        if existing > 0:
            self.pacientes = list(
                Paciente.objects.filter(id_clinico__startswith="SEED-"),
            )
            self.log(f"Seed pacientes already exist ({existing}), using existing.")
            return

        self.log_section("4. SEEDING PACIENTES (55 patients)")

        admin_user = self.users.get("seed_admin@fetal.com")
        today = date.today()

        for i in range(55):
            nombre = random.choice(NOMBRES_FEMENINOS)
            ap_pat = random.choice(APELLIDOS)
            ap_mat = random.choice(APELLIDOS)

            # Age between 18 and 42 (typical childbearing age)
            age = random.randint(18, 42)
            birth_date = today - timedelta(days=age * 365 + random.randint(0, 365))

            peso = round(random.uniform(45, 95), 1)
            altura = round(random.uniform(145, 170), 1)

            estado_civil_opts = ["soltero", "casado", "union_libre", "divorciado"]
            tipo_sangre_opts = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]

            paciente = Paciente(
                id_clinico=f"SEED-PAC-{i + 1:04d}",
                nombre=nombre,
                apellido_paterno=ap_pat,
                apellido_materno=ap_mat,
                fecha_nacimiento=birth_date,
                genero="femenino",
                ci=f"{random.randint(5000000, 9999999)}",
                telefono=f"+591{random.randint(70000000, 79999999)}",
                email=f"seed.paciente{i + 1}@email.com",
                direccion=f"{random.choice(CALLES_LA_PAZ)} #{random.randint(100, 2500)}",
                ciudad=random.choice(CIUDADES_BOLIVIA),
                pais="Bolivia",
                estado_civil=random.choice(estado_civil_opts),
                ocupacion=random.choice(
                    [
                        "Comerciante",
                        "Ama de casa",
                        "Profesional",
                        "Estudiante",
                        "Empleada",
                        "Administrativa",
                    ],
                ),
                contacto_emergencia_nombre=f"{random.choice(NOMBRES_MASCULINOS)} {ap_pat}",
                contacto_emergencia_telefono=f"+591{random.randint(70000000, 79999999)}",
                contacto_emergencia_relacion=random.choice(
                    ["Esposo", "Padre", "Hermano", "Madre"],
                ),
                tipo_sangre=random.choice(tipo_sangre_opts),
                factor_rh=random.choice(["positivo", "negativo"]),
                estado_paciente="activo",
                peso_kg=Decimal(str(peso)),
                altura_cm=Decimal(str(altura)),
                observaciones=f"Paciente seed #{i + 1} para pruebas del sistema.",
                created_by=admin_user,
            )

            # Ensure unique CI
            while Paciente.objects.filter(ci=paciente.ci).exists():
                paciente.ci = f"{random.randint(5000000, 9999999)}"

            try:
                paciente.save()
                self.pacientes.append(paciente)
            except Exception as e:
                self.log_warning(f"  Error creating patient {i + 1}: {e}")
                continue

            if (i + 1) % 10 == 0:
                self.log(f"  Created {i + 1}/55 patients...")

        self.stats["pacientes"] = len(self.pacientes)
        self.log(f"  Total patients created: {self.stats['pacientes']}")

    # =============================================================================
    # 5. ANTECEDENTES
    # =============================================================================

    def _seed_antecedentes(self):
        """Seed antecedentes"""
        from antecedentes.models import (
            AntecedenteGinecoObstetrico,
            AntecedentePatologico,
        )

        existing = AntecedenteGinecoObstetrico.objects.filter(
            paciente__id_clinico__startswith="SEED-",
        ).count()
        if existing > 0:
            self.log(f"Seed antecedentes already exist ({existing}), skipping.")
            return

        self.log_section("5. SEEDING ANTECEDENTES")

        admin_user = self.users.get("seed_admin@fetal.com")
        for paciente in self.pacientes[:40]:  # 40 patients with medical history
            # Gineco-obstetric
            AntecedenteGinecoObstetrico.objects.create(
                paciente=paciente,
                menarquia_edad=random.randint(11, 15),
                ciclos_menstruales=random.choice(
                    ["regular", "regular", "regular", "irregular"],
                ),
                duracion_ciclo_dias=random.randint(26, 32),
                duracion_menstruacion_dias=random.randint(3, 6),
                fecha_ultima_menstruacion=random_date(
                    date(2025, 6, 1), date(2026, 3, 1),
                ),
                gestas=random.randint(1, 5),
                partos=random.randint(0, 3),
                abortos=random.randint(0, 1),
                cesareas=random.randint(0, 2),
                hijos_vivos=random.randint(0, 4),
                metodo_anticonceptivo_actual=random.choice(
                    [None, "DIU", "Pildoras", "Inyectable", None, None],
                ),
                inicio_vida_sexual_edad=random.randint(15, 22),
                numero_parejas_sexuales=random.choice([1, 1, 1, 2, 3]),
                modificado_por=admin_user,
            )

            # Patologico
            tiene_hta = random.random() < 0.1
            tiene_diabetes = random.random() < 0.05
            tiene_alergias = random.random() < 0.15
            preeclampsia_previa = random.random() < 0.08

            AntecedentePatologico.objects.create(
                paciente=paciente,
                tipo="personal",
                tiene_alergias=tiene_alergias,
                alergias_medicamentos="Penicilina - urticaria"
                if tiene_alergias and random.random() < 0.5
                else None,
                alergias_alimentos="Mariscos" if random.random() < 0.05 else None,
                diabetes=tiene_diabetes,
                diabetes_tipo="tipo2" if tiene_diabetes else None,
                hipertension=tiene_hta,
                cardiopatias=random.random() < 0.02,
                nefropatias=False,
                trastornos_coagulacion=False,
                anemia=random.random() < 0.2,
                lupus=False,
                artritis_reumatoide=False,
                asma=random.random() < 0.05,
                preeclampsia_previa=preeclampsia_previa,
                eclampsia_previa=False,
                diabetes_gestacional_previa=random.random() < 0.05,
                hemorragia_postparto_previa=random.random() < 0.03,
                otras_enfermedades=None,
                cirugiasanteriores="Apendicectomia 2018"
                if random.random() < 0.1
                else None,
                registrado_por=admin_user,
            )

            self.stats["antecedentes_gineco"] = (
                self.stats.get("antecedentes_gineco", 0) + 1
            )
            self.stats["antecedentes_patologicos"] = (
                self.stats.get("antecedentes_patologicos", 0) + 1
            )

        self.log("  Created 40 gineco-obstetric + 40 patologicos antecedentes.")

    # =============================================================================
    # 6. EMBARAZOS
    # =============================================================================

    def _seed_embarazos(self):
        """Seed embarazos"""
        from embarazos.models import Embarazo

        existing = Embarazo.objects.filter(
            paciente__id_clinico__startswith="SEED-",
        ).count()
        if existing > 0:
            self.embarazos = list(
                Embarazo.objects.filter(paciente__id_clinico__startswith="SEED-"),
            )
            self.log(f"Seed embarazos already exist ({existing}), using existing.")
            return

        self.log_section("6. SEEDING EMBARAZOS (35 pregnancies)")

        admin_user = self.users.get("seed_admin@fetal.com")
        medicos = [u for u in self.users.values() if u.rol == "medico"]
        today = date.today()

        pacientes_con_embarazo = random.sample(
            self.pacientes, min(35, len(self.pacientes)),
        )

        for idx, paciente in enumerate(pacientes_con_embarazo):
            # Random gestational age: 4 to 40 weeks
            semanas_gest = random.randint(4, 40)
            fur = today - timedelta(weeks=semanas_gest)
            fpp = fur + timedelta(days=280)

            numero_gesta = random.randint(1, 5)
            numero_para = random.randint(0, min(numero_gesta - 1, 3))
            numero_abortos = random.randint(0, min(numero_gesta - numero_para - 1, 1))
            numero_cesareas = random.randint(0, min(numero_para, 2))

            tipo = random.choices(
                ["simple", "gemelar", "multiple"], weights=[92, 7, 1],
            )[0]
            riesgo = random.choices(["bajo", "medio", "alto"], weights=[60, 30, 10])[0]
            estado = random.choices(
                ["activo", "finalizado", "perdida"], weights=[55, 40, 5],
            )[0]

            peso_pre = round(random.uniform(45, 90), 1)
            talla = round(random.uniform(145, 170), 1)

            embarazo = Embarazo(
                paciente=paciente,
                numero_gesta=numero_gesta,
                numero_para=numero_para,
                numero_abortos=numero_abortos,
                numero_cesareas=numero_cesareas,
                fecha_ultima_menstruacion=fur,
                fecha_probable_parto=fpp,
                tipo_embarazo=tipo,
                riesgo_embarazo=riesgo,
                estado=estado,
                medico_responsable=random.choice(medicos),
                peso_pregestacional=Decimal(str(peso_pre)),
                talla_materna=Decimal(str(talla)),
                notas=f"Embarazo {numero_gesta} de {paciente.nombre}. {tipo}. Riesgo: {riesgo}.",
                created_by=admin_user,
            )

            try:
                embarazo.full_clean()
                embarazo.save()
                self.embarazos.append(embarazo)
            except Exception as e:
                self.log_warning(
                    f"  Error creating pregnancy for {paciente.nombre}: {e}",
                )
                continue

            if (idx + 1) % 10 == 0:
                self.log(f"  Created {idx + 1}/35 pregnancies...")

        self.stats["embarazos"] = len(self.embarazos)
        self.log(f"  Total pregnancies created: {self.stats['embarazos']}")

    # =============================================================================
    # 7. CONTROLES PRENATALES
    # =============================================================================

    def _seed_controles_prenatales(self):
        """Seed controles prenatales"""
        from controles.models import ControlPrenatal

        existing = ControlPrenatal.objects.filter(
            paciente__id_clinico__startswith="SEED-",
        ).count()
        if existing > 0:
            self.controles = list(
                ControlPrenatal.objects.filter(paciente__id_clinico__startswith="SEED-"),
            )
            self.log(f"Seed controles already exist ({existing}), using existing.")
            return

        self.log_section("7. SEEDING CONTROLES PRENATALES (120 controls)")

        admin_user = self.users.get("seed_admin@fetal.com")
        medicos = [u for u in self.users.values() if u.rol == "medico"]
        active_embarazos = [
            e for e in self.embarazos if e.estado in ["activo", "finalizado"]
        ]
        count = 0

        for embarazo in active_embarazos:
            # Each pregnancy gets 2-6 controls depending on gestational age
            semanas_actuales = (
                date.today() - embarazo.fecha_ultima_menstruacion
            ).days // 7
            num_controles = min(max(2, semanas_actuales // 6), 8)

            for ctrl_num in range(1, num_controles + 1):
                semanas_ctrl = min(ctrl_num * 5 + random.randint(8, 14), 40)
                fecha_ctrl = embarazo.fecha_ultima_menstruacion + timedelta(
                    weeks=semanas_ctrl,
                )
                if fecha_ctrl > date.today():
                    fecha_ctrl = date.today() - timedelta(days=random.randint(1, 60))

                # Clinically realistic vital signs
                pa_sys = random.randint(95, 135)
                pa_dia = random.randint(60, 85)
                fc_materna = random.randint(72, 95)
                temp = round(random.uniform(36.2, 37.2), 1)

                peso_actual = (
                    float(embarazo.peso_pregestacional or 65)
                    + (semanas_ctrl * 0.35)
                    + round(random.uniform(-1, 3), 1)
                )
                peso_actual = clamp(peso_actual, 40, 150)
                talla = float(embarazo.talla_materna or 158)

                alt_uterina = (
                    round(semanas_ctrl + random.uniform(-2, 2), 1)
                    if semanas_ctrl >= 20
                    else None
                )
                alt_uterina = clamp(alt_uterina, 0, 45) if alt_uterina else None

                fcf = random.randint(120, 160)
                presentacion = random.choice(
                    ["cefalica", "cefalica", "cefalica", "podalica", None],
                )
                movimientos = random.choices(
                    ["presentes", "presentes", "presentes", "ausentes", "disminuidos"],
                    weights=[75, 10, 8, 2, 5],
                )[0]
                edema = random.choices(
                    ["no", "no", "leve", "moderado"], weights=[60, 20, 15, 5],
                )[0]
                proteinuria = random.choices(
                    ["negativa", "negativa", "negativa", "trazas"],
                    weights=[70, 15, 10, 5],
                )[0]

                ctrl = ControlPrenatal(
                    embarazo=embarazo,
                    paciente=embarazo.paciente,
                    medico=random.choice(medicos),
                    numero_control=ctrl_num,
                    fecha_control=fecha_ctrl,
                    semanas_gestacion=min(semanas_ctrl, 42),
                    dias_gestacion=random.randint(0, 6),
                    peso_actual=Decimal(str(round(peso_actual, 1))),
                    peso_pregestacional=embarazo.peso_pregestacional,
                    talla=Decimal(str(talla)),
                    presion_arterial_sistolica=pa_sys,
                    presion_arterial_diastolica=pa_dia,
                    frecuencia_cardiaca=fc_materna,
                    temperatura=Decimal(str(temp)),
                    altura_uterina=Decimal(str(alt_uterina)) if alt_uterina else None,
                    frecuencia_cardiaca_fetal=fcf,
                    presentacion_fetal=presentacion,
                    movimientos_fetales=movimientos,
                    edema=edema,
                    proteinuria=proteinuria,
                    observaciones=random.choice(OBSERVACIONES_CONTROL),
                    created_by=admin_user,
                )

                try:
                    ctrl.full_clean()
                    ctrl.save()
                    self.controles.append(ctrl)
                    count += 1
                except Exception as e:
                    self.log_warning(f"  Error creating control: {e}")
                    continue

                if count % 20 == 0 and count > 0:
                    self.log(f"  Created {count} controls...")

        self.stats["controles"] = count
        self.log(f"  Total prenatal controls created: {count}")

    # =============================================================================
    # 8. ECOGRAFIAS
    # =============================================================================

    def _seed_ecografias(self):
        """Seed ecografias"""
        from ecografias.models import AnatomiaFetal, AnexosFetales, Ecografia

        existing = Ecografia.objects.filter(
            paciente__id_clinico__startswith="SEED-",
        ).count()
        if existing > 0:
            self.ecografias = list(
                Ecografia.objects.filter(paciente__id_clinico__startswith="SEED-"),
            )
            self.log(f"Seed ecografias already exist ({existing}), using existing.")
            return

        self.log_section("8. SEEDING ECOGRAFIAS (45 ultrasounds)")

        admin_user = self.users.get("seed_admin@fetal.com")
        medicos = [u for u in self.users.values() if u.rol == "medico"]
        active_embarazos = [
            e for e in self.embarazos if e.estado in ["activo", "finalizado"]
        ]
        count = 0

        for embarazo in active_embarazos:
            num_ecos = random.randint(1, 3)
            for eco_idx in range(num_ecos):
                base_semana = 12 + eco_idx * 12  # 12, 24, 36 weeks
                semanas = min(base_semana + random.randint(-2, 2), 40)
                fecha_eco = embarazo.fecha_ultima_menstruacion + timedelta(
                    weeks=semanas,
                )
                if fecha_eco > date.today():
                    fecha_eco = date.today() - timedelta(days=random.randint(1, 90))

                if semanas < 14:
                    tipo = "primer_trimestre"
                elif semanas < 28:
                    tipo = "segundo_trimestre"
                else:
                    tipo = "tercer_trimestre"

                fcf = (
                    random.randint(130, 165)
                    if semanas >= 10
                    else random.randint(110, 130)
                )

                eco = Ecografia(
                    embarazo=embarazo,
                    paciente=embarazo.paciente,
                    medico=random.choice(medicos),
                    fecha_ecografia=fecha_eco,
                    tipo_ecografia=tipo,
                    indicacion=random.choice(
                        [
                            "control_rutina",
                            "control_crecimiento",
                            "evaluacion_bienestar",
                        ],
                    ),
                    edad_gestacional_semanas=int(semanas),
                    edad_gestacional_dias=random.randint(0, 6),
                    numero_fetos=1,
                    vitalidad_fetal=True,
                    frecuencia_cardiaca_fetal=fcf,
                    indice_liquido_amniotico=Decimal(
                        str(round(random.uniform(8, 20), 1)),
                    ),
                    localizacion_placenta=random.choice(
                        [
                            "Fondo",
                            "Anterior",
                            "Posterior",
                            "Lateral derecho",
                            "Lateral izquierdo",
                        ],
                    ),
                    grado_madurez_placenta=0
                    if semanas < 28
                    else (1 if semanas < 34 else (2 if semanas < 38 else 3)),
                    calidad_estudio=random.choice(
                        ["buena", "buena", "excelente", "regular"],
                    ),
                    diagnostico=random.choice(DIAGNOSTICOS_ULTRASONIDO),
                    observaciones="Sin hallazgos patologicoss."
                    if random.random() < 0.8
                    else "Se recomienda seguimiento.",
                    created_by=admin_user,
                )

                try:
                    eco.full_clean()
                    eco.save()
                    self.ecografias.append(eco)
                    count += 1
                except Exception as e:
                    self.log_warning(f"  Error creating ultrasound: {e}")
                    continue

                # Biometria Fetal - Clinically realistic values by gestational age
                biometria = self._generate_biometria(eco, semanas)
                try:
                    biometria.full_clean()
                    biometria.save()
                except Exception:
                    pass

                # Anatomia Fetal
                anatomia = AnatomiaFetal(
                    ecografia=eco,
                    craneo_normal=True,
                    cerebro_normal=True,
                    cerebelo_normal=True,
                    perfil_facial_normal=True,
                    labios_normales=True,
                    corazon_normal=True,
                    pulmones_normales=True,
                    estomago_normal=True,
                    rinones_normales=True,
                    vejiga_normal=True,
                    columna_normal=True,
                    extremidades_superiores_normales=True,
                    extremidades_inferiores_normales=True,
                    genitales_visibles=semanas >= 20,
                    sexo_fetal=random.choice(["masculino", "femenino"])
                    if semanas >= 20
                    else "indeterminado",
                    translucencia_nucal=Decimal(str(round(random.uniform(1.0, 2.2), 1)))
                    if semanas < 14
                    else None,
                    hueso_nasal_presente=True,
                    created_by=admin_user,
                )
                try:
                    anatomia.full_clean()
                    anatomia.save()
                except Exception:
                    pass

                # Anexos Fetales
                anexos = AnexosFetales(
                    ecografia=eco,
                    placenta_localizacion=eco.localizacion_placenta,
                    placenta_grosor=Decimal(str(round(random.uniform(20, 40), 1))),
                    numero_vasos_cordon=3,
                    circular_cordon=random.random() < 0.1,
                    liquido_amniotico_normal=True,
                    longitud_cervical=Decimal(str(round(random.uniform(30, 45), 1))),
                    created_by=admin_user,
                )
                try:
                    anexos.full_clean()
                    anexos.save()
                except Exception:
                    pass

                if count % 10 == 0 and count > 0:
                    self.log(f"  Created {count} ultrasounds...")

        self.stats["ecografias"] = count
        self.log(f"  Total ultrasounds created: {count}")

    def _generate_biometria(self, ecografia, semanas):
        """Generate clinically realistic biometry values by gestational age."""
        from ecografias.models import BiometriaFetal

        # Reference ranges (approximate mean values by gestational age in weeks)
        # BPD (mm), HC (mm), AC (mm), FL (mm)
        biometry_data = {
            10: {"bpd": 15, "hc": 55, "ac": 45, "fl": 7},
            12: {"bpd": 21, "hc": 75, "ac": 58, "fl": 10},
            14: {"bpd": 28, "hc": 100, "ac": 78, "fl": 15},
            16: {"bpd": 35, "hc": 125, "ac": 100, "fl": 21},
            18: {"bpd": 42, "hc": 150, "ac": 125, "fl": 27},
            20: {"bpd": 49, "hc": 175, "ac": 150, "fl": 33},
            22: {"bpd": 55, "hc": 200, "ac": 175, "fl": 39},
            24: {"bpd": 61, "hc": 220, "ac": 198, "fl": 44},
            26: {"bpd": 67, "hc": 240, "ac": 220, "fl": 49},
            28: {"bpd": 72, "hc": 260, "ac": 240, "fl": 54},
            30: {"bpd": 77, "hc": 278, "ac": 260, "fl": 58},
            32: {"bpd": 82, "hc": 295, "ac": 280, "fl": 62},
            34: {"bpd": 86, "hc": 310, "ac": 300, "fl": 66},
            36: {"bpd": 90, "hc": 325, "ac": 320, "fl": 70},
            38: {"bpd": 93, "hc": 338, "ac": 340, "fl": 73},
            40: {"bpd": 96, "hc": 350, "ac": 358, "fl": 76},
        }

        # Find closest week
        week = int(round(semanas))
        closest_week = min(biometry_data.keys(), key=lambda x: abs(x - week))
        ref = biometry_data[closest_week]

        # Add random variation (+/- 10%)
        def variation(val):
            """Apply random variation to a value."""
            return round(val * random.uniform(0.9, 1.1), 1)

        peso_est = int(
            ref["ac"] * ref["bpd"] * ref["fl"] * 0.0015 + random.randint(-100, 100),
        )
        peso_est = max(100, min(4500, peso_est))

        return BiometriaFetal(
            ecografia=ecografia,
            diametro_biparietal=Decimal(str(variation(ref["bpd"]))),
            circunferencia_cefalica=Decimal(str(variation(ref["hc"]))),
            circunferencia_abdominal=Decimal(str(variation(ref["ac"]))),
            longitud_femur=Decimal(str(variation(ref["fl"]))),
            diametro_occipito_frontal=Decimal(str(variation(ref["bpd"] * 1.15))),
            longitud_humero=Decimal(str(variation(ref["fl"] * 0.85))),
            peso_fetal_estimado=peso_est,
            percentil_peso=random.randint(15, 85),
            diametro_transverso_cerebelo=Decimal(str(variation(ref["bpd"] * 0.5)))
            if week >= 14
            else None,
        )

    # =============================================================================
    # 9. TIPOS DE EXAMENES + LABORATORIO
    # =============================================================================

    def _seed_tipos_examenes(self):
        """Seed tipos examenes"""
        from laboratorio.models import TipoExamen

        if TipoExamen.objects.exists():
            self.tipos_examenes = list(TipoExamen.objects.all())
            self.log(
                f"Tipos de examenes already exist ({len(self.tipos_examenes)}), using existing.",
            )
            return

        self.log_section("9. SEEDING TIPOS DE EXAMENES")

        admin_user = self.users.get("seed_admin@fetal.com")
        examenes = [
            (
                "Hemograma Completo",
                "HEM-001",
                "hematologia",
                "Hemograma completo con formula leucocitaria",
                "Ayunas de 8 horas",
                24,
                Decimal("25.00"),
            ),
            (
                "Glucosa en Ayunas",
                "GLU-001",
                "bioquimica",
                "Nivel de glucosa en sangre en ayunas",
                "Ayunas obligatorio 8-12 horas",
                12,
                Decimal("15.00"),
            ),
            (
                "Perfil Tiroideo",
                "TIR-001",
                "hormonal",
                "TSH, T3, T4 libre",
                "Sin preparacion especial",
                48,
                Decimal("80.00"),
            ),
            (
                "Grupo Sanguineo y Rh",
                "GRP-001",
                "inmunologia",
                "Determinacion de grupo ABO y factor Rh",
                "Sin preparacion especial",
                12,
                Decimal("20.00"),
            ),
            (
                "VDRL",
                "VDL-001",
                "serologia",
                "Prueba de deteccion de sifilis",
                "Sin preparacion especial",
                24,
                Decimal("18.00"),
            ),
            (
                "VIH (ELISA)",
                "VIH-001",
                "inmunologia",
                "Deteccion de anticuerpos anti-VIH",
                "Sin preparacion especial",
                48,
                Decimal("35.00"),
            ),
            (
                "Toxoplasma IgG/IgM",
                "TOX-001",
                "inmunologia",
                "Deteccion de anticuerpos para Toxoplasma",
                "Sin preparacion especial",
                48,
                Decimal("45.00"),
            ),
            (
                "Rubeola IgG",
                "RUB-001",
                "inmunologia",
                "Inmunidad contra rubeola",
                "Sin preparacion especial",
                48,
                Decimal("30.00"),
            ),
            (
                "Urocultivo",
                "URO-001",
                "microbiologia",
                "Cultivo de orina con antibiograma",
                "Primera miccion de la manana",
                72,
                Decimal("40.00"),
            ),
            (
                "Urianalisis Completo",
                "URI-001",
                "urinalisis",
                "Examen fisico, quimico y microscopico de orina",
                "Muestra de primera miccion",
                12,
                Decimal("15.00"),
            ),
            (
                "Creatinina Sérica",
                "CRE-001",
                "bioquimica",
                "Funcion renal - creatinina",
                "Ayunas de 6 horas",
                24,
                Decimal("18.00"),
            ),
            (
                "Urea Sérica",
                "URE-001",
                "bioquimica",
                "Funcion renal - urea",
                "Ayunas de 6 horas",
                24,
                Decimal("15.00"),
            ),
            (
                "Perfil Lipidico",
                "LIP-001",
                "bioquimica",
                "Colesterol total, HDL, LDL, trigliceridos",
                "Ayunas de 12 horas",
                48,
                Decimal("50.00"),
            ),
            (
                "Proteinas Totales",
                "PRO-001",
                "bioquimica",
                "Proteinas totales y albumina",
                "Ayunas de 8 horas",
                24,
                Decimal("20.00"),
            ),
            (
                "Coagulacion Sanguinea",
                "COA-001",
                "hematologia",
                "TP, TTPa, INR",
                "Ayunas de 4 horas",
                24,
                Decimal("30.00"),
            ),
        ]

        for nombre, codigo, cat, desc, prep, tiempo, precio in examenes:
            tipo, created = TipoExamen.objects.get_or_create(
                codigo=codigo,
                defaults={
                    "nombre": nombre,
                    "categoria": cat,
                    "descripcion": desc,
                    "preparacion": prep,
                    "tiempo_resultado": tiempo,
                    "precio": precio,
                    "activo": True,
                    "created_by": admin_user,
                },
            )
            if created:
                self.log(f"  Created exam: {nombre}")
            self.tipos_examenes.append(tipo)
            self.stats["tipos_examenes"] = self.stats.get("tipos_examenes", 0) + 1

    def _seed_laboratorio(self):
        """Seed laboratorio"""
        from laboratorio.models import (
            ExamenLaboratorio,
            ResultadoLaboratorio,
            ValorReferencia,
        )

        existing = ExamenLaboratorio.objects.filter(
            paciente__id_clinico__startswith="SEED-",
        ).count()
        if existing > 0:
            self.log(f"Seed laboratorio already exist ({existing}), skipping.")
            return

        self.log_section("10. SEEDING LABORATORIO (25 lab results)")

        admin_user = self.users.get("seed_admin@fetal.com")
        medicos = [u for u in self.users.values() if u.rol == "medico"]
        count_examenes = 0
        count_resultados = 0

        # Create valor referencia for each tipo examen
        ref_data = {
            "hematologia": [
                (
                    "Hemoglobina",
                    Decimal("12.0"),
                    Decimal("16.0"),
                    "g/dL",
                    Decimal("7.0"),
                    Decimal("20.0"),
                ),
                (
                    "Hematocrito",
                    Decimal("36.0"),
                    Decimal("46.0"),
                    "%",
                    Decimal("20.0"),
                    Decimal("55.0"),
                ),
                (
                    "Leucocitos",
                    Decimal(4500),
                    Decimal(11000),
                    "celulas/mm3",
                    Decimal(2000),
                    Decimal(30000),
                ),
                (
                    "Plaquetas",
                    Decimal(150000),
                    Decimal(400000),
                    "celulas/mm3",
                    Decimal(50000),
                    Decimal(700000),
                ),
            ],
            "bioquimica": [
                (
                    "Glucosa",
                    Decimal(70),
                    Decimal(100),
                    "mg/dL",
                    Decimal(40),
                    Decimal(400),
                ),
                (
                    "Creatinina",
                    Decimal("0.6"),
                    Decimal("1.1"),
                    "mg/dL",
                    Decimal("0.3"),
                    Decimal("5.0"),
                ),
                (
                    "Urea",
                    Decimal(15),
                    Decimal(40),
                    "mg/dL",
                    Decimal(5),
                    Decimal(100),
                ),
                (
                    "Colesterol Total",
                    Decimal(0),
                    Decimal(200),
                    "mg/dL",
                    Decimal(0),
                    Decimal(500),
                ),
            ],
            "hormonal": [
                (
                    "TSH",
                    Decimal("0.4"),
                    Decimal("4.0"),
                    "UI/L",
                    Decimal("0.1"),
                    Decimal("20.0"),
                ),
                (
                    "T4 Libre",
                    Decimal("0.8"),
                    Decimal("1.8"),
                    "ng/dL",
                    Decimal("0.3"),
                    Decimal("4.0"),
                ),
            ],
        }

        for tipo_examen in self.tipos_examenes:
            params = ref_data.get(tipo_examen.categoria, [])
            for param, vmin, vmax, unit, crit_low, crit_high in params:
                ValorReferencia.objects.get_or_create(
                    tipo_examen=tipo_examen,
                    parametro=param,
                    defaults={
                        "valor_minimo": vmin,
                        "valor_maximo": vmax,
                        "unidad": unit,
                        "es_critico_bajo": crit_low,
                        "es_critico_alto": crit_high,
                    },
                )

        # Create lab exams
        pacientes_con_lab = random.sample(self.pacientes, min(25, len(self.pacientes)))
        for paciente in pacientes_con_lab:
            tipo = random.choice(self.tipos_examenes)
            fecha_sol = random_date(date(2025, 9, 1), date(2026, 4, 1))
            estado = random.choices(
                ["solicitado", "en_proceso", "completado", "completado", "completado"],
                weights=[5, 5, 60, 15, 15],
            )[0]

            control = random.choice(self.controles) if self.controles else None

            examen = ExamenLaboratorio(
                paciente=paciente,
                control_prenatal=control,
                tipo_examen=tipo,
                medico_solicitante=random.choice(medicos) if medicos else None,
                estado=estado,
                prioridad=random.choices(["normal", "urgente"], weights=[90, 10])[0],
                indicaciones="Control de embarazo. Semana correspondiente.",
                created_by=admin_user,
            )

            if estado in ["en_proceso", "completado"]:
                examen.fecha_muestra = fecha_sol + timedelta(days=1)
            if estado == "completado":
                examen.fecha_resultado = fecha_sol + timedelta(
                    days=random.randint(1, 3),
                )

            try:
                examen.full_clean()
                examen.save()
                count_examenes += 1
            except Exception:
                continue

            # Generate results if completed
            if estado == "completado":
                valores_ref = list(ValorReferencia.objects.filter(tipo_examen=tipo))
                for vr in valores_ref[:3]:  # Up to 3 results per exam
                    if vr.valor_minimo and vr.valor_maximo:
                        # Generate value within or slightly outside normal range
                        if random.random() < 0.85:  # 85% normal
                            valor = random_decimal(vr.valor_minimo, vr.valor_maximo)
                            es_normal = True
                            es_critico = False
                        else:  # 15% slightly abnormal
                            if random.random() < 0.5:
                                valor = random_decimal(
                                    vr.valor_minimo * Decimal("0.8"),
                                    vr.valor_minimo * Decimal("0.95"),
                                )
                            else:
                                valor = random_decimal(
                                    vr.valor_maximo * Decimal("1.05"),
                                    vr.valor_maximo * Decimal("1.2"),
                                )
                            es_normal = False
                            es_critico = False
                    else:
                        valor = None
                        es_normal = True
                        es_critico = False

                    ResultadoLaboratorio.objects.create(
                        examen=examen,
                        valor_referencia=vr,
                        valor_numerico=valor,
                        es_normal=es_normal,
                        es_critico=es_critico,
                        created_by=admin_user,
                    )
                    count_resultados += 1

            if count_examenes % 5 == 0:
                self.log(f"  Created {count_examenes} lab exams...")

        self.stats["examenes_laboratorio"] = count_examenes
        self.stats["resultados_laboratorio"] = count_resultados
        self.log(f"  Total: {count_examenes} exams, {count_resultados} results.")

    # =============================================================================
    # 10. CITAS
    # =============================================================================

    def _seed_citas(self):
        """Seed citas"""
        from citas.models import Cita

        existing = Cita.objects.filter(paciente__id_clinico__startswith="SEED-").count()
        if existing > 0:
            self.log(f"Seed citas already exist ({existing}), skipping.")
            return

        self.log_section("11. SEEDING CITAS (18 appointments)")

        admin_user = self.users.get("seed_admin@fetal.com")
        medicos = [u for u in self.users.values() if u.rol == "medico"]
        count = 0

        pacientes_con_cita = random.sample(self.pacientes, min(18, len(self.pacientes)))

        for paciente in pacientes_con_cita:
            fecha = random_date(date(2026, 4, 1), date(2026, 5, 15))
            hora = dtime(random.randint(8, 16), random.choice([0, 15, 30, 45]))
            estado = random.choices(
                ["agendada", "confirmada", "completada", "cancelada"],
                weights=[30, 20, 40, 10],
            )[0]

            cita = Cita(
                paciente=paciente,
                medico=random.choice(medicos),
                consultorio=random.choice(self.consultorios)
                if self.consultorios
                else None,
                fecha_cita=fecha,
                hora_cita=hora,
                duracion=30,
                tipo_cita=random.choice(["control", "primera_vez", "seguimiento"]),
                estado=estado,
                motivo=random.choice(
                    [
                        "Control prenatal de rutina",
                        "Evaluacion de resultados de laboratorio",
                        "Seguimiento de embarazo de riesgo",
                        "Primera consulta prenatal",
                        "Revision post-parto",
                        "Consulta por molestias",
                    ],
                ),
                creado_por=admin_user,
            )

            try:
                cita.full_clean()
                cita.save()
                count += 1
            except Exception as e:
                self.log_warning(f"  Error creating appointment: {e}")
                continue

        self.stats["citas"] = count
        self.log(f"  Total appointments created: {count}")

    # =============================================================================
    # 11. PARTOS
    # =============================================================================

    def _seed_partos(self):
        """Seed partos"""
        from partos.models import Parto

        existing = Parto.objects.filter(
            paciente__id_clinico__startswith="SEED-",
        ).count()
        if existing > 0:
            self.log(f"Seed partos already exist ({existing}), skipping.")
            return

        self.log_section("12. SEEDING PARTOS (12 deliveries)")

        admin_user = self.users.get("seed_admin@fetal.com")
        medicos = [u for u in self.users.values() if u.rol == "medico"]
        finalizados = [e for e in self.embarazos if e.estado == "finalizado"]
        count = 0

        # If not enough finished pregnancies, create partos for some active ones too
        activos = [e for e in self.embarazos if e.estado == "activo"]
        needed = max(0, 12 - len(finalizados))
        sample_size = min(needed, len(activos))
        candidatos = (
            finalizados[:12]
            if len(finalizados) >= 12
            else finalizados + random.sample(activos, sample_size)
        )

        for embarazo in candidatos[:12]:
            fecha_parto = random_date(
                embarazo.fecha_ultima_menstruacion + timedelta(days=250),
                min(
                    embarazo.fecha_ultima_menstruacion + timedelta(days=295),
                    date.today(),
                ),
            )

            semanas = (fecha_parto - embarazo.fecha_ultima_menstruacion).days // 7
            dias = (fecha_parto - embarazo.fecha_ultima_menstruacion).days % 7
            eg_texto = f"{semanas}+{dias}"

            tipo_parto = random.choices(
                [
                    "vaginal_espontaneo",
                    "cesarea_electiva",
                    "cesarea_urgencia",
                    "vaginal_instrumentado",
                ],
                weights=[55, 25, 15, 5],
            )[0]

            perdida = (
                random.randint(200, 600)
                if tipo_parto.startswith("vaginal")
                else random.randint(400, 900)
            )

            parto = Parto(
                paciente=embarazo.paciente,
                embarazo=embarazo,
                medico_responsable=random.choice(medicos) if medicos else None,
                fecha_parto=timezone.make_aware(
                    datetime.combine(
                        fecha_parto, dtime(random.randint(6, 22), random.randint(0, 59)),
                    ),
                ),
                fecha_ingreso=timezone.make_aware(
                    datetime.combine(
                        fecha_parto - timedelta(hours=random.randint(2, 8)),
                        dtime(random.randint(6, 18), 0),
                    ),
                ),
                edad_gestacional_parto=eg_texto,
                tipo_parto=tipo_parto,
                presentacion_fetal=random.choices(
                    ["cefalica", "podalica"], weights=[90, 10],
                )[0],
                estado_membranas=random.choice(["integras", "rotas_espontaneas"]),
                caracteristicas_liquido=random.choice(
                    ["Claro", "Claro", "Ligeramente meconial"],
                ),
                duracion_trabajo_parto_horas=Decimal(
                    str(round(random.uniform(4, 14), 2)),
                ),
                episiotomia=random.random() < 0.15,
                desgarros=random.random() < 0.1,
                placenta_completa=True,
                peso_placenta=random.randint(400, 650),
                perdida_sanguinea_estimada=perdida,
                hemorragia_postparto=random.random() < 0.05,
                oxitocina_utilizada=random.random() < 0.4,
                parto_finalizado=True,
                trabajo_parto_espontaneo=tipo_parto == "vaginal_espontaneo",
                observaciones_parto="Parto sin complicaciones. Apgar 8-9.",
                created_by=admin_user,
            )

            try:
                parto.full_clean()
                parto.save()
                count += 1
            except Exception as e:
                self.log_warning(f"  Error creating delivery: {e}")
                continue

        self.stats["partos"] = count
        self.log(f"  Total deliveries created: {count}")

    # =============================================================================
    # 12. CALCULADORAS DE RIESGO
    # =============================================================================

    def _seed_calculadoras_riesgo(self):
        """Seed calculadoras riesgo"""
        from calculadoras.models import (
            BiomarcadorMOM,
            CalculadoraRiesgo,
            MedicionEcografica,
        )

        existing = CalculadoraRiesgo.objects.filter(
            paciente__id_clinico__startswith="SEED-",
        ).count()
        if existing > 0:
            self.log(f"Seed calculadoras already exist ({existing}), skipping.")
            return

        self.log_section("13. SEEDING CALCULADORAS DE RIESGO (20 risk assessments)")

        admin_user = self.users.get("seed_admin@fetal.com")
        count = 0

        pacientes_con_calc = random.sample(self.pacientes, min(20, len(self.pacientes)))

        for paciente in pacientes_con_calc:
            tipo = random.choice(["preeclampsia", "trisomias", "diabetes_gestacional"])
            semanas = random.randint(8, 20)
            dias = random.randint(0, 6)
            edad_mat = (
                paciente.edad if hasattr(paciente, "edad") else random.randint(20, 38)
            )
            peso = float(paciente.peso_kg or 65)
            talla = float(paciente.altura_cm or 158)

            if tipo == "preeclampsia":
                riesgo_pct = round(random.uniform(0.5, 15.0), 3)
                ratio_den = max(5, int(100 / riesgo_pct))
                ratio = f"1:{ratio_den}"
                cat = (
                    "bajo"
                    if riesgo_pct < 3
                    else ("intermedio" if riesgo_pct < 8 else "alto")
                )
                interp = f"Riesgo de preeclampsia {cat} ({riesgo_pct}%). {'Se recomienda AAS 150mg' if cat in ['intermedio', 'alto'] else 'Continuar control habitual.'}"
                rec = (
                    "Aspirina 150mg nocturna desde semana 12 hasta semana 36."
                    if cat in ["intermedio", "alto"]
                    else "Control prenatal rutinario."
                )
            elif tipo == "trisomias":
                riesgo_pct = round(random.uniform(0.1, 5.0), 3)
                ratio_den = max(50, int(1000 / riesgo_pct))
                ratio = f"1:{ratio_den}"
                cat = (
                    "bajo"
                    if riesgo_pct < 1
                    else ("intermedio" if riesgo_pct < 2.5 else "alto")
                )
                interp = (
                    f"Riesgo de trisomia 21: {cat}. Marcadores ecograficos normales."
                )
                rec = (
                    "Continuar seguimiento. Ofrecer NIPT si riesgo intermedio."
                    if cat != "bajo"
                    else "Seguimiento habitual."
                )
            else:  # diabetes
                riesgo_pct = round(random.uniform(2.0, 25.0), 3)
                ratio_den = max(4, int(100 / riesgo_pct))
                ratio = f"1:{ratio_den}"
                cat = (
                    "bajo"
                    if riesgo_pct < 8
                    else ("intermedio" if riesgo_pct < 15 else "alto")
                )
                interp = f"Riesgo de diabetes gestacional: {cat}."
                rec = (
                    "Test de O'Sullivan en semana 24-28."
                    if cat == "bajo"
                    else "Considerar screening anticipado."
                )

            calc = CalculadoraRiesgo(
                paciente=paciente,
                embarazo=random.choice(self.embarazos) if self.embarazos else None,
                tipo=tipo,
                edad_gestacional_semanas=semanas,
                edad_gestacional_dias=dias,
                edad_materna=edad_mat,
                peso_kg=Decimal(str(round(peso, 2))),
                talla_cm=Decimal(str(round(talla, 2))),
                etnia="mestiza",
                tabaquismo=random.random() < 0.05,
                hta_cronica=random.random() < 0.08,
                diabetes_previa=random.random() < 0.03,
                preeclampsia_previa=random.random() < 0.05,
                paridad=random.randint(0, 3),
                riesgo_porcentaje=Decimal(str(riesgo_pct)),
                riesgo_ratio=ratio,
                categoria_riesgo=cat,
                interpretacion_clinica=interp,
                recomendaciones=rec,
                conducta_sugerida=rec,
                calculado_por=random.choice(
                    [u for u in self.users.values() if u.rol == "medico"],
                ),
                created_by=admin_user,
            )

            try:
                calc.full_clean()
                calc.save()
                count += 1

                # Add biomarkers for some
                if random.random() < 0.5:
                    marcador = random.choice(["pappa", "bhcg", "plgf", "pam"])
                    mom_val = round(random.uniform(0.6, 1.5), 3)
                    BiomarcadorMOM.objects.create(
                        calculadora=calc,
                        marcador=marcador,
                        valor_crudo=Decimal(str(round(random.uniform(10, 200), 4))),
                        unidad=random.choice(["mIU/mL", "ng/mL", "mmHg"]),
                        mediana_esperada=Decimal(
                            str(round(random.uniform(10, 200), 4)),
                        ),
                        mom_calculado=Decimal(str(mom_val)),
                        dentro_rango=0.8 <= mom_val <= 1.2,
                        created_by=admin_user,
                    )

                # Add ultrasound measurements
                if random.random() < 0.4:
                    MedicionEcografica.objects.create(
                        calculadora=calc,
                        crl_mm=Decimal(str(round(random.uniform(45, 85), 2)))
                        if semanas < 14
                        else None,
                        nt_mm=Decimal(str(round(random.uniform(1.0, 2.5), 2)))
                        if semanas < 14
                        else None,
                        fcf_lpm=random.randint(150, 175),
                        created_by=admin_user,
                    )

            except Exception as e:
                self.log_warning(f"  Error creating risk calculation: {e}")
                continue

        self.stats["calculadoras_riesgo"] = count
        self.log(f"  Total risk calculations created: {count}")

    # =============================================================================
    # 13. TRIAJE
    # =============================================================================

    def _seed_triaje(self):
        """Seed triaje"""
        from triaje.models import TriajeEnfermeria

        existing = TriajeEnfermeria.objects.filter(
            paciente__id_clinico__startswith="SEED-",
        ).count()
        if existing > 0:
            self.log(f"Seed triaje already exist ({existing}), skipping.")
            return

        self.log_section("14. SEEDING TRIAJE (15 triage assessments)")

        admin_user = self.users.get("seed_admin@fetal.com")
        enfermeros = [u for u in self.users.values() if u.rol == "enfermero"]
        if not enfermeros:
            self.log_warning("No enfermero users found, creating triages with admin.")
            enfermeros = list(self.users.values())[:1]

        count = 0
        pacientes_con_triaje = random.sample(
            self.pacientes, min(15, len(self.pacientes)),
        )

        for paciente in pacientes_con_triaje:
            _fecha = random_date(date(2026, 3, 1), date(2026, 4, 10))

            triaje = TriajeEnfermeria(
                paciente=paciente,
                peso_kg=Decimal(str(round(random.uniform(50, 90), 2))),
                talla_cm=Decimal(str(round(random.uniform(148, 168), 2))),
                presion_sistolica=random.randint(100, 135),
                presion_diastolica=random.randint(65, 85),
                temperatura=Decimal(str(round(random.uniform(36.0, 37.2), 1))),
                frecuencia_cardiaca=random.randint(68, 95),
                frecuencia_respiratoria=random.randint(14, 20),
                saturacion_oxigeno=random.randint(96, 100),
                motivo_visita=random.choice(
                    [
                        "Control prenatal programado",
                        "Revision de resultados de laboratorio",
                        "Malestar general",
                        "Dolor abdominal leve",
                        "Cefalea moderada",
                    ],
                ),
                dolor_escala=random.randint(0, 4),
                nivel_conciencia="alerta",
                observaciones="Paciente colaboradora, sin signos de alarma evidentes.",
                enfermera=random.choice(enfermeros),
                created_by=admin_user,
            )

            try:
                triaje.full_clean()
                triaje.save()
                count += 1
            except Exception as e:
                self.log_warning(f"  Error creating triage: {e}")
                continue

        self.stats["triaje"] = count
        self.log(f"  Total triage assessments created: {count}")

    # =============================================================================
    # 14. EVOLUCIONES
    # =============================================================================

    def _seed_evoluciones(self):
        """Seed evoluciones"""
        from evoluciones.models import EvolucionEmbarazo

        existing = EvolucionEmbarazo.objects.filter(
            paciente__id_clinico__startswith="SEED-",
        ).count()
        if existing > 0:
            self.log(f"Seed evoluciones already exist ({existing}), skipping.")
            return

        self.log_section("15. SEEDING EVOLUCIONES (30 pregnancy evolutions)")

        _admin_user = self.users.get("seed_admin@fetal.com")
        medicos = [u for u in self.users.values() if u.rol == "medico"]
        count = 0

        for embarazo in self.embarazos[:15]:
            for _ in range(2):
                fecha = random_date(embarazo.fecha_ultima_menstruacion, date.today())
                tipo = random.choice(["control", "ecografia", "laboratorio", "cita"])

                EvolucionEmbarazo.objects.create(
                    embarazo=embarazo,
                    paciente=embarazo.paciente,
                    fecha_evento=fecha,
                    tipo_evento=tipo,
                    descripcion=random.choice(OBSERVACIONES_CONTROL),
                    medico=random.choice(medicos) if medicos else None,
                )
                count += 1

        self.stats["evoluciones"] = count
        self.log(f"  Total pregnancy evolutions created: {count}")

    # =============================================================================
    # 15. NOTAS DE EVOLUCION
    # =============================================================================

    def _seed_notas_evolucion(self):
        """Seed notas evolucion"""
        from notas_evolucion.models import NotaEvolucion

        existing = NotaEvolucion.objects.filter(
            paciente__id_clinico__startswith="SEED-",
        ).count()
        if existing > 0:
            self.log(f"Seed notas evolucion already exist ({existing}), skipping.")
            return

        self.log_section("16. SEEDING NOTAS DE EVOLUCION (20 medical notes)")

        admin_user = self.users.get("seed_admin@fetal.com")
        medicos = [u for u in self.users.values() if u.rol == "medico"]
        count = 0

        pacientes_con_nota = random.sample(self.pacientes, min(20, len(self.pacientes)))

        for paciente in pacientes_con_nota:
            fecha = random_date(date(2026, 1, 1), date(2026, 4, 9))
            semanas = random.randint(12, 38)

            nota = NotaEvolucion(
                paciente=paciente,
                embarazo=random.choice(self.embarazos) if self.embarazos else None,
                medico=random.choice(medicos) if medicos else None,
                fecha_consulta=timezone.make_aware(
                    datetime.combine(
                        fecha, dtime(random.randint(8, 17), random.choice([0, 30])),
                    ),
                ),
                tipo_consulta=random.choice(
                    ["control_prenatal", "seguimiento", "control_prenatal"],
                ),
                motivo_consulta=random.choice(
                    [
                        "Control prenatal de rutina",
                        "Seguimiento de embarazo",
                        "Evaluacion de signos vitales",
                        "Control de crecimiento fetal",
                    ],
                ),
                presion_arterial_sistolica=random.randint(100, 130),
                presion_arterial_diastolica=random.randint(65, 85),
                frecuencia_cardiaca=random.randint(70, 90),
                frecuencia_respiratoria=random.randint(14, 18),
                temperatura=Decimal(str(round(random.uniform(36.2, 37.0), 1))),
                saturacion_oxigeno=random.randint(96, 100),
                edad_gestacional_semanas=semanas,
                edad_gestacional_dias=random.randint(0, 6),
                altura_uterina=Decimal(
                    str(round(semanas + random.uniform(-1.5, 1.5), 1)),
                )
                if semanas >= 20
                else None,
                frecuencia_cardiaca_fetal=random.randint(130, 160),
                presentacion_fetal=random.choice(["Cefalica", "Cefalica", "Podalica"]),
                movimientos_fetales="Presentes y activos",
                examen_fisico="Paciente en buen estado general. Mucosas rosadas y humedas. Cardiopulmonar sin alteraciones.",
                examen_obstetrico="Abdomen gravido, globuloso. Altura uterina concordante con edad gestacional.",
                diagnosticos=f"Embarazo de {semanas} semanas. Control prenatal de rutina.",
                plan_tratamiento="Continuar con vitaminas prenatales. Proximo control en 4 semanas.",
                indicaciones="Signos de alarma explicados. Acudir a urgencias si sangrado, cefalea intensa o disminucion de movimientos fetales.",
                created_by=admin_user,
            )

            try:
                nota.full_clean()
                nota.save()
                count += 1
            except Exception as e:
                self.log_warning(f"  Error creating medical note: {e}")
                continue

        self.stats["notas_evolucion"] = count
        self.log(f"  Total medical notes created: {count}")

    # =============================================================================
    # 16. VACUNAS
    # =============================================================================

    def _seed_tipos_vacunas(self):
        """Seed tipos vacunas"""
        from vacunas.models import TipoVacuna

        if TipoVacuna.objects.exists():
            self.tipos_vacunas = list(TipoVacuna.objects.all())
            self.log(
                f"Tipos de vacunas already exist ({len(self.tipos_vacunas)}), using existing.",
            )
            return

        self.log_section("17. SEEDING TIPOS DE VACUNAS")

        admin_user = self.users.get("seed_admin@fetal.com")
        vacunas_data = [
            (
                "Influenza (Gripe)",
                "Vacuna contra la influenza estacional, recomendada en embarazo",
                1,
                None,
                "Reaccion alergica severa previa",
                "Dolor local leve, febricula transitoria",
                True,
            ),
            (
                "Tdap (Tetanos, Difteria, Tos Ferina)",
                "Vacuna triple bacteriana para proteccion neonatal",
                1,
                None,
                "Reaccion neurologica previa",
                "Dolor e inflamacion en sitio de aplicacion",
                True,
            ),
            (
                "Hepatitis B",
                "Vacuna contra Hepatitis B para embarazadas no inmunizadas",
                3,
                30,
                "Alergia a levadura",
                "Dolor local, malestar general",
                False,
            ),
            (
                "COVID-19",
                "Vacuna contra SARS-CoV-2, recomendada en embarazo",
                2,
                21,
                "Reaccion anafilactica a componente",
                "Dolor local, fatiga, cefalea",
                True,
            ),
            (
                "Neumococo",
                "Vacuna neumococica para grupos de riesgo",
                1,
                None,
                "Reaccion alergica previa",
                "Dolor local, fiebre leve",
                False,
            ),
        ]

        for (
            nombre,
            desc,
            dosis,
            intervalo,
            contra,
            efectos,
            obligatoria,
        ) in vacunas_data:
            tv, created = TipoVacuna.objects.get_or_create(
                nombre=nombre,
                defaults={
                    "descripcion": desc,
                    "dosis_requeridas": dosis,
                    "intervalo_dosis_dias": intervalo,
                    "contraindicaciones": contra,
                    "efectos_secundarios": efectos,
                    "obligatoria_embarazo": obligatoria,
                    "activo": True,
                    "created_by": admin_user,
                },
            )
            if created:
                self.log(f"  Created vaccine: {nombre}")
            self.tipos_vacunas.append(tv)
            self.stats["tipos_vacunas"] = self.stats.get("tipos_vacunas", 0) + 1

    def _seed_vacunas(self):
        """Seed vacunas"""
        from vacunas.models import RegistroVacuna

        existing = RegistroVacuna.objects.filter(
            paciente__id_clinico__startswith="SEED-",
        ).count()
        if existing > 0:
            self.log(f"Seed vacunas already exist ({existing}), skipping.")
            return

        self.log_section("18. SEEDING REGISTROS DE VACUNAS (20 vaccination records)")

        admin_user = self.users.get("seed_admin@fetal.com")
        enfermeros = [u for u in self.users.values() if u.rol == "enfermero"] or list(
            self.users.values(),
        )[:2]
        count = 0

        pacientes_con_vacuna = random.sample(
            self.pacientes, min(15, len(self.pacientes)),
        )

        for paciente in pacientes_con_vacuna:
            num_vacunas = random.randint(1, 2)
            for _ in range(num_vacunas):
                tipo = random.choice(self.tipos_vacunas)
                fecha = random_date(date(2026, 1, 1), date(2026, 4, 5))

                reg = RegistroVacuna(
                    paciente=paciente,
                    embarazo=random.choice(self.embarazos) if self.embarazos else None,
                    tipo_vacuna=tipo,
                    fecha_aplicacion=timezone.make_aware(
                        datetime.combine(fecha, dtime(random.randint(8, 15), 0)),
                    ),
                    numero_dosis=1,
                    lote=f"L{random.randint(100000, 999999)}",
                    laboratorio=random.choice(
                        [
                            "Instituto Llorens",
                            "GlaxoSmithKline",
                            "Sanofi Pasteur",
                            "Pfizer",
                        ],
                    ),
                    via_administracion="intramuscular",
                    sitio_aplicacion=random.choice(
                        ["Deltoides izquierdo", "Deltoides derecho", "Muslo izquierdo"],
                    ),
                    aplicado_por=random.choice(enfermeros),
                    observaciones="Vacuna aplicada sin incidentes.",
                    created_by=admin_user,
                )

                try:
                    reg.full_clean()
                    reg.save()
                    count += 1
                except Exception as e:
                    self.log_warning(f"  Error creating vaccination: {e}")
                    continue

        self.stats["vacunas"] = count
        self.log(f"  Total vaccination records created: {count}")

    # =============================================================================
    # 17. NOTIFICACIONES
    # =============================================================================

    def _seed_notificaciones(self):
        """Seed notificaciones"""
        from notificaciones.models import Notificacion

        existing = Notificacion.objects.filter(
            usuario__email__startswith="seed_",
        ).count()
        if existing > 0:
            self.log(f"Seed notificaciones already exist ({existing}), skipping.")
            return

        self.log_section("19. SEEDING NOTIFICACIONES (30 notifications)")

        notif_templates = [
            (
                "cita_proxima",
                "alta",
                "Recordatorio: Cita proxima",
                "Tiene una cita agendada para los proximos dias.",
            ),
            (
                "examen_listo",
                "normal",
                "Resultados de laboratorio listos",
                "Sus resultados de laboratorio estan disponibles.",
            ),
            (
                "alerta_advertencia",
                "alta",
                "Atencion: Control pendiente",
                "Tiene un control prenatal pendiente de realizar.",
            ),
            (
                "recordatorio_control",
                "normal",
                "Recordatorio de control prenatal",
                "Le recordamos que debe asistir a su control prenatal.",
            ),
            (
                "cita_confirmada",
                "baja",
                "Cita confirmada",
                "Su cita ha sido confirmada exitosamente.",
            ),
            (
                "alerta_critica",
                "urgente",
                "Valor de laboratorio fuera de rango",
                "Se detecto un valor que requiere atencion medica.",
            ),
            (
                "recordatorio_medicacion",
                "normal",
                "Recordatorio de medicacion",
                "No olvide tomar sus vitaminas prenatales.",
            ),
            (
                "mensaje_medico",
                "baja",
                "Mensaje de su medico",
                "Su medico le ha enviado un mensaje importante.",
            ),
        ]

        usuarios_notif = list(self.users.values())
        count = 0

        for _ in range(30):
            tipo, prioridad, titulo, mensaje = random.choice(notif_templates)
            usuario = random.choice(usuarios_notif)
            fecha_creacion = random_date(date(2026, 3, 1), date(2026, 4, 10))

            Notificacion.objects.create(
                usuario=usuario,
                tipo=tipo,
                prioridad=prioridad,
                titulo=titulo,
                mensaje=mensaje,
                leida=random.random() < 0.4,
                metadata={"seed": True},
                fecha_creacion=timezone.make_aware(
                    datetime.combine(
                        fecha_creacion,
                        dtime(random.randint(7, 20), random.randint(0, 59)),
                    ),
                ),
            )
            count += 1

        self.stats["notificaciones"] = count
        self.log(f"  Total notifications created: {count}")

    # =============================================================================
    # 18. IA MEDICA
    # =============================================================================

    def _seed_ia_medica(self):
        """Seed ia medica"""
        from ia_medica.models import (
            AnalisisLaboratorioML,
            ConfiguracionModeloIA,
            ConsultaIA,
            EstadisticasIA,
        )

        existing = ConsultaIA.objects.count()
        if existing > 0:
            self.log(f"Seed IA medica already exist ({existing} consultas), skipping.")
            return

        self.log_section("20. SEEDING IA MEDICA")

        count = 0

        # AI Consultations
        consultas_data = [
            (
                "preeclampsia",
                "Cual es el riesgo de preeclampsia en una paciente de 35 anos con HTA cronica",
                "El riesgo de preeclampsia se incrementa significativamente con hipertension cronica y edad materna avanzada. Se recomienda calcular el riesgo con la calculadora FMF. Factores de riesgo incluyen: HTA cronica (LR 2.3), edad >35 (LR 1.5). Se sugiere AAS 150mg desde semana 12.",
                85,
            ),
            (
                "diabetes",
                "Como manejar la diabetes gestacional diagnosticada en semana 28",
                "El manejo inicial incluye medidas dieteticas: control de carbohidratos (40-45%), distribucion en 6 comidas. Monitoreo de glucemia: ayunas <95, 1h postprandial <140. Si no se logran metas en 1-2 semanas, iniciar insulinoterapia.",
                92,
            ),
            (
                "laboratorio",
                "Interpretar hemoglobina de 10.2 g/dL en embarazo de segundo trimestre",
                "Hemoglobina de 10.2 g/dL indica anemia leve en segundo trimestre (cutoff <10.5). Es fisiologica por hemodilucion pero requiere suplementacion. Se recomienda sulfato ferroso 120mg/dia + acido folico 5mg. Control en 4 semanas.",
                88,
            ),
            (
                "rciu",
                "Parametros ecograficos sugestivos de RCIU en semana 32",
                "Los criterios ecograficos de RCIU incluyen: EFW <p10, AC <p10, relacion CC/CA aumentada. Doppler de arteria umbilical es clave para manejo. Si IP aumentado o flujo diastolico ausente/reverso, considerar finalizacion del embarazo.",
                90,
            ),
            (
                "edad_gestacional",
                "Discordancia entre FUM y ecografia de primer trimestre en 10 dias",
                "Cuando hay discordancia >7 dias entre FUM y ecografia de primer trimestre (CRL), se debe ajustar la fecha probable de parto por ecografia. El CRL en primer trimestre es el parametro mas preciso para datar (margen error +/- 5-7 dias).",
                94,
            ),
            (
                "general",
                "Suplementacion recomendada durante el embarazo",
                "Suplementacion estandar: Acido folico 0.4-5mg/dia (desde preconcepcion), Hierro 30-60mg/dia, Calcio 1-1.5g/dia, Vitamina D 600 UI/dia. En poblacion de altura, considerar suplementacion adicional de hierro.",
                87,
            ),
            (
                "emergencia",
                "Manejo de hemorragia vaginal en segundo trimestre",
                "Evaluacion inicial: signos vitales, estabilizacion si necesario. Ecografia urgente para descartar placenta previa. NO tacto vaginal hasta descartar placenta previa. Si placenta previa: reposo, corticoides si <34 sem, evaluar necesidad de transfusion.",
                95,
            ),
            (
                "laboratorio",
                "Plaquetas de 95,000 en semana 36 de embarazo",
                "Trombocitopenia leve-moderada en tercer trimestre. Diagnostico diferencial: trombocitopenia gestacional (65%), preeclampsia/HELLP (20%), PTI (4%). Solicitar: perfil hepatico, LDH, frotis periferico. Si asintomatica y resto normal, probablemente gestacional.",
                91,
            ),
        ]

        # Reload pacientes from DB if in-memory list is empty (e.g. after partial seed run)
        if not self.pacientes:

            from pacientes.models import Paciente
            self.pacientes = list(Paciente.objects.all())

        usuarios_ia = list(self.users.values())
        for categoria, consulta, respuesta, confianza in consultas_data:
            paciente = (
                random.choice(self.pacientes)
                if (self.pacientes and random.random() < 0.7)
                else None
            )
            ConsultaIA.objects.create(
                usuario=random.choice(usuarios_ia),
                paciente=paciente,
                consulta_original=consulta,
                consulta_procesada=consulta.lower().strip(),
                idioma_detectado="auto",
                categoria=categoria,
                respuesta_ia=respuesta,
                confianza=confianza,
                requiere_ml=random.random() < 0.3,
                util=random.choice([True, True, True, False]),
                rating=random.randint(3, 5),
                tiempo_respuesta_ms=random.randint(200, 1500),
                metadata={"seed": True},
            )
            count += 1

        # AI Lab Analysis
        if not self.pacientes:

            from pacientes.models import Paciente
            self.pacientes = list(Paciente.objects.all())
        for _ in range(5 if self.pacientes else 0):
            paciente = random.choice(self.pacientes)
            AnalisisLaboratorioML.objects.create(
                paciente=paciente,
                tipo_analisis=random.choice(["hemograma", "glucosa", "completo"]),
                datos_entrada={
                    "hemoglobina": round(random.uniform(9, 14), 1),
                    "hematocrito": round(random.uniform(28, 42), 1),
                },
                prediccion=random.choice(
                    [
                        "Anemia leve del embarazo",
                        "Riesgo de diabetes gestacional bajo",
                        "Parametros dentro de normalidad",
                    ],
                ),
                riesgo_detectado=random.choice(["bajo", "medio", "bajo"]),
                probabilidad=round(random.uniform(0.65, 0.95), 3),
                confianza_modelo=round(random.uniform(75, 95), 1),
                patologias_detectadas=["Anemia leve"] if random.random() < 0.4 else [],
                alertas_criticas=[],
                recomendaciones=["Suplementacion con hierro", "Control en 4 semanas"]
                if random.random() < 0.4
                else ["Seguimiento habitual"],
                acciones_sugeridas=["Solicitar hemograma de control"],
                valores_fuera_rango=[],
                modelo_usado="RandomForest_v2",
                version_modelo="2.1",
            )
            count += 1

        # Model Config
        ConfiguracionModeloIA.objects.create(
            nombre_modelo="NLP Obstetrico",
            tipo_modelo="nlp",
            version="1.0.0",
            descripcion="Modelo de procesamiento de lenguaje natural para consultas obstetricas",
            estado="produccion",
            activo=True,
            precision=89.5,
            recall=85.2,
            f1_score=87.3,
            accuracy=88.1,
            parametros={"max_tokens": 512, "temperature": 0.7},
            features_usadas=["categoria", "edad_gestacional", "antecedentes"],
            dataset_entrenamiento="10,000 consultas obstetricas anonimizadas",
            fecha_entrenamiento=timezone.now() - timedelta(days=30),
            epocas=20,
            total_predicciones=1500,
            predicciones_correctas=1350,
            ultima_prediccion=timezone.now(),
        )

        ConfiguracionModeloIA.objects.create(
            nombre_modelo="ML Laboratorio",
            tipo_modelo="ml_laboratorio",
            version="2.1.0",
            descripcion="Modelo de machine learning para analisis de resultados de laboratorio",
            estado="produccion",
            activo=True,
            precision=92.3,
            recall=88.7,
            f1_score=90.5,
            accuracy=91.0,
            parametros={"n_estimators": 200, "max_depth": 15},
            features_usadas=[
                "hemoglobina",
                "hematocrito",
                "glucosa",
                "creatinina",
                "plaquetas",
            ],
            dataset_entrenamiento="5,000 resultados de laboratorio con validacion medica",
            fecha_entrenamiento=timezone.now() - timedelta(days=15),
            epocas=50,
            total_predicciones=800,
            predicciones_correctas=730,
            ultima_prediccion=timezone.now(),
        )

        # Statistics
        EstadisticasIA.objects.create(
            fecha=date.today(),
            total_consultas=13,
            consultas_por_categoria={
                "preeclampsia": 3,
                "diabetes": 2,
                "laboratorio": 4,
                "rciu": 1,
                "general": 2,
                "emergencia": 1,
            },
            tiempo_respuesta_promedio_ms=650,
            total_analisis_ml=5,
            alertas_criticas_generadas=1,
            patologias_detectadas={"anemia": 3, "riesgo_diabetes": 1},
            precision_promedio=89.2,
            confianza_promedio=87.5,
            total_feedback=10,
            feedback_positivo=8,
            rating_promedio=4.2,
            usuarios_activos=4,
            nuevos_usuarios=1,
        )

        self.stats["ia_consultas"] = count
        self.log(f"  Total AI records created: {count}")

    # =============================================================================
    # 19. AUDITORIA
    # =============================================================================

    def _seed_auditoria(self):
        """Seed auditoria"""
        from auditoria.models import RegistroAuditoria

        existing = RegistroAuditoria.objects.count()
        if existing > 0:
            self.log(f"Seed auditoria already exist ({existing}), skipping.")
            return

        self.log_section("21. SEEDING AUDITORIA (15 audit records)")

        admin_user = self.users.get("seed_admin@fetal.com")
        modules = [
            "Paciente",
            "Embarazo",
            "ControlPrenatal",
            "Ecografia",
            "Laboratorio",
            "Cita",
            "Usuario",
        ]
        acciones = ["crear", "actualizar", "crear", "crear", "actualizar"]
        count = 0

        for _ in range(15):
            RegistroAuditoria.objects.create(
                modulo=random.choice(modules),
                accion=random.choice(acciones),
                registro_id=random.randint(1, 100),
                usuario=admin_user,
                fecha=timezone.make_aware(
                    datetime.combine(
                        random_date(date(2026, 3, 1), date.today()),
                        dtime(random.randint(7, 19), random.randint(0, 59)),
                    ),
                ),
                datos_anteriores=None,
                datos_nuevos={"seed": True, "modulo": "seeder"},
                ip_address=f"192.168.1.{random.randint(1, 254)}",
                user_agent="Mozilla/5.0 (Seed Data Generator)",
            )
            count += 1

        self.stats["auditoria"] = count
        self.log(f"  Total audit records created: {count}")

    # =============================================================================
    # SUMMARY
    # =============================================================================

    def _print_summary(self):
        """Print summary"""
        self.log_section("SEEDING COMPLETE - SUMMARY")
        self.stdout.write(
            self.style.SUCCESS(f"""
  {"=" * 50}
  {"Module":<30} {"Records":>8}
  {"=" * 50}
  {"Roles":<30} {self.stats.get("roles", 0):>8}
  {"Usuarios":<30} {self.stats.get("usuarios", 0):>8}
  {"Consultorios":<30} {self.stats.get("consultorios", 0):>8}
  {"Pacientes":<30} {self.stats.get("pacientes", 0):>8}
  {"Antecedentes Gineco":<30} {self.stats.get("antecedentes_gineco", 0):>8}
  {"Antecedentes Patologicos":<30} {self.stats.get("antecedentes_patologicos", 0):>8}
  {"Embarazos":<30} {self.stats.get("embarazos", 0):>8}
  {"Controles Prenatales":<30} {self.stats.get("controles", 0):>8}
  {"Ecografias":<30} {self.stats.get("ecografias", 0):>8}
  {"Tipos Examenes":<30} {self.stats.get("tipos_examenes", 0):>8}
  {"Examenes Laboratorio":<30} {self.stats.get("examenes_laboratorio", 0):>8}
  {"Resultados Laboratorio":<30} {self.stats.get("resultados_laboratorio", 0):>8}
  {"Citas":<30} {self.stats.get("citas", 0):>8}
  {"Partos":<30} {self.stats.get("partos", 0):>8}
  {"Calculadoras Riesgo":<30} {self.stats.get("calculadoras_riesgo", 0):>8}
  {"Triaje":<30} {self.stats.get("triaje", 0):>8}
  {"Evoluciones":<30} {self.stats.get("evoluciones", 0):>8}
  {"Notas Evolucion":<30} {self.stats.get("notas_evolucion", 0):>8}
  {"Tipos Vacunas":<30} {self.stats.get("tipos_vacunas", 0):>8}
  {"Vacunas":<30} {self.stats.get("vacunas", 0):>8}
  {"Notificaciones":<30} {self.stats.get("notificaciones", 0):>8}
  {"IA Consultas/Analisis":<30} {self.stats.get("ia_consultas", 0):>8}
  {"Auditoria":<30} {self.stats.get("auditoria", 0):>8}
  {"=" * 50}

  All users have password: admin123
  Users created:
    - seed_admin@fetal.com (administrador/superuser)
    - seed_dr.garcia@fetal.com (medico)
    - seed_dr.mamani@fetal.com (medico)
    - seed_dr.lopez@fetal.com (medico)
    - seed_nurse.rosa@fetal.com (enfermero)
    - seed_nurse.ana@fetal.com (enfermero)
  {"=" * 50}
        """),
        )
