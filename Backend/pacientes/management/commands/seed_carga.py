# -*- coding: utf-8 -*-
"""Seed de CARGA — genera un volumen grande de pacientes con historia clínica
completa, para pruebas de rendimiento, CRUD masivo, concurrencia y auditoría.

NO reemplaza a `seed_demo` (que crea 15 pacientes para la demo funcional):
este comando es independiente y está pensado para volumen.

Uso:
    python manage.py seed_carga                      # 250 completos + 250 editables
    python manage.py seed_carga --completos 100 --editables 50
    python manage.py seed_carga --tenant clinica_demo
    python manage.py seed_carga --limpiar            # borra lo generado antes (por marca)

Qué genera por paciente COMPLETO:
    - Datos personales realistas (nombres y ciudades bolivianas, edad 15-45)
    - Antecedentes gineco-obstétricos
    - 1 embarazo (activo o finalizado)
    - 2-8 controles prenatales con signos vitales variados (normales y de riesgo)
    - 1-3 ecografías con biometría
    - 1-4 exámenes de laboratorio (panel prenatal; el catálogo se siembra solo)
    - 0-2 registros de vacunación
    - Desenlace: parto (con recién nacido) o pérdida, según corresponda

Los pacientes EDITABLES se crean más livianos (datos + embarazo) porque su
propósito es ser modificados por las pruebas de CRUD, no ser leídos.

Todos los registros llevan la marca `MARCA_CARGA` en `observaciones`/`notas`
para poder identificarlos y limpiarlos sin tocar datos reales.
"""
from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django_tenants.utils import schema_context

MARCA_CARGA = "[SEED-CARGA]"
SCHEMA_POR_DEFECTO = "clinica_demo"

# ── Datos bolivianos reales ────────────────────────────────────────────────
NOMBRES = [
    "María", "Ana", "Rosa", "Carmen", "Lucía", "Elena", "Sofía", "Isabel", "Teresa",
    "Patricia", "Gabriela", "Sandra", "Claudia", "Miriam", "Valentina", "Daniela",
    "Fernanda", "Andrea", "Verónica", "Silvia", "Nayra", "Wara", "Yola", "Justina",
    "Feliza", "Bernarda", "Eugenia", "Rufina", "Modesta", "Zenobia", "Alicia", "Nelly",
]
APELLIDOS = [
    "Quispe", "Mamani", "Condori", "Flores", "Choque", "Apaza", "Huanca", "Limachi",
    "Ticona", "Poma", "Yujra", "Marca", "Cusi", "Callisaya", "Chura", "Colque",
    "Vargas", "Torrez", "Mendoza", "Ramos", "López", "García", "Rojas", "Céspedes",
    "Justiniano", "Suárez", "Peña", "Áñez", "Roca", "Montaño", "Ávila", "Salvatierra",
]
# Ciudad → localidades/zonas cercanas reales
CIUDADES = {
    "La Paz": ["Sopocachi", "Miraflores", "Villa Fátima", "San Pedro", "Achumani", "Mallasa"],
    "El Alto": ["Ciudad Satélite", "Villa Adela", "Río Seco", "Senkata", "16 de Julio"],
    "Santa Cruz de la Sierra": ["Plan Tres Mil", "Equipetrol", "Villa 1ro de Mayo", "Pampa de la Isla", "Warnes"],
    "Cochabamba": ["Cercado", "Quillacollo", "Sacaba", "Tiquipaya", "Vinto", "Colcapirhua"],
    "Viacha": ["Centro", "Villa Remedios"],
    "Montero": ["Centro", "Barrio Norte"],
    "Sucre": ["Centro Histórico", "Alto Delicias"],
    "Oruro": ["Centro", "Sud Oeste"],
}
OCUPACIONES = [
    "Comerciante", "Ama de casa", "Agricultora", "Docente", "Enfermera", "Estudiante",
    "Costurera", "Empleada doméstica", "Vendedora ambulante", "Secretaria", "Cocinera",
]
ESTADOS_CIVILES = ["soltero", "casado", "union_libre", "divorciado", "viudo"]
# Las choices REALES del modelo llevan el signo pegado ("O+", "A-"...) y
# factor_rh es "positivo"/"negativo" — no "+"/"-". El generador inventaba
# valores que el modelo rechaza; se corrige el GENERADOR, no el modelo.
TIPOS_SANGRE = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]


