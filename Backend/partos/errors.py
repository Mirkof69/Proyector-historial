"""=============================================================================
MÓDULO: PARTOS - ERRORS
=============================================================================
✅ Errores personalizados para el módulo de partos
✅ Mensajes descriptivos y códigos de error específicos
✅ Facilita el manejo de excepciones en views y serializers
=============================================================================
"""

from rest_framework import status
from rest_framework.exceptions import APIException

# ═══════════════════════════════════════════════════════════════════════════
# ERRORES GENERALES DE PARTO
# ═══════════════════════════════════════════════════════════════════════════


class PartoNotFoundError(APIException):
    """Error cuando no se encuentra un parto"""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Parto no encontrado"
    default_code = "parto_not_found"


class PartoAlreadyFinalizadoError(APIException):
    """Error cuando se intenta modificar un parto ya finalizado"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "El parto ya ha sido finalizado y no puede ser modificado"
    default_code = "parto_already_finalizado"


class PartoNotFinalizadoError(APIException):
    """Error cuando se requiere que el parto esté finalizado"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "El parto aún no ha sido finalizado"
    default_code = "parto_not_finalizado"


class PartoInvalidDateError(APIException):
    """Error cuando las fechas del parto son inválidas"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Fechas del parto inválidas: fecha de inicio no puede ser posterior a fecha de parto"
    default_code = "parto_invalid_date"


class PartoSinPacienteError(APIException):
    """Error cuando se intenta crear un parto sin paciente"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Debe especificar un paciente para el parto"
    default_code = "parto_sin_paciente"


class PartoSinEmbarazoError(APIException):
    """Error cuando se intenta crear un parto sin embarazo asociado"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Debe especificar un embarazo para el parto"
    default_code = "parto_sin_embarazo"


class CesareaSinIndicacionesError(APIException):
    """Error cuando una cesárea no tiene indicaciones especificadas"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Las cesáreas deben tener indicaciones médicas especificadas"
    default_code = "cesarea_sin_indicaciones"


class EdadGestacionalInvalidaError(APIException):
    """Error cuando la edad gestacional tiene formato inválido"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "Formato de edad gestacional inválido. Use formato: 39 o 39+2 (semanas+días)"
    )
    default_code = "edad_gestacional_invalida"


class DuracionTrabajoPartoInvalidaError(APIException):
    """Error cuando la duración del trabajo de parto es inválida"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Duración de trabajo de parto inválida o muy prolongada"
    default_code = "duracion_trabajo_parto_invalida"


class PerdidaSanguineaExcesivaError(APIException):
    """Error cuando la pérdida sanguínea reportada es muy alta"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Pérdida sanguínea muy alta, favor de revisar el valor ingresado"
    default_code = "perdida_sanguinea_excesiva"


# ═══════════════════════════════════════════════════════════════════════════
# ERRORES DE RECIÉN NACIDO
# ═══════════════════════════════════════════════════════════════════════════


class RecienNacidoNotFoundError(APIException):
    """Error cuando no se encuentra un recién nacido"""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Recién nacido no encontrado"
    default_code = "recien_nacido_not_found"


class PesoRecienNacidoInvalidoError(APIException):
    """Error cuando el peso del recién nacido está fuera de rango"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Peso del recién nacido fuera de rango válido (300g - 6000g)"
    default_code = "peso_recien_nacido_invalido"


class ApgarScoreInvalidoError(APIException):
    """Error cuando el score de Apgar es inválido"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Score de Apgar inválido. Debe estar entre 0 y 10"
    default_code = "apgar_score_invalido"


class ApgarInconsistenteError(APIException):
    """Error cuando los scores de Apgar son inconsistentes"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Los scores de Apgar son inconsistentes. Es inusual que el Apgar a 1 minuto sea mucho mayor que el de 5 minutos"
    default_code = "apgar_inconsistente"


class NumeroGemeloInvalidoError(APIException):
    """Error cuando el número de gemelo es inválido"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Número de gemelo inválido. Debe estar entre 1 y 5"
    default_code = "numero_gemelo_invalido"


class RecienNacidoDuplicadoError(APIException):
    """Error cuando ya existe un recién nacido con ese número de gemelo"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "Ya existe un recién nacido con ese número de gemelo para este parto"
    )
    default_code = "recien_nacido_duplicado"


