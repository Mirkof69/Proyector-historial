"""Importación de pacientes desde Excel: plantilla, vista previa y alta.

Flujo: el usuario descarga la plantilla, la llena, la sube y ve fila por
fila qué se va a crear y qué tiene errores; recién al confirmar se crean las
filas válidas. Cada fila pasa por el MISMO serializer que el formulario, así
que una importación no puede saltarse ninguna validación (CI, teléfono,
consentimiento de la Ley 164...).
"""
from datetime import date, datetime
from io import BytesIO

from django.db import transaction
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from .fields import compute_search_hash
from .models import Paciente

MAX_FILAS = 2000
SI = {"si", "sí", "s", "yes", "y", "x", "1", "true", "verdadero"}

#: (campo, encabezado, obligatorio, ejemplo, ayuda)
COLUMNAS = [
    ("ci", "CI", True, "7894561", "Cédula de identidad, sin extensión."),
    ("nombre", "Nombre", True, "María", ""),
    ("apellido_paterno", "Apellido paterno", True, "Quispe", ""),
    ("apellido_materno", "Apellido materno", False, "Mamani", ""),
    ("fecha_nacimiento", "Fecha de nacimiento", True, "15/03/1995", "DD/MM/AAAA o fecha de Excel."),
    ("telefono", "Teléfono", False, "71234567", ""),
    ("email", "Correo", False, "maria@correo.bo", ""),
    ("direccion", "Dirección", False, "Av. Busch 123", ""),
    ("ciudad", "Ciudad", False, "La Paz", ""),
    ("ocupacion", "Ocupación", False, "Comerciante", ""),
    ("tipo_sangre", "Tipo de sangre", False, "O+", "A+, A-, B+, B-, O+, O-, AB+ o AB-."),
    ("contacto_emergencia_nombre", "Contacto de emergencia", False, "Juan Quispe", ""),
    ("contacto_emergencia_telefono", "Teléfono de emergencia", False, "72345678", ""),
    ("consentimiento_datos_aceptado", "Consentimiento firmado", True, "SI",
     "SI solo si la paciente firmó el consentimiento de datos (Ley 164). Sin él no se registra."),
]
ENCABEZADO_A_CAMPO = {encabezado.lower(): campo for campo, encabezado, *_ in COLUMNAS}


def generar_plantilla() -> bytes:
    libro = Workbook()
    hoja = libro.active
    hoja.title = "Pacientes"
    negrita, obligatorio = Font(bold=True), PatternFill("solid", fgColor="FDE68A")
    for col, (_, encabezado, oblig, ejemplo, _) in enumerate(COLUMNAS, start=1):
        celda = hoja.cell(row=1, column=col, value=encabezado + (" *" if oblig else ""))
        celda.font = negrita
        if oblig:
            celda.fill = obligatorio
        hoja.cell(row=2, column=col, value=ejemplo)
        hoja.column_dimensions[get_column_letter(col)].width = max(14, len(encabezado) + 4)
    hoja.freeze_panes = "A2"

    ayuda = libro.create_sheet("Instrucciones")
    ayuda.append(["Columna", "Obligatoria", "Cómo llenarla"])
    for celda in ayuda[1]:
        celda.font = negrita
    for _, encabezado, oblig, _, texto in COLUMNAS:
        ayuda.append([encabezado, "Sí" if oblig else "No", texto])
    ayuda.append([])
    ayuda.append(["La fila 2 de la hoja Pacientes es un ejemplo: bórrela antes de importar."])
    ayuda.append([f"Máximo {MAX_FILAS} filas por archivo. Las pacientes con un CI ya registrado se omiten."])
    ayuda.column_dimensions["A"].width = 28
    ayuda.column_dimensions["C"].width = 80

    salida = BytesIO()
    libro.save(salida)
    return salida.getvalue()


def _valor(v):
    if v is None:
        return ""
    if isinstance(v, datetime):
        return v.date().isoformat()
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def _fecha(texto: str) -> str:
    """Acepta DD/MM/AAAA, DD-MM-AAAA y AAAA-MM-DD; devuelve ISO o el texto tal cual."""
    for formato in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y"):
        try:
            return datetime.strptime(texto, formato).date().isoformat()
        except ValueError:
            continue
    return texto