def _tipo_ecografia(semanas: int) -> str:
    """Tipo de ecografia segun el trimestre (choices reales del modelo)."""
    if semanas < 14:
        return "primer_trimestre"
    if semanas < 28:
        # la morfologica se hace en el 2do trimestre (semanas 20-24)
        return "morfologica" if 20 <= semanas <= 24 and random.random() < 0.5 else "segundo_trimestre"
    return random.choices(["tercer_trimestre", "doppler"], [70, 30])[0]


def _rango(a, b, dec=1):
    """Decimal con EXACTAMENTE `dec` decimales.

    Ojo: un float de Python arrastra dígitos al convertirse a Decimal
    (Decimal(67.35) == 67.35000000000000142…) y el DecimalValidator de Django
    lo rechaza. Por eso se construye desde el string ya redondeado.
    """
    return Decimal(f"{random.uniform(a, b):.{dec}f}")


class Command(BaseCommand):
    help = "Genera pacientes con historia clínica completa para pruebas de carga."

    def add_arguments(self, parser):
        parser.add_argument("--completos", type=int, default=250,
                            help="Pacientes con historia clínica completa (default 250)")
        parser.add_argument("--editables", type=int, default=250,
                            help="Pacientes livianos destinados a pruebas de edición (default 250)")
        parser.add_argument("--tenant", type=str, default=SCHEMA_POR_DEFECTO)
        parser.add_argument("--limpiar", action="store_true",
                            help="Elimina los registros marcados con [SEED-CARGA] y termina")
        parser.add_argument("--semilla", type=int, default=2026,
                            help="Semilla aleatoria (reproducibilidad)")

    # ── Entrada ────────────────────────────────────────────────────────────
    def handle(self, *args, **opts):
        random.seed(opts["semilla"])
        self._contadores_ci = {"99": 0, "98": 0}
        with schema_context(opts["tenant"]):
            if opts["limpiar"]:
                self._limpiar()
                return
            self._preparar_catalogos()
            n_c = self._crear_lote(opts["completos"], completo=True, etiqueta="COMPLETO")
            n_e = self._crear_lote(opts["editables"], completo=False, etiqueta="EDITABLE")
            self.stdout.write(self.style.SUCCESS(
                f"\n[OK] seed_carga: {n_c} completos + {n_e} editables = {n_c + n_e} pacientes",
            ))
            self._validar_lote()

    # ── Verificación: los datos deben cumplir las reglas del sistema ───────
    def _validar_lote(self):
        """Corre full_clean() sobre TODO lo sembrado y reporta lo que no valida.

        Por qué existe: `objects.create()` NO ejecuta las validaciones del
        modelo. Sin esta comprobación el seed puede meter en la base datos
        que la API o un formulario rechazarían —pasó de verdad: el generador
        inventaba tipo_sangre="O" (el modelo exige "O+"/"O-"), factor_rh="+"
        (exige "positivo"/"negativo") y tipo_ecografia="obstetrica" (no es
        una opción)— y nadie se enteraba porque la fila entraba igual.

        La regla es: el sistema manda y el generador se adapta. Si esto
        reporta errores se corrige el GENERADOR, nunca la validación.
        """
        from collections import Counter

        from controles.models import ControlPrenatal
        from ecografias.models import Ecografia
        from embarazos.models import Embarazo
        from laboratorio.models import ExamenLaboratorio
        from pacientes.models import Paciente
        from partos.models import Parto
        from vacunas.models import RegistroVacuna

        pacientes = Paciente.objects.filter(observaciones__contains=MARCA_CARGA)
        grupos = [
            ("Paciente", pacientes),
            ("Embarazo", Embarazo.objects.filter(paciente__in=pacientes)),
            ("ControlPrenatal", ControlPrenatal.objects.filter(paciente__in=pacientes)),
            ("Ecografia", Ecografia.objects.filter(paciente__in=pacientes)),
            ("ExamenLaboratorio", ExamenLaboratorio.objects.filter(paciente__in=pacientes)),
            ("RegistroVacuna", RegistroVacuna.objects.filter(paciente__in=pacientes)),
            ("Parto", Parto.objects.filter(paciente__in=pacientes)),
        ]
        total_invalidos = 0
        self.stdout.write("\nValidación contra las reglas del sistema (full_clean):")
        for nombre, qs in grupos:
            errores = Counter()
            invalidos = 0
            for obj in qs.iterator():
                try:
                    obj.full_clean()
                except Exception as exc:  # ValidationError y afines
                    invalidos += 1
                    detalle = getattr(exc, "message_dict", {"__all__": [str(exc)]})
                    for campo, msgs in detalle.items():
                        errores[f"{campo}: {msgs[0][:70]}"] += 1
            total_invalidos += invalidos
            marca = "OK" if invalidos == 0 else "FALLA"
            self.stdout.write(
                f"  [{marca}] {nombre}: {qs.count()} registros, {invalidos} inválidos",
            )
            for msg, veces in errores.most_common(5):
                self.stdout.write(self.style.ERROR(f"        {veces} x {msg}"))
        if total_invalidos:
            self.stdout.write(self.style.ERROR(
                f"\n[FALLA] {total_invalidos} registros no cumplen las reglas del "
                "sistema. Corregí el GENERADOR (no la validación) y volvé a sembrar.",
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                "\n[OK] Todos los registros sembrados pasan full_clean().",
            ))

    # ── Catálogos que deben existir ────────────────────────────────────────
    def _preparar_catalogos(self):
        """Crea el catálogo mínimo (tipos de vacuna, tipos de examen) si falta."""
        from pacientes.models import Paciente
        from usuarios.models import Usuario
        from vacunas.models import TipoVacuna

        # Un contador POR PREFIJO, calculado desde las CI que ya existen.
        #
        # Antes era un solo contador inicializado con el total de pacientes
        # sembrados, y los dos lotes (prefijo "99" completos, "98" editables)
        # se pisaban: al re-sembrar sobre una base donde ya se habían borrado
        # pacientes, el contador arrancaba por debajo del máximo real y los
        # editables chocaban contra CIs vivas -> "llave duplicada viola
        # restricción de unicidad «pacientes_ci_hash_key»" y el lote entero
        # se perdía. La unicidad del sistema es correcta; lo que estaba mal
        # era el generador.
        #
        # `ci` está cifrada, así que no se puede ordenar por prefijo en SQL:
        # se recorren en Python los pacientes del seed (unos cientos) y se
        # toma el máximo sufijo de cada prefijo.
        self._contadores_ci = {"99": 0, "98": 0}
        for ci_existente in Paciente.objects.filter(
            observaciones__contains=MARCA_CARGA,
        ).values_list("ci", flat=True):
            texto = str(ci_existente or "")
            prefijo = texto[:2]
            if prefijo in self._contadores_ci and texto[2:].isdigit():
                self._contadores_ci[prefijo] = max(
                    self._contadores_ci[prefijo], int(texto[2:]),
                )
        # Ídem para numero_parto (UNIQUE): continúa desde los ya existentes
        from partos.models import Parto

        self._contador_parto = Parto.objects.filter(
            numero_parto__startswith="P-CARGA-",
        ).count()

        self.medico = Usuario.objects.filter(rol="medico").first() or Usuario.objects.first()
        if not self.medico:
            msg = "No hay usuarios en el tenant: cree al menos uno antes de sembrar."
            raise RuntimeError(msg)

        vacunas_base = [
            ("Antitetánica (dT)", 2, 28, True),
            ("Influenza estacional", 1, 0, True),
            ("Hepatitis B", 3, 30, False),
        ]
        self.tipos_vacuna = []
        for nombre, dosis, intervalo, obligatoria in vacunas_base:
            tv, _ = TipoVacuna.objects.get_or_create(
                nombre=nombre,
                defaults={
                    "descripcion": f"{nombre} — esquema del embarazo (MSP Bolivia)",
                    "dosis_requeridas": dosis,
                    "intervalo_dosis_dias": intervalo,
                    "edad_minima_aplicacion": 12,
                    "contraindicaciones": "Reacción alérgica severa a dosis previa",
                    "efectos_secundarios": "Dolor local, febrícula",
                    "obligatoria_embarazo": obligatoria,
                    "activo": True,
                    "created_by": self.medico,
                },
            )
            self.tipos_vacuna.append(tv)

        from laboratorio.models import TipoExamen

        # El catálogo de exámenes venía VACÍO en el tenant, así que la lista
        # quedaba en [] y no se creaba ni un laboratorio: la sección
        # "Laboratorio" de la historia clínica salía vacía para las 500.
        # Se siembra el panel prenatal básico del MSP boliviano.
        examenes_base = [
            ("Hemograma completo", "HEM-001", "hematologia", 24, "35.00"),
            ("Glucemia en ayunas", "BIO-001", "bioquimica", 12, "20.00"),
            ("Grupo sanguíneo y factor Rh", "INM-001", "inmunologia", 24, "40.00"),
            ("Examen general de orina", "URI-001", "urinalisis", 12, "25.00"),
            ("VDRL / sífilis", "SER-001", "serologia", 48, "45.00"),
        ]
        self.tipos_examen = []
        for nombre, codigo, categoria, horas, precio in examenes_base:
            te, _ = TipoExamen.objects.get_or_create(
                codigo=codigo,
                defaults={
                    "nombre": nombre,
                    "categoria": categoria,
                    "descripcion": f"{nombre} — control prenatal de rutina",
                    "preparacion": "Ayuno de 8 horas" if categoria == "bioquimica" else "Sin preparación especial",
                    "tiempo_resultado": horas,
                    "precio": Decimal(precio),
                    "activo": True,
                    "created_by": self.medico,
                },
            )
            self.tipos_examen.append(te)

    # ── Limpieza ───────────────────────────────────────────────────────────
    def _limpiar(self):
        """Borra los pacientes de carga y sus dependencias PROTEGIDAS.

        Paciente tiene 3 relaciones con on_delete=PROTECT (Parto,
        TriajeEnfermeria, EvolucionEmbarazo): un delete directo lanza
        ProtectedError. Hay que borrar esas hijas primero; el resto es CASCADE.
        """
        from evoluciones.models import EvolucionEmbarazo
        from pacientes.models import Paciente
        from partos.models import Parto
        from triaje.models import TriajeEnfermeria

        qs = Paciente.objects.filter(observaciones__contains=MARCA_CARGA)
        ids = list(qs.values_list("id", flat=True))
        n_partos = Parto.objects.filter(paciente_id__in=ids).delete()[0]
        n_triaje = TriajeEnfermeria.objects.filter(paciente_id__in=ids).delete()[0]
        n_evol = EvolucionEmbarazo.objects.filter(paciente_id__in=ids).delete()[0]
        n_pac = qs.delete()[0]
        self.stdout.write(self.style.WARNING(
            f"[LIMPIEZA] {len(ids)} pacientes de carga eliminados "
            f"(protegidas borradas antes: {n_partos} partos, {n_triaje} triajes, "
            f"{n_evol} evoluciones; total filas {n_pac})",
        ))

    # ── Generación ─────────────────────────────────────────────────────────
    def _crear_lote(self, cantidad: int, completo: bool, etiqueta: str) -> int:
        creados = 0
        errores: dict[str, int] = {}
        for i in range(cantidad):
            try:
                with transaction.atomic():
                    self._crear_paciente_completo(i, completo, etiqueta)
                creados += 1
            except Exception as e:  # noqa: BLE001 — se agrupa y se reporta al final
                # Se agrupa por mensaje para saber CUÁNTOS fallan por CADA causa
                clave = str(e).split("\n")[0][:160]
                errores[clave] = errores.get(clave, 0) + 1
            if creados and creados % 50 == 0:
                self.stdout.write(f"  {etiqueta}: {creados}/{cantidad}…")
        fallidos = sum(errores.values())
        self.stdout.write(self.style.SUCCESS(
            f"  {etiqueta}: {creados} creados, {fallidos} fallidos"))
        for msg, n in sorted(errores.items(), key=lambda x: -x[1]):
            self.stdout.write(self.style.ERROR(f"     {n}x  {msg}"))
        return creados

    def _crear_paciente_completo(self, i: int, completo: bool, etiqueta: str):
        from antecedentes.models import AntecedenteGinecoObstetrico
        from controles.models import ControlPrenatal
        from ecografias.models import BiometriaFetal, Ecografia
        from embarazos.models import Embarazo
        from pacientes.models import Paciente

        hoy = date.today()
        edad = random.randint(15, 45)
        ciudad = random.choice(list(CIUDADES))
        zona = random.choice(CIUDADES[ciudad])
        # CI ÚNICA y determinista: prefijo por lote + contador global. Con
        # random puro había colisiones (ci_hash tiene unique=True) y el lote
        # fallaba a mitad de camino.
        prefijo = "99" if completo else "98"
        self._contadores_ci[prefijo] += 1
        ci = f"{prefijo}{self._contadores_ci[prefijo]:05d}"

        # Rh ponderado como en la poblacion real (~85% positivo)
        grupo = random.choice(["O", "A", "B", "AB"])
        tipo_sangre = grupo + random.choices(["+", "-"], [85, 15])[0]

        paciente = Paciente(
            nombre=random.choice(NOMBRES),
            apellido_paterno=random.choice(APELLIDOS),
            apellido_materno=random.choice(APELLIDOS),
            fecha_nacimiento=hoy - timedelta(days=edad * 365 + random.randint(0, 364)),
            genero="femenino",
            ci=ci,
            telefono=f"7{random.randint(1000000, 9999999)}",
            email=f"paciente.carga{i}.{random.randint(100, 999)}@ejemplo.bo",
            direccion=f"{zona}, calle {random.randint(1, 40)} Nº {random.randint(100, 999)}",
            ciudad=ciudad,
            estado_civil=random.choice(ESTADOS_CIVILES),
            ocupacion=random.choice(OCUPACIONES),
            tipo_sangre=tipo_sangre,
            # Coherente con el grupo: un "O-" no puede ser Rh positivo.
            factor_rh="negativo" if tipo_sangre.endswith("-") else "positivo",
            peso_kg=_rango(45, 90),
            altura_cm=random.randint(145, 175),
            contacto_emergencia_nombre=f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)}",
            contacto_emergencia_telefono=f"7{random.randint(1000000, 9999999)}",
            contacto_emergencia_relacion=random.choice(["Esposo", "Madre", "Hermana", "Padre"]),
            # Consentimiento informado (Ley 164) — el sistema lo exige
            consentimiento_datos_aceptado=True,
            consentimiento_datos_fecha=timezone.now(),
            observaciones=f"{MARCA_CARGA} {etiqueta} — generado para pruebas de carga",
            activo=True,
            estado_paciente="activo",
        )
        paciente.save()

        # ── Antecedentes gineco-obstétricos ──
        gestas = random.randint(1, 5)
        partos_prev = random.randint(0, max(0, gestas - 1))
        abortos_prev = random.randint(0, max(0, gestas - 1 - partos_prev))
        AntecedenteGinecoObstetrico.objects.create(
            paciente=paciente,
            menarquia_edad=random.randint(10, 16),
            ciclos_menstruales="regular" if random.random() > 0.25 else "irregular",
            duracion_ciclo_dias=random.randint(26, 32),
            duracion_menstruacion_dias=random.randint(3, 7),
            fecha_ultima_menstruacion=hoy - timedelta(days=random.randint(30, 250)),
            gestas=gestas,
            partos=partos_prev,
            abortos=abortos_prev,
            hijos_vivos=partos_prev,
            metodo_anticonceptivo_actual=random.choice(
                ["ninguno", "preservativo", "diu", "inyectable", "oral"]),
            tiempo_uso_anticonceptivo_meses=random.randint(0, 60),
            fecha_suspension_anticonceptivo=hoy - timedelta(days=random.randint(30, 400)),
        )

        # ── Embarazo ──
        semanas_actuales = random.randint(6, 40)
        fum = hoy - timedelta(weeks=semanas_actuales)
        # gestas ya incluye el embarazo actual
        embarazo = Embarazo.objects.create(
            paciente=paciente,
            numero_gesta=partos_prev + abortos_prev + 1,
            numero_para=partos_prev,
            numero_abortos=abortos_prev,
            fecha_ultima_menstruacion=fum,
            fecha_probable_parto=fum + timedelta(weeks=40),
            tipo_embarazo=random.choices(["simple", "gemelar", "multiple"], [92, 7, 1])[0],
            riesgo_embarazo=random.choices(["bajo", "medio", "alto"], [60, 27, 13])[0],
            estado="activo",
            medico_responsable=self.medico,
            notas=f"{MARCA_CARGA} {etiqueta}",
        )

        if not completo:
            # Los "editables" quedan aquí: paciente + antecedentes + embarazo.
            return

        # ── Controles prenatales (signos normales Y de riesgo) ──
        peso_pre = _rango(45, 85, 2)
        talla = _rango(145, 175, 1)  # el modelo valida talla en CENTÍMETROS (>=130)
        n_controles = random.randint(2, 8)
        for c in range(n_controles):
            sem = max(6, semanas_actuales - (n_controles - c - 1) * 4)
            riesgo = embarazo.riesgo_embarazo == "alto" and random.random() < 0.5
            ControlPrenatal.objects.create(
                embarazo=embarazo,
                paciente=paciente,
                medico=self.medico,
                numero_control=c + 1,
                fecha_control=fum + timedelta(weeks=sem),
                semanas_gestacion=sem,
                dias_gestacion=random.randint(0, 6),
                # ganancia ponderal acumulada según semanas (todo en Decimal)
                peso_actual=peso_pre + Decimal(f"{sem * random.uniform(0.2, 0.5):.2f}"),
                peso_pregestacional=peso_pre,
                talla=talla,
                # Riesgo → hipertensión; normal → PA fisiológica del embarazo
                presion_arterial_sistolica=random.randint(140, 165) if riesgo else random.randint(95, 128),
                presion_arterial_diastolica=random.randint(90, 105) if riesgo else random.randint(60, 84),
                frecuencia_cardiaca=random.randint(65, 100),
                temperatura=_rango(36.0, 37.4),
                altura_uterina=max(8, sem - random.randint(0, 3)) if sem >= 12 else None,
                frecuencia_cardiaca_fetal=random.randint(110, 160) if sem >= 12 else None,
                movimientos_fetales=random.choices(
                    ["presentes", "disminuidos", "ausentes"], [85, 12, 3])[0] if sem >= 20 else "presentes",
                edema=random.choices(["no", "leve", "moderado", "severo"], [70, 20, 7, 3])[0],
                proteinuria=random.choices(
                    ["negativa", "trazas", "positiva_1", "positiva_2"], [78, 12, 7, 3])[0],
                observaciones=f"{MARCA_CARGA} control {c + 1}",
            )

        # ── Ecografías con biometría ──
        for e in range(random.randint(1, 3)):
            # max(6, …): con embarazos de <8 semanas randint(8, 7) reventaba
            # con "empty range in randrange".
            tope = max(6, min(38, semanas_actuales))
            sem_eco = random.randint(6, tope)
            eco = Ecografia.objects.create(
                embarazo=embarazo, paciente=paciente, medico=self.medico,
                fecha_ecografia=fum + timedelta(weeks=sem_eco),
                # "obstetrica" NO es una opcion del modelo; el tipo real
                # depende del trimestre en que se hace el estudio.
                tipo_ecografia=_tipo_ecografia(sem_eco),
                indicacion="control_rutina",
                edad_gestacional_semanas=sem_eco,
                edad_gestacional_dias=random.randint(0, 6),
                numero_fetos=2 if embarazo.tipo_embarazo == "gemelar" else 1,
                frecuencia_cardiaca_fetal=random.randint(120, 165),
                indice_liquido_amniotico=_rango(4.0, 26.0),
                bolsillo_maximo=_rango(2.0, 8.0),
                localizacion_placenta=random.choice(["anterior", "posterior", "fundica", "previa"]),
                calidad_estudio=random.choice(["excelente", "buena", "regular"]),
                limitaciones_tecnicas="",
                diagnostico=f"Embarazo de {sem_eco} semanas. {MARCA_CARGA}",
                observaciones=f"{MARCA_CARGA} ecografía {e + 1}",
            )
            if sem_eco >= 12:
                BiometriaFetal.objects.create(
                    ecografia=eco,
                    diametro_biparietal=_rango(20, 95),
                    circunferencia_cefalica=_rango(80, 350),
                    circunferencia_abdominal=_rango(60, 350),
                    longitud_femur=_rango(10, 75),
                    peso_fetal_estimado=random.randint(100, 3800),
                )

        # ── Vacunas ──
        from vacunas.models import RegistroVacuna

        for tv in random.sample(self.tipos_vacuna, k=random.randint(0, 2)):
            RegistroVacuna.objects.create(
                paciente=paciente, embarazo=embarazo, tipo_vacuna=tv,
                fecha_aplicacion=timezone.now() - timedelta(days=random.randint(1, 120)),
                numero_dosis=1, lote=f"L{random.randint(10000, 99999)}",
                laboratorio=random.choice(["Sinopharm", "Pfizer", "Instituto Butantan"]),
                via_administracion="intramuscular",
                sitio_aplicacion="deltoides_izquierdo",
                aplicado_por=self.medico,
                proxima_dosis_fecha=date.today() + timedelta(days=random.randint(30, 180)),
                observaciones=f"{MARCA_CARGA}",
            )

        # ── Exámenes de laboratorio (panel prenatal) ──
        from laboratorio.models import ExamenLaboratorio

        for te in random.sample(self.tipos_examen, k=random.randint(1, 4)):
            solicitud = timezone.now() - timedelta(days=random.randint(5, 200))
            # Mayoría completados; algunos en curso, como en la vida real.
            estado = random.choices(
                ["completado", "en_proceso", "solicitado"], [75, 15, 10])[0]
            ExamenLaboratorio.objects.create(
                paciente=paciente,
                tipo_examen=te,
                medico_solicitante=self.medico,
                fecha_solicitud=solicitud,
                fecha_muestra=solicitud + timedelta(days=1) if estado != "solicitado" else None,
                fecha_resultado=solicitud + timedelta(days=2) if estado == "completado" else None,
                estado=estado,
                prioridad=random.choices(["normal", "urgente", "stat"], [85, 12, 3])[0],
                indicaciones=te.preparacion,
                observaciones=f"{MARCA_CARGA} panel prenatal",
            )

        # ── Desenlace: parto o pérdida (solo si el embarazo está a término) ──
        if semanas_actuales >= 37 and random.random() < 0.7:
            self._crear_parto(paciente, embarazo, fum, semanas_actuales)
        elif semanas_actuales < 20 and random.random() < 0.08:
            embarazo.estado = "perdida"
            embarazo.save(update_fields=["estado"])

    def _crear_parto(self, paciente, embarazo, fum, semanas):
        from partos.models import Parto, RecienNacido

        self._contador_parto += 1

        fecha_parto = timezone.make_aware(
            datetime.combine(fum + timedelta(weeks=semanas), datetime.min.time()),
        ) + timedelta(hours=random.randint(0, 23))
        parto = Parto.objects.create(
            paciente=paciente, embarazo=embarazo, medico_responsable=self.medico,
            # numero_parto es UNIQUE: con random puro había colisiones
            numero_parto=f"P-CARGA-{self._contador_parto:06d}",
            fecha_ingreso=fecha_parto - timedelta(hours=random.randint(2, 12)),
            fecha_inicio_trabajo_parto=fecha_parto - timedelta(hours=random.randint(1, 10)),
            fecha_parto=fecha_parto,
            edad_gestacional_parto=f"{semanas}+{random.randint(0, 6)}",
            tipo_parto=random.choices(
                ["vaginal_espontaneo", "cesarea_electiva", "cesarea_emergencia", "vaginal_instrumentado"],
                [62, 18, 15, 5])[0],
            observaciones_parto=f"{MARCA_CARGA}",
        )
        gemelos = 2 if embarazo.tipo_embarazo == "gemelar" else 1
        for n in range(gemelos):
            RecienNacido.objects.create(
                parto=parto,
                numero_gemelo=n + 1,
                fecha_nacimiento=fecha_parto,
                sexo=random.choice(["masculino", "femenino"]),
                peso_nacimiento=random.randint(1800, 4200),
                talla_nacimiento=_rango(42, 54, 1),
                perimetro_cefalico=_rango(30, 38, 1),
                apgar_1_minuto=random.choices([9, 8, 7, 6, 4], [50, 25, 15, 7, 3])[0],
                apgar_5_minutos=random.choices([10, 9, 8, 7], [55, 30, 12, 3])[0],
                observaciones_rn=f"{MARCA_CARGA}",
            )
        embarazo.estado = "finalizado"
        embarazo.save(update_fields=["estado"])