# ═══════════════════════════════════════════════════════════════════════════
# ERRORES DE PARTOGRAMA
# ═══════════════════════════════════════════════════════════════════════════


class PartogramaNotFoundError(APIException):
    """Error cuando no se encuentra un registro de partograma"""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Registro de partograma no encontrado"
    default_code = "partograma_not_found"


class DilatacionInvalidaError(APIException):
    """Error cuando la dilatación cervical es inválida"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Dilatación cervical inválida. Debe estar entre 0 y 10 cm"
    default_code = "dilatacion_invalida"


class FCFInvalidaError(APIException):
    """Error cuando la frecuencia cardíaca fetal es inválida"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Frecuencia cardíaca fetal inválida. Debe estar entre 80 y 200 lpm"
    default_code = "fcf_invalida"


class PresionArterialInvalidaError(APIException):
    """Error cuando la presión arterial es inválida"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Presión arterial inválida. Valores fuera de rango"
    default_code = "presion_arterial_invalida"


class PartogramaPartoFinalizadoError(APIException):
    """Error cuando se intenta registrar partograma en parto finalizado"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "No se puede registrar partograma en un parto finalizado"
    default_code = "partograma_parto_finalizado"


class PartogramaDuplicadoError(APIException):
    """Error cuando ya existe un registro en esa hora"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Ya existe un registro de partograma para esa hora"
    default_code = "partograma_duplicado"


class HorasTrabajoPartoInvalidasError(APIException):
    """Error cuando las horas de trabajo de parto son inválidas"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "Horas de trabajo de parto inválidas. Debe estar entre 0 y 48 horas"
    )
    default_code = "horas_trabajo_parto_invalidas"


# ═══════════════════════════════════════════════════════════════════════════
# ERRORES DE COMPLICACIONES
# ═══════════════════════════════════════════════════════════════════════════


class ComplicacionNotFoundError(APIException):
    """Error cuando no se encuentra una complicación"""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Complicación no encontrada"
    default_code = "complicacion_not_found"


class ComplicacionSinDescripcionError(APIException):
    """Error cuando una complicación no tiene descripción"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "La complicación debe tener una descripción detallada"
    default_code = "complicacion_sin_descripcion"


class CirugiaSinTipoError(APIException):
    """Error cuando se marca cirugía pero no se especifica el tipo"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "Si requirió cirugía, debe especificar el tipo de cirugía realizada"
    )
    default_code = "cirugia_sin_tipo"


class SeveridadInvalidaError(APIException):
    """Error cuando la severidad de la complicación es inválida"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Severidad de complicación inválida"
    default_code = "severidad_invalida"


# ═══════════════════════════════════════════════════════════════════════════
# ERRORES DE APGAR SCORE DETALLADO
# ═══════════════════════════════════════════════════════════════════════════


class ApgarDetalladoNotFoundError(APIException):
    """Error cuando no se encuentra un Apgar Score Detallado"""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Apgar Score Detallado no encontrado"
    default_code = "apgar_detallado_not_found"


class ApgarDetalladoDuplicadoError(APIException):
    """Error cuando ya existe un Apgar para ese minuto"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Ya existe una evaluación Apgar detallada para ese minuto"
    default_code = "apgar_detallado_duplicado"


class ComponenteApgarInvalidoError(APIException):
    """Error cuando un componente del Apgar es inválido"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Componente de Apgar inválido. Debe ser 0, 1 o 2"
    default_code = "componente_apgar_invalido"


class MinutoEvaluacionInvalidoError(APIException):
    """Error cuando el minuto de evaluación es inválido"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Minuto de evaluación inválido. Debe ser entre 1 y 60"
    default_code = "minuto_evaluacion_invalido"


# ═══════════════════════════════════════════════════════════════════════════
# ERRORES DE PERMISOS Y AUTENTICACIÓN
# ═══════════════════════════════════════════════════════════════════════════


