"""La auditoría no puede llenarse de ruido del propio sistema.

Por qué existe este archivo
---------------------------
La auditoría existe para responder una pregunta: **¿quién tocó los datos de
esta paciente?** Todo lo que no ayude a responderla solo hace la tabla más
grande y las consultas más lentas.

Medido sobre la base real el 5 de septiembre de 2026, con 41.367 registros
ocupando 36 MB:

    notificaciones   17.929   43,3%
    paciente          9.046   21,9%
    notificacion      8.835   21,4%
    Usuario           1.582    3,8%
    outstandingtoken  1.387    3,4%

**El 64,7% de la auditoría era «se creó una notificación».** El sistema
auditaba sus propios avisos, y como los avisos se generan solos —una alerta por
cada control prenatal, una por cada paciente registrada— la tabla crecía en
círculo: más notificaciones, más auditoría de notificaciones, y ninguna de esas
filas sirve para reconstruir nada.

Otro 3,4% eran tokens JWT, que se crean y rotan en cada login.

Cada test declara el resultado ESPERADO y lo compara con el OBTENIDO.
"""

import datetime

from django.test import TestCase

from auditoria.models import RegistroAuditoria
from auditoria.signals import EXCLUIR_MODELOS, debe_auditar_modelo
from notificaciones.models import Notificacion, TipoNotificacion
from pacientes.models import Paciente
from usuarios.models import Usuario


class LoQueSeAuditaYLoQueNoTest(TestCase):
    """La lista de exclusiones tiene que dejar fuera el ruido y solo el ruido."""

    def test_las_notificaciones_NO_se_auditan(self):
        """ESPERADO: excluido.

        Es el 64,7% de la tabla. Que el sistema se mande un aviso a sí mismo
        no es un hecho que un hospital necesite poder reconstruir.
        """
        assert debe_auditar_modelo(Notificacion) is False, (
            "Las notificaciones volvieron a auditarse: eran dos de cada tres "
            "filas de la auditoría."
        )

    def test_las_pacientes_SI_se_auditan(self):
        """ESPERADO: se audita.

        Es lo contrario del test anterior y hay que comprobarlo: una lista de
        exclusiones demasiado amplia apagaría justo lo que importa.
        """
        assert debe_auditar_modelo(Paciente) is True, (
            "Dejaron de auditarse las pacientes. La auditoría existe para esto."
        )

    def test_los_usuarios_SI_se_auditan(self):
        """ESPERADO: se audita. Cambiar un rol tiene que quedar registrado."""
        assert debe_auditar_modelo(Usuario) is True

    def test_la_propia_auditoria_no_se_audita_a_si_misma(self):
        """ESPERADO: excluido. Sin esto, cada registro generaría otro."""
        assert debe_auditar_modelo(RegistroAuditoria) is False

    def test_la_exclusion_nombra_modelos_que_existen_de_verdad(self):
        """ESPERADO: los modelos del proyecto que se excluyen se pueden importar.

        Una exclusión mal escrita —`Notificaciones` en vez de `Notificacion`—
        no da ningún error: simplemente no excluye nada y la tabla se sigue
        llenando. Es un fallo silencioso, así que se comprueba a propósito.
        """
        from django.apps import apps

        nombres_reales = {m.__name__ for m in apps.get_models()}
        # Los de Django y los de terceros (Session, ContentType, ...) no hace
        # falta comprobarlos; los del proyecto sí.
        del_proyecto = {
            "RegistroAuditoria", "Notificacion",
            "HistorialNotificaciones", "ConfiguracionNotificaciones",
        }
        for nombre in del_proyecto:
            assert nombre in EXCLUIR_MODELOS, f"{nombre} salió de la exclusión."
            assert nombre in nombres_reales, (
                f"'{nombre}' está en EXCLUIR_MODELOS pero no existe ningún "
                f"modelo con ese nombre: la exclusión no excluye nada."
            )


class CrearUnaPacienteNoInundaLaAuditoriaTest(TestCase):
    """El recorrido real: una paciente nueva dispara avisos automáticos."""

    def test_registrar_una_paciente_deja_pocos_registros_no_docenas(self):
        """ESPERADO: menos de 5 registros de auditoría.

        Crear una paciente dispara el signal que le crea notificaciones. Con
        las notificaciones auditándose, cada alta generaba su propio registro
        más uno por cada aviso: así se llegó a 26.764 filas de ruido.
        """
        antes = RegistroAuditoria.objects.count()

        Paciente.objects.create(
            nombre="Valentina", apellido_paterno="Yujra",
            apellido_materno="Avila", fecha_nacimiento=datetime.date(1994, 4, 4),
            genero="femenino", ci="6661122",
        )

        nuevos = RegistroAuditoria.objects.count() - antes
        assert nuevos < 5, (
            f"Registrar UNA paciente generó {nuevos} filas de auditoría."
        )

    def test_pero_el_alta_de_la_paciente_SI_queda_registrada(self):
        """ESPERADO: existe el registro del módulo `paciente`.

        Reducir el ruido no puede llevarse por delante la señal.
        """
        paciente = Paciente.objects.create(
            nombre="Teresa", apellido_paterno="Huanca",
            apellido_materno="Cusi", fecha_nacimiento=datetime.date(1990, 9, 9),
            genero="femenino", ci="6661133",
        )

        assert RegistroAuditoria.objects.filter(
            modulo="paciente", registro_id=str(paciente.id),
        ).exists(), "El alta de la paciente dejó de auditarse."

    def test_crear_una_notificacion_a_mano_tampoco_genera_auditoria(self):
        """ESPERADO: 0 registros nuevos."""
        usuaria = Usuario.objects.create_user(
            email="dra.ruido@test.bo", nombre="Elena",
            apellido_paterno="Choque", password="clave-de-prueba-123", rol="medico",
        )
        antes = RegistroAuditoria.objects.count()

        Notificacion.objects.create(
            usuario=usuaria, tipo=TipoNotificacion.ALERTA_ADVERTENCIA,
            titulo="Aviso", mensaje="Cuerpo",
        )

        assert RegistroAuditoria.objects.count() == antes, (
            "Crear una notificación volvió a generar un registro de auditoría."
        )


