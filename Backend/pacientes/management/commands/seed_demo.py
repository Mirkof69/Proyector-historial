"""
Comando: python manage.py seed_demo
Crea datos de prueba realistas para la clínica demo:
- 1 médico + 1 enfermera + 1 recepcionista
- 15 pacientes bolivianas con embarazos activos
- Controles prenatales con signos vitales
- Citas programadas
- Triaje de enfermería
- Alertas médicas de ejemplo
"""
import random
from datetime import date, datetime, timedelta

from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context

SCHEMA = "clinica_demo"

PACIENTES_DATA = [
    ("María", "Quispe", "Mamani", "1234567", date(1995, 3, 15), "O+", "bajo", 28),
    ("Ana", "Flores", "Condori", "2345678", date(1998, 7, 22), "A+", "medio", 20),
    ("Carmen", "Mamani", "Huanca", "3456789", date(1990, 11, 5), "B+", "alto", 35),
    ("Lucía", "Choque", "Quispe", "4567890", date(2000, 1, 30), "O-", "bajo", 16),
    ("Rosa", "Apaza", "Flores", "5678901", date(1993, 5, 18), "AB+", "medio", 32),
    ("Valentina", "Vargas", "López", "6789012", date(1997, 9, 12), "A-", "bajo", 24),
    ("Gabriela", "Torrez", "Chávez", "7890123", date(1992, 4, 7), "O+", "alto", 38),
    ("Sandra", "Limachi", "Cusi", "8901234", date(1999, 12, 25), "B-", "bajo", 12),
    ("Patricia", "Mendoza", "Poma", "9012345", date(1988, 8, 3), "O+", "medio", 40),
    ("Elena", "Huanca", "Ramos", "0123456", date(1996, 2, 14), "A+", "bajo", 26),
    ("Sofía", "Condori", "Yujra", "1122334", date(2001, 6, 20), "O+", "bajo", 10),
    ("Isabel", "Ramos", "Marca", "2233445", date(1991, 10, 8), "B+", "medio", 36),
    ("Claudia", "López", "Quispe", "3344556", date(1994, 3, 27), "AB-", "alto", 30),
    ("Teresa", "García", "Mamani", "4455667", date(1987, 7, 11), "O+", "alto", 42),
    ("Miriam", "Poma", "Choque", "5566778", date(2002, 1, 5), "A+", "bajo", 8),
]


