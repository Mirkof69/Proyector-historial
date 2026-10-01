"""Embarazos, citas y pacientes se paginan, filtran y resumen EN EL SERVIDOR.

Antes las tres pantallas descargaban TODAS las páginas en bucle y filtraban en
el navegador: Embarazos y Citas bajaban además TODAS las pacientes (~34
peticiones con 3.200 pacientes) solo para poner nombres que el serializer del
listado ya trae. Las cifras de cabecera (activos, alto riesgo, citas de hoy,
edad promedio...) se calculaban sobre lo descargado. Ahora cada pantalla pide
una página y un `resumen` calculado con los MISMOS filtros que el listado.
"""
import datetime
from io import BytesIO

from django.test import TestCase
from django.utils import timezone
from openpyxl import load_workbook
from rest_framework.test import APIClient

from auditoria.models import RegistroAuditoria
from citas.models import Cita
from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario


def _paciente(nombre, apellido, ci, nacimiento=datetime.date(1995, 5, 5), **extra):
    return Paciente.objects.create(nombre=nombre, apellido_paterno=apellido, apellido_materno="Test",
                                   fecha_nacimiento=nacimiento, genero="femenino", ci=ci, **extra)


class ListadoEmbarazosServidorTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(email="emb.srv@test.bo", nombre="Eva", apellido_paterno="Emb",
                                                 password="clave-segura-123", rol="medico")
        hoy = timezone.localdate()
        semanas = lambda n: hoy - datetime.timedelta(weeks=n)  # noqa: E731
        a_termino = _paciente("Rosa", "Quispe", "8800101")
        primer = _paciente("Lidia", "Condori", "8800102")
        segundo = _paciente("Nora", "Mamani", "8800103")
        historica = _paciente("Olga", "Flores", "8800104")
        # 38 semanas, alto riesgo, FPP en 14 días: a término, 3.er trimestre y próximo parto.
        Embarazo.objects.create(paciente=a_termino, numero_gesta=2, fecha_ultima_menstruacion=semanas(38),
                                fecha_probable_parto=hoy + datetime.timedelta(days=14),
                                riesgo_embarazo="alto", estado="activo", notas="placenta previa")
        Embarazo.objects.create(paciente=primer, numero_gesta=1, fecha_ultima_menstruacion=semanas(10),
                                riesgo_embarazo="bajo", estado="activo")
        Embarazo.objects.create(paciente=segundo, numero_gesta=1, fecha_ultima_menstruacion=semanas(20),
                                riesgo_embarazo="medio", estado="activo")
        # 205 embarazos terminados (más que el tope de 200 por página). Su FUM
        # es de hace más de un año: NO deben contar como «a término» hoy.
        Embarazo.objects.bulk_create([
            Embarazo(paciente=historica, numero_gesta=i + 1, fecha_ultima_menstruacion=semanas(60 + i),
                     fecha_probable_parto=semanas(20 + i), riesgo_embarazo="bajo", estado="finalizado")
            for i in range(205)
        ])

    def setUp(self):
        self.c = APIClient()
        self.c.force_authenticate(self.medico)

    def test_la_pagina_trae_el_nombre_y_el_total_real(self):
        """La tabla no necesita bajar las pacientes: el listado ya trae el nombre."""
        r = self.c.get("/api/embarazos/", {"page_size": 20}).json()
        self.assertEqual(r["count"], 208)
        self.assertEqual(len(r["results"]), 20)
        self.assertTrue(all(e["paciente_nombre"] for e in r["results"]))

    def test_resumen_cuenta_todo_y_solo_activos(self):
        r = self.c.get("/api/embarazos/resumen/").json()
        self.assertEqual(r["total"], 208)
        self.assertEqual(r["activos"], 3)
        self.assertEqual(r["alto_riesgo"], 1)
        self.assertEqual(r["a_termino"], 1)
        self.assertEqual((r["primer_trimestre"], r["segundo_trimestre"], r["tercer_trimestre"]), (1, 1, 1))
        self.assertEqual(len(r["proximos_partos"]), 1)
        self.assertIn("Quispe", r["proximos_partos"][0]["paciente_nombre"])
        self.assertEqual([a["semanas"] for a in r["alertas_termino"]], [38])

    def test_resumen_respeta_los_filtros_de_la_pantalla(self):
        self.assertEqual(self.c.get("/api/embarazos/resumen/", {"riesgo_embarazo": "alto"}).json()["total"], 1)
        self.assertEqual(self.c.get("/api/embarazos/resumen/", {"estado": "finalizado"}).json()["activos"], 0)
        # Búsqueda por apellido (campo cifrado) y por notas (en claro).
        self.assertEqual(self.c.get("/api/embarazos/resumen/", {"search": "condori"}).json()["total"], 1)
        self.assertEqual(self.c.get("/api/embarazos/", {"search": "placenta"}).json()["count"], 1)

    def test_excel_con_filtros_etiquetas_y_auditado(self):
        r = self.c.get("/api/embarazos/exportar-excel/", {"estado": "activo"})
        self.assertEqual(r.status_code, 200)
        filas = list(load_workbook(BytesIO(r.content)).active.iter_rows(values_only=True))
        self.assertEqual(filas[0][0], "Paciente")
        self.assertEqual(len(filas), 4, filas)  # encabezado + 3 activos
        self.assertIn("Alto", [v for fila in filas for v in fila])
        self.assertTrue(RegistroAuditoria.objects.filter(accion="EXPORTAR", modulo="embarazos").exists())


class ListadoCitasServidorTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Usuario.objects.create_user(email="cit.adm@test.bo", nombre="Ada", apellido_paterno="Cit",
                                                password="clave-segura-123", rol="administrador")
        cls.medico = Usuario.objects.create_user(email="cit.med@test.bo", nombre="Mia", apellido_paterno="Cit",
                                                 password="clave-segura-123", rol="medico")
        otro = Usuario.objects.create_user(email="cit.otro@test.bo", nombre="Leo", apellido_paterno="Otro",
                                           password="clave-segura-123", rol="medico")
        p = _paciente("Juana", "Choque", "8800201")
        hoy = timezone.localdate()
        ayer = hoy - datetime.timedelta(days=1)
        manana = hoy + datetime.timedelta(days=1)

        def cita(fecha, hora, estado, medico=None, motivo="Control"):
            return Cita(paciente=p, medico=medico or cls.medico, fecha_cita=fecha,
                        hora_cita=datetime.time(hora, 0), estado=estado, motivo=motivo, tipo_cita="control")

        # bulk_create: Cita.save() valida «no en el pasado» y las atrasadas
        # justamente están en el pasado.
        Cita.objects.bulk_create([
            cita(hoy, 10, "agendada"),
            cita(hoy, 8, "confirmada", motivo="Ecografía morfológica"),
            cita(hoy, 9, "completada"),
            cita(ayer, 9, "confirmada"),   # atrasada
            cita(ayer, 10, "cancelada"),   # cerrada: no es atrasada
            cita(manana, 9, "en_espera", medico=otro),
            # 201 canceladas a futuro: más que el tope de 200 por página.
            *[cita(manana + datetime.timedelta(days=i), 11, "cancelada") for i in range(201)],
        ])

    def setUp(self):
        self.c = APIClient()
        self.c.force_authenticate(self.admin)

    def test_resumen_cuenta_todas_con_los_mismos_filtros(self):
        r = self.c.get("/api/citas/citas/resumen/").json()
        self.assertEqual(r["total"], 207)
        self.assertEqual(r["agendada"], 1)
        self.assertEqual(r["confirmada"], 2)
        self.assertEqual(r["en_espera"], 1)
        self.assertEqual(r["cancelada"], 202)
        self.assertEqual(r["hoy"], 2)
        self.assertEqual(r["atrasadas"], 1)
        hoy = timezone.localdate().isoformat()
        filtrado = self.c.get("/api/citas/citas/resumen/", {"fecha_desde": hoy, "fecha_hasta": hoy}).json()
        self.assertEqual(filtrado["total"], 3)

    def test_el_medico_solo_cuenta_sus_citas(self):
        self.c.force_authenticate(self.medico)
        self.assertEqual(self.c.get("/api/citas/citas/resumen/").json()["en_espera"], 0)

    def test_busca_por_motivo_en_el_servidor(self):
        """La pantalla buscaba el motivo en el navegador; ahora lo hace el backend."""
        r = self.c.get("/api/citas/citas/", {"search": "morfológica"}).json()
        self.assertEqual(r["count"], 1)

    def test_ordenar_por_fecha_desempata_por_hora(self):
        hoy = timezone.localdate().isoformat()
        r = self.c.get("/api/citas/citas/", {"fecha_cita": hoy, "ordering": "fecha_cita"}).json()
        self.assertEqual([c["hora_cita"][:5] for c in r["results"]], ["08:00", "09:00", "10:00"])
        r = self.c.get("/api/citas/citas/", {"fecha_cita": hoy, "ordering": "-fecha_cita"}).json()
        self.assertEqual([c["hora_cita"][:5] for c in r["results"]], ["10:00", "09:00", "08:00"])


class ListadoPacientesServidorTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(email="pac.srv@test.bo", nombre="Pia", apellido_paterno="Pac",
                                                 password="clave-segura-123", rol="medico")
        anio = timezone.localdate().year
        # Nacidas el 1 de enero: la edad es exactamente la resta de años.
        nacida = lambda edad: datetime.date(anio - edad, 1, 1)  # noqa: E731
        _paciente("Ana", "Adolescente", "8800301", nacida(17), ciudad="La Paz")
        joven = _paciente("Bea", "Joven", "8800302", nacida(22), ciudad="El Alto")
        anosa = _paciente("Cira", "Anosa", "8800303", nacida(36), ciudad="Cochabamba")
        _paciente("Dora", "Mayor", "8800304", nacida(41), ciudad="Cochabamba", activo=False)
        hoy = timezone.localdate()
        Embarazo.objects.create(paciente=anosa, numero_gesta=3, fecha_ultima_menstruacion=hoy - datetime.timedelta(weeks=12),
                                estado="activo")
        Embarazo.objects.create(paciente=joven, numero_gesta=1, fecha_ultima_menstruacion=hoy - datetime.timedelta(weeks=80),
                                estado="finalizado")

    def setUp(self):
        self.c = APIClient()
        self.c.force_authenticate(self.medico)

    def contar(self, **q):
        return self.c.get("/api/pacientes/", {"page_size": 1, **q}).json()["count"]

    def test_filtros_de_la_pantalla_en_el_servidor(self):
        self.assertEqual(self.contar(ciudad="cochabamba"), 2)
        self.assertEqual(self.contar(activo="true"), 3)
        self.assertEqual(self.contar(con_embarazo_activo="true"), 1)
        self.assertEqual(self.contar(estado_obstetrico="gestando"), 1)
        self.assertEqual(self.contar(estado_obstetrico="con_historial"), 1)
        self.assertEqual(self.contar(estado_obstetrico="sin_embarazo"), 2)

    def test_resumen_calcula_la_edad_promedio_sobre_todas(self):
        r = self.c.get("/api/pacientes/resumen/").json()
        self.assertEqual(r["total"], 4)
        self.assertEqual(r["activos"], 3)
        self.assertEqual(r["embarazadas"], 1)
        self.assertEqual(r["nuevos_mes"], 4)
        self.assertEqual(r["promedio_edad"], round((17 + 22 + 36 + 41) / 4))
        self.assertEqual(r["rangos_edad"], {"<15": 0, "15-19": 1, "20-24": 1, "25-29": 0,
                                            "30-34": 0, "35-39": 1, ">=40": 1})
        self.assertEqual(r["anosas_gestando"], 1)
        self.assertEqual(r["registros_por_mes"][timezone.localdate().month - 1], 4)
        self.assertEqual({c["ciudad"]: c["total"] for c in r["por_ciudad"]},
                         {"La Paz": 1, "El Alto": 1, "Cochabamba": 2})
        filtrado = self.c.get("/api/pacientes/resumen/", {"ciudad": "cochabamba"}).json()
        self.assertEqual((filtrado["total"], filtrado["promedio_edad"]), (2, round((36 + 41) / 2)))

    def test_no_ordena_por_nombres_cifrados(self):
        """Ordenar por `nombre` en SQL ordenaba por el texto cifrado: se ignora."""
        r = self.c.get("/api/pacientes/", {"ordering": "nombre"})
        self.assertEqual(r.status_code, 200)
        ids = [p["id_clinico"] for p in self.c.get("/api/pacientes/", {"ordering": "id_clinico"}).json()["results"]]
        self.assertEqual(ids, sorted(ids))

    def test_excel_con_filtros_y_auditado(self):
        r = self.c.get("/api/pacientes/exportar-excel/", {"ciudad": "cochabamba"})
        self.assertEqual(r.status_code, 200)
        filas = list(load_workbook(BytesIO(r.content)).active.iter_rows(values_only=True))
        self.assertEqual(filas[0][0], "ID clínico")
        self.assertEqual(len(filas), 3, filas)
        self.assertTrue(RegistroAuditoria.objects.filter(accion="EXPORTAR", modulo="pacientes").exists())
        # El Excel individual de una paciente sigue en su ruta de detalle.
        una = Paciente.objects.first()
        self.assertEqual(self.c.get(f"/api/pacientes/{una.pk}/exportar-excel/").status_code, 200)