class SoloLasAlertasQueImportanDejanRastroTest(TestCase):
    """El rastro inmutable es una prueba legal, no un registro de todo."""

    def test_una_alerta_critica_SI_deja_rastro(self):
        """ESPERADO: se audita.

        Si una paciente sufre un daño y hubo un valor crítico sin atender, hay
        que poder demostrar que el sistema avisó, a quién y cuándo. Esto es lo
        único que hace falta conservar de las notificaciones.
        """
        from notificaciones.services import _auditar_notificacion

        antes = RegistroAuditoria.objects.filter(modulo="notificaciones").count()
        _auditar_notificacion(
            [], tipo="alerta_critica", prioridad="critica",
            titulo="Presión arterial en rango crítico", entidad_id=1,
            fue_fallback=False,
        )

        assert RegistroAuditoria.objects.filter(modulo="notificaciones").count() == antes + 1, (
            "Una alerta crítica dejó de auditarse. Es justo la que hay que "
            "poder demostrar ante un valor no atendido a tiempo."
        )

    def test_un_recordatorio_rutinario_NO_deja_rastro(self):
        """ESPERADO: 0 registros nuevos.

        Eran 14.612 de las 15.694 pendientes: puro volumen sin valor
        probatorio, enterrando las 1.082 que sí lo tenían.
        """
        from notificaciones.services import _auditar_notificacion

        antes = RegistroAuditoria.objects.filter(modulo="notificaciones").count()
        for prioridad in ("baja", "normal"):
            _auditar_notificacion(
                [], tipo="recordatorio", prioridad=prioridad,
                titulo="Recordatorio de control", entidad_id=1,
                fue_fallback=False,
            )

        assert RegistroAuditoria.objects.filter(modulo="notificaciones").count() == antes, (
            "Los recordatorios rutinarios volvieron a auditarse: eran el "
            "43,3% de la tabla."
        )

    def test_las_de_prioridad_alta_tambien_dejan_rastro(self):
        """ESPERADO: se audita. 'alta' está en el límite y hay que fijarlo."""
        from notificaciones.services import _auditar_notificacion

        antes = RegistroAuditoria.objects.filter(modulo="notificaciones").count()
        _auditar_notificacion(
            [], tipo="alerta_advertencia", prioridad="alta",
            titulo="Factores de riesgo", entidad_id=1, fue_fallback=False,
        )

        assert RegistroAuditoria.objects.filter(modulo="notificaciones").count() == antes + 1


class LosNombresDeAccionSeGuardanCanonicosTest(TestCase):
    """El signal escribía en minúsculas, saltándose la normalización."""

    def test_el_signal_guarda_CREAR_no_crear(self):
        """ESPERADO: 'CREAR'.

        El signal usaba `objects.create(accion="crear")`, que no pasa por
        `RegistroAuditoria.registrar()` —donde se normaliza—. Comprobado sobre
        la base real: 17.929 'CREAR' conviviendo con 15.681 'crear' para el
        mismo hecho, así que filtrar por el nombre canónico se dejaba fuera
        casi la mitad de los registros.
        """
        paciente = Paciente.objects.create(
            nombre="Canonica", apellido_paterno="Prueba",
            apellido_materno="Accion", fecha_nacimiento=datetime.date(1991, 1, 1),
            genero="femenino", ci="6661144",
        )

        registro = RegistroAuditoria.objects.filter(
            modulo="paciente", registro_id=str(paciente.id),
        ).first()

        assert registro.accion == "CREAR", (
            f"Se guardó como '{registro.accion}'. Volvió el nombre legado."
        )

    def test_el_signal_guarda_EDITAR_no_actualizar(self):
        """ESPERADO: 'EDITAR'.

        Era el peor de los dos: había 1.123 ediciones guardadas como
        'actualizar' y ninguna como 'EDITAR', así que filtrar por 'EDITAR'
        devolvía cero y parecía que nunca se hubiera modificado ningún dato.
        """
        paciente = Paciente.objects.create(
            nombre="Editada", apellido_paterno="Prueba",
            apellido_materno="Accion", fecha_nacimiento=datetime.date(1991, 1, 1),
            genero="femenino", ci="6661155",
        )
        paciente.telefono = "70012345"
        paciente.save()

        acciones = set(
            RegistroAuditoria.objects
            .filter(modulo="paciente", registro_id=str(paciente.id))
            .values_list("accion", flat=True),
        )

        assert "EDITAR" in acciones, (
            f"La edición no se guardó como 'EDITAR'. Acciones encontradas: "
            f"{sorted(acciones)}"
        )
        assert "actualizar" not in acciones
