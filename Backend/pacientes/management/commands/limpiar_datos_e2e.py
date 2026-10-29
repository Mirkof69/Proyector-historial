"""Borra los datos que crean las pruebas E2E (pacientes con apellido «E2E»).

Uso: python manage.py limpiar_datos_e2e --schema=clinica

Borra en orden (imágenes, ecografías, exámenes de laboratorio, controles,
partos, triajes, notas, vacunas, citas, antecedentes, embarazos, pacientes) porque la historia clínica está protegida contra el borrado en
cascada. Los exámenes quedan cuando una corrida se corta antes de deshacer
la importación del laboratorio. Los usuarios de prueba (correo @e2e.test)
no se borran —su auditoría es inmutable (Ley 164)—: se desactivan y se les
quita el cargo; luego se borran los cargos «E2E …». Nunca toca pacientes reales: solo las de apellido paterno «E2E».

Con --ci borra además la paciente de ese CI: la del guion de demostración
(Backend/e2e/guion), que se registra con nombre realista para ensayar en vivo.
"""
import os

from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context

from clientes.constantes import ESQUEMA_PRINCIPAL


class Command(BaseCommand):
    help = "Borra las pacientes de prueba E2E y toda su historia"

    def add_arguments(self, parser):
        parser.add_argument("--schema", default=ESQUEMA_PRINCIPAL)
        parser.add_argument("--ci", default="", help="CI de la paciente del guion de demostración")

    def handle(self, *args, **opciones):
        from antecedentes.models import (
            AntecedenteGinecoObstetrico,
            AntecedentePatologico,
        )
        from citas.models import Cita
        from consultorios.models import Consultorio
        from controles.models import ControlPrenatal
        from ecografias.models import Ecografia, ImagenEcografia
        from embarazos.models import Embarazo
        from laboratorio.models import ExamenLaboratorio, ResultadoLaboratorio
        from notas_evolucion.models import NotaEvolucion
        from notificaciones.models import Notificacion
        from pacientes.models import Paciente
        from partos.models import Parto
        from roles.models import Cargo
        from triaje.models import TriajeEnfermeria
        from usuarios.models import Usuario
        from vacunas.models import RegistroVacuna

        with schema_context(opciones["schema"]):
            # El apellido va cifrado: no se puede filtrar en la base, se compara
            # ya descifrado.
            ci = opciones["ci"]
            ids = [p.id for p in Paciente.objects.only("id", "apellido_paterno", "ci")
                   if p.apellido_paterno == "E2E" or (ci and p.ci == ci)]
            for imagen in ImagenEcografia.objects.filter(ecografia__paciente_id__in=ids):
                ruta = imagen.imagen.path if imagen.imagen else None
                imagen.delete()
                if ruta and os.path.exists(ruta):
                    os.remove(ruta)
            # Sus avisos también: si no, la campana llevaba a registros borrados.
            # Se anotan antes de borrar y se quitan al final, para llevarse
            # también los «Cita Eliminada» que el propio borrado genera.
            entidades = {
                "paciente": ids,
                "cita": list(Cita.objects.filter(paciente_id__in=ids).values_list("id", flat=True)),
                "embarazo": list(Embarazo.objects.filter(paciente_id__in=ids).values_list("id", flat=True)),
                "control": list(ControlPrenatal.objects.filter(paciente_id__in=ids).values_list("id", flat=True)),
                "examen": list(ExamenLaboratorio.objects.filter(paciente_id__in=ids).values_list("id", flat=True)),
                "resultado_laboratorio": list(ResultadoLaboratorio.objects.filter(
                    examen__paciente_id__in=ids).values_list("id", flat=True)),
            }
            cuentas = {
                "ecografías": Ecografia.objects.filter(paciente_id__in=ids).delete()[0],
                "exámenes": ExamenLaboratorio.objects.filter(paciente_id__in=ids).delete()[0],
                "controles": ControlPrenatal.objects.filter(paciente_id__in=ids).delete()[0],
                "partos": Parto.objects.filter(paciente_id__in=ids).delete()[0],
                "triajes": TriajeEnfermeria.objects.filter(paciente_id__in=ids).delete()[0],
                "notas": NotaEvolucion.objects.filter(paciente_id__in=ids).delete()[0],
                "vacunas": RegistroVacuna.objects.filter(paciente_id__in=ids).delete()[0],
                "citas": Cita.objects.filter(paciente_id__in=ids).delete()[0],
                # El triaje crea los antecedentes de la paciente al abrir sus datos clínicos.
                "antecedentes": AntecedentePatologico.objects.filter(paciente_id__in=ids).delete()[0]
                + AntecedenteGinecoObstetrico.objects.filter(paciente_id__in=ids).delete()[0],
                "embarazos": Embarazo.objects.filter(paciente_id__in=ids).delete()[0],
                "pacientes": Paciente.objects.filter(id__in=ids).delete()[0],
            }
            # Y los de registros que la propia prueba ya borró (no estaban para
            # anotarlos): el mensaje lleva el nombre de la paciente «… E2E …».
            avisos = Notificacion.objects.filter(mensaje__contains=" E2E ")
            for tipo, entidad_ids in entidades.items():
                avisos |= Notificacion.objects.filter(entidad_tipo=tipo, entidad_id__in=entidad_ids)
            cuentas["avisos"] = avisos.delete()[0]
            # Primero los usuarios: el cargo no se borra mientras alguien lo tenga.
            usuarios = list(Usuario.objects.filter(email__endswith="@e2e.test"))
            for usuario in usuarios:
                usuario.cargo, usuario.activo = None, False
                usuario.save()
            cuentas["usuarios desactivados"] = len(usuarios)
            cuentas["cargos"] = Cargo.objects.filter(nombre__startswith="E2E ").delete()[0]
            cuentas["consultorios"] = Consultorio.objects.filter(codigo__startswith="E2E").delete()[0]
        self.stdout.write(self.style.SUCCESS(f"Datos E2E borrados: {cuentas}"))
