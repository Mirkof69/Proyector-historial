"""Los eventos clínicos generan notificación y SIEMPRE llegan a alguien.

Regresión de un fallo silencioso: `EmbarazosConfig.ready()` no importaba
`embarazos/signals.py`, así que los 4 receivers del módulo nunca se
conectaron. Medido sobre la base real: **177 embarazos de alto riesgo y cero
alertas emitidas**. Tampoco se calculaba la fecha probable de parto.

Y al conectarlos aparecieron tres bugs latentes más:
  - la alerta crítica se saltaba si el embarazo no tenía médico asignado
    (`if ... and instance.medico_responsable`), sin fallback ni aviso;
  - dos notificaciones se creaban sin `usuario=`, que es obligatorio: habrían
    reventado con IntegrityError en cada embarazo finalizado;
  - los receivers declaraban `_sender` / `_created`, y Django envía `sender` y
    `created` como keyword: al conectarlos fallaban con TypeError.
"""
import datetime

from django.db.models.signals import post_save, pre_save
from django.test import TestCase

from embarazos.models import Embarazo
from notificaciones.models import Notificacion
from pacientes.models import Paciente
from usuarios.models import Usuario


def _receivers(signal, sender):
    encontrados = signal._live_receivers(sender)
    if isinstance(encontrados, tuple):
        encontrados = encontrados[0]
    return {getattr(r, "__name__", str(r)) for r in encontrados}


class SignalsDeEmbarazoConectadosTest(TestCase):
    """Meta-test: los receivers TIENEN que estar registrados.

    Caza la clase de bug completa —signals definidos pero nunca conectados
    porque `ready()` no importa el módulo—, que ya ocurrió dos veces en este
    proyecto: en auditoría y en embarazos.
    """

    def test_los_receivers_de_embarazo_estan_conectados(self):
        nombres = _receivers(post_save, Embarazo)
        for esperado in (
            "embarazo_creado",
            "embarazo_finalizado",
            "alertar_embarazo_alto_riesgo",
            "recordatorio_fecha_probable_parto",
        ):
            self.assertIn(
                esperado, nombres,
                f"{esperado} no está conectado: ¿ready() dejó de importar signals?",
            )

    def test_la_validacion_previa_esta_conectada(self):
        self.assertIn("validar_embarazo", _receivers(pre_save, Embarazo))


class NotificacionesDeEventosClinicosTest(TestCase):
    def setUp(self):
        self.medico = Usuario.objects.create_user(
            email="medica@test.bo", nombre="Lucía", apellido_paterno="Condori",
            password="clave12345", rol="medico",
        )
        # Administrador activo: es el fallback cuando no hay médico asignado.
        self.admin = Usuario.objects.create_user(
            email="admin@test.bo", nombre="Admin", apellido_paterno="Sistema",
            password="clave12345", rol="administrador",
        )
        self.paciente = Paciente.objects.create(
            id_clinico="PAC-NOTIF-1", nombre="Rosa", apellido_paterno="Mamani",
            fecha_nacimiento=datetime.date(1994, 4, 4), genero="femenino",
            ci="96000001",
        )

    def _embarazo(self, medico, riesgo="normal", **extra):
        return Embarazo.objects.create(
            paciente=self.paciente, numero_gesta=1, medico_responsable=medico,
            fecha_ultima_menstruacion=datetime.date.today() - datetime.timedelta(weeks=30),
            estado="activo", riesgo_embarazo=riesgo, **extra,
        )

    def _notifs(self, embarazo):
        return Notificacion.objects.filter(entidad_tipo="embarazo", entidad_id=embarazo.id)

    def test_alta_de_embarazo_avisa_al_medico(self):
        embarazo = self._embarazo(self.medico)
        avisos = self._notifs(embarazo).filter(titulo="Nuevo Embarazo Registrado")
        self.assertEqual(avisos.count(), 1)
        self.assertEqual(avisos.first().usuario, self.medico)

    def test_alto_riesgo_genera_alerta_critica(self):
        embarazo = self._embarazo(self.medico, riesgo="alto")
        alerta = self._notifs(embarazo).filter(prioridad="critica").first()
        self.assertIsNotNone(alerta, "un embarazo de alto riesgo debe alertar")
        self.assertIn("Alto Riesgo", alerta.titulo)
        self.assertEqual(alerta.usuario, self.medico)

    def test_alto_riesgo_SIN_medico_igual_llega_a_alguien(self):
        """El caso que estaba roto: sin médico asignado, la alerta CRÍTICA
        simplemente no se emitía. Ahora cae al fallback de administradores."""
        embarazo = self._embarazo(None, riesgo="alto")
        alerta = self._notifs(embarazo).filter(prioridad="critica").first()
        self.assertIsNotNone(
            alerta,
            "una alerta crítica sin médico asignado NO puede quedarse sin emitir",
        )
        self.assertEqual(alerta.usuario, self.admin, "debió caer al administrador")

    def test_ninguna_notificacion_queda_sin_destinatario(self):
        """`usuario` es obligatorio: una notificación huérfana no la ve nadie."""
        self._embarazo(None, riesgo="alto")
        self.assertEqual(
            Notificacion.objects.filter(usuario__isnull=True).count(), 0,
        )

    def test_finalizar_el_embarazo_avisa_y_no_rompe_el_guardado(self):
        """Se dispara al registrar un parto: si esto revienta, no se puede
        cerrar ningún embarazo. Antes creaba la notificación sin `usuario`."""
        embarazo = self._embarazo(self.medico)
        embarazo.estado = "finalizado"
        embarazo.save()  # no debe lanzar

        aviso = self._notifs(embarazo).filter(titulo="Embarazo Finalizado").first()
        self.assertIsNotNone(aviso)
        self.assertEqual(aviso.usuario, self.medico)

    def test_la_fecha_probable_de_parto_se_calcula_sola(self):
        """Regla de Naegele: FUM + 280 días. El receptor pre_save estaba
        muerto, así que la FPP quedaba vacía si no la mandaban."""
        fum = datetime.date.today() - datetime.timedelta(weeks=30)
        embarazo = self._embarazo(self.medico)
        self.assertEqual(
            embarazo.fecha_probable_parto, fum + datetime.timedelta(days=280),
        )

    def test_no_se_duplica_la_alerta_en_cada_guardado(self):
        """Anti-fatiga: mientras la alerta siga sin leerse no se repite."""
        embarazo = self._embarazo(self.medico, riesgo="alto")
        embarazo.save()
        embarazo.save()
        self.assertEqual(
            self._notifs(embarazo).filter(prioridad="critica").count(), 1,
        )


