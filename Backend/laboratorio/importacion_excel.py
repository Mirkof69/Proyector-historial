"""Importación de RESULTADOS de laboratorio desde Excel (.xlsx) o CSV.

Flujo (igual que la importación de pacientes): descargar la plantilla,
llenarla, subirla y ver fila por fila qué se va a guardar y qué tiene errores;
recién al confirmar se guarda.

El archivo del laboratorio no tiene por qué usar la plantilla: los
encabezados se reconocen por sinónimos («Cédula», «Carnet», «Resultado»…) y,
si falta alguno obligatorio, la API devuelve los encabezados del archivo para
que el usuario diga qué columna es cada dato (`mapeo`). Un CSV puede venir
separado por coma, punto y coma o tabulador, en UTF-8 o Latin-1.

Cada importación confirmada queda registrada (ImportacionLaboratorio) con lo
que creó, y se puede deshacer entera.

Una fila = un parámetro de un examen («CI 7894561, HEM001, 12/09/2026,
Hemoglobina, 11.8»). Las filas con la misma paciente, examen y fecha forman UN
examen completado con todos sus resultados. Cada valor se evalúa contra su
rango de referencia (normal / anormal / crítico) igual que si se cargara a
mano, y un examen se guarda entero o no se guarda.
"""
from __future__ import annotations

import csv
import io
import re
import unicodedata
from collections import OrderedDict
from datetime import datetime, time
from decimal import Decimal, InvalidOperation
from io import BytesIO

from django.db import transaction
from django.utils import timezone
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

MAX_FILAS = 5000

#: (campo, encabezado, obligatorio, ejemplo, ayuda)
COLUMNAS = [
    ("ci", "CI de la paciente", True, "7894561", "La paciente tiene que estar registrada."),
    ("codigo", "Código de examen", True, "HEM001", "Ver la hoja «Catálogo»."),
    ("fecha", "Fecha del resultado", True, "12/09/2026", "DD/MM/AAAA o fecha de Excel. No puede ser futura."),
    ("parametro", "Parámetro", True, "Hemoglobina", "Tal como aparece en la hoja «Catálogo»."),
    ("valor", "Valor", True, "11.8", "Número (con punto o coma) o texto si el parámetro es cualitativo."),
    ("observaciones", "Observaciones", False, "", ""),
]
ENCABEZADO_A_CAMPO = {enc.lower(): campo for campo, enc, *_ in COLUMNAS}
#: Otros nombres con que los laboratorios llaman a cada columna (sin tildes, en minúsculas).
SINONIMOS = {
    "ci": ("ci", "ci de la paciente", "cedula", "cedula de identidad", "carnet", "carnet de identidad",
           "documento", "nro documento", "ci paciente"),
    "codigo": ("codigo de examen", "codigo", "cod examen", "cod", "codigo examen"),
    "fecha": ("fecha del resultado", "fecha", "fecha resultado", "fecha de resultado", "fecha muestra"),
    "parametro": ("parametro", "analito", "prueba", "determinacion", "item"),
    "valor": ("valor", "resultado", "valor obtenido"),
    "observaciones": ("observaciones", "observacion", "obs", "comentario", "comentarios", "nota"),
}


class MapeoIncompleto(ValueError):
    """Falta identificar columnas obligatorias: hay que pedirle el mapeo al usuario."""

    def __init__(self, encabezados: list[str], sugerido: dict[str, str], faltan: list[str]):
        super().__init__("Faltan columnas obligatorias: " + ", ".join(faltan))
        self.encabezados, self.sugerido, self.faltan = encabezados, sugerido, faltan


def _normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9]", " ", sin_tildes).split())


def mapeo_automatico(encabezados: list[str]) -> dict[str, str]:
    """{campo: encabezado del archivo} para los que se reconocen."""
    mapeo = {}
    for enc in encabezados:
        n = _normalizar(enc)
        for campo, nombres in SINONIMOS.items():
            if campo not in mapeo and n in nombres:
                mapeo[campo] = enc
    return mapeo


