"""Epicrisis del parto, edad gestacional del recién nacido (Capurro/Ballard) y partograma.

Esperado vs obtenido en cada prueba. Fallos que previenen:
- una epicrisis firmada que se puede seguir editando (deja de ser un documento);
- un código CIE-10 mal escrito o un egreso antes del parto;
- un Capurro con puntos que la escala no tiene, o la fórmula mal aplicada;
- el PDF del partograma con columnas vacías (leía campos que no existen).
"""
import datetime
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from embarazos.models import Embarazo
from pacientes.models import Paciente
from partos.edad_gestacional_rn import semanas_ballard, semanas_capurro, validar_capurro
from partos.models import CampoAdicionalEpicrisis, Epicrisis, PartogramaRegistro, RecienNacido
from usuarios.models import Usuario

CAPURRO_TERMINO = {"textura_piel": 15, "forma_oreja": 24, "glandula_mamaria": 10,
                   "formacion_pezon": 10, "pliegues_plantares": 15}


class EscalasTest(TestCase):
    def test_capurro_formula(self):
        """ESPERADO: 204 + 74 = 278 días = 39,7 semanas."""
        self.assertEqual(semanas_capurro(CAPURRO_TERMINO), Decimal("39.7"))

    def test_capurro_puntos_que_no_existen(self):
        errores = validar_capurro(CAPURRO_TERMINO | {"forma_oreja": 12})
        self.assertIn("forma_oreja", errores)
        self.assertIn("textura_piel", validar_capurro({k: v for k, v in CAPURRO_TERMINO.items() if k != "textura_piel"}))

    def test_ballard_extremos(self):
        """ESPERADO: −10 → 20 semanas; 50 → 44 semanas; 35 → 38 semanas."""
        self.assertEqual([semanas_ballard(p) for p in (-10, 50, 35)],
                         [Decimal("20.0"), Decimal("44.0"), Decimal("38.0")])