class UsuarioNoAutorizadoError(APIException):
    """Error cuando el usuario no tiene permisos"""

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "No tiene permisos para realizar esta acción"
    default_code = "usuario_no_autorizado"


class MedicoResponsableRequeridoError(APIException):
    """Error cuando se requiere un médico responsable"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Debe asignar un médico responsable para esta acción"
    default_code = "medico_responsable_requerido"


# ═══════════════════════════════════════════════════════════════════════════
# ERRORES DE RELACIONES Y FOREIGN KEYS
# ═══════════════════════════════════════════════════════════════════════════


class PacienteNotFoundError(APIException):
    """Error cuando no se encuentra el paciente"""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Paciente no encontrado"
    default_code = "paciente_not_found"


class EmbarazoNotFoundError(APIException):
    """Error cuando no se encuentra el embarazo"""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Embarazo no encontrado"
    default_code = "embarazo_not_found"


class EmbarazoNoActivoError(APIException):
    """Error cuando el embarazo no está activo"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "El embarazo no está activo o ya finalizó"
    default_code = "embarazo_no_activo"


class EmbarazoYaTienePartoError(APIException):
    """Error cuando el embarazo ya tiene un parto registrado"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Este embarazo ya tiene un parto registrado"
    default_code = "embarazo_ya_tiene_parto"


# ═══════════════════════════════════════════════════════════════════════════
# ERRORES DE VALIDACIÓN DE DATOS
# ═══════════════════════════════════════════════════════════════════════════


class DatosIncompletosError(APIException):
    """Error cuando faltan datos requeridos"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Datos incompletos. Faltan campos requeridos"
    default_code = "datos_incompletos"


class FormatoInvalidoError(APIException):
    """Error cuando el formato de datos es inválido"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Formato de datos inválido"
    default_code = "formato_invalido"


class ValorFueraDeRangoError(APIException):
    """Error cuando un valor está fuera del rango permitido"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Valor fuera del rango permitido"
    default_code = "valor_fuera_de_rango"


# ═══════════════════════════════════════════════════════════════════════════
# ERRORES DE ESTADÍSTICAS Y REPORTES
# ═══════════════════════════════════════════════════════════════════════════


class FechaRangoInvalidoError(APIException):
    """Error cuando el rango de fechas es inválido"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Rango de fechas inválido. La fecha de inicio debe ser anterior a la fecha de fin"
    default_code = "fecha_rango_invalido"


class SinDatosParaEstadisticasError(APIException):
    """Error cuando no hay datos para generar estadísticas"""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = (
        "No se encontraron datos para generar estadísticas en el período especificado"
    )
    default_code = "sin_datos_para_estadisticas"


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES HELPER PARA MANEJO DE ERRORES
# ═══════════════════════════════════════════════════════════════════════════


def raise_parto_not_found(parto_id=None):
    """Helper para lanzar error de parto no encontrado"""
    if parto_id:
        raise PartoNotFoundError(f"Parto con ID {parto_id} no encontrado")
    raise PartoNotFoundError


def raise_recien_nacido_not_found(rn_id=None):
    """Helper para lanzar error de recién nacido no encontrado"""
    if rn_id:
        raise RecienNacidoNotFoundError(f"Recién nacido con ID {rn_id} no encontrado")
    raise RecienNacidoNotFoundError


def raise_partograma_not_found(partograma_id=None):
    """Helper para lanzar error de partograma no encontrado"""
    if partograma_id:
        raise PartogramaNotFoundError(
            f"Partograma con ID {partograma_id} no encontrado",
        )
    raise PartogramaNotFoundError


def raise_complicacion_not_found(complicacion_id=None):
    """Helper para lanzar error de complicación no encontrada"""
    if complicacion_id:
        raise ComplicacionNotFoundError(
            f"Complicación con ID {complicacion_id} no encontrada",
        )
    raise ComplicacionNotFoundError


def validate_date_range(fecha_inicio, fecha_fin):
    """Valida que el rango de fechas sea válido"""
    if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
        raise FechaRangoInvalidoError