def leer_tabla(archivo, nombre: str = "") -> tuple[list[str], list[tuple]]:
    """(encabezados, filas) de un .xlsx o un .csv. ValueError si no se puede leer."""
    contenido = archivo.read()
    if contenido[:4] == b"PK\x03\x04":
        try:
            libro = load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)
        except Exception as e:
            raise ValueError("El archivo no es un Excel válido (.xlsx) ni un CSV.") from e
        hoja = libro["Resultados"] if "Resultados" in libro.sheetnames else libro.worksheets[0]
        filas = list(hoja.iter_rows(values_only=True))
    else:
        if b"\x00" in contenido[:4096] or nombre.lower().endswith((".xls", ".xlsx", ".pdf")):
            raise ValueError("El archivo no es un Excel válido (.xlsx) ni un CSV.")
        for codificacion in ("utf-8-sig", "cp1252"):
            try:
                texto = contenido.decode(codificacion)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("No se pudo leer el CSV: guárdelo como UTF-8.")
        muestra = texto[:4096]
        try:
            separador = csv.Sniffer().sniff(muestra, delimiters=",;\t").delimiter
        except csv.Error:
            separador = ";" if muestra.count(";") > muestra.count(",") else ","
        filas = [tuple(f) for f in csv.reader(io.StringIO(texto), delimiter=separador)]
    if not filas:
        return [], []
    encabezados = [_texto(h).rstrip(" *") for h in filas[0]]
    return encabezados, filas[1:]


def _texto(v) -> str:
    if v is None:
        return ""
    if isinstance(v, datetime):
        return v.date().isoformat()
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def _fecha(v):
    if isinstance(v, datetime):
        return v.date()
    texto = _texto(v)
    for formato in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    return None


def _numero(texto: str):
    limpio = texto.replace(" ", "").replace(",", ".")
    if not re.fullmatch(r"[-+]?\d+(\.\d+)?", limpio):
        return None
    try:
        return Decimal(limpio)
    except InvalidOperation:
        return None


def generar_plantilla() -> bytes:
    from .models import ValorReferencia

    libro = Workbook()
    hoja = libro.active
    hoja.title = "Resultados"
    negrita, amarillo = Font(bold=True), PatternFill("solid", fgColor="FDE68A")
    for col, (_, enc, oblig, ejemplo, _) in enumerate(COLUMNAS, start=1):
        celda = hoja.cell(row=1, column=col, value=enc + (" *" if oblig else ""))
        celda.font = negrita
        if oblig:
            celda.fill = amarillo
        hoja.cell(row=2, column=col, value=ejemplo)
        hoja.column_dimensions[get_column_letter(col)].width = max(16, len(enc) + 4)
    hoja.freeze_panes = "A2"

    catalogo = libro.create_sheet("Catálogo")
    catalogo.append(["Código", "Examen", "Parámetro", "Rango normal", "Unidad"])
    for celda in catalogo[1]:
        celda.font = negrita
    for vr in ValorReferencia.objects.select_related("tipo_examen").order_by("tipo_examen__codigo", "parametro"):
        catalogo.append([vr.tipo_examen.codigo, vr.tipo_examen.nombre, vr.parametro, vr.rango_texto(), vr.unidad])
    for letra, ancho in zip("ABCDE", (10, 40, 30, 20, 12), strict=True):
        catalogo.column_dimensions[letra].width = ancho

    ayuda = libro.create_sheet("Instrucciones")
    ayuda.append(["Columna", "Obligatoria", "Cómo llenarla"])
    for celda in ayuda[1]:
        celda.font = negrita
    for _, enc, oblig, _, texto in COLUMNAS:
        ayuda.append([enc, "Sí" if oblig else "No", texto])
    ayuda.append([])
    ayuda.append(["Una fila por parámetro. Las filas con la misma CI, examen y fecha forman un solo examen."])
    ayuda.append(["La fila 2 de «Resultados» es un ejemplo: bórrela antes de importar."])
    ayuda.append([f"Máximo {MAX_FILAS} filas por archivo."])
    ayuda.column_dimensions["A"].width = 24
    ayuda.column_dimensions["C"].width = 80

    salida = BytesIO()
    libro.save(salida)
    return salida.getvalue()


