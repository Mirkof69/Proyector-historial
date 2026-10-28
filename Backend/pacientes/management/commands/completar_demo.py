"""Completa la demostración con lo que se deriva de los datos clínicos cargados.

    python manage.py completar_demo --schema=clinica_demo

Los generadores (seed_demo, seed_carga, seed_all) cargaban pacientes, embarazos
y 8.047 controles, pero solo 15 citas, ningún consultorio ni horario de
atención, y todas las pacientes con la fecha de registro del día de la carga.
Así la agenda de la médica salía vacía, «Consultorios» también, y los reportes
de citas y de altas por mes daban 0/0 o variaciones de −99,9 %.

Este comando no inventa hechos clínicos: los deriva de los que ya existen.
- Consultorios y sus horarios, y la disponibilidad de cada médico (lun–vie).
- Una cita COMPLETADA por cada control prenatal ya hecho (misma fecha, misma
  médica): cada control fue una consulta.
- La PRÓXIMA cita de cada embarazo activo según su último control: cada 4
  semanas hasta la 28, cada 2 hasta la 36 y cada semana después; si ya venció,
  se reprograma en los próximos días hábiles.
- La fecha de registro de la paciente y del embarazo pasa a ser la de su
  primera atención (antes, todas el mismo día de la carga); sin controles, la
  captación a las 8 semanas de la FUM.
- seed_carga dejaba el último control de TODOS los embarazos en curso el día
  de la carga (1.187 controles el mismo día) y la solicitud de cada examen de
  laboratorio también (el campo tenía auto_now_add): los gráficos por día
  quedaban vacíos salvo un pico. Cada embarazo en curso se corre entre 0 y 27
  días hacia atrás con TODAS sus fechas juntas (la edad gestacional de cada
  atención no cambia) y cada examen vuelve a caer dentro de su embarazo.

- La carga es una foto del día en que se corrió: semanas después el Panel no
  mostraba actividad reciente. Sus fechas se adelantan los días transcurridos
  (nunca más allá de hoy), así que la demo queda al día cada vez que se corre.

Las correcciones de fechas usan update()/bulk_update(): son datos sintéticos
de la carga y no deben llenar la auditoría con miles de ediciones de «Sistema».

Es idempotente: se puede correr de nuevo sin duplicar nada.
"""
from collections import defaultdict
from datetime import date, datetime, time, timedelta

import random

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count, F, Max, Min
from django.utils import timezone
from django_tenants.utils import schema_context

CONSULTORIOS = [
    ("CON-01", "Consultorio 1 · Ginecología y Obstetricia", "ginecologia", "Planta baja", True),
    ("CON-02", "Consultorio 2 · Ginecología y Obstetricia", "ginecologia", "Planta baja", True),
    ("ECO-01", "Sala de Ecografía", "ecografia", "Primer piso", True),
    ("LAB-01", "Toma de muestras", "laboratorio", "Planta baja", False),
    ("PRO-01", "Sala de procedimientos", "procedimientos", "Primer piso", False),
    ("URG-01", "Urgencias obstétricas", "urgencias", "Planta baja", False),
]
INICIO, FIN, PASO = time(8, 0), time(18, 0), 30  # minutos


def _franjas():
    actual = datetime.combine(date.today(), INICIO)
    fin = datetime.combine(date.today(), FIN)
    while actual < fin:
        if not (time(12, 0) <= actual.time() < time(14, 0)):  # almuerzo
            yield actual.time()
        actual += timedelta(minutes=PASO)


FRANJAS = list(_franjas())

MARCA_CARGA = "[SEED-CARGA]"
MARCA_REPARTIDO = "[fechas-repartidas]"
# Un día con más exámenes pedidos que esto no es atención real sino la carga.
UMBRAL_DIA_DE_CARGA = 300


def _habil(dia: date) -> date:
    while dia.weekday() >= 5:
        dia += timedelta(days=1)
    return dia


