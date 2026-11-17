"""Matriz única de los listados con buscador y filtros (DOM real obtenido con tools/sonda_dom.py).

La usan las grabaciones de Selenium IDE (tools/generar_side.py) y las pruebas de Selenium WebDriver
(tests/ui/test_buscadores_ui.py), para que ambas herramientas prueben exactamente lo mismo.

Campos: clave, nombre del módulo, ruta, rol que lo usa, texto de ayuda del buscador, encabezado de la columna de
la que se toma el término de búsqueda y, si lo hay, el texto del filtro desplegable.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Listado:
    clave: str
    modulo: str
    ruta: str
    rol: str
    buscador: str
    columna: str
    filtro: str = ""
    requisito: str = "RF-04"
    vacio: bool = True   # False: el listado nunca queda vacío al buscar (la auditoría registra la propia búsqueda)


LISTADOS = [
    Listado("pacientes", "Pacientes", "/dashboard/pacientes", "recepcion", "Buscar por nombre, CI o ID...", "Paciente", requisito="RF-02"),
    Listado("citas", "Citas", "/dashboard/citas", "recepcion", "Buscar por paciente, médico, motivo, ID clínico...", "Paciente", "Estado", "RF-20"),
    Listado("consultorios", "Consultorios", "/dashboard/consultorios", "recepcion", "Buscar por código, nombre o área", "Nombre", "Tipo"),
    Listado("triaje", "Triaje", "/dashboard/triaje", "enfermera", "Buscar por paciente, motivo...", "Paciente", requisito="RF-16"),
    Listado("vacunas", "Vacunas", "/dashboard/vacunas", "enfermera", "Buscar por paciente, vacuna, lote o lab...", "Paciente", "Todos los estados", "RF-14"),
    Listado("notas", "Notas de evolución", "/dashboard/notas-evolucion", "enfermera", "Buscar por paciente, médico o motivo...", "Paciente", requisito="RF-15"),
    Listado("controles", "Control prenatal", "/dashboard/controles", "enfermera", "Buscar por paciente (nombre o CI), ID clínico...", "Paciente", requisito="RF-06"),
    Listado("laboratorio", "Laboratorio", "/dashboard/laboratorio", "laboratorista", "Buscar paciente o examen...", "Paciente", "Estado", "RF-12"),
    Listado("embarazos", "Embarazo", "/dashboard/embarazos", "medico", "Buscar por nombre, CI o ID...", "Paciente", "Filtrar Riesgo", "RF-05"),
    Listado("ecografias", "Ecografía", "/dashboard/ecografias", "medico", "Buscar...", "Paciente", requisito="RF-07"),
    Listado("partos", "Partos", "/dashboard/partos", "medico", "Buscar paciente...", "Nombre Paciente", "Tipo de parto", "RF-11"),
    Listado("historias", "Historia clínica", "/dashboard/historia-clinica", "medico", "Buscar por nombre, documento o N° historia...", "Nombre Completo"),
    Listado("antecedentes", "Antecedentes", "/dashboard/antecedentes", "medico", "Buscar por nombre de paciente...", "Paciente"),
    Listado("alertas", "Alertas", "/dashboard/alertas", "medico", "Buscar por paciente, tipo o mensaje...", "Paciente", "Todas las severidades", "RF-06"),
    Listado("usuarios", "Usuarios", "/dashboard/usuarios", "administrador", "Buscar por nombre o email...", "Nombre Completo", "Filtrar por rol", "RF-21"),
    Listado("auditoria", "Auditoría", "/dashboard/auditoria", "administrador", "Buscar: nombre, correo, ruta, detalle, IP…", "Quién", "Acción", "RF-22", vacio=False),
    Listado("notificaciones", "Notificaciones", "/dashboard/notificaciones", "administrador", "Buscar en notificaciones...", "Contenido", "Tipo", "RF-20"),
]

# término que ningún registro contiene: el listado debe quedar vacío
SIN_RESULTADOS = "zzqa-sin-coincidencias-999"

# JavaScript que toma del primer registro una palabra de la columna indicada (solo letras, 4 o más) para buscarla
JS_TERMINO = ("const ths=[...document.querySelectorAll('.ant-table-thead th')];"
              "const i=ths.findIndex(t=>t.innerText.trim()==='%s');"
              "const fila=document.querySelector('.ant-table-tbody tr.ant-table-row');"
              "const txt=(fila&&i>=0?fila.children[i].innerText:'');"
              "const p=txt.split(/\\s+/).filter(w=>/^[A-Za-zÁÉÍÓÚÑáéíóúñü]{4,}$/.test(w)&&w!=='QA');"
              "return p.length?p[0]:'';")

# Nombre de la primera paciente que devuelve la búsqueda avanzada (solo activas): primera palabra de letras de la fila
JS_TERMINO_REAL = ("const filas=[...document.querySelectorAll('.ant-table-tbody tr.ant-table-row')]"
                   ".filter(f=>!f.innerText.includes('QA '));"
                   "const txt=filas.length?filas[0].innerText:'';"
                   "const p=txt.split(/\\s+/).filter(w=>/^[A-Za-zÁÉÍÓÚÑáéíóúñü]{4,}$/.test(w)&&w!=='años');"
                   "return p.length?p[0]:'';")