class TareasDeRecordatorioTest(TestCase):
    """Las tareas periódicas avisan a personal real, no a nadie.

    Los cuatro bloques de `notificaciones/tasks.py` estaban guardados por
    `if hasattr(paciente, "usuario")`. `Paciente` NO tiene relación `usuario`
    (el sistema no da cuentas a las pacientes), así que la condición era
    siempre falsa y ninguna de esas alertas se emitió jamás: recordatorio de
    cita, examen pendiente, control prenatal atrasado y primer control sin
    registrar. Ahora avisan al profesional que puede actuar, con fallback.
    """

    def setUp(self):
        self.medico = Usuario.objects.create_user(
            email="medica2@test.bo", nombre="Rita", apellido_paterno="García",
            password="clave12345", rol="medico",
        )
        self.paciente = Paciente.objects.create(
            id_clinico="PAC-TAREA-1", nombre="Elsa", apellido_paterno="Cusi",
            fecha_nacimiento=datetime.date(1990, 8, 8), genero="femenino",
            ci="96000002",
        )

    def test_paciente_no_tiene_relacion_usuario(self):
        """Deja fijado el hecho del que dependía el bug: si algún día se
        agrega esa relación, este test avisa para revisar las tareas."""
        self.assertFalse(
            hasattr(self.paciente, "usuario"),
            "Paciente ganó una relación `usuario`: revisar notificaciones/tasks.py",
        )

    def test_recordatorio_de_cita_avisa_al_medico(self):
        from citas.models import Cita
        from django.utils import timezone

        from notificaciones.tasks import enviar_recordatorios_citas

        momento = timezone.localtime() + datetime.timedelta(hours=3)
        Cita.objects.create(
            paciente=self.paciente, medico=self.medico,
            fecha_cita=momento.date(), hora_cita=momento.time(),
            estado="agendada", tipo_cita="control",
            motivo="Control prenatal de rutina",
        )
        resultado = enviar_recordatorios_citas()

        self.assertEqual(resultado["enviadas"], 1, "el recordatorio no se envió")
        aviso = Notificacion.objects.filter(entidad_tipo="cita").first()
        self.assertIsNotNone(aviso)
        self.assertEqual(aviso.usuario, self.medico)

    def test_la_consulta_de_citas_usa_los_campos_reales_del_modelo(self):
        """Regresión: la tarea filtraba por `fecha_hora`, que no existe en
        Cita (son `fecha_cita` y `hora_cita`). Lanzaba FieldError SIEMPRE, así
        que jamás se envió un recordatorio de cita."""
        from notificaciones.tasks import enviar_recordatorios_citas

        # Sin citas cargadas debe devolver 0, no reventar.
        self.assertEqual(enviar_recordatorios_citas(), {"enviadas": 0})
