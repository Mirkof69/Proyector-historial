"""Tipos de reporte que «Generar reporte PDF» sabe producir.

Sin filas en TipoReporte la pantalla decía «No hay tipos de reporte
configurados» y no se podía generar nada. Los códigos coinciden con
reportes/services/generador_reportes.py::REPORTES.
"""
from django.db import migrations

TIPOS = [
    ("RPT-PACIENTES", "Pacientes registradas", "Listado de pacientes con edad, ciudad y número de embarazos.", "paciente", True),
    ("RPT-EMBARAZOS", "Embarazos y clasificación de riesgo", "Embarazos registrados con FUM, FPP, riesgo y estado.", "clinico", True),
    ("RPT-CONTROLES", "Controles prenatales", "Controles del período con signos vitales y alertas críticas.", "clinico", True),
    ("RPT-PARTOS", "Partos y recién nacidos", "Partos por tipo, edad gestacional, peso y Apgar del recién nacido.", "estadistico", True),
    ("RPT-CITAS", "Agenda y asistencia", "Citas del período por médico, tipo y estado.", "institucional", True),
    ("RPT-ALERTAS", "Alertas médicas", "Alertas clínicas generadas por controles y laboratorio, con su estado.", "clinico", True),
    ("RPT-LAB", "Laboratorio: valores fuera de rango", "Resultados anormales y críticos del período.", "clinico", True),
    ("RPT-INDICADORES", "Indicadores de gestión obstétrica", "Cobertura, calidad y resultados perinatales con su meta.", "institucional", False),
]


def crear(apps, _schema_editor):
    TipoReporte = apps.get_model("reportes", "TipoReporte")
    for codigo, nombre, descripcion, categoria, con_fechas in TIPOS:
        TipoReporte.objects.get_or_create(codigo=codigo, defaults={
            "nombre": nombre, "descripcion": descripcion, "categoria": categoria, "frecuencia": "bajo_demanda",
            "activo": True, "formato_pdf": True, "formato_excel": True, "formato_csv": True, "formato_json": True,
            "incluir_fecha_inicio": con_fechas, "incluir_fecha_fin": con_fechas,
            "permitir_medico": True, "permitir_administrador": True,
        })


def quitar(apps, _schema_editor):
    apps.get_model("reportes", "TipoReporte").objects.filter(codigo__in=[t[0] for t in TIPOS]).delete()


class Migration(migrations.Migration):
    dependencies = [("reportes", "0009_alter_dashboardkpi_categoria_and_more")]
    operations = [migrations.RunPython(crear, quitar)]
