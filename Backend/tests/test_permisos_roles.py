"""Tests del sistema de permisos por rol (RBAC).

Por qué existe este archivo
---------------------------
`RolPermiso` calculaba el nivel mínimo exigido como el **máximo** de los
niveles de los roles permitidos:

    self._nivel_minimo = max(_ROLE_HIERARCHY.get(r, 0) for r in roles_requeridos)

Como "administrador" (nivel 100) aparece en casi todas las tuplas, el mínimo
exigido acababa siendo 100 SIEMPRE. Un médico (80) fallaba la comprobación
`nivel >= 100` aunque su rol estuviera explícitamente en la lista de
permitidos. El efecto en la clínica:

  - `triaje` — enfermería no podía registrar un triaje
  - `evoluciones` — los médicos no podían escribir notas de evolución
  - `consultorios` — los médicos no podían gestionarlos
  - `laboratorio` (resultados) — ni médicos ni laboratoristas
  - `auditoria` — los médicos no podían consultarla

Es decir: solo el administrador podía usar esos cinco módulos, aunque los
permisos declaraban otra cosa. El nombre de la variable, `_nivel_minimo`, dice
exactamente lo que debía calcularse: el mínimo.

Cada test declara el resultado ESPERADO y lo compara con el OBTENIDO.
"""

from django.test import TestCase

from core.permissions import (
    EsMedicoOEnfermera,
    EsMedicoOEnfermeraOLaboratorista,
    EsSoloAdministrador,
    EsSoloMedico,
    PuedeVerAuditoria,
)
from usuarios.models import Usuario


class _Peticion:
    """Petición mínima: `has_permission` solo mira `request.user`."""

    def __init__(self, user):
        self.user = user


def _usuario(rol, correo):
    return Usuario.objects.create_user(
        email=correo,
        nombre="Prueba",
        apellido_paterno="Rol",
        password="clave-de-prueba-123",
        rol=rol,
    )


class PermisosPorRolTest(TestCase):
    """Cada rol declarado como permitido tiene que poder entrar."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = _usuario("administrador", "admin@rol.test")
        cls.medico = _usuario("medico", "medico@rol.test")
        cls.enfermera = _usuario("enfermera", "enfermera@rol.test")
        cls.laboratorista = _usuario("laboratorista", "lab@rol.test")
        cls.recepcion = _usuario("recepcion", "recepcion@rol.test")

    def _permite(self, permiso, usuario):
        return permiso.has_permission(_Peticion(usuario), view=None)

    def test_el_medico_puede_ver_la_auditoria(self):
        """ESPERADO: True — el permiso declara ('medico', 'administrador')."""
        assert self._permite(PuedeVerAuditoria, self.medico) is True, (
            "Un médico no puede consultar la auditoría pese a estar en la lista "
            "de roles permitidos."
        )

    def test_la_enfermera_puede_registrar_triaje(self):
        """ESPERADO: True — `EsMedicoOEnfermera` la incluye.

        Sin esto, enfermería no puede hacer triaje: el trabajo que más hace.
        """
        assert self._permite(EsMedicoOEnfermera, self.enfermera) is True

    def test_el_medico_puede_escribir_evoluciones(self):
        """ESPERADO: True — `EsMedicoOEnfermera` incluye a los médicos."""
        assert self._permite(EsMedicoOEnfermera, self.medico) is True

    def test_el_medico_puede_gestionar_consultorios(self):
        """ESPERADO: True — `EsSoloMedico` es ('medico', 'administrador')."""
        assert self._permite(EsSoloMedico, self.medico) is True

    def test_el_laboratorista_puede_cargar_resultados(self):
        """ESPERADO: True — su rol está en la tupla permitida."""
        assert self._permite(EsMedicoOEnfermeraOLaboratorista, self.laboratorista) is True

    def test_el_administrador_puede_todo(self):
        """ESPERADO: True en los cinco permisos."""
        for permiso in (
            PuedeVerAuditoria,
            EsSoloMedico,
            EsMedicoOEnfermera,
            EsMedicoOEnfermeraOLaboratorista,
            EsSoloAdministrador,
        ):
            assert self._permite(permiso, self.admin) is True


class PermisosSiguenNegandoTest(TestCase):
    """Arreglar el permiso no puede abrir la puerta a quien no debe pasar."""

    @classmethod
    def setUpTestData(cls):
        cls.medico = _usuario("medico", "medico2@rol.test")
        cls.enfermera = _usuario("enfermera", "enfermera2@rol.test")
        cls.recepcion = _usuario("recepcion", "recepcion2@rol.test")

    def _permite(self, permiso, usuario):
        return permiso.has_permission(_Peticion(usuario), view=None)

    def test_recepcion_no_ve_la_auditoria(self):
        """ESPERADO: False — recepción no está en la tupla."""
        assert self._permite(PuedeVerAuditoria, self.recepcion) is False

    def test_recepcion_no_escribe_evoluciones(self):
        """ESPERADO: False — no es personal clínico."""
        assert self._permite(EsMedicoOEnfermera, self.recepcion) is False

    def test_la_enfermera_no_gestiona_consultorios(self):
        """ESPERADO: False — `EsSoloMedico` no la incluye."""
        assert self._permite(EsSoloMedico, self.enfermera) is False

    def test_el_medico_no_es_administrador(self):
        """ESPERADO: False — un médico no accede a lo reservado al admin."""
        assert self._permite(EsSoloAdministrador, self.medico) is False

    def test_un_usuario_sin_rol_no_pasa(self):
        """ESPERADO: False en todos los permisos."""
        sin_rol = Usuario.objects.create_user(
            email="sinrol@rol.test",
            nombre="Sin",
            apellido_paterno="Rol",
            password="clave-de-prueba-123",
        )
        sin_rol.rol = ""
        for permiso in (PuedeVerAuditoria, EsSoloMedico, EsMedicoOEnfermera):
            assert self._permite(permiso, sin_rol) is False

    def test_un_anonimo_no_pasa(self):
        """ESPERADO: False — sin autenticar no hay rol que comprobar."""

        class Anonimo:
            is_authenticated = False
            rol = "administrador"  # aunque mienta sobre su rol

        assert self._permite(PuedeVerAuditoria, Anonimo()) is False
