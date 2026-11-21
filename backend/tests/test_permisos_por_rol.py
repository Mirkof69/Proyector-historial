"""Cada rol recibe los permisos de su tabla, y el frontend no pide permisos inexistentes.

Fallos que previene:
- En la base no había grupos ni permisos: un médico entraba y casi no veía
  pantallas; solo el administrador usaba el sistema.
- El frontend pedía 10 permisos que no existen (`view_calculoclinico`,
  `view_accesslog`…): esas pantallas solo las veía el superusuario.
"""
import re
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import Permission
from django.test import TestCase

from usuarios.models import Usuario
from usuarios.permisos_por_rol import sincronizar_grupos

FRONT = Path(settings.FRONTEND_DIR) / "src"
ARCHIVOS_CON_PERMISOS = [
    FRONT / "routes" / "AppRoutes.tsx",
    FRONT / "components" / "layout" / "mainMenuItems.tsx",
    FRONT / "pages" / "Dashboard" / "DashboardHome.tsx",
]


def _permisos(usuario):
    return {p.split(".")[1] for p in Usuario.objects.get(pk=usuario.pk).get_all_permissions()}


class PermisosPorRolTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        sincronizar_grupos()

    def _crear(self, rol, email):
        return Usuario.objects.create_user(email=email, nombre="N", apellido_paterno="A",
                                           password="clave-segura-123", rol=rol)

    def test_un_medico_nuevo_ve_lo_clinico_sin_asignar_nada_a_mano(self):
        medico = self._crear("medico", "m.rol@test.bo")
        perms = _permisos(medico)
        for p in ("view_paciente", "add_embarazo", "view_parto", "add_ecografia", "view_reciennacido"):
            self.assertIn(p, perms)
        self.assertNotIn("delete_paciente", perms)   # borrar es cosa del administrador

    def test_la_configuracion_del_sistema_es_solo_del_administrador(self):
        perms = _permisos(self._crear("medico", "m.conf@test.bo"))
        self.assertNotIn("view_sistemaconfiguracion", perms)
        self.assertNotIn("change_configuracionmodeloia", perms)
        self.assertIn("view_reportegenerado", perms)   # el resto de reportes sí

    def test_enfermeria_no_tiene_partos_ni_reportes(self):
        """Igual que el backend (FetalMedicalPermission le bloquea /api/partos y /api/reportes)."""
        perms = _permisos(self._crear("enfermera", "e.rol@test.bo"))
        self.assertIn("add_controlprenatal", perms)
        self.assertNotIn("view_parto", perms)
        self.assertNotIn("view_reportegenerado", perms)

    def test_recepcion_solo_pacientes_y_citas(self):
        perms = _permisos(self._crear("recepcion", "r.rol@test.bo"))
        self.assertIn("add_paciente", perms)
        self.assertIn("add_cita", perms)
        self.assertNotIn("view_controlprenatal", perms)
        self.assertNotIn("view_ecografia", perms)

    def test_al_cambiar_de_rol_cambian_los_permisos(self):
        u = self._crear("medico", "cambio.rol@test.bo")
        u.rol = "recepcion"
        u.save()
        perms = _permisos(u)
        self.assertNotIn("view_parto", perms)
        self.assertIn("view_cita", perms)

    def test_todo_permiso_que_pide_el_frontend_existe(self):
        pedidos = set()
        for archivo in ARCHIVOS_CON_PERMISOS:
            pedidos |= set(re.findall(r"\b(?:view|add|change|delete)_[a-z]+\b", archivo.read_text(encoding="utf-8")))
        self.assertGreater(len(pedidos), 30)
        existentes = set(Permission.objects.values_list("codename", flat=True))
        self.assertEqual(sorted(pedidos - existentes), [])


class SincronizarTrasMigrarTest(TestCase):
    """Tras re-sembrar la demo (esquema nuevo + migrate), los 4 grupos por rol
    quedaron con 0 permisos y un médico veía «Acceso restringido» en Pacientes.

    Causa: se sincronizaba en el post_migrate de la app «usuarios», antes de que
    Django creara los permisos de las apps que van detrás en INSTALLED_APPS.
    ESPERADO: la sincronización corre con la ÚLTIMA app, cuando ya existen todos.
    """

    def test_solo_sincroniza_al_terminar_la_ultima_app(self):
        from unittest.mock import patch

        from django.apps import apps

        from usuarios import signals

        con_modelos = [a for a in apps.get_app_configs() if a.models_module is not None]
        with patch.object(signals, "sincronizar_grupos") as sincronizar:
            signals.sincronizar_tras_migrar(sender=apps.get_app_config("usuarios"))
            sincronizar.assert_not_called()
            signals.sincronizar_tras_migrar(sender=con_modelos[-1])
            sincronizar.assert_called_once()

    def test_grupos_vacios_se_reparan_al_migrar(self):
        from django.apps import apps
        from django.contrib.auth.models import Group

        from usuarios import signals

        sincronizar_grupos()
        Group.objects.get(name="Rol: medico").permissions.clear()
        con_modelos = [a for a in apps.get_app_configs() if a.models_module is not None]
        signals.sincronizar_tras_migrar(sender=con_modelos[-1])
        self.assertGreater(Group.objects.get(name="Rol: medico").permissions.count(), 50)
