"""Tests del sistema de auditoría — DEMOSTRACIÓN de trazabilidad clínica.

Prueban que TODA acción relevante queda registrada con: quién (usuario), cuándo
(fecha), qué acción semántica (crear/editar/eliminar/login, no un GET), sobre qué
registro, y que el log es INMUTABLE y con PII redactada.
"""
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from pacientes.models import Paciente

from .models import RegistroAuditoria

Usuario = get_user_model()


def _usuario(email="aud@test.bo", rol="medico"):
    return Usuario.objects.create_user(
        email=email, nombre="Aud", apellido_paterno="Itor", password="x", rol=rol,
    )


def _paciente(ci="AUD001"):
    return Paciente.objects.create(
        id_clinico=f"PAC-{ci}", nombre="Auditada", apellido_paterno="Test",
        fecha_nacimiento=date(1990, 1, 1), genero="femenino", ci=ci,
    )


class AuditoriaCrudTest(TestCase):
    """El CRUD de registros clínicos se audita automáticamente vía señales."""

    def test_crear_paciente_genera_auditoria(self):
        # "CREAR", no "crear". Este test exigia el nombre antiguo, que era
        # justamente el fallo: el signal escribia en minusculas saltandose
        # `canonica()`, y convivian 17.929 'CREAR' con 15.681 'crear' para el
        # mismo hecho. Quien filtrara por el nombre canonico se dejaba fuera
        # casi la mitad de los registros.
        p = _paciente()
        reg = RegistroAuditoria.objects.filter(
            accion="CREAR", registro_id=str(p.id),
        ).first()
        self.assertIsNotNone(reg, "Crear un paciente debe generar un registro de auditoría")
        self.assertIsNotNone(reg.fecha)  # cuándo
        self.assertTrue(reg.modulo)      # sobre qué módulo

    def test_editar_paciente_genera_auditoria_editar(self):
        # "EDITAR", no "actualizar". Era el peor de los dos nombres legados:
        # habia 1.123 ediciones guardadas como 'actualizar' y CERO como
        # 'EDITAR', asi que filtrar por el nombre canonico devolvia nada y
        # parecia que nunca se hubiera modificado ningun dato de ninguna
        # paciente.
        p = _paciente("AUD002")
        p.telefono = "77712345"
        p.save()
        self.assertTrue(
            RegistroAuditoria.objects.filter(accion="EDITAR", registro_id=str(p.id)).exists(),
        )

    def test_eliminar_paciente_genera_auditoria(self):
        # "DESACTIVAR", no "eliminar". Habia 3.390 registros con el nombre
        # legado, y dar de baja una paciente se guardaba unas veces como
        # 'eliminar' y otras como 'DESACTIVAR_PACIENTE': ninguna consulta las
        # encontraba todas.
        p = _paciente("AUD003")
        pid = p.id
        p.delete()
        self.assertTrue(
            RegistroAuditoria.objects.filter(accion="DESACTIVAR", registro_id=str(pid)).exists(),
        )

    def test_auditoria_registra_accion_semantica_no_get(self):
        """La acción registrada es semántica (CREAR/EDITAR/DESACTIVAR), nunca
        un verbo HTTP como GET, y siempre con el nombre canónico."""
        _paciente("AUD004")
        acciones = set(RegistroAuditoria.objects.values_list("accion", flat=True))
        self.assertIn("CREAR", acciones)
        self.assertNotIn("crear", acciones)
        self.assertNotIn("GET", acciones)
        self.assertNotIn("get", acciones)


class AuditoriaLoginTest(TestCase):
    """Login exitoso y fallido quedan registrados."""

    def test_login_exitoso_auditado(self):
        u = _usuario("login@test.bo")
        RegistroAuditoria.registrar(
            usuario=u, accion="LOGIN", modulo="Usuario",
            registro_id=str(u.id), detalle="Login exitoso",
        )
        reg = RegistroAuditoria.objects.filter(accion="LOGIN", usuario=u).first()
        self.assertIsNotNone(reg)
        self.assertEqual(reg.usuario, u)
        self.assertIsNotNone(reg.fecha)

    def test_login_fallido_auditado(self):
        RegistroAuditoria.registrar(
            usuario=None, accion="LOGIN_FALLIDO", modulo="Usuario",
            detalle="Contraseña incorrecta para desconocido@test.bo",
        )
        self.assertTrue(RegistroAuditoria.objects.filter(accion="LOGIN_FALLIDO").exists())


class AuditoriaInmutabilidadTest(TestCase):
    """El registro de auditoría no se puede borrar ni alterar (integridad legal)."""

    def test_no_se_puede_eliminar_registro(self):
        u = _usuario("inmut@test.bo")
        reg = RegistroAuditoria.registrar(usuario=u, accion="LOGIN", modulo="Usuario")
        pk = reg.pk
        try:
            reg.delete()
        except Exception:
            pass  # se espera que el delete esté bloqueado
        self.assertTrue(
            RegistroAuditoria.objects.filter(pk=pk).exists(),
            "El registro de auditoría no debe poder eliminarse",
        )

    def test_registro_tiene_checksum(self):
        u = _usuario("checksum@test.bo")
        reg = RegistroAuditoria.registrar(usuario=u, accion="LOGIN", modulo="Usuario")
        self.assertTrue(reg.checksum, "Cada registro debe llevar checksum de integridad")

    def test_usuario_desnormalizado_preserva_historial(self):
        """Si el usuario se elimina, el nombre queda para el historial."""
        u = _usuario("desnorm@test.bo")
        reg = RegistroAuditoria.registrar(usuario=u, accion="LOGIN", modulo="Usuario")
        self.assertTrue(reg.usuario_nombre)


class AuditoriaPiiTest(TestCase):
    """La PII del paciente se redacta en el snapshot de auditoría."""

    def test_pii_redactada_en_datos(self):
        p = _paciente("AUD005")
        reg = RegistroAuditoria.objects.filter(accion="CREAR", registro_id=str(p.id)).first()
        self.assertIsNotNone(reg)
        datos = reg.datos_nuevos or {}
        # El CI real no debe quedar en claro en la auditoría.
        if "ci" in datos:
            self.assertNotEqual(datos.get("ci"), "AUD005")