def leer_filas(archivo, nombre: str = "", mapeo: dict[str, str] | None = None) -> list[dict]:
    """Filas como {campo: valor crudo} con su número.

    `mapeo` = {campo: encabezado del archivo}; si no se da, se reconoce por
    sinónimos. MapeoIncompleto si falta una columna obligatoria; ValueError si
    el archivo no se puede leer.
    """
    encabezados, datos = leer_tabla(archivo, nombre)
    if not encabezados:
        return []
    usado = mapeo_automatico(encabezados) | {k: v for k, v in (mapeo or {}).items() if v}
    desconocidos = [v for v in usado.values() if v not in encabezados]
    if desconocidos:
        raise ValueError("El mapeo nombra columnas que el archivo no tiene: " + ", ".join(desconocidos))
    faltan = [enc for campo, enc, oblig, *_ in COLUMNAS if oblig and campo not in usado]
    if faltan:
        raise MapeoIncompleto(encabezados, usado, faltan)
    indice = {campo: encabezados.index(enc) for campo, enc in usado.items()}
    resultado = []
    for numero, fila in enumerate(datos, start=2):
        valores = {campo: (fila[i] if i < len(fila) else None) for campo, i in indice.items()}
        if not any(_texto(v) for v in valores.values()):
            continue
        if len(resultado) >= MAX_FILAS:
            raise ValueError(f"El archivo tiene más de {MAX_FILAS} filas. Divídalo en varios.")
        resultado.append({"fila": numero, "datos": valores})
    return resultado


def _validar_fila(f, pacientes, tipos, rangos, hoy):
    """(clave_de_examen, datos_limpios) o lista de errores."""
    d = f["datos"]
    errores = []
    ci, codigo, parametro = _texto(d.get("ci")), _texto(d.get("codigo")).upper(), _texto(d.get("parametro"))
    valor_txt = _texto(d.get("valor"))
    fecha = _fecha(d.get("fecha"))
    paciente = pacientes.get(ci)
    tipo = tipos.get(codigo)
    if not ci:
        errores.append("Falta la CI de la paciente")
    elif paciente is None:
        errores.append(f"No hay ninguna paciente registrada con CI {ci}")
    if tipo is None:
        errores.append(f"El código de examen «{codigo}» no está en el catálogo")
    if fecha is None:
        errores.append("Fecha inválida (use DD/MM/AAAA)")
    elif fecha > hoy:
        errores.append("La fecha del resultado no puede ser futura")
    rango = rangos.get((tipo.pk, parametro.lower())) if tipo else None
    if tipo and rango is None:
        errores.append(f"«{parametro}» no es un parámetro de {tipo.codigo} (ver hoja «Catálogo»)")
    if not valor_txt:
        errores.append("Falta el valor")
    numero = None
    if rango is not None and valor_txt:
        numerico = rango.valor_minimo is not None or rango.valor_maximo is not None
        numero = _numero(valor_txt)
        if numerico and numero is None:
            errores.append(f"{parametro} se mide con números: «{valor_txt}» no es un número")
    if errores:
        return None, errores
    limpio = {"paciente": paciente, "tipo": tipo, "fecha": fecha, "rango": rango, "numero": numero,
              "texto": "" if numero is not None else valor_txt, "observaciones": _texto(d.get("observaciones"))}
    return (paciente.pk, tipo.pk, fecha), limpio