def leer_filas(archivo) -> list[dict]:
    """Filas del Excel como {campo: texto}, con su número de fila. Lanza ValueError si el archivo no sirve."""
    try:
        libro = load_workbook(archivo, read_only=True, data_only=True)
    except Exception as e:
        raise ValueError("El archivo no es un Excel válido (.xlsx).") from e
    hoja = libro["Pacientes"] if "Pacientes" in libro.sheetnames else libro.worksheets[0]
    filas = hoja.iter_rows(values_only=True)
    encabezados = [(_valor(h).rstrip(" *").lower()) for h in next(filas, [])]
    campos = [ENCABEZADO_A_CAMPO.get(h) for h in encabezados]
    faltan = [enc for campo, enc, oblig, *_ in COLUMNAS if oblig and campo not in campos]
    if faltan:
        raise ValueError("Faltan columnas obligatorias: " + ", ".join(faltan) + ". Use la plantilla.")

    resultado = []
    for numero, fila in enumerate(filas, start=2):
        datos = {c: _valor(v) for c, v in zip(campos, fila, strict=False) if c}
        if not any(datos.values()):
            continue
        if len(resultado) >= MAX_FILAS:
            raise ValueError(f"El archivo tiene más de {MAX_FILAS} filas. Divídalo en varios.")
        if datos.get("fecha_nacimiento"):
            datos["fecha_nacimiento"] = _fecha(datos["fecha_nacimiento"])
        datos["consentimiento_datos_aceptado"] = datos.get("consentimiento_datos_aceptado", "").lower() in SI
        datos.setdefault("genero", "femenino")
        resultado.append({"fila": numero, "datos": datos})
    return resultado


def _errores_planos(errores) -> list[str]:
    planos = []
    for campo, mensajes in errores.items():
        nombre = next((enc for c, enc, *_ in COLUMNAS if c == campo), campo)
        for m in mensajes if isinstance(mensajes, list) else [mensajes]:
            planos.append(f"{nombre}: {m}")
    return planos


def procesar(filas: list[dict], contexto: dict, confirmar: bool) -> dict:
    """Valida cada fila; si `confirmar`, crea las válidas (cada una en su savepoint)."""
    from .serializers import PacienteCreateUpdateSerializer

    # El CI va cifrado (IV aleatorio): la comparación se hace por su hash.
    hashes = {f["datos"].get("ci", ""): compute_search_hash(f["datos"].get("ci", "")) for f in filas}
    existentes = set(Paciente.objects.filter(ci_hash__in=hashes.values()).values_list("ci_hash", flat=True))
    ci_existentes = {ci for ci, h in hashes.items() if h in existentes}
    vistos, salida = set(), []
    for f in filas:
        datos, ci = f["datos"], f["datos"].get("ci", "")
        fila = {"fila": f["fila"], "ci": ci,
                "nombre": " ".join(x for x in (datos.get("nombre"), datos.get("apellido_paterno"),
                                                datos.get("apellido_materno")) if x)}
        if ci and (ci in ci_existentes or ci in vistos):
            fila.update(estado="duplicada",
                        errores=["Ya existe una paciente con este CI" if ci in ci_existentes
                                 else "CI repetido en el archivo"])
            salida.append(fila)
            continue
        vistos.add(ci)
        serializer = PacienteCreateUpdateSerializer(data=datos, context=contexto)
        if not serializer.is_valid():
            fila.update(estado="error", errores=_errores_planos(serializer.errors))
        elif confirmar:
            try:
                with transaction.atomic():
                    paciente = serializer.save(created_by=contexto["request"].user)
                fila.update(estado="creada", errores=[], id=paciente.id, id_clinico=paciente.id_clinico)
            except Exception as e:  # una fila rota no tumba las demás
                fila.update(estado="error", errores=[f"No se pudo guardar: {e}"])
        else:
            fila.update(estado="valida", errores=[])
        salida.append(fila)

    cuenta = {e: sum(1 for f in salida if f["estado"] == e) for e in ("valida", "creada", "error", "duplicada")}
    return {"resumen": {"total": len(salida), **cuenta, "confirmado": confirmar}, "filas": salida}
