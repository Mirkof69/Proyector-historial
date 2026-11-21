"""Cargos del hospital: otros funcionarios sin programar, y sin abrir huecos.

Fallos que previene:
- La pantalla «Roles y permisos» guardaba permisos que ningún código leía
  (`CatRol.permisos`): el administrador creía restringir algo y no cambiaba nada.
- Un cargo que AGREGARA módulos a su rol saltaría la regla del backend
  (core/permissions.py); por eso solo puede quitarlos.
- Ocultar un módulo en la pantalla sin bloquearlo en la API: la API lo rechaza.
"""
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from auditoria.models import RegistroAuditoria
from roles.models import Cargo
from usuarios.models import Usuario
from usuarios.permisos_por_rol import nombre_grupo, permisos_de_usuario, sincronizar_grupos
from usuarios.serializers import UsuarioCreateUpdateSerializer

CLAVE = "clave-segura-123"


def _usuario(email, rol="medico", cargo=None):
    return Usuario.objects.create_user(email=email, nombre="N", apellido_paterno="A",
                                       password=CLAVE, rol=rol, cargo=cargo)


def _cliente(usuario):
    """Con token real: así pasa por la autenticación, donde se aplica el cargo."""
    cliente = APIClient()
    cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(usuario).access_token}")
    return cliente


def _permisos(usuario):
    """Lo que recibe el frontend al entrar (login y verificación MFA)."""
    return set(permisos_de_usuario(Usuario.objects.get(pk=usuario.pk)))


class CargoModeloTest(TestCase):
    def test_un_cargo_no_puede_agregar_modulos_a_su_rol(self):
        """ESPERADO: recepción con laboratorio se rechaza. OBTENIDO: ValidationError en «modulos»."""
        with self.assertRaises(ValidationError) as error:
            Cargo.objects.create(nombre="Admisión", rol_base="recepcion", modulos=["citas", "laboratorio"])
        self.assertIn("modulos", error.exception.message_dict)

    def test_administrador_no_es_rol_base(self):
        with self.assertRaises(ValidationError):
            Cargo.objects.create(nombre="Director", rol_base="administrador", modulos=[])

    def test_pacientes_y_notificaciones_siempre_quedan(self):
        cargo = Cargo.objects.create(nombre="Caja", rol_base="recepcion", modulos=["citas"])
        self.assertEqual(cargo.modulos, ["pacientes", "citas", "notificaciones"])


class CargoPermisosTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        sincronizar_grupos()
        cls.obstetriz = Cargo.objects.create(
            nombre="Obstetriz", rol_base="medico",
            modulos=["embarazos", "controles", "ecografias", "partos", "citas"])

    def test_el_usuario_toma_el_rol_base_y_solo_los_modulos_del_cargo(self):
        """ESPERADO: rol médico (y su grupo); ve partos y controles, no laboratorio ni IA."""
        usuario = _usuario("obst@test.bo", rol="recepcion", cargo=self.obstetriz)
        self.assertEqual(Usuario.objects.get(pk=usuario.pk).rol, "medico")
        perms = _permisos(usuario)
        self.assertIn("add_parto", perms)
        self.assertIn("add_controlprenatal", perms)
        self.assertNotIn("view_examenlaboratorio", perms)
        self.assertNotIn("view_imagenecografica", perms)   # IA médica
        self.assertEqual([g.name for g in usuario.groups.all()], [nombre_grupo("medico")])

    def test_el_detalle_del_usuario_tampoco_muestra_los_modulos_quitados(self):
        from usuarios.serializers import UsuarioDetailSerializer

        usuario = _usuario("obst.det@test.bo", cargo=self.obstetriz)
        apps = {p["app_label"] for p in UsuarioDetailSerializer(usuario).data["permisos"]}
        self.assertIn("partos", apps)
        self.assertNotIn("laboratorio", apps)

    def test_la_api_rechaza_el_modulo_que_el_cargo_no_incluye(self):
        """ESPERADO: laboratorio 403 con el nombre del cargo; partos 200."""
        cliente = _cliente(_usuario("obst.api@test.bo", cargo=self.obstetriz))
        respuesta = cliente.get("/api/laboratorios/examenes/")
        self.assertEqual(respuesta.status_code, 403)
        self.assertIn("Obstetriz", str(respuesta.data["detail"]))
        self.assertEqual(cliente.get("/api/partos/").status_code, 200)

    def test_sin_cargo_nada_cambia(self):
        self.assertEqual(_cliente(_usuario("med@test.bo")).get("/api/laboratorios/examenes/").status_code, 200)

    def test_cambiar_el_rol_base_cambia_el_rol_de_sus_usuarios(self):
        usuario = _usuario("obst.cambio@test.bo", cargo=self.obstetriz)
        self.obstetriz.rol_base = "enfermera"
        self.obstetriz.modulos = ["controles", "citas"]
        self.obstetriz.save()
        usuario.refresh_from_db()
        self.assertEqual(usuario.rol, "enfermera")
        self.assertNotIn("add_parto", _permisos(usuario))

    def test_un_cargo_desactivado_no_se_asigna_a_nadie_mas(self):
        self.obstetriz.activo = False
        self.obstetriz.save()
        datos = {"email": "nueva@test.bo", "nombre": "N", "apellido_paterno": "A", "password": CLAVE + "X!",
                 "password_confirm": CLAVE + "X!", "cargo": self.obstetriz.pk}
        serializer = UsuarioCreateUpdateSerializer(data=datos)
        self.assertFalse(serializer.is_valid())
        self.assertIn("cargo", serializer.errors)

    def test_con_cargo_no_hace_falta_mandar_el_rol(self):
        datos = {"email": "sinrol@test.bo", "nombre": "N", "apellido_paterno": "A", "password": CLAVE + "X!",
                 "password_confirm": CLAVE + "X!", "cargo": self.obstetriz.pk}
        serializer = UsuarioCreateUpdateSerializer(data=datos)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.save().rol, "medico")


class CargoApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        sincronizar_grupos()
        cls.admin = _usuario("admin.cargos@test.bo", rol="administrador")

    def test_solo_el_administrador_crea_cargos(self):
        datos = {"nombre": "Nutricionista", "rol_base": "enfermera", "modulos": ["controles", "citas"]}
        self.assertEqual(_cliente(_usuario("med.c@test.bo")).post("/api/roles/cargos/", datos, format="json")
                         .status_code, 403)
        respuesta = _cliente(self.admin).post("/api/roles/cargos/", datos, format="json")
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        self.assertEqual(respuesta.data["modulos"], ["pacientes", "controles", "citas", "notificaciones"])
        self.assertTrue(RegistroAuditoria.objects.filter(modulo="Cargos", accion="CREAR").exists())

    def test_la_api_rechaza_modulos_ajenos_con_mensaje(self):
        respuesta = _cliente(self.admin).post(
            "/api/roles/cargos/", {"nombre": "Caja", "rol_base": "recepcion", "modulos": ["partos"]}, format="json")
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("Partos", str(respuesta.data["modulos"]))

    def test_modulos_elegibles_por_rol(self):
        datos = _cliente(self.admin).get("/api/roles/cargos/modulos/").data
        self.assertEqual([r["rol"] for r in datos], ["medico", "enfermera", "laboratorista", "recepcion"])
        recepcion = {m["modulo"]: m for m in datos[3]["modulos"]}
        self.assertTrue(recepcion["pacientes"]["obligatorio"])
        self.assertNotIn("partos", recepcion)

    def test_un_cargo_con_usuarios_no_se_borra(self):
        cargo = Cargo.objects.create(nombre="Archivo", rol_base="recepcion", modulos=["citas"])
        _usuario("archivo@test.bo", cargo=cargo)
        respuesta = _cliente(self.admin).delete(f"/api/roles/cargos/{cargo.pk}/")
        self.assertEqual(respuesta.status_code, 409)
        self.assertTrue(Cargo.objects.filter(pk=cargo.pk).exists())