class Command(BaseCommand):
    help = "Deriva citas, consultorios, horarios y fechas de registro de los datos clínicos de la demo"

    def add_arguments(self, parser):
        parser.add_argument("--schema", default="clinica_demo")

    def handle(self, *args, **opciones):
        with schema_context(opciones["schema"]):
            r = {
                "consultorios": self._consultorios(),
                "disponibilidades": self._disponibilidad(),
            }
            r.update(self._repartir_embarazos_de_carga())
            r.update(self._poner_al_dia_la_carga())
            r.update(self._fechas_de_laboratorio(solo_carga=r["dias_adelantados"] > 0))
            r.update(self._citas())
            r.update(self._fechas_de_registro())
        self.stdout.write(self.style.SUCCESS(f"Demo completada: {r}"))

    # ── Consultorios y horarios ──────────────────────────────────────────────
    def _consultorios(self) -> int:
        from consultorios.models import Consultorio, HorarioConsultorio

        creados = 0
        for codigo, nombre, tipo, piso, ecografo in CONSULTORIOS:
            c, nuevo = Consultorio.objects.get_or_create(codigo=codigo, defaults={
                "nombre": nombre, "tipo_consultorio": tipo, "piso": piso, "edificio": "Bloque A",
                "ubicacion": f"Bloque A, {piso.lower()}", "capacidad_personas": 3, "tiene_ecografo": ecografo,
                "tiene_bano": tipo in ("ginecologia", "urgencias"), "activo": True})
            creados += nuevo
            for dia in range(5):
                HorarioConsultorio.objects.get_or_create(consultorio=c, dia_semana=dia, hora_inicio=INICIO,
                                                         defaults={"hora_fin": FIN, "activo": True})
        return creados

    def _medicos(self):
        from usuarios.models import Usuario

        # Sin las cuentas de las pruebas de QA (@pruebas.test, @e2e.test): no atienden pacientes.
        return list(Usuario.objects.filter(rol="medico", activo=True).exclude(email__endswith=".test").order_by("id"))

    def _disponibilidad(self) -> int:
        from citas.models import Disponibilidad

        creadas = 0
        for medico in self._medicos():
            for dia in range(5):
                for inicio, fin in ((time(8, 0), time(12, 0)), (time(14, 0), time(18, 0))):
                    _, nueva = Disponibilidad.objects.get_or_create(
                        medico=medico, dia_semana=dia, hora_inicio=inicio, hora_fin=fin,
                        defaults={"duracion_cita": PASO, "activo": True})
                    creadas += nueva
        return creadas

    # ── Citas ────────────────────────────────────────────────────────────────
    def _citas(self) -> dict:
        from citas.models import Cita
        from consultorios.models import Consultorio
        from controles.models import ControlPrenatal
        from embarazos.models import Embarazo

        medicos = self._medicos()
        if not medicos:
            return {"citas_pasadas": 0, "citas_proximas": 0}
        consultorios = list(Consultorio.objects.filter(tipo_consultorio="ginecologia").order_by("codigo"))
        sala = {m.pk: consultorios[i % len(consultorios)] for i, m in enumerate(medicos)} if consultorios else {}
        validos = {m.pk for m in medicos}

        ocupadas = defaultdict(set)  # (médico, fecha) -> horas tomadas
        for medico_id, fecha, hora in Cita.objects.values_list("medico_id", "fecha_cita", "hora_cita"):
            ocupadas[(medico_id, fecha)].add(hora)
        ya_tiene = set(Cita.objects.values_list("paciente_id", "fecha_cita"))

        def franja(medico_id, fecha, desde=None):
            for h in FRANJAS:
                if (desde is None or h > desde) and h not in ocupadas[(medico_id, fecha)]:
                    ocupadas[(medico_id, fecha)].add(h)
                    return h
            return None

        # Una cita completada por cada control ya hecho.
        pasadas = []
        controles = (ControlPrenatal.objects.filter(fecha_control__lt=timezone.localdate())
                     .values("id", "paciente_id", "medico_id", "fecha_control", "numero_control").order_by("id"))
        for c in controles:
            medico_id = c["medico_id"] if c["medico_id"] in validos else medicos[c["id"] % len(medicos)].pk
            if (c["paciente_id"], c["fecha_control"]) in ya_tiene:
                continue
            hora = franja(medico_id, c["fecha_control"])
            if hora is None:
                continue
            ya_tiene.add((c["paciente_id"], c["fecha_control"]))
            pasadas.append(Cita(
                paciente_id=c["paciente_id"], medico_id=medico_id, consultorio=sala.get(medico_id),
                fecha_cita=c["fecha_control"], hora_cita=hora, duracion=PASO,
                tipo_cita="primera_vez" if c["numero_control"] == 1 else "control", estado="completada",
                motivo=f"Control prenatal n.º {c['numero_control']}"))
        Cita.objects.bulk_create(pasadas, batch_size=1000)

        # La próxima cita de cada embarazo activo, según su último control.
        hoy = timezone.localdate()
        ahora = timezone.localtime().time()
        proximas = []
        ultimos = {}
        for c in (ControlPrenatal.objects.filter(embarazo__estado="activo")
                  .values("embarazo_id", "fecha_control", "medico_id", "semanas_gestacion").order_by("fecha_control")):
            ultimos[c["embarazo_id"]] = c
        futuras = set(Cita.objects.filter(fecha_cita__gte=hoy).values_list("paciente_id", flat=True))
        for i, emb in enumerate(Embarazo.objects.filter(estado="activo").values("id", "paciente_id").order_by("id")):
            if emb["paciente_id"] in futuras:
                continue
            ultimo = ultimos.get(emb["id"])
            semanas = (ultimo or {}).get("semanas_gestacion") or 0
            intervalo = 7 if semanas >= 36 else 14 if semanas >= 28 else 28
            fecha = (ultimo["fecha_control"] + timedelta(days=intervalo)) if ultimo else hoy
            if fecha < hoy:  # control vencido: se reprograma en los próximos días hábiles
                fecha = hoy + timedelta(days=i % 10)
            fecha = _habil(fecha)
            medico_id = (ultimo or {}).get("medico_id")
            if medico_id not in validos:
                medico_id = medicos[i % len(medicos)].pk
            hora = None
            while hora is None and fecha <= hoy + timedelta(days=60):
                hora = franja(medico_id, fecha, desde=ahora if fecha == hoy else None)
                if hora is None:
                    fecha = _habil(fecha + timedelta(days=1))
            if hora is None:
                continue
            futuras.add(emb["paciente_id"])
            proximas.append(Cita(
                paciente_id=emb["paciente_id"], medico_id=medico_id, consultorio=sala.get(medico_id),
                fecha_cita=fecha, hora_cita=hora, duracion=PASO, tipo_cita="control",
                estado="confirmada" if fecha <= hoy + timedelta(days=1) else "agendada",
                motivo="Control prenatal programado"))
        Cita.objects.bulk_create(proximas, batch_size=1000)
        return {"citas_pasadas": len(pasadas), "citas_proximas": len(proximas)}

    # ── Fechas de la carga masiva ────────────────────────────────────────────
    def _repartir_embarazos_de_carga(self) -> dict:
        from citas.models import Cita
        from controles.models import ControlPrenatal
        from ecografias.models import Ecografia
        from embarazos.models import Embarazo
        from vacunas.models import RegistroVacuna

        hoy = timezone.localdate()
        pendientes = (Embarazo.objects.filter(estado="activo", notas__contains=MARCA_CARGA)
                      .exclude(notas__contains=MARCA_REPARTIDO)
                      .values("id", "paciente_id", "fecha_ultima_menstruacion", "notas"))
        ocupadas = defaultdict(set)
        for medico_id, fecha, hora in Cita.objects.values_list("medico_id", "fecha_cita", "hora_cita"):
            ocupadas[(medico_id, fecha)].add(hora)
        movidos = 0
        for emb in pendientes:
            fum = emb["fecha_ultima_menstruacion"]
            # Determinista (igual en cada máquina) y sin pasar de 41 semanas hoy.
            atraso = (emb["id"] * 7919) % 28
            if fum:
                atraso = max(0, min(atraso, 41 * 7 - (hoy - fum).days))
            with transaction.atomic():
                if atraso:
                    d = timedelta(days=atraso)
                    Embarazo.objects.filter(pk=emb["id"]).update(
                        fecha_ultima_menstruacion=F("fecha_ultima_menstruacion") - d,
                        fecha_probable_parto=F("fecha_probable_parto") - d)
                    ControlPrenatal.objects.filter(embarazo_id=emb["id"]).update(fecha_control=F("fecha_control") - d)
                    Ecografia.objects.filter(embarazo_id=emb["id"]).update(fecha_ecografia=F("fecha_ecografia") - d)
                    RegistroVacuna.objects.filter(embarazo_id=emb["id"]).update(
                        fecha_aplicacion=F("fecha_aplicacion") - d, proxima_dosis_fecha=F("proxima_dosis_fecha") - d)
                    # Las citas que este comando derivó de esos controles se van con ellos,
                    # a una hora libre de la misma médica (sin turnos dobles).
                    citas = list(Cita.objects.filter(paciente_id=emb["paciente_id"], estado="completada",
                                                     motivo__startswith="Control prenatal n.º"))
                    for c in citas:
                        ocupadas[(c.medico_id, c.fecha_cita)].discard(c.hora_cita)
                        c.fecha_cita -= d
                        libre = next((h for h in FRANJAS if h not in ocupadas[(c.medico_id, c.fecha_cita)]), None)
                        c.hora_cita = libre or c.hora_cita
                        ocupadas[(c.medico_id, c.fecha_cita)].add(c.hora_cita)
                    Cita.objects.bulk_update(citas, ["fecha_cita", "hora_cita"])
                notas = f"{emb['notas'] or ''} {MARCA_REPARTIDO}".strip()
                Embarazo.objects.filter(pk=emb["id"]).update(notas=notas)
            movidos += 1
        return {"embarazos_de_carga_repartidos": movidos}

    def _poner_al_dia_la_carga(self) -> dict:
        from citas.models import Cita
        from controles.models import ControlPrenatal
        from ecografias.models import Ecografia
        from embarazos.models import Embarazo
        from pacientes.models import Paciente
        from partos.models import Parto, RecienNacido
        from vacunas.models import RegistroVacuna

        hoy = timezone.localdate()
        pacientes = set(Embarazo.objects.filter(notas__contains=MARCA_CARGA).values_list("paciente_id", flat=True))
        ultimo = ControlPrenatal.objects.filter(paciente_id__in=pacientes).aggregate(m=Max("fecha_control"))["m"]
        if not pacientes or not ultimo or ultimo >= hoy:
            return {"dias_adelantados": 0}
        d = timedelta(days=(hoy - ultimo).days)
        de_carga = {"paciente_id__in": pacientes}
        with transaction.atomic():
            Embarazo.objects.filter(**de_carga).update(
                fecha_ultima_menstruacion=F("fecha_ultima_menstruacion") + d,
                fecha_probable_parto=F("fecha_probable_parto") + d)
            ControlPrenatal.objects.filter(**de_carga).update(fecha_control=F("fecha_control") + d)
            Ecografia.objects.filter(**de_carga).update(
                fecha_ecografia=F("fecha_ecografia") + d,
                proxima_ecografia_recomendada=F("proxima_ecografia_recomendada") + d)
            RegistroVacuna.objects.filter(**de_carga).update(
                fecha_aplicacion=F("fecha_aplicacion") + d, proxima_dosis_fecha=F("proxima_dosis_fecha") + d)
            Parto.objects.filter(**de_carga).update(
                fecha_ingreso=F("fecha_ingreso") + d, fecha_inicio_trabajo_parto=F("fecha_inicio_trabajo_parto") + d,
                fecha_parto=F("fecha_parto") + d, hora_rotura_membranas=F("hora_rotura_membranas") + d)
            RecienNacido.objects.filter(parto__paciente_id__in=pacientes).update(
                fecha_nacimiento=F("fecha_nacimiento") + d)
            Paciente.objects.filter(pk__in=pacientes).update(fecha_registro=F("fecha_registro") + d)
            Embarazo.objects.filter(**de_carga).update(fecha_registro=F("fecha_registro") + d)
            # Las citas atendidas que salieron de esos controles se mueven con ellos, a
            # una hora libre de la misma médica.
            ocupadas = defaultdict(set)
            for medico_id, fecha, hora in Cita.objects.values_list("medico_id", "fecha_cita", "hora_cita"):
                ocupadas[(medico_id, fecha)].add(hora)
            citas = list(Cita.objects.filter(estado="completada", motivo__startswith="Control prenatal n.º", **de_carga))
            for c in citas:
                ocupadas[(c.medico_id, c.fecha_cita)].discard(c.hora_cita)
            for c in citas:
                c.fecha_cita += d
                libre = next((h for h in FRANJAS if h not in ocupadas[(c.medico_id, c.fecha_cita)]), None)
                c.hora_cita = libre or c.hora_cita
                ocupadas[(c.medico_id, c.fecha_cita)].add(c.hora_cita)
            Cita.objects.bulk_update(citas, ["fecha_cita", "hora_cita"], batch_size=1000)
        return {"dias_adelantados": d.days}

    def _fechas_de_laboratorio(self, solo_carga: bool = False) -> dict:
        """Cada examen pedido el día de la carga vuelve a caer dentro de su embarazo:
        en la fecha de su control si lo tiene; si no, en un día del embarazo.
        Tras adelantar la carga se recolocan todos sus exámenes del mismo modo."""
        from controles.models import ControlPrenatal
        from embarazos.models import Embarazo
        from laboratorio.models import ExamenLaboratorio

        dias = list(ExamenLaboratorio.objects.values("fecha_solicitud__date").annotate(n=Count("id"))
                    .filter(n__gte=UMBRAL_DIA_DE_CARGA).values_list("fecha_solicitud__date", flat=True))
        if solo_carga:
            pacientes = Embarazo.objects.filter(notas__contains=MARCA_CARGA).values_list("paciente_id", flat=True)
            examenes = ExamenLaboratorio.objects.filter(paciente_id__in=pacientes)
        elif dias:
            examenes = ExamenLaboratorio.objects.filter(fecha_solicitud__date__in=dias)
        else:
            return {"examenes_reubicados": 0}
        ahora = timezone.now()
        hoy = timezone.localdate()
        controles = dict(ControlPrenatal.objects.values_list("id", "fecha_control"))
        embarazos = defaultdict(list)
        for pid, fum, fin, estado in Embarazo.objects.values_list(
                "paciente_id", "fecha_ultima_menstruacion", "fecha_probable_parto", "estado"):
            if fum:
                embarazos[pid].append((fum, fin if estado != "activo" and fin else hoy))
        cambiados = []
        for ex in examenes.only(
                "id", "paciente_id", "control_prenatal_id", "fecha_solicitud", "fecha_muestra", "fecha_resultado"):
            azar = random.Random(ex.id)
            dia = controles.get(ex.control_prenatal_id)
            if dia is None and embarazos.get(ex.paciente_id):
                fum, fin = max(embarazos[ex.paciente_id])
                final = min(fin, hoy - timedelta(days=1))
                inicio = min(fum + timedelta(weeks=6), final)
                dia = inicio + timedelta(days=azar.randint(0, (final - inicio).days))
            if dia is None:
                continue
            solicitud = timezone.make_aware(datetime.combine(dia, time(azar.randint(8, 16), azar.randint(0, 59))))
            ex.fecha_solicitud = min(solicitud, ahora)
            if ex.fecha_muestra:
                ex.fecha_muestra = min(ex.fecha_solicitud + timedelta(hours=azar.randint(1, 20)), ahora)
            if ex.fecha_resultado:
                ex.fecha_resultado = min(ex.fecha_solicitud + timedelta(days=1, hours=azar.randint(1, 30)), ahora)
            cambiados.append(ex)
        ExamenLaboratorio.objects.bulk_update(cambiados, ["fecha_solicitud", "fecha_muestra", "fecha_resultado"],
                                              batch_size=1000)
        return {"examenes_reubicados": len(cambiados)}

    # ── Fechas de registro ───────────────────────────────────────────────────
    def _fechas_de_registro(self) -> dict:
        from controles.models import ControlPrenatal
        from embarazos.models import Embarazo
        from pacientes.models import Paciente

        def momento(d):
            return timezone.make_aware(datetime.combine(d, time(9, 0)))

        primera_por_paciente = dict(ControlPrenatal.objects.values("paciente_id").annotate(p=Min("fecha_control"))
                                    .values_list("paciente_id", "p"))
        primera_por_embarazo = dict(ControlPrenatal.objects.values("embarazo_id").annotate(p=Min("fecha_control"))
                                    .values_list("embarazo_id", "p"))
        # Sin controles: la captación, 8 semanas después de la FUM del primer embarazo.
        primera_fum = Embarazo.objects.values("paciente_id").annotate(f=Min("fecha_ultima_menstruacion"))
        for pid, fum in primera_fum.values_list("paciente_id", "f"):
            if fum and pid not in primera_por_paciente:
                primera_por_paciente[pid] = min(fum + timedelta(weeks=8), timezone.localdate())
        pacientes = embarazos = 0
        for pid, registro in Paciente.objects.values_list("id", "fecha_registro"):
            primera = primera_por_paciente.get(pid)
            if primera and registro and primera < timezone.localtime(registro).date():
                Paciente.objects.filter(pk=pid).update(fecha_registro=momento(primera))
                pacientes += 1
        for eid, registro in Embarazo.objects.values_list("id", "fecha_registro"):
            primera = primera_por_embarazo.get(eid)
            if primera and registro and primera < timezone.localtime(registro).date():
                Embarazo.objects.filter(pk=eid).update(fecha_registro=momento(primera))
                embarazos += 1
        return {"pacientes_fecha_registro": pacientes, "embarazos_fecha_registro": embarazos}