class BaseParto(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(email="med.epi@test.bo", nombre="Marta", apellido_paterno="Epi",
                                                 password="clave-segura-123", rol="medico")
        cls.admin = Usuario.objects.create_user(email="adm.epi@test.bo", nombre="Ana", apellido_paterno="Adm",
                                                password="clave-segura-123", rol="administrador")
        cls.enfermera = Usuario.objects.create_user(email="enf.epi@test.bo", nombre="Eva", apellido_paterno="Enf",
                                                    password="clave-segura-123", rol="enfermera")
        p = Paciente.objects.create(nombre="Epi", apellido_paterno="Crisis", apellido_materno="X", ci="7911333",
                                    fecha_nacimiento=datetime.date(1993, 5, 1), genero="femenino")
        emb = Embarazo.objects.create(paciente=p, numero_gesta=1, tipo_embarazo="simple",
                                      fecha_ultima_menstruacion=timezone.localdate() - datetime.timedelta(weeks=39))
        c = APIClient()
        c.force_authenticate(cls.medico)
        r = c.post("/api/partos/", {
            "embarazo": emb.id, "tipo_parto": "vaginal_espontaneo",
            "fecha_parto": (timezone.now() - datetime.timedelta(days=2)).isoformat(),
            "paciente": p.id, "edad_gestacional_parto": "39+0", "parto_finalizado": True, "episiotomia": True, "tipo_episiotomia": "mediolateral",
            "sexo_bebe": "femenino", "peso_bebe": 3200, "talla_bebe": 50, "apgar_1min": 8, "apgar_5min": 9,
        }, format="json")
        assert r.status_code == 201, r.content[:300]
        cls.parto_id = r.json()["id"]
        cls.rn = RecienNacido.objects.get(parto_id=cls.parto_id)

    def cliente(self, usuario=None):
        c = APIClient()
        c.force_authenticate(usuario or self.medico)
        return c


class CapurroApiTest(BaseParto):
    def test_registrar_capurro_calcula_semanas(self):
        r = self.cliente().patch(f"/api/partos/recien-nacidos/{self.rn.id}/",
                                 {"metodo_edad_gestacional": "capurro", "capurro_items": CAPURRO_TERMINO}, format="json")
        self.assertEqual(r.status_code, 200, r.content[:300])
        self.assertEqual(r.json()["edad_gestacional_examen_semanas"], "39.7")
        self.assertEqual(r.json()["clasificacion_edad_gestacional"], "termino")

    def test_capurro_incompleto_400(self):
        r = self.cliente().patch(f"/api/partos/recien-nacidos/{self.rn.id}/",
                                 {"metodo_edad_gestacional": "capurro", "capurro_items": {"textura_piel": 15}},
                                 format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("capurro_items", r.json())

    def test_ballard_pretermino(self):
        r = self.cliente().patch(f"/api/partos/recien-nacidos/{self.rn.id}/",
                                 {"metodo_edad_gestacional": "ballard", "ballard_puntaje": 20}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual((r.json()["edad_gestacional_examen_semanas"], r.json()["clasificacion_edad_gestacional"]),
                         ("32.0", "pretermino"))

    def test_tablas_para_el_formulario(self):
        r = self.cliente().get("/api/partos/edad-gestacional-rn/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["capurro"]), 5)
        self.assertEqual(r.json()["capurro_constante_dias"], 204)


class EpicrisisTest(BaseParto):
    URL = "/api/partos/epicrisis/"

    def datos(self, **extra):
        return {"parto": self.parto_id, "fecha_egreso": timezone.now().isoformat(),
                "diagnostico_ingreso": "Embarazo de 39 semanas en trabajo de parto", "cie10_ingreso": "o80",
                "diagnostico_egreso": "Puerperio fisiológico", "cie10_egreso": "Z39.0",
                "resumen_clinico": "Parto eutócico sin complicaciones.", **extra}

    def test_sugerencia_trae_lo_que_ya_sabe_el_sistema(self):
        r = self.cliente().get(f"{self.URL}sugerencia/?parto={self.parto_id}")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Episiotomía", r.json()["procedimientos"])
        self.assertIn("3200 g", r.json()["resumen_clinico"])

    def test_egreso_sugerido_vale_aunque_el_parto_sea_de_este_minuto(self):
        # Antes la sugerencia truncaba los segundos de «ahora»: redactada en el
        # mismo minuto del parto, quedaba antes del parto y no se podía guardar.
        from partos.models import Parto

        Parto.objects.filter(pk=self.parto_id).update(fecha_parto=timezone.now())
        egreso = self.cliente().get(f"{self.URL}sugerencia/?parto={self.parto_id}").json()["fecha_egreso"]
        r = self.cliente().post(self.URL, self.datos(fecha_egreso=egreso), format="json")
        self.assertEqual(r.status_code, 201, r.content[:400])

    def test_crear_normaliza_cie10_y_calcula_dias(self):
        r = self.cliente().post(self.URL, self.datos(), format="json")
        self.assertEqual(r.status_code, 201, r.content[:400])
        self.assertEqual((r.json()["cie10_ingreso"], r.json()["dias_internacion"], r.json()["estado"]), ("O80", 2, "borrador"))

    def test_cie10_invalido_y_egreso_antes_del_parto(self):
        r = self.cliente().post(self.URL, self.datos(
            cie10_egreso="parto", fecha_egreso=(timezone.now() - datetime.timedelta(days=10)).isoformat()), format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("cie10_egreso", r.json())
        self.assertIn("fecha_egreso", r.json())

    def test_referencia_exige_establecimiento_y_metodo_exige_consejeria(self):
        r = self.cliente().post(self.URL, self.datos(tipo_egreso="referencia", metodo_anticonceptivo="implante"),
                                format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("establecimiento_referencia", r.json())
        self.assertIn("consejeria_anticoncepcion", r.json())

    def test_firmar_bloquea_edicion_y_reabrir_solo_admin(self):
        e = self.cliente().post(self.URL, self.datos(), format="json").json()
        sin_matricula = self.cliente().post(f"{self.URL}{e['id']}/firmar/", {}, format="json")
        self.assertEqual(sin_matricula.status_code, 400)
        firmada = self.cliente().post(f"{self.URL}{e['id']}/firmar/", {"matricula_profesional": "MP-1234"}, format="json")
        self.assertEqual((firmada.status_code, firmada.json()["estado"]), (200, "firmada"))
        editar = self.cliente().patch(f"{self.URL}{e['id']}/", {"pronostico": "malo"}, format="json")
        self.assertEqual(editar.status_code, 400)
        self.assertEqual(self.cliente().delete(f"{self.URL}{e['id']}/").status_code, 409)
        self.assertEqual(self.cliente().post(f"{self.URL}{e['id']}/reabrir/", {"motivo": "Corregir diagnóstico"},
                                             format="json").status_code, 403)
        reabierta = self.cliente(self.admin).post(f"{self.URL}{e['id']}/reabrir/", {"motivo": "Corregir diagnóstico"},
                                                 format="json")
        self.assertEqual((reabierta.status_code, reabierta.json()["estado"]), (200, "borrador"))
        from auditoria.models import RegistroAuditoria

        self.assertEqual(set(RegistroAuditoria.objects.filter(modulo="Epicrisis").values_list("accion", flat=True))
                         >= {"CREAR", "FIRMAR", "REABRIR"}, True)

    def test_campos_propios_del_hospital(self):
        """ESPERADO: el administrador define un campo obligatorio y la epicrisis lo exige y lo valida."""
        definir = self.cliente(self.admin).post("/api/partos/epicrisis-campos/", {
            "clave": "grupo_sanguineo_rn", "etiqueta": "Grupo sanguíneo del RN", "tipo": "opcion",
            "opciones": ["O+", "O-", "A+", "B+"], "obligatorio": True}, format="json")
        self.assertEqual(definir.status_code, 201, definir.content[:300])
        self.assertEqual(self.cliente().post("/api/partos/epicrisis-campos/", {"clave": "x", "etiqueta": "x"},
                                             format="json").status_code, 403)
        falta = self.cliente().post(self.URL, self.datos(), format="json")
        self.assertEqual(falta.status_code, 400)
        mal = self.cliente().post(self.URL, self.datos(campos_adicionales={"grupo_sanguineo_rn": "Z"}), format="json")
        self.assertEqual(mal.status_code, 400)
        bien = self.cliente().post(self.URL, self.datos(campos_adicionales={"grupo_sanguineo_rn": "O+"}), format="json")
        self.assertEqual(bien.status_code, 201, bien.content[:300])

    def test_pdf(self):
        e = self.cliente().post(self.URL, self.datos(), format="json").json()
        r = self.cliente().get(f"{self.URL}{e['id']}/pdf/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "application/pdf")
        self.assertTrue(r.content.startswith(b"%PDF"))

    def test_enfermeria_no_accede(self):
        self.assertEqual(self.cliente(self.enfermera).get(self.URL).status_code, 403)

    def test_una_sola_epicrisis_por_parto(self):
        self.cliente().post(self.URL, self.datos(), format="json")
        r = self.cliente().post(self.URL, self.datos(), format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Epicrisis.objects.filter(parto_id=self.parto_id).count(), 1)


class PartogramaPdfTest(BaseParto):
    def test_pdf_con_los_campos_reales(self):
        inicio = timezone.now() - datetime.timedelta(hours=6)
        for h, dil in enumerate([4, 5, 7, 9]):
            PartogramaRegistro.objects.create(parto_id=self.parto_id, hora_registro=inicio + datetime.timedelta(hours=h),
                                              horas_trabajo_parto=h, dilatacion_cervical=dil, estacion_fetal="0",
                                              contracciones_10min=3, fcf_baseline=140)
        r = self.cliente().get(f"/api/partos/{self.parto_id}/partograma-pdf/")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.content.startswith(b"%PDF"))
        self.assertEqual(CampoAdicionalEpicrisis.objects.count(), 0)
