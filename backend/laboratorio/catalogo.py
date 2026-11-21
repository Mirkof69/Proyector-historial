"""Catálogo de tipos de examen del laboratorio: una sola fuente de códigos.

Por qué existe
--------------
Los rangos de referencia (comando `poblar_valores_referencia`) buscaban cada
examen con `TipoExamen.objects.get(codigo="HEM001")`, pero nadie creaba esos
tipos: el comando no cargaba NADA y, sin parámetros, ningún resultado de
laboratorio se podía registrar ni importar (cada resultado apunta a un
parámetro con su rango). Además la demo usaba otros códigos («HEM-001»).

Aquí están los tipos con el código que usan los rangos, y
`asegurar_tipos_examen()` los crea si faltan (idempotente).
"""
from __future__ import annotations

from decimal import Decimal

#: código -> (nombre, categoría, horas hasta el resultado, preparación)
TIPOS_EXAMEN: dict[str, tuple[str, str, int, str]] = {
    "HEM001": ("Hemograma completo", "hematologia", 24, "Sin preparación especial"),
    "HEM002": ("Coagulación (TP/INR, TTPa, fibrinógeno, dímero D)", "hematologia", 24, "Sin preparación especial"),
    "BIO001": ("Glucemia en ayunas", "bioquimica", 12, "Ayuno de 8 horas"),
    "BIO002": ("Curva de tolerancia a la glucosa (PTOG 75 g)", "bioquimica", 24, "Ayuno de 8 horas"),
    "BIO003": ("Perfil lipídico", "bioquimica", 24, "Ayuno de 12 horas"),
    "BIO004": ("Función renal (urea, creatinina, ácido úrico)", "bioquimica", 24, "Sin preparación especial"),
    "BIO005": ("Calcio sérico", "bioquimica", 24, "Sin preparación especial"),
    "BIO006": ("Función hepática", "bioquimica", 24, "Ayuno de 8 horas"),
    "HOR001": ("β-hCG cuantitativa", "hormonal", 24, "Sin preparación especial"),
    "HOR002": ("Perfil tiroideo (TSH, T3, T4 libre)", "hormonal", 48, "Sin preparación especial"),
    "HOR003": ("FSH", "hormonal", 48, "Día 3 del ciclo si no hay embarazo"),
    "HOR004": ("LH", "hormonal", 48, "Día 3 del ciclo si no hay embarazo"),
    "HOR005": ("Estradiol", "hormonal", 48, "Sin preparación especial"),
    "HOR006": ("Progesterona", "hormonal", 48, "Sin preparación especial"),
    "HOR007": ("Prolactina", "hormonal", 48, "Reposo de 30 minutos antes de la muestra"),
    "HOR008": ("Hormona antimülleriana (AMH)", "hormonal", 72, "Sin preparación especial"),
    "SER001": ("Grupo sanguíneo y factor Rh", "inmunologia", 24, "Sin preparación especial"),
    "SER002": ("VIH (prueba de tamizaje)", "serologia", 24, "Consentimiento informado"),
    "SER003": ("VDRL / sífilis", "serologia", 48, "Sin preparación especial"),
    "SER004": ("Panel TORCH", "serologia", 72, "Sin preparación especial"),
    "SER005": ("CA-125", "serologia", 72, "Sin preparación especial"),
    "SER006": ("Alfafetoproteína (AFP)", "serologia", 72, "Sin preparación especial"),
    "SER007": ("Hepatitis B (HBsAg)", "serologia", 48, "Sin preparación especial"),
    "SER008": ("HE4", "serologia", 72, "Sin preparación especial"),
    "SER009": ("Antígeno carcinoembrionario (CEA)", "serologia", 72, "Sin preparación especial"),
    "SER010": ("Hepatitis C (anti-VHC)", "serologia", 48, "Sin preparación especial"),
    "MIC001": ("Cultivo de estreptococo del grupo B", "microbiologia", 72, "Hisopado vaginal y rectal, semana 35-37"),
    "MIC002": ("Chlamydia y gonorrea (PCR)", "microbiologia", 72, "Sin preparación especial"),
    "URI001": ("Examen general de orina", "urinalisis", 12, "Primera orina de la mañana"),
    "CIT001": ("Papanicolaou (citología cervical)", "citologia", 168, "Sin duchas vaginales 48 horas antes"),
}

#: Panel prenatal de rutina (MSP Bolivia): lo que pide la demo y un control habitual.
PANEL_PRENATAL = ["HEM001", "BIO001", "SER001", "URI001", "SER003", "SER002"]


def asegurar_tipos_examen(usuario=None) -> int:
    """Crea los tipos de examen que falten. Devuelve cuántos creó."""
    from .models import TipoExamen

    creados = 0
    for codigo, (nombre, categoria, horas, preparacion) in TIPOS_EXAMEN.items():
        # `nombre` es único: si el examen ya existe con otro código (la demo
        # usaba «HEM-001»), se adopta y se le pone el código del catálogo. Los
        # exámenes de las pacientes apuntan al tipo por id, no por código.
        TipoExamen.objects.filter(nombre__iexact=nombre).exclude(codigo=codigo).update(codigo=codigo)
        _, nuevo = TipoExamen.objects.get_or_create(
            codigo=codigo,
            defaults={
                "nombre": nombre,
                "categoria": categoria,
                "descripcion": nombre,
                "preparacion": preparacion,
                "tiempo_resultado": horas,
                "precio": Decimal("0.00"),
                "activo": True,
                "created_by": usuario,
            },
        )
        creados += nuevo
    return creados
