"""Tests para el módulo de Notificaciones."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import Notificacion

Usuario = get_user_model()


def _usuario(email="notif@test.bo"):
    return Usuario.objects.create_user(
        email=email, nombre="Noti", apellido_paterno="User", password="x",
    )


class NotificacionModelTest(TestCase):
    def setUp(self):
        self.user = _usuario()

    def test_marcar_como_leida(self):
        n = Notificacion.objects.create(
            usuario=self.user, tipo="cita_proxima", titulo="Cita",
            mensaje="Tiene una cita mañana",
        )
        self.assertFalse(n.leida)
        n.marcar_como_leida()
        n.refresh_from_db()
        self.assertTrue(n.leida)
        self.assertIsNotNone(n.fecha_leida)

    def test_marcar_leida_es_idempotente(self):
        n = Notificacion.objects.create(
            usuario=self.user, tipo="cita_proxima", titulo="X", mensaje="y",
        )
        n.marcar_como_leida()
        primera = n.fecha_leida
        n.marcar_como_leida()  # segunda vez no debe cambiar la fecha
        self.assertEqual(n.fecha_leida, primera)


class NotificacionApiTest(APITestCase):
    def setUp(self):
        self.user = _usuario("a@test.bo")
        self.otro = _usuario("b@test.bo")

    def test_requiere_autenticacion(self):
        resp = self.client.get("/api/notificaciones/")
        self.assertIn(resp.status_code, (401, 403))

    def test_usuario_solo_ve_sus_notificaciones(self):
        Notificacion.objects.create(usuario=self.user, tipo="cita_proxima", titulo="mía", mensaje="m")
        Notificacion.objects.create(usuario=self.otro, tipo="cita_proxima", titulo="ajena", mensaje="m")
        self.client.force_authenticate(self.user)
        resp = self.client.get("/api/notificaciones/")
        if resp.status_code == 200:
            data = resp.data.get("results", resp.data)
            titulos = [n.get("titulo") for n in data]
            self.assertNotIn("ajena", titulos)


class NotificacionClinicaServiceTest(TestCase):
    """Prueba el servicio de notificación clínica con rigor de producción:
    destinatario correcto, FALLBACK a admin si el médico es null/inactivo, y
    rastro de auditoría de la notificación."""

    def setUp(self):
        from .services import crear_notificacion_clinica
        self.crear = crear_notificacion_clinica
        self.medico = Usuario.objects.create_user(
            email="medico@test.bo", nombre="Med", apellido_paterno="Ico",
            password="x", rol="medico",
        )
        self.admin = Usuario.objects.create_user(
            email="admin@test.bo", nombre="Adm", apellido_paterno="In",
            password="x", rol="administrador",
        )

    def test_notifica_al_medico_asignado(self):
        creadas = self.crear(
            destinatario_preferido=self.medico, tipo="examen_critico",
            titulo="Crítico", mensaje="Valor crítico", prioridad="critica",
            entidad_tipo="resultado_laboratorio", entidad_id=1,
        )
        self.assertEqual(len(creadas), 1)
        self.assertEqual(creadas[0].usuario, self.medico)

    def test_fallback_a_admin_si_medico_es_none(self):
        """Turno rotativo / sin médico asignado: debe caer a administradores,
        nunca perderse en silencio."""
        creadas = self.crear(
            destinatario_preferido=None, tipo="examen_critico",
            titulo="Crítico sin médico", mensaje="x", prioridad="critica",
            entidad_tipo="resultado_laboratorio", entidad_id=2,
        )
        self.assertTrue(creadas)
        self.assertIn(self.admin, [n.usuario for n in creadas])

    def test_fallback_a_admin_si_medico_inactivo(self):
        """Médico de licencia (activo=False): fallback a admin."""
        self.medico.activo = False
        self.medico.save(update_fields=["activo"])
        creadas = self.crear(
            destinatario_preferido=self.medico, tipo="alerta_critica",
            titulo="Crítico médico inactivo", mensaje="x", prioridad="critica",
        )
        self.assertIn(self.admin, [n.usuario for n in creadas])
        self.assertNotIn(self.medico, [n.usuario for n in creadas])

    def test_deja_rastro_de_auditoria(self):
        """La notificación clínica debe registrarse en la auditoría inmutable
        (exigible ante un valor crítico no atendido a tiempo)."""
        from auditoria.models import RegistroAuditoria
        antes = RegistroAuditoria.objects.filter(modulo="notificaciones").count()
        self.crear(
            destinatario_preferido=self.medico, tipo="examen_critico",
            titulo="Auditar", mensaje="x", prioridad="critica", entidad_id=99,
        )
        despues = RegistroAuditoria.objects.filter(modulo="notificaciones").count()
        self.assertGreater(despues, antes)

    def test_anti_fatiga_no_duplica_alerta_sin_leer(self):
        """Dos disparos del MISMO evento crítico sin leer → una sola notificación
        (evita saturar al médico y que empiece a ignorar alertas)."""
        kw = dict(
            destinatario_preferido=self.medico, tipo="examen_critico",
            titulo="Crítico repetido", mensaje="x", prioridad="critica",
            entidad_tipo="resultado_laboratorio", entidad_id=555,
        )
        self.crear(**kw)
        self.crear(**kw)  # repetido
        total = Notificacion.objects.filter(
            usuario=self.medico, entidad_tipo="resultado_laboratorio", entidad_id=555,
        ).count()
        self.assertEqual(total, 1)

    def test_anti_fatiga_reenvia_tras_marcar_leida(self):
        """Si el médico YA leyó la alerta, un nuevo disparo sí notifica de nuevo."""
        kw = dict(
            destinatario_preferido=self.medico, tipo="examen_critico",
            titulo="Crítico", mensaje="x", prioridad="critica",
            entidad_tipo="resultado_laboratorio", entidad_id=556,
        )
        primera = self.crear(**kw)
        primera[0].marcar_como_leida()
        self.crear(**kw)
        total = Notificacion.objects.filter(
            usuario=self.medico, entidad_tipo="resultado_laboratorio", entidad_id=556,
        ).count()
        self.assertEqual(total, 2)


@override_settings(
    ESCALAMIENTO_NIVEL2_MINUTOS=15, ESCALAMIENTO_NIVEL3_MINUTOS=30,
    ESCALAMIENTO_ROL_NIVEL2="jefe_guardia", ESCALAMIENTO_ROL_NIVEL3="coordinacion_medica",
)
class EscalamientoTest(TestCase):
    """Escalamiento multinivel de alertas críticas por timeout de lectura."""

    def setUp(self):
        from .services import escalar_notificaciones_criticas
        self.escalar = escalar_notificaciones_criticas
        self.medico = Usuario.objects.create_user(
            email="m@test.bo", nombre="M", apellido_paterno="D", password="x", rol="medico",
        )
        self.jefe = Usuario.objects.create_user(
            email="jefe@test.bo", nombre="J", apellido_paterno="G", password="x", rol="jefe_guardia",
        )
        self.coord = Usuario.objects.create_user(
            email="coord@test.bo", nombre="C", apellido_paterno="M", password="x", rol="coordinacion_medica",
        )

    def _critica(self, edad_min, prioridad="critica", entidad_id=1, leida=False):
        n = Notificacion.objects.create(
            usuario=self.medico, tipo="examen_critico", prioridad=prioridad,
            titulo="Crítico", mensaje="Valor crítico", entidad_tipo="resultado_laboratorio",
            entidad_id=entidad_id, leida=leida,
        )
        # fecha_creacion es auto_now_add: la envejecemos con update().
        Notificacion.objects.filter(id=n.id).update(
            fecha_creacion=timezone.now() - timedelta(minutes=edad_min),
        )
        return n

    def test_escala_a_jefe_guardia_a_los_15min(self):
        self._critica(edad_min=16)
        escaladas = self.escalar()
        self.assertEqual(escaladas, 1)
        self.assertTrue(
            Notificacion.objects.filter(usuario=self.jefe, metadata__es_escalamiento=True).exists(),
        )

    def test_escala_a_coordinacion_a_los_30min(self):
        self._critica(edad_min=31, entidad_id=2)
        self.escalar()
        self.assertTrue(
            Notificacion.objects.filter(usuario=self.coord, metadata__nivel=3).exists(),
        )

    def test_no_escala_antes_del_umbral(self):
        self._critica(edad_min=5, entidad_id=3)
        self.assertEqual(self.escalar(), 0)

    def test_solo_escala_criticas(self):
        """Una alerta ALTA (no crítica) vieja NO debe escalar."""
        self._critica(edad_min=40, prioridad="alta", entidad_id=4)
        self.assertEqual(self.escalar(), 0)

    def test_no_escala_si_ya_fue_leida(self):
        self._critica(edad_min=40, entidad_id=5, leida=True)
        self.assertEqual(self.escalar(), 0)

    def test_no_re_escala_al_mismo_nivel(self):
        """Correr dos veces con la misma antigüedad no duplica el escalamiento."""
        self._critica(edad_min=16, entidad_id=6)
        self.escalar()
        segunda = self.escalar()
        self.assertEqual(segunda, 0)

    def test_escalamiento_deja_auditoria_con_motivo_timeout(self):
        from auditoria.models import RegistroAuditoria
        self._critica(edad_min=16, entidad_id=7)
        self.escalar()
        reg = RegistroAuditoria.objects.filter(
            modulo="notificaciones", accion="EDITAR",
        ).order_by("-fecha").first()
        self.assertIsNotNone(reg)
        self.assertIn("timeout", reg.detalle.lower())
        self.assertIn("escalamiento", reg.detalle.lower())
