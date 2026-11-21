"""Población SIMULADA para probar el sistema entero con volumen realista.

    python manage.py simular_poblacion --confirmo-simulacion
    python manage.py simular_poblacion --confirmo-simulacion --pacientes 1300 --imagenes-ia 600

No son personas reales: ninguna fuente pública publica fichas de pacientes.
Las proporciones salen de cifras oficiales de Bolivia (ver EDADES_MATERNAS,
HEMOGLOBINA y su nota en seed_carga.py) y las imágenes de ecografía son
REALES, del banco público FETAL_PLANES_DB (Burgos-Artizzu et al., 2020),
analizadas por la IA del sistema igual que desde la pantalla.

Corre en la clínica real solo con --confirmo-simulacion: es para probar antes
de empezar con pacientes reales. Después se restaura el respaldo de la base
limpia (`backup_base_limpia_*.sql`) desde la pantalla Respaldos, que se lleva
también su rastro en la auditoría. Todo lo generado lleva la marca
[SEED-CARGA] (`seed_carga --limpiar` lo borra, pero la auditoría queda).

Qué agrega sobre seed_carga (que crea pacientes, embarazos, controles,
ecografías con biometría, laboratorio, vacunas y partos):
- antecedentes patológicos, un triaje y una nota de evolución por paciente;
- la epicrisis de cada parto (con CIE-10);
- imágenes reales de ecografía en la ficha y su análisis por la IA;
- citas, consultorios y fechas (completar_demo) y las alertas clínicas.
"""
from __future__ import annotations

import os
import random
from datetime import timedelta
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import transaction
from django.utils import timezone
from django_tenants.utils import schema_context

from clientes.constantes import ESQUEMA_PRINCIPAL

from .completar_demo import Command as CompletarDemo
from .seed_carga import MARCA_CARGA
from .seed_carga import Command as SeedCarga

IMAGENES = Path(settings.DATOS_IA_DIR) / "extraidos" / "fetal_planes_db" / "Images"