def procesar(filas: list[dict], usuario, confirmar: bool) -> dict:
    from pacientes.fields import compute_search_hash
    from pacientes.models import Paciente

    from .models import ExamenLaboratorio, ResultadoLaboratorio, TipoExamen, ValorReferencia

    hoy = timezone.localdate()
    cis = {_texto(f["datos"].get("ci")) for f in filas} - {""}
    por_hash = {compute_search_hash(ci): ci for ci in cis}
    pacientes = {por_hash[p.ci_hash]: p for p in Paciente.objects.filter(ci_hash__in=por_hash)}
    tipos = {t.codigo.upper(): t for t in TipoExamen.objects.all()}
    rangos = {(vr.tipo_examen_id, vr.parametro.lower()): vr for vr in ValorReferencia.objects.all()}

    salida, grupos = [], OrderedDict()
    for f in filas:
        clave, resultado = _validar_fila(f, pacientes, tipos, rangos, hoy)
        fila = {"fila": f["fila"], "ci": _texto(f["datos"].get("ci")), "examen": _texto(f["datos"].get("codigo")),
                "parametro": _texto(f["datos"].get("parametro")), "valor": _texto(f["datos"].get("valor"))}
        if clave is None:
            fila.update(estado="error", errores=resultado)
        else:
            fila.update(estado="valida", errores=[])
            grupos.setdefault(clave, []).append((fila, resultado))
        salida.append(fila)

    # Un parámetro repetido en el mismo examen, o ya cargado antes, se omite.
    for clave, items in grupos.items():
        vistos = set()
        paciente_id, tipo_id, fecha = clave
        ya_cargados = set(ResultadoLaboratorio.objects.filter(
            examen__paciente_id=paciente_id, examen__tipo_examen_id=tipo_id, examen__fecha_resultado__date=fecha,
        ).values_list("valor_referencia_id", flat=True))
        for fila, r in items:
            if r["rango"].pk in vistos or r["rango"].pk in ya_cargados:
                fila.update(estado="duplicada", errores=["Este parámetro ya está cargado para ese examen y fecha"])
            vistos.add(r["rango"].pk)

    creados: dict[str, list[int]] = {"resultados": [], "examenes": []}
    if confirmar:
        for (paciente_id, tipo_id, fecha), items in grupos.items():
            validos = [(fila, r) for fila, r in items if fila["estado"] == "valida"]
            if not validos:
                continue
            momento = timezone.make_aware(datetime.combine(fecha, time(8, 0)))
            try:
                with transaction.atomic():
                    examen = ExamenLaboratorio.objects.filter(
                        paciente_id=paciente_id, tipo_examen_id=tipo_id, fecha_resultado__date=fecha,
                    ).first()
                    examen_nuevo = examen is None
                    examen = examen or ExamenLaboratorio.objects.create(
                        paciente_id=paciente_id, tipo_examen_id=tipo_id, medico_solicitante=usuario,
                        fecha_solicitud=momento, fecha_muestra=momento, fecha_resultado=momento,
                        estado="completado", prioridad="normal",
                        observaciones="Resultados importados desde Excel", created_by=usuario,
                    )
                    ids = []
                    for fila, r in validos:
                        ids.append(ResultadoLaboratorio.objects.create(
                            examen=examen, valor_referencia=r["rango"], valor_numerico=r["numero"],
                            valor_texto=r["texto"], observaciones=r["observaciones"], created_by=usuario,
                        ).pk)
                        fila.update(estado="creada", examen_id=examen.pk)
                creados["resultados"] += ids
                if examen_nuevo:
                    creados["examenes"].append(examen.pk)
            except Exception as e:  # un examen roto no tumba los demás
                for fila, _ in validos:
                    fila.update(estado="error", errores=[f"No se pudo guardar: {e}"])

    cuenta = {e: sum(1 for f in salida if f["estado"] == e) for e in ("valida", "creada", "error", "duplicada")}
    examenes = len({k for k, items in grupos.items() if any(f["estado"] in ("valida", "creada") for f, _ in items)})
    return {"resumen": {"total": len(salida), **cuenta, "examenes": examenes, "confirmado": confirmar},
            "filas": salida, "creados": creados}


def deshacer(importacion, usuario, motivo: str) -> dict:
    """Anula un lote: borra sus resultados y los exámenes que creó y quedaron vacíos."""
    from .models import ExamenLaboratorio, ResultadoLaboratorio

    if importacion.anulada:
        raise ValueError("Esta importación ya fue anulada.")
    with transaction.atomic():
        borrados = ResultadoLaboratorio.objects.filter(pk__in=importacion.resultados_creados).count()
        ResultadoLaboratorio.objects.filter(pk__in=importacion.resultados_creados).delete()
        vacios = ExamenLaboratorio.objects.filter(pk__in=importacion.examenes_creados).exclude(
            pk__in=ResultadoLaboratorio.objects.values("examen_id"))
        examenes = vacios.count()
        vacios.delete()
        importacion.anulada = True
        importacion.motivo_anulacion = motivo
        importacion.anulada_por = usuario
        importacion.fecha_anulacion = timezone.now()
        importacion.save()
    return {"resultados_borrados": borrados, "examenes_borrados": examenes}
