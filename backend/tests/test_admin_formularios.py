"""Todos los formularios del admin se pueden abrir.

Fallo que previene: campos inexistentes en `fieldsets` (`fecha_finalizacion`,
`hijos_vivos`, `embarazo_id`, `plg`, `unidad`, `observaciones_generales`…) y
un `__init__` que leía `self.parto` sin parto. Django no los detecta al
arrancar: el admin de ese modelo da 500 al abrirlo. Se encontraron 7 así.
"""
from django.contrib import admin
from django.test import RequestFactory, TestCase

from usuarios.models import Usuario


class FormulariosDelAdminTest(TestCase):
    def test_todos_los_formularios_del_admin_se_construyen(self):
        """ESPERADO: ningún error al construir el formulario de alta de cada modelo."""
        superusuario = Usuario(is_superuser=True, is_staff=True, activo=True)
        errores = []
        for modelo, modelo_admin in admin.site._registry.items():
            peticion = RequestFactory().get("/")
            peticion.user = superusuario
            try:
                modelo_admin.get_form(peticion)()
                modelo_admin.get_fieldsets(peticion)
            except Exception as e:  # noqa: BLE001 - se reportan todos juntos
                errores.append(f"{modelo.__name__}: {type(e).__name__}: {e}")
        self.assertGreater(len(admin.site._registry), 50)
        self.assertEqual(errores, [], "\n".join(errores))
