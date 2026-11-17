r"""Depura de la base los datos sintéticos QA que crearon las pruebas (borrado físico). Por defecto SOLO CUENTA.

La baja lógica que hace cada corrida no oculta a las pacientes QA de los listados ni de las cifras de la clínica.
Esta herramienta las quita de verdad, junto con todo lo que cuelga de ellas (embarazos, controles, ecografías,
laboratorio, triajes, citas, partos, alertas, notas, vacunas, antecedentes).

Se ejecuta con el Python del sistema (necesita sus modelos), desde la carpeta Backend:

    cd ..\Backend
    .venv\Scripts\python manage.py shell -c "exec(open(r'..\automatizacion\tools\purgar_qa.py', encoding='utf-8').read())"

Para borrar hay que pedirlo de forma explícita con la variable de entorno PURGAR_QA=SI y tener un respaldo
reciente (RESPALDO_DIARIO.bat). Sin esa variable solo informa lo que borraría.

Qué se considera dato QA (deben cumplirse LAS TRES condiciones):
  1. el nombre empieza con «QA »;
  2. la cédula empieza con 99 y tiene 9 dígitos (las cédulas reales de la clínica tienen 7);
  3. la paciente se registró después del inicio de la automatización (13/11/2026 22:00).
"""
import datetime
import os

from django.contrib.admin.utils import NestedObjects
from django.db import router, transaction
from django_tenants.utils import schema_context

from pacientes.models import Paciente

INICIO = datetime.datetime(2026, 11, 13, 22, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=-4)))

with schema_context("clinica"):
    candidatas = Paciente.objects.filter(fecha_registro__gte=INICIO)
    qa = [p for p in candidatas if str(p.nombre).startswith("QA ") and str(p.ci).startswith("99") and len(str(p.ci)) == 9]
    reales = Paciente.objects.count() - len(qa)
    print(f"Pacientes en la base: {Paciente.objects.count()} | QA a depurar: {len(qa)} | quedarían: {reales}")
    colector = NestedObjects(using=router.db_for_write(Paciente))
    colector.collect(qa)
    por_modelo = {}
    for modelo, objetos in colector.model_objs.items():
        por_modelo[modelo._meta.label] = len(objetos)
    for etiqueta, n in sorted(por_modelo.items(), key=lambda x: -x[1]):
        print(f"  {etiqueta}: {n}")
    if colector.protected:
        print(f"  PROTEGIDOS (impiden el borrado): {len(colector.protected)} · {sorted({type(o).__name__ for o in colector.protected})}")
    if os.environ.get("PURGAR_QA") != "SI":
        print("Solo conteo. Para borrar: respaldo reciente y PURGAR_QA=SI.")
    elif colector.protected:
        print("No se borra: hay registros protegidos. Revise la lista anterior.")
    else:
        with transaction.atomic():
            ids = [p.id for p in qa]
            borrados, detalle = Paciente.objects.filter(id__in=ids).delete()
            if Paciente.objects.count() != reales:
                raise RuntimeError("El total de pacientes no coincide con lo esperado: se revierte todo")
        print(f"Depurado: {borrados} registros. Pacientes en la base: {Paciente.objects.count()}")
        for etiqueta, n in sorted(detalle.items(), key=lambda x: -x[1]):
            print(f"  {etiqueta}: {n}")