class Command(SeedCarga):
    help = "Carga una población simulada (estadísticas oficiales de Bolivia + ecografías reales públicas)"

    def add_arguments(self, parser):
        parser.add_argument("--pacientes", type=int, default=1300)
        parser.add_argument("--imagenes-ia", type=int, default=600,
                            help="Ecografías reales a analizar con la IA (cada una tarda ~1 s)")
        parser.add_argument("--semilla", type=int, default=2026)
        parser.add_argument("--confirmo-simulacion", action="store_true",
                            help="Obligatorio: los datos son simulados y se cargan en la clínica real")

    def handle(self, *args, **opts):
        if not opts["confirmo_simulacion"]:
            raise CommandError("Datos SIMULADOS en la clínica real: confírmelo con --confirmo-simulacion.")
        random.seed(opts["semilla"])
        from usuarios.models import Usuario

        self.enfermera = (Usuario.objects.filter(rol="enfermera", activo=True).exclude(email__endswith=".test")
                          .order_by("fecha_creacion").first())
        with schema_context(ESQUEMA_PRINCIPAL):
            self._preparar_catalogos()
            creados = self._crear_lote(opts["pacientes"], completo=True, etiqueta="SIMULADA")
            from pacientes.models import Paciente

            pacientes = list(Paciente.objects.filter(observaciones__contains=MARCA_CARGA).order_by("id"))
            r = {"pacientes": creados}
            r["antecedentes, triajes y notas"] = self._por_paciente(pacientes)
            r["epicrisis"] = self._epicrisis()
            self.stdout.write(f"  {r}")
            r["imágenes analizadas por la IA"] = self._ecografias_con_ia(opts["imagenes_ia"])
            completar = CompletarDemo(stdout=StringIO())
            completar._consultorios()
            completar._disponibilidad()
            r.update(completar._repartir_embarazos_de_carga())
            r.update(completar._poner_al_dia_la_carga())
            completar._fechas_de_laboratorio(solo_carga=True)
            completar._liberar_turnos()
            r.update(completar._citas())
            r["citas perdidas o canceladas"] = self._inasistencias()
            r.update(completar._fechas_de_registro())
            self._validar_lote()
        call_command("generar_alertas_clinicas", "--schema", ESQUEMA_PRINCIPAL, stdout=StringIO())
        self.stdout.write(self.style.SUCCESS(f"Población simulada lista: {r}"))

    # ── Por paciente: antecedentes, triaje y nota de evolución ──────────────
    def _por_paciente(self, pacientes) -> int:
        from antecedentes.models import AntecedentePatologico
        from controles.models import ControlPrenatal
        from notas_evolucion.models import NotaEvolucion
        from triaje.models import TriajeEnfermeria

        hechos = 0
        for p in pacientes:
            control = ControlPrenatal.objects.filter(paciente=p).order_by("-fecha_control").first()
            with transaction.atomic():
                gineco = getattr(p, "antecedente_gineco", None)
                multipara = (gineco.partos if gineco else 0) or 0
                AntecedentePatologico.objects.create(
                    paciente=p, tipo="personal",
                    tiene_alergias=random.random() < 0.10,
                    alergias_medicamentos="Penicilina" if random.random() < 0.05 else "",
                    anemia=random.random() < 0.30, hipertension=random.random() < 0.03,
                    diabetes=random.random() < 0.02, asma=random.random() < 0.05,
                    preeclampsia_previa=multipara > 0 and random.random() < 0.08,
                    diabetes_gestacional_previa=multipara > 0 and random.random() < 0.03,
                    hemorragia_postparto_previa=multipara > 0 and random.random() < 0.04,
                    registrado_por=self.medico,
                )
                if control is None:
                    continue
                momento = timezone.make_aware(
                    timezone.datetime.combine(control.fecha_control, timezone.datetime.min.time()),
                ) + timedelta(hours=random.randint(8, 16))
                sist, diast = control.presion_arterial_sistolica, control.presion_arterial_diastolica
                fiebre = random.random() < 0.03
                if self.enfermera:
                    TriajeEnfermeria.objects.create(
                        paciente=p, enfermera=self.enfermera, fecha_registro=momento - timedelta(minutes=30),
                        peso_kg=control.peso_actual, talla_cm=control.talla,
                        presion_sistolica=sist, presion_diastolica=diast,
                        temperatura=round(random.uniform(38.1, 39.0) if fiebre else float(control.temperatura or 36.6), 1),
                        frecuencia_cardiaca=control.frecuencia_cardiaca or 80,
                        frecuencia_respiratoria=random.randint(14, 20), saturacion_oxigeno=random.randint(91, 98),
                        motivo_visita=f"Control prenatal, {control.semanas_gestacion} semanas",
                        dolor_escala=random.choices([0, 2, 4, 6], [70, 18, 9, 3])[0],
                        prioridad="urgente" if sist >= 160 or diast >= 110 else ("alto" if sist >= 140 or fiebre else "normal"),
                        estado="completado", observaciones=MARCA_CARGA,
                    )
                hta = sist >= 140 or diast >= 90
                diagnosticos = [f"Embarazo de {control.semanas_gestacion} semanas"]
                if hta:
                    diagnosticos.append("Hipertensión gestacional (O13)" if sist < 160 else "Preeclampsia severa (O14.1)")
                NotaEvolucion.objects.create(
                    paciente=p, embarazo=control.embarazo, control_prenatal=control, medico=self.medico,
                    fecha_consulta=momento, tipo_consulta="control_prenatal",
                    motivo_consulta="Control prenatal de rutina",
                    presion_arterial_sistolica=sist, presion_arterial_diastolica=diast,
                    frecuencia_cardiaca=control.frecuencia_cardiaca, edad_gestacional_semanas=control.semanas_gestacion,
                    frecuencia_cardiaca_fetal=control.frecuencia_cardiaca_fetal,
                    examen_fisico=f"PA {sist}/{diast} mmHg, peso {control.peso_actual} kg, edema {control.edema}.",
                    diagnosticos="; ".join(diagnosticos),
                    plan_tratamiento=("Antihipertensivo, control en 1 semana y laboratorio de preeclampsia."
                                      if hta else "Hierro y ácido fólico; próximo control según calendario."),
                    observaciones=MARCA_CARGA,
                )
            hechos += 1
        return hechos

    # ── Citas a las que la paciente no fue ──────────────────────────────────
    def _inasistencias(self) -> int:
        """Una cita perdida (~10 %) o cancelada (~4 %) unos días antes de algunos
        controles, a la que la paciente no fue y que reprogramó.

        completar_demo crea una cita COMPLETADA por cada control: sin esto la
        asistencia de la semana salía 100 % y el reporte de agenda no tenía
        ninguna falta, algo que no pasa en ninguna consulta real.
        """
        from citas.models import Cita

        ocupadas = set(Cita.objects.values_list("medico_id", "fecha_cita", "hora_cita"))
        nuevas = []
        for cita in Cita.objects.filter(estado="completada", motivo__startswith="Control prenatal").iterator():
            tirada = random.random()
            if tirada >= 0.14:
                continue
            fecha = cita.fecha_cita - timedelta(days=random.randint(3, 7))
            while fecha.weekday() >= 5:
                fecha -= timedelta(days=1)
            if (cita.medico_id, fecha, cita.hora_cita) in ocupadas:
                continue
            ocupadas.add((cita.medico_id, fecha, cita.hora_cita))
            nuevas.append(Cita(
                paciente_id=cita.paciente_id, medico_id=cita.medico_id, consultorio_id=cita.consultorio_id,
                fecha_cita=fecha, hora_cita=cita.hora_cita, duracion=cita.duracion, tipo_cita="control",
                estado="no_asistio" if tirada < 0.10 else "cancelada",
                motivo=f"{cita.motivo} (no se realizó)", observaciones=MARCA_CARGA))
        Cita.objects.bulk_create(nuevas, batch_size=1000)
        return len(nuevas)

    # ── Epicrisis de cada parto ──────────────────────────────────────────────
    def _epicrisis(self) -> int:
        from partos.models import Parto
        from partos.models_epicrisis import Epicrisis

        hechas = 0
        for parto in Parto.objects.filter(observaciones_parto__contains=MARCA_CARGA, epicrisis__isnull=True):
            cesarea = parto.tipo_parto.startswith("cesarea")
            egreso = min(parto.fecha_parto + timedelta(days=3 if cesarea else 2), timezone.now())
            Epicrisis.objects.create(
                parto=parto, medico=self.medico, creado_por=self.medico, fecha_egreso=egreso,
                diagnostico_ingreso=f"Embarazo de {parto.edad_gestacional_parto} semanas en trabajo de parto",
                cie10_ingreso="O80" if not cesarea else "O82",
                diagnostico_egreso="Puerperio inmediato sin complicaciones" if random.random() < 0.9
                else "Puerperio con anemia posparto", cie10_egreso="Z39.0",
                resumen_clinico=f"{parto.get_tipo_parto_display()} el {parto.fecha_parto:%d/%m/%Y}. {MARCA_CARGA}",
                condicion_materna_egreso="sana", tipo_egreso="alta_medica",
                consejeria_anticoncepcion=True, lactancia_materna_exclusiva=random.random() < 0.85,
                signos_alarma_explicados=True, pronostico="bueno",
                proximo_control=(egreso + timedelta(days=7)).date(),
                estado="firmada" if random.random() < 0.8 else "borrador",
            )
            hechas += 1
        return hechas

    # ── Ecografías reales analizadas por la IA ───────────────────────────────
    def _ecografias_con_ia(self, cantidad: int) -> dict:
        import requests

        from ecografias.models import Ecografia, ImagenEcografia
        from ia_medica.models import AnalisisCNN, ImagenEcografica
        from ia_medica.services.result_mapping import IANoDisponible, defaults_analisis_cnn

        archivos = sorted(IMAGENES.glob("*.png"))
        if not archivos:
            return {"error": f"no hay imágenes en {IMAGENES}"}
        random.shuffle(archivos)
        url = os.environ.get("AI_SERVICE_URL", "http://localhost:8001")
        ecos = list(Ecografia.objects.filter(observaciones__contains=MARCA_CARGA, edad_gestacional_semanas__gte=18)
                    .select_related("paciente").order_by("?")[:cantidad])
        cuenta = {"analizadas": 0, "errores": 0}
        for eco, ruta in zip(ecos, archivos, strict=False):
            with open(ruta, "rb") as f:
                datos = f.read()
            try:
                resp = requests.post(f"{url}/api/analyze", files={"file": (ruta.name, datos, "image/png")},
                                     data={"modelo": "redes_medidas"}, timeout=60)
                resp.raise_for_status()
                defaults = defaults_analisis_cnn(resp.json(), self.medico, "redes_medidas")
            except (requests.RequestException, IANoDisponible, ValueError):
                cuenta["errores"] += 1
                continue
            with transaction.atomic(), open(ruta, "rb") as f:
                imagen = ImagenEcografica(
                    paciente=eco.paciente, subida_por=self.medico, nombre_original=ruta.name,
                    tamanio_bytes=len(datos), formato="png", tipo_imagen="eco_2d",
                    semana_gestacional=eco.edad_gestacional_semanas, estado="analizada",
                    descripcion=f"FETAL_PLANES_DB (público). {MARCA_CARGA}",
                )
                imagen.imagen.save(ruta.name, File(f), save=True)
                AnalisisCNN.objects.update_or_create(imagen=imagen, defaults=defaults)
                f.seek(0)
                en_ficha = ImagenEcografia(ecografia=eco, tipo_imagen="anatomia", titulo="Corte ecográfico",
                                           descripcion="Imagen real del banco público FETAL_PLANES_DB",
                                           calidad_imagen="buena", es_imagen_principal=True,
                                           analisis_ia={k: v for k, v in defaults.items()
                                                        if isinstance(v, (str, int, float, bool, list, dict))})
                en_ficha.imagen.save(ruta.name, File(f), save=True)
            cuenta["analizadas"] += 1
            if cuenta["analizadas"] % 50 == 0:
                self.stdout.write(f"  IA: {cuenta['analizadas']}/{len(ecos)}…")
        return cuenta