class Command(BaseCommand):
    help = "Crea datos de prueba para la demo de Fetal Medical Bolivia"

    def handle(self, *args, **kwargs):
        with schema_context(SCHEMA):
            self._crear_usuarios()
            self._crear_pacientes()
            self._crear_antecedentes_obstetricos()
            self._crear_embarazos_anteriores()
            self._crear_analisis_cnn()
            self._crear_laboratorio_5nf()
            self._crear_mediciones_ecograficas_5nf()
            self._crear_notas_evolucion()
            self._crear_evoluciones_embarazo()
            self._crear_ecografias()
            self._crear_notificaciones()
        self.stdout.write(self.style.SUCCESS("[OK] Seed data creado exitosamente"))

    def _crear_usuarios(self):
        from usuarios.models import Usuario

        usuarios = [
            {
                "email": "dra.garcia@fetalmedical.bo",
                "nombre": "María Elena",
                "apellido_paterno": "García",
                "apellido_materno": "Soliz",
                "rol": "medico",
                "especialidad": "Ginecología y Obstetricia",
                "registro_profesional": "MP-12345",
                "password": "Demo2026!",
            },
            {
                "email": "enf.mamani@fetalmedical.bo",
                "nombre": "Rosa",
                "apellido_paterno": "Mamani",
                "apellido_materno": "Condori",
                "rol": "enfermera",
                "especialidad": "",
                "registro_profesional": "ENF-5678",
                "password": "Demo2026!",
            },
            {
                "email": "recep.flores@fetalmedical.bo",
                "nombre": "Juan Carlos",
                "apellido_paterno": "Flores",
                "apellido_materno": "Quispe",
                "rol": "recepcion",
                "especialidad": "",
                "registro_profesional": "",
                "password": "Demo2026!",
            },
        ]

        for u in usuarios:
            if not Usuario.objects.filter(email=u["email"]).exists():
                usuario = Usuario.objects.create_user(
                    email=u["email"],
                    nombre=u["nombre"],
                    apellido_paterno=u["apellido_paterno"],
                    apellido_materno=u["apellido_materno"],
                    rol=u["rol"],
                    especialidad=u.get("especialidad") or None,
                    activo=True,
                    mfa_enabled=False,
                    mfa_obligatorio=False,
                    password=u["password"],
                )
                self.stdout.write(f"  [+] Usuario creado: {u['email']}")
            else:
                self.stdout.write(f"  [=] Ya existe: {u['email']}")

    def _crear_pacientes(self):
        from controles.models import ControlPrenatal
        from embarazos.models import Embarazo
        from pacientes.models import Paciente
        from usuarios.models import Usuario

        medico = Usuario.objects.filter(rol="medico").first()
        today = date.today()

        for nombre, ap_pat, ap_mat, ci, fnac, grupo, riesgo, semanas in PACIENTES_DATA:
            # Crear paciente
            from pacientes.fields import compute_search_hash
            ci_hash = compute_search_hash(str(ci))
            existing = Paciente.objects.filter(ci_hash=ci_hash).first()
            if existing:
                paciente = existing
                created = False
            else:
                paciente = Paciente(
                    ci=ci,
                    nombre=nombre,
                    apellido_paterno=ap_pat,
                    apellido_materno=ap_mat,
                    fecha_nacimiento=fnac,
                    # El sistema es exclusivamente gineco-obstetrico: toda
                    # paciente es femenina. El seed lo omitia y dejaba el campo
                    # obligatorio vacio (detectado en la auditoria de integridad).
                    genero="femenino",
                    tipo_sangre=grupo,
                    telefono=f"7{random.randint(1000000, 9999999)}",
                    ciudad=random.choice(["La Paz", "El Alto", "Cochabamba"]),
                    # Los choices del modelo son la forma canonica en masculino
                    # ("soltero"/"casado"); la UI ya los muestra en femenino via
                    # getEstadoCivilConGenero(). El seed guardaba "soltera"/"casada",
                    # valores que NO existen en choices.
                    estado_civil=random.choice(["soltero", "casado", "union_libre"]),
                    activo=True,
                    estado_paciente="activo",
                )
                paciente.save()
                created = True

            if not created:
                continue

            self.stdout.write(f"  [+] Paciente: {nombre} {ap_pat}")

            # Calcular FUM
            fum = today - timedelta(weeks=semanas, days=random.randint(0, 6))
            fpp = fum + timedelta(weeks=40)

            # Saltar si ya tiene embarazo activo
            if paciente.embarazos.filter(estado="activo").exists():
                continue

            # Crear embarazo
            embarazo = Embarazo.objects.create(
                paciente=paciente,
                numero_gesta=random.randint(1, 4),
                numero_para=random.randint(0, 2),
                numero_abortos=0,
                numero_cesareas=random.randint(0, 1),
                fecha_ultima_menstruacion=fum,
                fecha_probable_parto=fpp,
                tipo_embarazo="simple",
                riesgo_embarazo=riesgo,
                estado="activo",
                peso_pregestacional=round(random.uniform(52, 75), 1),
                talla_materna=round(random.uniform(150, 168), 1),
                medico_responsable=medico,
            )

            # Crear controles prenatales
            num_controles = max(1, semanas // 4)
            for i in range(num_controles):
                semana_control = max(4, semanas - (i * 4))
                fecha_control = today - timedelta(weeks=(num_controles - i - 1) * 4)

                # PA normal o con alerta
                if riesgo == "alto":
                    sistolica = random.randint(130, 155)
                    diastolica = random.randint(85, 100)
                else:
                    sistolica = random.randint(100, 120)
                    diastolica = random.randint(60, 80)

                from decimal import Decimal
                def d(v, p=1):
                    return Decimal(str(round(v, p)))
                au = semana_control - 2 if semana_control > 12 else None
                ControlPrenatal.objects.create(
                    embarazo=embarazo,
                    paciente=paciente,
                    numero_control=i + 1,
                    fecha_control=fecha_control,
                    semanas_gestacion=semana_control,
                    dias_gestacion=0,
                    peso_actual=d(random.uniform(56, 82)),
                    peso_pregestacional=d(float(embarazo.peso_pregestacional)),
                    talla=d(float(embarazo.talla_materna)),
                    presion_arterial_sistolica=sistolica,
                    presion_arterial_diastolica=diastolica,
                    frecuencia_cardiaca=random.randint(72, 92),
                    temperatura=d(random.uniform(36.2, 37.1)),
                    altura_uterina=d(au) if au else None,
                    frecuencia_cardiaca_fetal=random.randint(130, 160) if semana_control > 10 else None,
                    presentacion_fetal="cefalica" if semana_control > 28 else None,
                    movimientos_fetales="presentes" if semana_control > 20 else None,
                    medico=medico,
                    observaciones="Control prenatal de rutina.",
                )

            self._crear_cita(paciente, embarazo, today, semanas)

        self._crear_citas_pendientes()
        self._crear_triaje()
        self._crear_alertas_medicas()

    def _crear_citas_pendientes(self):
        try:
            import datetime as dt

            from citas.models import Cita
            from pacientes.models import Paciente
            from usuarios.models import Usuario
            medico = Usuario.objects.filter(rol="medico").first()
            today = date.today()
            for paciente in Paciente.objects.all():
                if Cita.objects.filter(paciente=paciente, estado="agendada").exists():
                    continue
                dias = random.randint(3, 25)
                hora = dt.time(random.randint(8, 16), random.choice([0, 30]))
                Cita.objects.create(
                    paciente=paciente,
                    medico=medico,
                    fecha_cita=today + timedelta(days=dias),
                    hora_cita=hora,
                    motivo="Control prenatal programado",
                    estado="agendada",
                    tipo_cita="control",
                )
            self.stdout.write(f"  [+] Citas creadas: {Cita.objects.count()}")
        except Exception as e:
            self.stdout.write(f"  [!] Citas: {e}")

    def _crear_cita(self, paciente, embarazo, today, semanas):
        try:
            import datetime as dt

            from citas.models import Cita
            from usuarios.models import Usuario
            medico = Usuario.objects.filter(rol="medico").first()
            dias_prox = random.randint(3, 25)
            fecha = today + timedelta(days=dias_prox)
            hora = dt.time(random.randint(8, 16), 0)
            Cita.objects.create(
                paciente=paciente,
                medico=medico,
                fecha_cita=fecha,
                hora_cita=hora,
                motivo="Control prenatal programado",
                estado="agendada",
                tipo_cita="control",
            )
        except Exception as e:
            self.stdout.write(f"  [!] Cita: {e}")

    def _crear_triaje(self):
        try:
            from pacientes.models import Paciente
            from triaje.models import TriajeEnfermeria
            from usuarios.models import Usuario

            enfermera = Usuario.objects.filter(rol="enfermera").first()
            pacientes = Paciente.objects.all()[:5]

            for paciente in pacientes:
                embarazo = paciente.embarazos.filter(estado="activo").first()
                if not embarazo:
                    continue
                from decimal import Decimal
                TriajeEnfermeria.objects.get_or_create(
                    paciente=paciente,
                    fecha_registro=date.today(),
                    defaults={
                        "enfermera": enfermera,
                        "presion_sistolica": random.randint(100, 130),
                        "presion_diastolica": random.randint(60, 85),
                        "frecuencia_cardiaca": random.randint(70, 90),
                        "temperatura": Decimal(str(round(random.uniform(36.2, 37.1), 1))),
                        "peso_kg": Decimal(str(round(random.uniform(58, 80), 1))),
                        "motivo_visita": "Control prenatal",
                        "talla_cm": Decimal(str(round(random.uniform(150, 168), 1))),
                        "frecuencia_respiratoria": random.randint(14, 20),
                    },
                )
        except Exception as e:
            self.stdout.write(f"  [!] Triaje: {e}")

    def _crear_alertas_medicas(self):
        try:
            from embarazos.models import Embarazo

            # Marcar los embarazos de alto riesgo como verificados
            alto_riesgo = Embarazo.objects.filter(riesgo_embarazo="alto")
            self.stdout.write(f"  [!] Embarazos alto riesgo: {alto_riesgo.count()}")
        except Exception as e:
            self.stdout.write(f"  [!] Alertas: {e}")

    def _crear_analisis_cnn(self):
        """Crea imagenes ecograficas y analisis CNN 5NF (PatologiaDetectadaCNN, AlertaCNNAnalisis)."""
        try:
            from django.contrib.auth import get_user_model

            from ia_medica.models import (
                AlertaCNNAnalisis,
                AnalisisCNN,
                ImagenEcografica,
                PatologiaDetectadaCNN,
            )
            from pacientes.models import Paciente
            from usuarios.models import Usuario

            medico = Usuario.objects.filter(rol="medico").first()
            User = get_user_model()
            user = User.objects.filter(email=medico.email).first() if medico else None

            casos_cnn = [
                {
                    "tipo": "normal",
                    "patologias": [("normal", 0.92, "", "Sin hallazgos patologicos",
                                    "Continuar controles prenatales segun protocolo.", "baja", False)],
                    "bpd": 88.2, "hc": 310.5, "ac": 290.1, "fl": 68.3, "peso": 2950.0,
                    "riesgo_pre": 0.02, "riesgo_prematuro": 0.05, "alerta": None,
                },
                {
                    "tipo": "oligohidramnios",
                    "patologias": [
                        ("oligohidramnios", 0.87, "O41.0", "Liquido amniotico insuficiente (ILA < 5 cm)",
                         "Monitoreo fetal intensivo. Considerar hospitalizacion.", "alta", True),
                        ("restriccion_crecimiento", 0.61, "O36.5", "Peso fetal < percentil 10",
                         "Doppler fetal semanal. Evaluar momento del parto.", "media-alta", True),
                    ],
                    "bpd": 78.1, "hc": 275.0, "ac": 240.5, "fl": 58.2, "peso": 1890.0,
                    "riesgo_pre": 0.12, "riesgo_prematuro": 0.55,
                    "alerta": ("Oligohidramnios severo detectado - Evaluacion urgente", "ALTO", "OLIGOHIDRAMNIOS"),
                },
                {
                    "tipo": "preeclampsia",
                    "patologias": [
                        ("preeclampsia_signos", 0.79, "O14", "Signos ecograficos asociados a preeclampsia",
                         "Monitoreo PA. Lab: proteinas, plaquetas, creatinina.", "alta", True),
                    ],
                    "bpd": 85.0, "hc": 298.3, "ac": 285.0, "fl": 64.1, "peso": 2700.0,
                    "riesgo_pre": 0.79, "riesgo_prematuro": 0.30,
                    "alerta": ("Signos de preeclampsia detectados - Seguimiento urgente", "CRITICO", "PREECLAMPSIA"),
                },
            ]

            # PNG 1x1 transparente como placeholder Grad-CAM
            gradcam_b64 = (
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQ"
                "VR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            )

            pacientes = Paciente.objects.all()[:3]
            created = 0

            for paciente, caso in zip(pacientes, casos_cnn, strict=False):
                if ImagenEcografica.objects.filter(paciente=paciente).exists():
                    continue

                embarazo = paciente.embarazos.filter(estado="activo").first()
                semanas = 0
                if embarazo:
                    delta = date.today() - embarazo.fecha_ultima_menstruacion
                    semanas = delta.days // 7

                img = ImagenEcografica.objects.create(
                    paciente=paciente,
                    subida_por=user,
                    nombre_original=f"eco_{caso['tipo']}_demo.jpg",
                    tamanio_bytes=random.randint(200000, 800000),
                    formato="jpg",
                    tipo_imagen="eco_2d",
                    semana_gestacional=semanas or 28,
                    descripcion=f"Ecografia demo - {caso['tipo']}",
                    estado="analizada",
                    es_principal=True,
                )

                analisis = AnalisisCNN.objects.create(
                    imagen=img,
                    realizado_por=user,
                    modelo_usado="efficientnet",
                    version_modelo="efficientnet_b4_v1.0",
                    resultado="normal" if caso["tipo"] == "normal" else "anomalia_moderada",
                    confianza=caso["patologias"][0][1],
                    score_general=round(caso["patologias"][0][1] * 100, 1),
                    bpd_mm=caso["bpd"],
                    hc_mm=caso["hc"],
                    ac_mm=caso["ac"],
                    fl_mm=caso["fl"],
                    riesgo_preeclampsia=caso["riesgo_pre"],
                    riesgo_parto_prematuro=caso["riesgo_prematuro"],
                    nivel_riesgo="ALTO" if caso["riesgo_pre"] > 0.5 else "MODERADO" if caso["riesgo_pre"] > 0.2 else "BAJO",
                    mapa_calor=gradcam_b64,
                    shap_valores={
                        "riesgo_preeclampsia": caso["riesgo_pre"],
                        "riesgo_parto_prematuro": caso["riesgo_prematuro"],
                    },
                    patologias=[p[0] for p in caso["patologias"]],
                    alertas=[caso["alerta"][0]] if caso["alerta"] else [],
                    predicciones=[{"pathology": p[0], "confidence": p[1]} for p in caso["patologias"]],
                    validado_por_medico=False,
                    tiempo_inferencia_ms=random.randint(800, 2500),
                )

                # 5NF: 1 fila por patología detectada
                for patologia, confianza, cie10, desc, rec, sev, req_esp in caso["patologias"]:
                    PatologiaDetectadaCNN.objects.get_or_create(
                        analisis=analisis,
                        patologia=patologia,
                        defaults={
                            "confianza": confianza,
                            "codigo_cie10": cie10,
                            "descripcion": desc,
                            "recomendacion": rec,
                            "severidad": sev,
                            "requiere_especialista": req_esp,
                        },
                    )

                # 5NF: 1 fila por alerta
                if caso["alerta"]:
                    msg, sev, cod = caso["alerta"]
                    AlertaCNNAnalisis.objects.get_or_create(
                        analisis=analisis,
                        codigo=cod,
                        defaults={"mensaje": msg, "severidad": sev, "procesada": False},
                    )

                created += 1

            self.stdout.write(f"  [+] Analisis CNN (5NF): {created} imagenes, patologias y alertas normalizadas")

        except Exception as e:
            import traceback
            self.stdout.write(f"  [!] CNN: {e}")
            self.stdout.write(traceback.format_exc())

    def _crear_laboratorio_5nf(self):
        """Crea hemogramas y bioquímicas con AlertaLaboratorio 5NF."""
        try:
            from decimal import Decimal

            from django.apps import apps
            from django.contrib.contenttypes.models import ContentType
            from django.utils import timezone

            from calculadoras.models import AlertaLaboratorio
            from pacientes.models import Paciente
            from usuarios.models import Usuario

            Hemograma = apps.get_model("calculadoras", "Hemograma")
            Bioquimica = apps.get_model("calculadoras", "Bioquimica")

            medico = Usuario.objects.filter(rol="medico").first()
            pacientes = list(Paciente.objects.all())

            # Datos de hemogramas por paciente (índice → valores relevantes)
            # (hemoglobina, hematocrito, leucocitos, plaquetas, es_critico, alertas_5nf)
            hemo_data = [
                (11.2, Decimal("33.5"), 7800, 210000, False, []),
                (9.1, Decimal("27.3"), 12500, 145000, True, [
                    ("Anemia moderada (Hb 9.1 g/dL) - Requiere suplementación hierro IV", "ALTO", "ANEMIA_MODERADA"),
                    ("Leucocitosis leve (12500/mm³) - Descartar proceso infeccioso", "MEDIO", "LEUCOCITOSIS"),
                ]),
                (10.5, Decimal("31.5"), 8200, 180000, False, [
                    ("Anemia leve (Hb 10.5 g/dL) - Suplementar hierro oral", "MEDIO", "ANEMIA_LEVE"),
                ]),
                (12.1, Decimal("36.3"), 6900, 230000, False, []),
                (8.3, Decimal("24.9"), 11000, 98000, True, [
                    ("Anemia severa (Hb 8.3 g/dL) - Evaluar transfusión", "CRITICO", "ANEMIA_SEVERA"),
                    ("Trombocitopenia leve (98000/mm³) - Vigilar sangrado", "ALTO", "TROMBOCITOPENIA"),
                ]),
            ]

            ct_hemo = ContentType.objects.get_for_model(Hemograma)
            ct_bio = ContentType.objects.get_for_model(Bioquimica)
            hemo_created = 0
            alerta_created = 0

            for i, paciente in enumerate(pacientes[:5]):
                embarazo = paciente.embarazos.filter(estado="activo").first()
                if Hemograma.objects.filter(paciente=paciente).exists():
                    continue

                hb, hcto, leuco, plaq, critico, alertas = hemo_data[i]
                semanas = 0
                if embarazo:
                    from datetime import date
                    delta = date.today() - embarazo.fecha_ultima_menstruacion
                    semanas = delta.days // 7

                hemo = Hemograma.objects.create(
                    paciente=paciente,
                    embarazo=embarazo,
                    medico_solicitante=medico,
                    fecha_toma=timezone.now(),
                    semanas_gestacion=semanas or 20,
                    hemoglobina=hb,
                    hematocrito=hcto,
                    eritrocitos=Decimal(str(round(hb / 3.0, 2))),
                    vcm=Decimal("82.5"),
                    hcm=Decimal("27.3"),
                    chcm=Decimal("33.1"),
                    rdw=Decimal("13.5"),
                    leucocitos=leuco,
                    neutrofilos=int(leuco * 0.65),
                    linfocitos=int(leuco * 0.28),
                    monocitos=int(leuco * 0.05),
                    plaquetas=plaq,
                    clasificacion="CRITICO" if critico else "NORMAL",
                    es_critico=critico,
                    alertas=[a[0] for a in alertas],
                    interpretacion_automatica=(
                        "Hemograma con alteraciones críticas que requieren atención." if critico
                        else "Hemograma dentro de parámetros normales para la gestante."
                    ),
                    activo=True,
                )
                hemo_created += 1

                # 5NF: 1 fila por alerta
                for msg, sev, cod in alertas:
                    AlertaLaboratorio.objects.create(
                        content_type=ct_hemo,
                        object_id=hemo.id,
                        mensaje=msg,
                        severidad=sev,
                        codigo=cod,
                        procesada=False,
                    )
                    alerta_created += 1

            # Bioquímica para pacientes de alto riesgo
            bio_data = [
                # (glucosa, creatinina, acido_urico, got, gpt, proteinas_totales, es_critico, alertas)
                (98, Decimal("0.72"), Decimal("4.2"), 22, 18, Decimal("7.1"), False, []),
                (115, Decimal("0.85"), Decimal("5.8"), 35, 42, Decimal("6.8"), False, [
                    ("Glucosa en ayunas elevada (115 mg/dL) - Screening diabetes gestacional", "MEDIO", "GLUCOSA_ALTA"),
                ]),
                (88, Decimal("0.68"), Decimal("6.9"), 18, 22, Decimal("6.5"), True, [
                    ("Ácido úrico elevado (6.9 mg/dL) - Vigilar signos preeclampsia", "ALTO", "ACIDO_URICO_ALTO"),
                ]),
            ]

            for i, paciente in enumerate(pacientes[:3]):
                embarazo = paciente.embarazos.filter(estado="activo").first()
                if Bioquimica.objects.filter(paciente=paciente).exists():
                    continue

                gluc, creat, au, got, gpt, prot, critico, alertas = bio_data[i]
                bio = Bioquimica.objects.create(
                    paciente=paciente,
                    embarazo=embarazo,
                    medico_solicitante=medico,
                    fecha_toma=timezone.now(),
                    glucosa_ayunas=Decimal(str(gluc)),
                    creatinina=creat,
                    acido_urico=au,
                    got_ast=got,
                    gpt_alt=gpt,
                    proteinas_totales=prot,
                    clasificacion="CRITICO" if critico else "NORMAL" if gluc < 110 else "ALTERADO",
                    es_critico=critico,
                    alertas=[a[0] for a in alertas],
                    activo=True,
                )

                for msg, sev, cod in alertas:
                    AlertaLaboratorio.objects.create(
                        content_type=ct_bio,
                        object_id=bio.id,
                        mensaje=msg,
                        severidad=sev,
                        codigo=cod,
                        procesada=False,
                    )
                    alerta_created += 1

            self.stdout.write(
                f"  [+] Hemogramas: {hemo_created} | "
                f"Bioquimicas: {Bioquimica.objects.count()} | "
                f"AlertaLaboratorio 5NF: {alerta_created}"
            )

        except Exception as e:
            import traceback
            self.stdout.write(f"  [!] Laboratorio 5NF: {e}")
            self.stdout.write(traceback.format_exc())

    def _crear_mediciones_ecograficas_5nf(self):
        """Crea CalculadoraRiesgo + MedicionEcografica (5NF) para pacientes de alto riesgo."""
        try:
            from decimal import Decimal

            from calculadoras.models import CalculadoraRiesgo, MedicionEcografica
            from pacientes.models import Paciente
            from usuarios.models import Usuario

            medico = Usuario.objects.filter(rol="medico").first()
            pacientes_alto = list(Paciente.objects.filter(
                embarazos__riesgo_embarazo="alto"
            ).distinct()[:4])

            # Datos de mediciones por paciente
            mediciones_data = [
                # (semanas, bpd, hc, ac, fl, efw, nt, crl, fcf, longitud_cervical)
                (32, Decimal("82.1"), Decimal("295.0"), Decimal("278.5"), Decimal("62.3"), 1890, None, None, 142, None),
                (28, Decimal("71.5"), Decimal("260.0"), Decimal("242.0"), Decimal("54.1"), 1250, None, None, 148, Decimal("32.5")),
                (12, None, None, None, None, None, Decimal("2.8"), Decimal("58.3"), 168, Decimal("38.0")),
                (36, Decimal("90.2"), Decimal("320.5"), Decimal("305.0"), Decimal("69.8"), 2780, None, None, 136, Decimal("28.5")),
            ]

            created = 0
            for paciente, (semanas, bpd, hc, ac, fl, efw, nt, crl, fcf, long_cerv) in zip(
                pacientes_alto, mediciones_data, strict=False,
            ):
                embarazo = paciente.embarazos.filter(estado="activo").first()
                if not embarazo:
                    continue
                if CalculadoraRiesgo.objects.filter(paciente=paciente).exists():
                    continue

                from datetime import date
                edad_mat = date.today().year - paciente.fecha_nacimiento.year

                calc = CalculadoraRiesgo.objects.create(
                    paciente=paciente,
                    embarazo=embarazo,
                    tipo="preeclampsia",
                    edad_gestacional_semanas=semanas,
                    edad_gestacional_dias=0,
                    edad_materna=edad_mat,
                    peso_kg=Decimal(str(round(random.uniform(60, 82), 1))),
                    talla_cm=Decimal(str(round(random.uniform(152, 168), 1))),
                    imc=Decimal("26.5"),
                    etnia="andina",
                    tabaquismo=False,
                    hta_cronica=embarazo.riesgo_embarazo == "alto",
                    diabetes_previa=False,
                    diabetes_tipo="ninguna",
                    lupus=False,
                    sindrome_antifosfolipido=False,
                    preeclampsia_previa=random.choice([True, False]),
                    diabetes_gestacional_previa=False,
                    parto_pretermino_previo=False,
                    macrosomia_previa=False,
                    historia_familiar_diabetes=False,
                    madre_con_preeclampsia=random.choice([True, False]),
                    paridad=embarazo.numero_para or 0,
                    metodo_concepcion="espontaneo",
                    riesgo_porcentaje=Decimal(str(round(random.uniform(5.0, 35.0), 1))),
                    categoria_riesgo="ALTO" if semanas < 20 else "MODERADO",
                    calculado_por=medico,
                )

                MedicionEcografica.objects.create(
                    calculadora=calc,
                    bpd_mm=bpd,
                    hc_mm=hc,
                    ac_mm=ac,
                    fl_mm=fl,
                    efw_gramos=efw,
                    nt_mm=nt,
                    crl_mm=crl,
                    fcf_lpm=fcf,
                    longitud_cervical_mm=long_cerv,
                    nt_percentil=95 if nt and float(nt) > 2.5 else 50,
                    efw_percentil=10 if efw and efw < 1400 else 50,
                    crl_percentil=50,
                    created_by=medico,
                )
                created += 1

            from calculadoras.models import MedicionEcografica as ME
            self.stdout.write(f"  [+] CalculadorasRiesgo: {created} | MedicionEcografica 5NF: {ME.objects.count()}")

        except Exception as e:
            import traceback
            self.stdout.write(f"  [!] Mediciones ecograficas 5NF: {e}")
            self.stdout.write(traceback.format_exc())

    def _crear_notas_evolucion(self):
        """Crea notas de evolución clínica para los primeros 8 pacientes."""
        try:
            from datetime import timedelta

            from django.apps import apps
            from django.utils import timezone

            from pacientes.models import Paciente
            from usuarios.models import Usuario

            NotaEvolucion = apps.get_model("notas_evolucion", "NotaEvolucion")
            medico = Usuario.objects.filter(rol="medico").first()

            notas_data = [
                {
                    "tipo_consulta": "control_prenatal",
                    "motivo": "Control prenatal de rutina semana 28. Paciente refiere movimientos fetales adecuados.",
                    "examen": "PA 110/70 mmHg. FCF 148 lpm. AU 26 cm. Edema +/++.",
                    "diagnosticos": "Embarazo de 28 semanas. Desarrollo fetal adecuado.",
                    "plan": "Continuar controles cada 2 semanas. Solicitar hemograma y bioquímica.",
                    "dias_atras": 14,
                },
                {
                    "tipo_consulta": "seguimiento",
                    "motivo": "Seguimiento por resultado de hemograma. Hb 9.1 g/dL en control anterior.",
                    "examen": "PA 105/68 mmHg. Palidez conjuntival leve. Mucosas semihúmedas.",
                    "diagnosticos": "Anemia ferropénica gestacional moderada. Embarazo 32 semanas.",
                    "plan": "Iniciar hierro IV (Ferrex 200 mg/sem x 4 semanas). Control en 3 semanas.",
                    "dias_atras": 7,
                },
                {
                    "tipo_consulta": "urgencia",
                    "motivo": "Urgencia por cefalea intensa y visión borrosa. PA elevada al ingreso.",
                    "examen": "PA 150/98 mmHg. Edema ++/+++. Proteinas en orina ++. FCF 136 lpm.",
                    "diagnosticos": "Preeclampsia con criterios de severidad. Semana 35.",
                    "plan": "Hospitalización. Sulfato de magnesio IV. Maduración pulmonar fetal. Evaluación cesárea.",
                    "dias_atras": 3,
                },
                {
                    "tipo_consulta": "control_prenatal",
                    "motivo": "Primera consulta prenatal. FUM hace 12 semanas. Desea confirmar embarazo.",
                    "examen": "PA 100/65 mmHg. Útero de 12 semanas. Sin edema. Murmullo vesicular normal.",
                    "diagnosticos": "Embarazo de 12 semanas por FUM. Primo gesta. Bajo riesgo.",
                    "plan": "Ecografía primer trimestre. Hemograma, VDRL, toxoplasma, VIH. Ácido fólico 5mg/día.",
                    "dias_atras": 21,
                },
                {
                    "tipo_consulta": "control_prenatal",
                    "motivo": "Control semana 36. Refiere contracciones irregulares desde ayer.",
                    "examen": "PA 118/75 mmHg. Bishop 4. Presentación cefálica encajada. FCF 142 lpm.",
                    "diagnosticos": "Embarazo 36 semanas. Amenaza de parto pretérmino tardío.",
                    "plan": "Monitoreo fetal continuo. Tocolisis con nifedipino. Hospitalización 24h observación.",
                    "dias_atras": 5,
                },
                {
                    "tipo_consulta": "seguimiento",
                    "motivo": "Control post-ecografía. ILA 4.2 cm. Restricción de crecimiento fetal.",
                    "examen": "PA 122/80 mmHg. AU 30 cm (percentil <10). FCF 158 lpm. Sin edema.",
                    "diagnosticos": "Oligohidramnios leve. Restricción crecimiento intrauterino semana 32.",
                    "plan": "Doppler fetal semanal. Reposo relativo. Control en 7 días. Si ILA<3 hospitalizar.",
                    "dias_atras": 2,
                },
                {
                    "tipo_consulta": "interconsulta",
                    "motivo": "Interconsulta de cardiología por hallazgo ecográfico de cardiopatía fetal.",
                    "examen": "PA 112/72 mmHg. Ecocardiograma fetal: CIV perimembranosa 4mm. FCF 145 lpm.",
                    "diagnosticos": "Cardiopatía congénita fetal (CIV). Semana 24. Derivada a medicina fetal.",
                    "plan": "Referir a cardiología pediátrica. Parto en centro terciario con UCIN neonatal.",
                    "dias_atras": 10,
                },
                {
                    "tipo_consulta": "control_prenatal",
                    "motivo": "Control rutinario semana 20. Ecografía morfológica normal.",
                    "examen": "PA 108/68 mmHg. FCF 152 lpm. AU 18 cm. Movimientos fetales presentes.",
                    "diagnosticos": "Embarazo 20 semanas. Morfología fetal normal. Sin complicaciones.",
                    "plan": "Vacuna antiTd. Glucosa en ayunas. Próximo control semana 24.",
                    "dias_atras": 30,
                },
            ]

            created = 0
            pacientes = list(Paciente.objects.all()[:8])

            for paciente, nota_d in zip(pacientes, notas_data, strict=False):
                embarazo = paciente.embarazos.filter(estado="activo").first()
                control = None
                if embarazo:
                    control = embarazo.controles.order_by("-fecha_control").first()

                if NotaEvolucion.objects.filter(paciente=paciente, tipo_consulta=nota_d["tipo_consulta"]).exists():
                    continue

                NotaEvolucion.objects.create(
                    paciente=paciente,
                    embarazo=embarazo,
                    control_prenatal=control,
                    medico=medico,
                    fecha_consulta=timezone.now() - timedelta(days=nota_d["dias_atras"]),
                    tipo_consulta=nota_d["tipo_consulta"],
                    motivo_consulta=nota_d["motivo"],
                    examen_fisico=nota_d["examen"],
                    diagnosticos=nota_d["diagnosticos"],
                    plan_tratamiento=nota_d["plan"],
                    presentacion_fetal="cefalica",
                    movimientos_fetales="presentes",
                    activo=True,
                )
                created += 1

            self.stdout.write(f"  [+] Notas de evolucion: {created}")

        except Exception as e:
            import traceback
            self.stdout.write(f"  [!] Notas evolucion: {e}")
            self.stdout.write(traceback.format_exc())

    def _crear_evoluciones_embarazo(self):
        """Crea eventos de evolución del embarazo (EvolucionEmbarazo)."""
        try:
            from datetime import date, timedelta

            from django.apps import apps

            from pacientes.models import Paciente
            from usuarios.models import Usuario

            EvolucionEmbarazo = apps.get_model("evoluciones", "EvolucionEmbarazo")
            medico = Usuario.objects.filter(rol="medico").first()
            today = date.today()

            eventos_por_paciente = [
                [
                    ("control", "Control prenatal semana 12. Signos vitales normales. Solicita exámenes de primer trimestre.", today - timedelta(days=56)),
                    ("ecografia", "Ecografía primer trimestre. LCC 58.3 mm. NT 1.8 mm. FCF 172 lpm. Anatomía normal.", today - timedelta(days=50)),
                    ("laboratorio", "Hemograma: Hb 12.1 g/dL. Bioquímica: glucosa 98 mg/dL. VDRL no reactivo. VIH negativo.", today - timedelta(days=48)),
                    ("control", "Control semana 20. Ecografía morfológica normal. Anatomía fetal completa sin alteraciones.", today - timedelta(days=28)),
                ],
                [
                    ("control", "Primera consulta prenatal. FUM confirmada. Embarazo 8 semanas. Inicia ácido fólico.", today - timedelta(days=84)),
                    ("laboratorio", "Hemograma: Hb 9.1 g/dL. Anemia ferropénica. Inicia sulfato ferroso 300mg/día.", today - timedelta(days=70)),
                    ("urgencia", "Urgencia por sangrado vaginal escaso. Ecografía: embrión vivo. Reposo absoluto 48h.", today - timedelta(days=45)),
                    ("control", "Control semana 24. Resolución sangrado. Hb 10.5 g/dL. Feto activo.", today - timedelta(days=14)),
                ],
                [
                    ("control", "Control semana 28 en paciente con HTA crónica. PA 140/90 ajustando metildopa.", today - timedelta(days=35)),
                    ("laboratorio", "Proteinuria 24h: 380 mg. Plaquetas 145000. Creatinina 0.85. Vigilancia estrecha.", today - timedelta(days=21)),
                    ("control", "Control semana 32. PA 150/95. Aumento edema. Signos de preeclampsia sobreañadida.", today - timedelta(days=7)),
                    ("otro", "Hospitalización preventiva por preeclampsia. Corticoides completados. Expectante.", today - timedelta(days=3)),
                ],
                [
                    ("control", "Control semana 16. Primer movimiento fetal referido. Sin molestias.", today - timedelta(days=42)),
                    ("ecografia", "Ecografía semana 18. Sexo femenino. Biometría normal. Placenta anterior.", today - timedelta(days=35)),
                    ("control", "Control semana 22. Peso 68 kg. AU 20 cm. FCF 148 lpm. Todo normal.", today - timedelta(days=14)),
                ],
            ]

            created = 0
            pacientes = list(Paciente.objects.all()[:4])

            for paciente, eventos in zip(pacientes, eventos_por_paciente, strict=False):
                embarazo = paciente.embarazos.filter(estado="activo").first()
                if not embarazo:
                    continue

                for tipo, descripcion, fecha in eventos:
                    if EvolucionEmbarazo.objects.filter(
                        embarazo=embarazo, tipo_evento=tipo, fecha_evento=fecha
                    ).exists():
                        continue
                    EvolucionEmbarazo.objects.create(
                        embarazo=embarazo,
                        paciente=paciente,
                        fecha_evento=fecha,
                        tipo_evento=tipo,
                        descripcion=descripcion,
                    )
                    created += 1

            self.stdout.write(f"  [+] EvolucionEmbarazo: {created}")

        except Exception as e:
            import traceback
            self.stdout.write(f"  [!] Evoluciones embarazo: {e}")
            self.stdout.write(traceback.format_exc())

    def _crear_antecedentes_obstetricos(self):
        """AntecedenteGinecoObstetrico para los 15 pacientes (1:1)."""
        try:
            from django.apps import apps

            from pacientes.models import Paciente

            AntGO = apps.get_model("antecedentes", "AntecedenteGinecoObstetrico")

            # ci → (menarquia, ciclos, dur_ciclo, dur_mens, gestas, partos, abortos, cesareas, hijos_vivos, ivsa, parejas, metodo_anticonceptivo)
            datos = {
                "1234567": (13, "regular", 28, 5, 2, 1, 0, 0, 1, 18, 2, "inyectable"),
                "2345678": (12, "regular", 30, 4, 1, 0, 0, 0, 0, 20, 1, "ninguno"),
                "3456789": (13, "irregular", 32, 6, 4, 2, 1, 1, 2, 17, 3, "aco"),
                "4567890": (14, "regular", 28, 5, 1, 0, 0, 0, 0, 19, 1, "ninguno"),
                "5678901": (12, "regular", 28, 5, 3, 1, 1, 0, 1, 17, 2, "diu"),
                "6789012": (13, "regular", 29, 4, 1, 0, 0, 0, 0, 21, 1, "condones"),
                "7890123": (11, "irregular", 35, 7, 4, 2, 1, 1, 2, 16, 4, "ninguno"),
                "8901234": (14, "regular", 28, 5, 1, 0, 0, 0, 0, 22, 1, "ninguno"),
                "9012345": (12, "irregular", 30, 6, 5, 3, 1, 1, 3, 17, 2, "ninguno"),
                "0123456": (13, "regular", 28, 5, 2, 1, 0, 0, 1, 20, 2, "inyectable"),
                "1122334": (14, "regular", 28, 4, 1, 0, 0, 0, 0, 19, 1, "ninguno"),
                "2233445": (12, "regular", 30, 5, 3, 1, 0, 1, 1, 18, 2, "diu"),
                "3344556": (13, "regular", 28, 5, 3, 1, 1, 1, 1, 18, 3, "ninguno"),
                "4455667": (11, "irregular", 35, 7, 6, 3, 2, 1, 3, 16, 2, "ninguno"),
                "5566778": (14, "regular", 28, 4, 1, 0, 0, 0, 0, 21, 1, "ninguno"),
            }

            created = 0
            for paciente in Paciente.objects.all():
                if AntGO.objects.filter(paciente=paciente).exists():
                    continue
                ci = str(paciente.ci) if hasattr(paciente, "ci") else ""
                # Descifrar CI (EncryptedCharField devuelve el valor en texto)
                try:
                    ci_str = str(ci)
                except Exception:
                    ci_str = ""
                d = datos.get(ci_str)
                if not d:
                    d = (13, "regular", 28, 5, 1, 0, 0, 0, 0, 20, 1, "ninguno")
                mena, ciclos, dur_ciclo, dur_mens, gestas, partos, abortos, cesareas, hijos, ivsa, parejas, met = d
                AntGO.objects.create(
                    paciente=paciente,
                    menarquia_edad=mena,
                    ciclos_menstruales=ciclos,
                    duracion_ciclo_dias=dur_ciclo,
                    duracion_menstruacion_dias=dur_mens,
                    gestas=gestas,
                    partos=partos,
                    abortos=abortos,
                    cesareas=cesareas,
                    hijos_vivos=hijos,
                    inicio_vida_sexual_edad=ivsa,
                    numero_parejas_sexuales=parejas,
                    metodo_anticonceptivo_actual=met if met != "ninguno" else None,
                )
                created += 1

            self.stdout.write(f"  [+] AntecedenteGinecoObstetrico: {created}")

        except Exception as e:
            import traceback
            self.stdout.write(f"  [!] Antecedentes obstetricos: {e}")
            self.stdout.write(traceback.format_exc())

    def _crear_embarazos_anteriores(self):
        """Embarazos finalizados del año pasado con parto y recién nacido.

        Pacientes con para > 0 tienen un historial real: embarazo 2024
        → Parto → RecienNacido (vivo, sano).  Patricia y Teresa, que tienen
        historial más largo, tienen también un aborto documentado.
        """
        try:
            from datetime import timedelta
            from decimal import Decimal

            from django.apps import apps
            from django.utils import timezone

            from embarazos.models import Embarazo
            from pacientes.models import Paciente
            from usuarios.models import Usuario

            Parto = apps.get_model("partos", "Parto")
            RecienNacido = apps.get_model("partos", "RecienNacido")

            medico = Usuario.objects.filter(rol="medico").first()

            # ci → lista de partos anteriores: (año_parto, semanas_parto, tipo_parto, peso_rn_g, talla_rn_cm, sexo_rn, apgar1, apgar5, destino, es_cesarea, riesgo_emb)
            historiales = {
                # Carmen Mamani (alto riesgo, 35 años): 2 partos anteriores
                "3456789": [
                    (2024, 39, "vaginal_espontaneo", 3320, Decimal("49.5"), "femenino", 8, 9, "alojamiento_conjunto", False, "bajo"),
                    (2022, 38, "vaginal_espontaneo", 3150, Decimal("48.0"), "masculino", 9, 9, "alojamiento_conjunto", False, "bajo"),
                ],
                # Gabriela Torrez (alto riesgo, 34 años): 1 cesárea anterior
                "7890123": [
                    (2023, 37, "cesarea_electiva", 2980, Decimal("48.0"), "femenino", 7, 9, "alojamiento_conjunto", True, "medio"),
                ],
                # Patricia Mendoza (37 años): 3 partos + registrar el aborto como embarazo perdida
                "9012345": [
                    (2024, 40, "vaginal_espontaneo", 3600, Decimal("51.0"), "masculino", 9, 10, "alojamiento_conjunto", False, "bajo"),
                    (2022, 38, "vaginal_instrumentado", 3280, Decimal("49.0"), "femenino", 7, 9, "alojamiento_conjunto", False, "bajo"),
                    (2020, 39, "vaginal_espontaneo", 3410, Decimal("50.0"), "masculino", 8, 9, "alojamiento_conjunto", False, "bajo"),
                ],
                # Teresa García (alto riesgo, 38 años): 3 partos
                "4455667": [
                    (2024, 38, "cesarea_urgencia", 3100, Decimal("49.0"), "femenino", 6, 8, "neonatologia", True, "alto"),
                    (2022, 37, "vaginal_espontaneo", 2900, Decimal("47.5"), "masculino", 8, 9, "alojamiento_conjunto", False, "medio"),
                    (2019, 40, "vaginal_espontaneo", 3550, Decimal("51.0"), "femenino", 9, 10, "alojamiento_conjunto", False, "bajo"),
                ],
                # Rosa Apaza (33 años): 1 parto
                "5678901": [
                    (2023, 39, "vaginal_espontaneo", 3200, Decimal("49.0"), "masculino", 8, 9, "alojamiento_conjunto", False, "bajo"),
                ],
                # Isabel Ramos (34 años): 1 cesárea
                "2233445": [
                    (2023, 38, "cesarea_electiva", 3050, Decimal("48.5"), "femenino", 8, 9, "alojamiento_conjunto", True, "medio"),
                ],
                # María Quispe (31 años): 1 parto
                "1234567": [
                    (2024, 39, "vaginal_espontaneo", 3400, Decimal("50.0"), "femenino", 9, 10, "alojamiento_conjunto", False, "bajo"),
                ],
                # Elena Huanca (30 años): 1 parto
                "0123456": [
                    (2024, 40, "vaginal_espontaneo", 3350, Decimal("50.5"), "masculino", 9, 9, "alojamiento_conjunto", False, "bajo"),
                ],
            }

            partos_creados = 0
            rn_creados = 0

            for paciente in Paciente.objects.all():
                try:
                    ci_val = str(paciente.ci)
                except Exception:
                    continue
                historial = historiales.get(ci_val, [])
                if not historial:
                    continue

                for idx, (anio, semanas, tipo_p, peso_rn, talla_rn, sexo, ap1, ap5, destino, es_ces, riesgo) in enumerate(historial):
                    # Calcular FUM del embarazo anterior
                    fecha_parto_dt = timezone.make_aware(
                        datetime(anio, random.randint(3, 10), random.randint(5, 25))
                    )
                    fum_ant = fecha_parto_dt.date() - timedelta(weeks=semanas)
                    fpp_ant = fum_ant + timedelta(weeks=40)

                    # Saltar si ya existe ese embarazo finalizado de ese año
                    if Embarazo.objects.filter(
                        paciente=paciente,
                        estado="finalizado",
                        fecha_ultima_menstruacion=fum_ant,
                    ).exists():
                        continue

                    emb_ant = Embarazo.objects.create(
                        paciente=paciente,
                        numero_gesta=len(historial) - idx,
                        numero_para=len(historial) - idx - 1,
                        numero_abortos=0,
                        numero_cesareas=sum(1 for h in historial[: len(historial) - idx - 1] if h[9]),
                        fecha_ultima_menstruacion=fum_ant,
                        fecha_probable_parto=fpp_ant,
                        tipo_embarazo="simple",
                        riesgo_embarazo=riesgo,
                        estado="finalizado",
                        peso_pregestacional=round(random.uniform(54, 72), 1),
                        talla_materna=round(random.uniform(152, 168), 1),
                        medico_responsable=medico,
                    )

                    # Crear parto — número único: ID_paciente-posición/año
                    numero_parto = f"{getattr(paciente, 'id', '?')}-{str(idx+1).zfill(2)}/{anio}"
                    if Parto.objects.filter(numero_parto=numero_parto).exists():
                        partos_creados += 1
                        continue
                    parto = Parto.objects.create(
                        paciente=paciente,
                        embarazo=emb_ant,
                        medico_responsable=medico,
                        numero_parto=numero_parto,
                        fecha_ingreso=fecha_parto_dt - timedelta(hours=random.randint(4, 14)),
                        fecha_inicio_trabajo_parto=fecha_parto_dt - timedelta(hours=random.randint(2, 8)),
                        fecha_parto=fecha_parto_dt,
                        edad_gestacional_parto=f"{semanas}+{random.randint(0,6)}",
                        tipo_parto=tipo_p,
                        presentacion_fetal="cefalica",
                        posicion_fetal="oia",
                        estado_membranas="rotas_espontaneas",
                        hora_rotura_membranas=fecha_parto_dt - timedelta(hours=random.randint(1, 5)),
                        caracteristicas_liquido="claro",
                        duracion_trabajo_parto_horas=Decimal(str(round(random.uniform(4.0, 14.0), 1))),
                        duracion_periodo_expulsivo_minutos=random.randint(15, 60) if not es_ces else None,
                        analgesia_utilizada=es_ces or random.choice([True, False]),
                        tipo_analgesia="epidural" if es_ces else "ninguna",
                        episiotomia=not es_ces and random.choice([True, False]),
                        tipo_episiotomia="mediolateral" if not es_ces and random.choice([True, False]) else "",
                        desgarros=False,
                        grado_desgarros="",
                        tipo_alumbramiento="dirigido",
                        placenta_completa=True,
                        peso_placenta=random.randint(480, 650),
                        perdida_sanguinea_estimada=random.randint(200, 400) if not es_ces else random.randint(400, 800),
                        hemorragia_postparto=False,
                        complicaciones_maternas="Ninguna" if riesgo == "bajo" else "Hipertensión controlada durante el trabajo de parto.",
                        oxitocina_utilizada=True,
                        dosis_oxitocina="10 UI en 500 mL SF a 20 gotas/min",
                        otros_medicamentos="",
                        observaciones_parto="Parto atendido sin complicaciones mayores." if riesgo in ("bajo", "medio") else "Parto de alto riesgo. Vigilancia estrecha.",
                        indicaciones_cesarea="Presentación podálica, cesárea anterior" if es_ces else "",
                        parto_finalizado=True,
                        trabajo_parto_espontaneo=not es_ces,
                        induccion_parto=False,
                        metodo_induccion="",
                        monitoreo_fetal_continuo=True,
                        apoyo_psicologico_realizado=False,
                        protocolo_duelo_aplicado=False,
                        observaciones_aborto="",
                    )
                    partos_creados += 1

                    # Crear recién nacido
                    RecienNacido.objects.create(
                        parto=parto,
                        numero_gemelo=1,
                        fecha_nacimiento=fecha_parto_dt,
                        sexo=sexo,
                        estado_nacimiento="vivo",
                        peso_nacimiento=peso_rn,
                        talla_nacimiento=talla_rn,
                        perimetro_cefalico=Decimal(str(round(random.uniform(33.0, 36.0), 1))),
                        apgar_1_minuto=ap1,
                        apgar_5_minutos=ap5,
                        apgar_10_minutos=min(ap5 + 1, 10),
                        requirio_reanimacion=ap1 < 7,
                        tipo_reanimacion="VPP breve" if ap1 < 7 else "",
                        malformaciones_congenitas=False,
                        descripcion_malformaciones="",
                        destino_rn=destino,
                        llanto_inmediato=ap1 >= 7,
                        respiracion_espontanea=True,
                        tono_muscular_normal=ap1 >= 7,
                        observaciones_rn="Recién nacido en buenas condiciones generales." if ap1 >= 7 else "RN requirió maniobras de reanimación básica.",
                    )
                    rn_creados += 1

            self.stdout.write(f"  [+] Partos anteriores: {partos_creados} | RecienNacidos: {rn_creados}")

        except Exception as e:
            import traceback
            self.stdout.write(f"  [!] Embarazos anteriores: {e}")
            self.stdout.write(traceback.format_exc())

    def _crear_notificaciones(self):
        """Crea notificaciones realistas para el médico: alertas lab, citas, tratamientos."""
        try:
            from datetime import timedelta

            from django.apps import apps
            from django.utils import timezone

            from pacientes.models import Paciente
            from usuarios.models import Usuario

            Notificacion = apps.get_model("notificaciones", "Notificacion")
            medico = Usuario.objects.filter(rol="medico").first()
            if not medico:
                return

            if Notificacion.objects.filter(usuario=medico).count() > 5:
                self.stdout.write("  [=] Notificaciones ya existen")
                return

            pacientes = list(Paciente.objects.all())
            notifs_data = [
                # Alertas críticas de laboratorio
                {
                    "tipo": "examen_critico",
                    "prioridad": "critica",
                    "titulo": "Hemograma Crítico — Carmen Mamani",
                    "mensaje": "Hb 8.3 g/dL y plaquetas 98,000/mm³. Requiere evaluación inmediata para descartar síndrome HELLP.",
                    "icono": "alert",
                    "color": "red",
                    "leida": False,
                    "dias_atras": 1,
                },
                {
                    "tipo": "examen_critico",
                    "prioridad": "urgente",
                    "titulo": "Resultado Bioquímica — Gabriela Torrez",
                    "mensaje": "Ácido úrico 6.9 mg/dL. Proteinuria 380 mg/24h. Signos de preeclampsia sobreañadida.",
                    "icono": "warning",
                    "color": "orange",
                    "leida": False,
                    "dias_atras": 0,
                },
                # Alertas CNN/IA
                {
                    "tipo": "alerta_critica",
                    "prioridad": "critica",
                    "titulo": "IA: Signos de preeclampsia detectados",
                    "mensaje": "Análisis CNN detectó signos ecográficos compatibles con preeclampsia (confianza 79%). Paciente: Carmen Mamani. Validación médica requerida.",
                    "icono": "robot",
                    "color": "red",
                    "leida": False,
                    "dias_atras": 0,
                },
                {
                    "tipo": "alerta_advertencia",
                    "prioridad": "alta",
                    "titulo": "IA: Oligohidramnios severo detectado",
                    "mensaje": "ILA estimado < 5 cm por CNN (confianza 87%). Paciente: Ana Flores. Monitoreo fetal intensivo recomendado.",
                    "icono": "robot",
                    "color": "orange",
                    "leida": False,
                    "dias_atras": 1,
                },
                # Recordatorios de tratamiento
                {
                    "tipo": "recordatorio_medicacion",
                    "prioridad": "alta",
                    "titulo": "Tratamiento Hierro IV — Ana Flores",
                    "mensaje": "Pendiente 2da dosis Ferrex 200 mg IV. Programada para hoy a las 10:00. Hb basal: 9.1 g/dL.",
                    "icono": "medicine",
                    "color": "blue",
                    "leida": False,
                    "dias_atras": 0,
                },
                {
                    "tipo": "recordatorio_medicacion",
                    "prioridad": "normal",
                    "titulo": "Sulfato de Magnesio — Teresa García",
                    "mensaje": "Paciente con preeclampsia severa. Verificar niveles de magnesio sérico (objetivo 4-6 mEq/L) antes de siguiente dosis.",
                    "icono": "medicine",
                    "color": "blue",
                    "leida": True,
                    "dias_atras": 2,
                },
                # Recordatorios de control
                {
                    "tipo": "recordatorio_control",
                    "prioridad": "alta",
                    "titulo": "Doppler Fetal Semanal — Rosa Apaza",
                    "mensaje": "Paciente con restricción crecimiento fetal. Doppler umbilical programado para esta semana. ILA basal: 4.2 cm.",
                    "icono": "calendar",
                    "color": "purple",
                    "leida": False,
                    "dias_atras": 0,
                },
                {
                    "tipo": "recordatorio_control",
                    "prioridad": "normal",
                    "titulo": "Control PA — Patricia Mendoza",
                    "mensaje": "Semana 40+3. Pendiente evaluación Bishop y decisión de conducta obstétrica. PA última medición: 128/82.",
                    "icono": "calendar",
                    "color": "green",
                    "leida": True,
                    "dias_atras": 3,
                },
                # Citas próximas
                {
                    "tipo": "cita_proxima",
                    "prioridad": "normal",
                    "titulo": "Cita mañana — Valentina Vargas (24 sem)",
                    "mensaje": "Control prenatal semana 24. Recordar solicitar PTOG 75g y ecografía morfológica si no fue realizada.",
                    "icono": "calendar",
                    "color": "blue",
                    "leida": False,
                    "dias_atras": 0,
                },
                {
                    "tipo": "cita_proxima",
                    "prioridad": "normal",
                    "titulo": "Cita mañana — Sofía Condori (10 sem)",
                    "mensaje": "Primera consulta prenatal. Paciente primigesta 24 años. Solicitará ecografía primer trimestre y panel TORCH.",
                    "icono": "calendar",
                    "color": "blue",
                    "leida": False,
                    "dias_atras": 0,
                },
                # Documentos y resultados listos
                {
                    "tipo": "examen_listo",
                    "prioridad": "normal",
                    "titulo": "Resultado Listo — Hemograma Lucía Choque",
                    "mensaje": "Hb 12.1 g/dL, leucocitos 7200, plaquetas 225,000. Dentro de rangos normales gestacionales.",
                    "icono": "file",
                    "color": "green",
                    "leida": True,
                    "dias_atras": 5,
                },
                {
                    "tipo": "examen_listo",
                    "prioridad": "normal",
                    "titulo": "Resultado Listo — PTOG 75g Elena Huanca",
                    "mensaje": "Glucosa basal 88 mg/dL. 1h: 142 mg/dL. 2h: 118 mg/dL. PTOG normal. No diabetes gestacional.",
                    "icono": "file",
                    "color": "green",
                    "leida": True,
                    "dias_atras": 4,
                },
                # Alerta alta para paciente con riesgo cromosómico
                {
                    "tipo": "alerta_advertencia",
                    "prioridad": "alta",
                    "titulo": "Marcador Bioquímico Alterado — Teresa García",
                    "mensaje": "PAPP-A 0.32 MoM (P5). Riesgo T21 combinado 1:85. Ofrecer amniocentesis según protocolo FMF.",
                    "icono": "warning",
                    "color": "orange",
                    "leida": False,
                    "dias_atras": 2,
                },
            ]

            created = 0
            for d in notifs_data:
                Notificacion.objects.create(
                    usuario=medico,
                    tipo=d["tipo"],
                    prioridad=d["prioridad"],
                    titulo=d["titulo"],
                    mensaje=d["mensaje"],
                    icono=d.get("icono", ""),
                    color=d.get("color", ""),
                    leida=d.get("leida", False),
                    fecha_leida=timezone.now() - timedelta(hours=1) if d.get("leida") else None,
                    archivada=False,
                    metadata={},
                    enviada_push=False,
                    enviada_email=False,
                    enviada_sms=False,
                )
                created += 1

            self.stdout.write(f"  [+] Notificaciones: {created}")

        except Exception as e:
            import traceback
            self.stdout.write(f"  [!] Notificaciones: {e}")
            self.stdout.write(traceback.format_exc())

    def _crear_ecografias(self):
        """Crea ecografías (incluyendo Biometria, Anatomia y Anexos) para pacientes con embarazos activos."""
        try:
            from decimal import Decimal

            from ecografias.models import (
                AnatomiaFetal,
                AnexosFetales,
                BiometriaFetal,
                Ecografia,
            )
            from pacientes.models import Paciente
            from usuarios.models import Usuario

            medico = Usuario.objects.filter(rol="medico").first()
            if not medico:
                return

            pacientes = Paciente.objects.filter(activo=True)
            created_ecos = 0

            for paciente in pacientes:
                embarazo = paciente.embarazos.filter(estado="activo").first()
                if not embarazo:
                    continue

                # Calcular semanas de gestación actual
                today = date.today()
                fum = embarazo.fecha_ultima_menstruacion
                semanas_actuales = (today - fum).days // 7

                if semanas_actuales < 6:
                    continue

                # Determinar ecografías a crear basadas en semanas actuales
                ecos_a_crear = []
                if semanas_actuales >= 12:
                    ecos_a_crear.append((12, "primer_trimestre", "control_rutina", "Ecografía del primer trimestre normal."))
                if semanas_actuales >= 20:
                    ecos_a_crear.append((20, "morfologica", "control_rutina", "Estudio morfológico detallado sin anomalías detectadas."))
                if semanas_actuales >= 28:
                    ecos_a_crear.append((28, "tercer_trimestre", "control_crecimiento", "Crecimiento fetal adecuado para la edad gestacional."))

                # Si no tiene ninguna histórica por semanas pero tiene al menos 6 semanas, creamos la actual
                if not ecos_a_crear:
                    ecos_a_crear.append((semanas_actuales, "primer_trimestre", "control_rutina", "Ecografía obstétrica de rutina."))

                for sem, tipo, ind, diag in ecos_a_crear:
                    fecha_eco = fum + timedelta(weeks=sem)
                    # Evitar duplicar
                    if Ecografia.objects.filter(embarazo=embarazo, edad_gestacional_semanas=sem).exists():
                        continue

                    # ILA e insertos de placenta realistas
                    ila = Decimal(str(round(random.uniform(10.0, 16.0), 1)))
                    fcf = random.randint(135, 155)

                    eco = Ecografia.objects.create(
                        embarazo=embarazo,
                        paciente=paciente,
                        medico=medico,
                        fecha_ecografia=fecha_eco,
                        tipo_ecografia=tipo,
                        indicacion=ind,
                        edad_gestacional_semanas=sem,
                        edad_gestacional_dias=0,
                        vitalidad_fetal=True,
                        frecuencia_cardiaca_fetal=fcf,
                        indice_liquido_amniotico=ila,
                        localizacion_placenta=random.choice(["anterior", "posterior", "fúndica"]),
                        grado_madurez_placenta=0 if sem < 20 else 1 if sem < 30 else 2,
                        diagnostico=diag,
                        observaciones="Paciente en buenas condiciones. Monitoreo habitual.",
                        created_by=medico,
                    )

                    # Crear biometría fetal realista según semanas
                    bpd = Decimal(str(round(sem * 2.8 + random.uniform(-2, 2), 1)))
                    hc = Decimal(str(round(sem * 9.8 + random.uniform(-10, 10), 1)))
                    ac = Decimal(str(round(sem * 9.5 + random.uniform(-10, 10), 1)))
                    fl = Decimal(str(round(sem * 2.1 + random.uniform(-2, 2), 1)))

                    # Calcular Hadlock manualmente para guardar un peso realista
                    ac_val = float(ac)
                    fl_val = float(fl)
                    hc_val = float(hc)
                    bpd_val = float(bpd)
                    log_peso = 1.3596 - 0.00386 * ac_val * fl_val + 0.0064 * hc_val + 0.00061 * bpd_val * ac_val + 0.0425 * ac_val + 0.174 * fl_val
                    peso_est = int(10**log_peso) if (ac_val and fl_val and hc_val and bpd_val) else None

                    BiometriaFetal.objects.create(
                        ecografia=eco,
                        diametro_biparietal=bpd,
                        circunferencia_cefalica=hc,
                        circunferencia_abdominal=ac,
                        longitud_femur=fl,
                        peso_fetal_estimado=peso_est,
                        percentil_peso=random.randint(25, 75),
                        created_by=medico,
                    )

                    # Crear Anatomía Fetal
                    AnatomiaFetal.objects.create(
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
                        genitales_visibles=sem >= 16,
                        sexo_fetal="femenino" if random.choice([True, False]) else "masculino",
                        created_by=medico,
                    )

                    # Crear Anexos Fetales
                    AnexosFetales.objects.create(
                        ecografia=eco,
                        placenta_localizacion=eco.localizacion_placenta,
                        placenta_grosor=Decimal(str(round(sem * 0.8 + 10, 1))),
                        placenta_insercion_cordon="central",
                        numero_vasos_cordon=3,
                        circular_cordon=False,
                        liquido_amniotico_normal=True,
                        longitud_cervical=Decimal(str(round(random.uniform(32, 45), 1))),
                        created_by=medico,
                    )

                    created_ecos += 1

            self.stdout.write(f"  [+] Ecografías creadas (con biometría, anatomía y anexos): {created_ecos}")

        except Exception as e:
            import traceback
            self.stdout.write(f"  [!] Ecografías: {e}")
            self.stdout.write(traceback.format_exc())
