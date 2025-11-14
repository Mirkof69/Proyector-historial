# =============================================================================
# SERIALIZERS DE PACIENTES
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: pacientes
# Descripción: Serializers completos para el módulo de pacientes.
#              Incluye serialización, validación y representación de datos.
# Autor: Sistema de Gestión Médica
# Versión: 2.0.0
# Última actualización: 2025-11-14
# =============================================================================

from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
import re
from .models import Paciente

# =============================================================================
# SERIALIZER COMPLETO DE PACIENTE (LECTURA)
# =============================================================================
class PacienteSerializer(serializers.ModelSerializer):
    """
    Serializer completo para la lectura de pacientes.

    Incluye todos los campos del modelo y campos calculados adicionales como:
    - Edad calculada
    - Nombre completo
    - Fórmula GPAC
    - Clasificación de paridad
    - Factores de riesgo
    - Índice de riesgo
    - Clasificación de riesgo
    """

    # Campos calculados (read-only)
    edad = serializers.SerializerMethodField()
    nombre_completo = serializers.SerializerMethodField()
    gpac = serializers.SerializerMethodField()
    paridad = serializers.SerializerMethodField()
    factores_riesgo = serializers.SerializerMethodField()
    indice_riesgo = serializers.SerializerMethodField()
    clasificacion_riesgo = serializers.SerializerMethodField()
    necesita_atencion_especializada = serializers.SerializerMethodField()

    # Campos con formato personalizado
    fecha_nacimiento_formatted = serializers.SerializerMethodField()
    fecha_registro_formatted = serializers.SerializerMethodField()

    # Campo de compatibilidad
    telefono = serializers.CharField(source='telefono_principal', required=False, allow_blank=True)

    class Meta:
        model = Paciente
        fields = '__all__'
        read_only_fields = [
            'id',
            'uuid',
            'fecha_registro',
            'fecha_modificacion',
            'fecha_inactivacion',
        ]

    def get_edad(self, obj):
        """Retorna la edad calculada del paciente."""
        return obj.calcular_edad()

    def get_nombre_completo(self, obj):
        """Retorna el nombre completo del paciente."""
        return obj.get_nombre_completo()

    def get_gpac(self, obj):
        """Retorna la fórmula obstétrica GPAC."""
        return obj.get_gpac_formatted()

    def get_paridad(self, obj):
        """Retorna la clasificación de paridad."""
        return obj.get_paridad()

    def get_factores_riesgo(self, obj):
        """Retorna la lista de factores de riesgo identificados."""
        return obj.tiene_riesgo_alto()

    def get_indice_riesgo(self, obj):
        """Retorna el índice numérico de riesgo (0-100)."""
        return obj.get_indice_riesgo()

    def get_clasificacion_riesgo(self, obj):
        """Retorna la clasificación de riesgo."""
        return obj.get_clasificacion_riesgo()

    def get_necesita_atencion_especializada(self, obj):
        """Indica si necesita atención especializada."""
        return obj.necesita_atencion_especializada()

    def get_fecha_nacimiento_formatted(self, obj):
        """Retorna fecha de nacimiento en formato legible."""
        if obj.fecha_nacimiento:
            return obj.fecha_nacimiento.strftime('%d/%m/%Y')
        return None

    def get_fecha_registro_formatted(self, obj):
        """Retorna fecha de registro en formato legible."""
        if obj.fecha_registro:
            return obj.fecha_registro.strftime('%d/%m/%Y %H:%M:%S')
        return None


# =============================================================================
# SERIALIZER PARA LISTADO DE PACIENTES (RESUMIDO)
# =============================================================================
class PacienteListSerializer(serializers.ModelSerializer):
    """
    Serializer resumido para listados de pacientes.

    Incluye solo los campos esenciales para mejorar el rendimiento
    en listados con muchos registros.
    """

    edad = serializers.SerializerMethodField()
    nombre_completo = serializers.SerializerMethodField()
    gpac = serializers.SerializerMethodField()
    indice_riesgo = serializers.SerializerMethodField()
    clasificacion_riesgo = serializers.SerializerMethodField()

    class Meta:
        model = Paciente
        fields = [
            'id',
            'uuid',
            'id_clinico',
            'cedula_identidad',
            'nombre',
            'apellido_paterno',
            'apellido_materno',
            'nombre_completo',
            'fecha_nacimiento',
            'edad',
            'genero',
            'telefono_principal',
            'email',
            'gpac',
            'gestas',
            'partos',
            'abortos',
            'cesareas',
            'indice_riesgo',
            'clasificacion_riesgo',
            'activo',
            'fecha_registro',
        ]

    def get_edad(self, obj):
        return obj.calcular_edad()

    def get_nombre_completo(self, obj):
        return obj.get_nombre_completo()

    def get_gpac(self, obj):
        return obj.get_gpac_formatted()

    def get_indice_riesgo(self, obj):
        return obj.get_indice_riesgo()

    def get_clasificacion_riesgo(self, obj):
        return obj.get_clasificacion_riesgo()


# =============================================================================
# SERIALIZER PARA CREAR PACIENTES
# =============================================================================
class PacienteCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para la creación de nuevos pacientes.

    Incluye validaciones personalizadas y generación automática de campos.
    """

    # Campo de compatibilidad
    telefono = serializers.CharField(source='telefono_principal', required=False, allow_blank=True)

    class Meta:
        model = Paciente
        exclude = [
            'id',
            'uuid',
            'fecha_registro',
            'fecha_modificacion',
            'fecha_inactivacion',
            'motivo_inactivacion',
        ]

    def validate_nombre(self, value):
        """Validar que el nombre solo contenga letras y espacios"""
        if not value:
            raise serializers.ValidationError("El nombre es obligatorio.")
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', value):
            raise serializers.ValidationError("El nombre solo puede contener letras.")
        return value.strip()

    def validate_apellido_paterno(self, value):
        """Validar que el apellido paterno solo contenga letras"""
        if not value:
            raise serializers.ValidationError("El apellido paterno es obligatorio.")
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', value):
            raise serializers.ValidationError("El apellido paterno solo puede contener letras.")
        return value.strip()

    def validate_apellido_materno(self, value):
        """Validar que el apellido materno solo contenga letras"""
        if value and not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', value):
            raise serializers.ValidationError("El apellido materno solo puede contener letras.")
        return value.strip() if value else None

    def validate_id_clinico(self, value):
        """Validar formato de ID clínico"""
        if not value:
            raise serializers.ValidationError("El ID clínico es obligatorio.")
        if not re.match(r'^HC-\d{3,}$', value):
            raise serializers.ValidationError("El ID Clínico debe tener el formato HC-001.")

        # Validar unicidad
        if self.instance:
            if Paciente.objects.filter(id_clinico=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("Ya existe un paciente con este ID clínico.")
        else:
            if Paciente.objects.filter(id_clinico=value).exists():
                raise serializers.ValidationError("Ya existe un paciente con este ID clínico.")
        return value

    def validate_cedula_identidad(self, value):
        """Validar que la CI solo contenga números y guiones"""
        if value:
            if not re.match(r'^[0-9\-]+$', value):
                raise serializers.ValidationError("La Cédula de Identidad solo puede contener números y guiones.")

            # Validar unicidad
            if self.instance:
                if Paciente.objects.filter(cedula_identidad=value).exclude(id=self.instance.id).exists():
                    raise serializers.ValidationError("Ya existe un paciente con esta cédula de identidad.")
            else:
                if Paciente.objects.filter(cedula_identidad=value).exists():
                    raise serializers.ValidationError("Ya existe un paciente con esta cédula de identidad.")
        return value

    def validate_telefono_principal(self, value):
        """Validar que el teléfono solo contenga números"""
        if value and not re.match(r'^[0-9\+\-\s\(\)]+$', value):
            raise serializers.ValidationError("El teléfono solo puede contener números.")
        return value

    def validate_email(self, value):
        """Validar formato de email"""
        if value:
            value = value.lower().strip()
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
                raise serializers.ValidationError("El formato del correo electrónico no es válido.")
        return value

    def validate_fecha_nacimiento(self, value):
        """Valida que la fecha de nacimiento sea válida."""
        if value:
            hoy = timezone.now().date()
            if value > hoy:
                raise serializers.ValidationError("La fecha de nacimiento no puede ser futura.")

            # Calcular edad
            edad = hoy.year - value.year - ((hoy.month, hoy.day) < (value.month, value.day))

            if edad < 10:
                raise serializers.ValidationError("La paciente debe tener al menos 10 años para registro obstétrico.")

            if edad > 120:
                raise serializers.ValidationError("La fecha de nacimiento parece incorrecta (edad mayor a 120 años).")

        return value

    def validate(self, data):
        """
        Validaciones a nivel de objeto (múltiples campos).
        """
        # Validar coherencia de fórmula obstétrica
        gestas = data.get('gestas', 0)
        partos = data.get('partos', 0)
        abortos = data.get('abortos', 0)
        cesareas = data.get('cesareas', 0)
        ectopicos = data.get('ectopicos', 0)
        molas = data.get('molas', 0)

        if gestas > 0:
            suma_resultados = partos + abortos + cesareas + ectopicos + molas
            if suma_resultados > gestas:
                raise serializers.ValidationError({
                    'gestas': f'La suma de partos ({partos}) + abortos ({abortos}) + cesáreas ({cesareas}) + ectópicos ({ectopicos}) + molas ({molas}) = {suma_resultados} no puede ser mayor que las gestas ({gestas}).'
                })

        # Validar hijos vivos
        hijos_vivos = data.get('hijos_vivos', 0)
        if hijos_vivos > (partos + cesareas):
            raise serializers.ValidationError({
                'hijos_vivos': f'El número de hijos vivos ({hijos_vivos}) no puede ser mayor que la suma de partos y cesáreas ({partos + cesareas}).'
            })

        # Validar peso de recién nacidos
        peso_max = data.get('peso_maximo_recien_nacido')
        peso_min = data.get('peso_minimo_recien_nacido')

        if peso_max and peso_min:
            if peso_min > peso_max:
                raise serializers.ValidationError({
                    'peso_minimo_recien_nacido': 'El peso mínimo no puede ser mayor que el peso máximo.'
                })

        # Validar que si fuma, tenga número de cigarrillos
        if data.get('fuma') and not data.get('cigarrillos_dia'):
            raise serializers.ValidationError({
                'cigarrillos_dia': 'Debe especificar el número de cigarrillos por día si la paciente fuma.'
            })

        # Validar que si consume alcohol, tenga frecuencia
        if data.get('consume_alcohol') and not data.get('frecuencia_alcohol'):
            raise serializers.ValidationError({
                'frecuencia_alcohol': 'Debe especificar la frecuencia de consumo de alcohol.'
            })

        # Validar que si consume drogas, tenga tipo
        if data.get('consume_drogas') and not data.get('tipo_drogas'):
            raise serializers.ValidationError({
                'tipo_drogas': 'Debe especificar el tipo de drogas consumidas.'
            })

        return data

    def create(self, validated_data):
        """Crea un nuevo paciente."""
        # Manejar campo de compatibilidad telefono
        if 'telefono' in validated_data and 'telefono_principal' not in validated_data:
            validated_data['telefono_principal'] = validated_data.pop('telefono')

        paciente = Paciente.objects.create(**validated_data)
        return paciente


# =============================================================================
# SERIALIZER PARA ACTUALIZAR PACIENTES
# =============================================================================
class PacienteUpdateSerializer(PacienteCreateSerializer):
    """
    Serializer para la actualización de pacientes existentes.

    Hereda de CreateSerializer para reutilizar validaciones.
    """

    def update(self, instance, validated_data):
        """Actualiza un paciente existente."""
        # Manejar campo de compatibilidad telefono
        if 'telefono' in validated_data and 'telefono_principal' not in validated_data:
            validated_data['telefono_principal'] = validated_data.pop('telefono')

        return super().update(instance, validated_data)


# =============================================================================
# SERIALIZER PARA DATOS BÁSICOS DE PACIENTE
# =============================================================================
class PacienteDatosBásicosSerializer(serializers.ModelSerializer):
    """
    Serializer con solo datos básicos del paciente.

    Usado para referencias rápidas en otros modelos (embarazos, controles, etc.)
    """

    edad = serializers.SerializerMethodField()
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Paciente
        fields = [
            'id',
            'uuid',
            'id_clinico',
            'cedula_identidad',
            'nombre',
            'apellido_paterno',
            'apellido_materno',
            'nombre_completo',
            'fecha_nacimiento',
            'edad',
            'genero',
            'telefono_principal',
            'email',
        ]

    def get_edad(self, obj):
        return obj.calcular_edad()

    def get_nombre_completo(self, obj):
        return obj.get_nombre_completo()


# =============================================================================
# SERIALIZER PARA ANTECEDENTES OBSTÉTRICOS
# =============================================================================
class PacienteAntecedentesObstetricosSerializer(serializers.ModelSerializer):
    """
    Serializer especializado en antecedentes obstétricos.

    Usado en consultas específicas de historial obstétrico.
    """

    nombre_completo = serializers.SerializerMethodField()
    gpac = serializers.SerializerMethodField()
    paridad = serializers.SerializerMethodField()

    class Meta:
        model = Paciente
        fields = [
            'id',
            'id_clinico',
            'nombre_completo',
            'gpac',
            'paridad',
            'gestas',
            'partos',
            'abortos',
            'cesareas',
            'ectopicos',
            'molas',
            'hijos_vivos',
            'hijos_muertos',
            'complicaciones_embarazos_previos',
            'peso_maximo_recien_nacido',
            'peso_minimo_recien_nacido',
            'partos_prematuros_previos',
            'preeclampsia_previa',
            'eclampsia_previa',
            'hemorragia_postparto_previa',
            'cirugia_uterina_previa',
            'incompetencia_cervical',
            'malformaciones_uterinas',
        ]

    def get_nombre_completo(self, obj):
        return obj.get_nombre_completo()

    def get_gpac(self, obj):
        return obj.get_gpac_formatted()

    def get_paridad(self, obj):
        return obj.get_paridad()


# =============================================================================
# SERIALIZER PARA FACTORES DE RIESGO
# =============================================================================
class PacienteFactoresRiesgoSerializer(serializers.ModelSerializer):
    """
    Serializer especializado en factores de riesgo.

    Usado para evaluaciones de riesgo y planificación de atención.
    """

    nombre_completo = serializers.SerializerMethodField()
    edad = serializers.SerializerMethodField()
    factores_riesgo = serializers.SerializerMethodField()
    indice_riesgo = serializers.SerializerMethodField()
    clasificacion_riesgo = serializers.SerializerMethodField()
    necesita_atencion_especializada = serializers.SerializerMethodField()

    class Meta:
        model = Paciente
        fields = [
            'id',
            'id_clinico',
            'nombre_completo',
            'edad',
            'factores_riesgo',
            'indice_riesgo',
            'clasificacion_riesgo',
            'necesita_atencion_especializada',
            # Factores de riesgo médicos
            'diabetes_previa',
            'hipertension_previa',
            'preeclampsia_previa',
            'eclampsia_previa',
            'hemorragia_postparto_previa',
            'cirugia_uterina_previa',
            'incompetencia_cervical',
            'malformaciones_uterinas',
            'enfermedades_tiroideas',
            'enfermedades_autoinmunes',
            'enfermedades_cardiovasculares',
            'enfermedades_renales',
            'epilepsia',
            'asma',
            'trombofilia',
            'vih',
            'hepatitis',
            # Hábitos
            'fuma',
            'cigarrillos_dia',
            'consume_alcohol',
            'frecuencia_alcohol',
            'consume_drogas',
            'tipo_drogas',
            # Antecedentes obstétricos de riesgo
            'cesareas',
            'abortos',
            'partos_prematuros_previos',
        ]

    def get_nombre_completo(self, obj):
        return obj.get_nombre_completo()

    def get_edad(self, obj):
        return obj.calcular_edad()

    def get_factores_riesgo(self, obj):
        return obj.tiene_riesgo_alto()

    def get_indice_riesgo(self, obj):
        return obj.get_indice_riesgo()

    def get_clasificacion_riesgo(self, obj):
        return obj.get_clasificacion_riesgo()

    def get_necesita_atencion_especializada(self, obj):
        return obj.necesita_atencion_especializada()


# =============================================================================
# SERIALIZER PARA DATOS SOCIOECONÓMICOS
# =============================================================================
class PacienteDatosSocioeconomicosSerializer(serializers.ModelSerializer):
    """
    Serializer especializado en datos socioeconómicos.

    Usado para análisis estadísticos y reportes sociales.
    """

    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Paciente
        fields = [
            'id',
            'id_clinico',
            'nombre_completo',
            'nivel_educativo',
            'ocupacion',
            'estado_civil',
            'vive_con',
            'situacion_vivienda',
            'tipo_vivienda',
            'acceso_agua_potable',
            'acceso_alcantarillado',
            'acceso_electricidad',
            'tiene_seguro',
            'tipo_seguro',
            'nombre_aseguradora',
        ]

    def get_nombre_completo(self, obj):
        return obj.get_nombre_completo()


# =============================================================================
# SERIALIZER PARA CONTACTOS DE EMERGENCIA
# =============================================================================
class PacienteContactosEmergenciaSerializer(serializers.ModelSerializer):
    """
    Serializer especializado en contactos de emergencia.

    Usado para acceso rápido a contactos en situaciones de emergencia.
    """

    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Paciente
        fields = [
            'id',
            'id_clinico',
            'nombre_completo',
            'telefono_principal',
            'telefono_secundario',
            'email',
            'direccion',
            'ciudad',
            'departamento',
            'contacto_emergencia_nombre',
            'contacto_emergencia_telefono',
            'contacto_emergencia_relacion',
            'contacto_emergencia2_nombre',
            'contacto_emergencia2_telefono',
            'contacto_emergencia2_relacion',
        ]

    def get_nombre_completo(self, obj):
        return obj.get_nombre_completo()


# =============================================================================
# SERIALIZER PARA ESTADÍSTICAS DE PACIENTE
# =============================================================================
class PacienteEstadisticasSerializer(serializers.Serializer):
    """
    Serializer para estadísticas generales de pacientes.

    No está asociado directamente al modelo, sino que recibe datos
    procesados para mostrar estadísticas agregadas.
    """

    total_pacientes = serializers.IntegerField()
    pacientes_activos = serializers.IntegerField()
    pacientes_inactivos = serializers.IntegerField()
    edad_promedio = serializers.FloatField()
    edad_minima = serializers.IntegerField()
    edad_maxima = serializers.IntegerField()

    # Estadísticas obstétricas
    total_embarazos = serializers.IntegerField()
    total_partos = serializers.IntegerField()
    total_cesareas = serializers.IntegerField()
    total_abortos = serializers.IntegerField()

    # Distribución por riesgo
    pacientes_bajo_riesgo = serializers.IntegerField()
    pacientes_riesgo_moderado = serializers.IntegerField()
    pacientes_alto_riesgo = serializers.IntegerField()
    pacientes_riesgo_muy_alto = serializers.IntegerField()

    # Factores de riesgo más comunes
    con_diabetes = serializers.IntegerField()
    con_hipertension = serializers.IntegerField()
    con_preeclampsia_previa = serializers.IntegerField()
    fumadoras = serializers.IntegerField()

    # Datos socioeconómicos
    con_seguro_medico = serializers.IntegerField()
    sin_seguro_medico = serializers.IntegerField()


# =============================================================================
# SERIALIZER PARA BÚSQUEDA DE PACIENTES
# =============================================================================
class PacienteBusquedaSerializer(serializers.Serializer):
    """
    Serializer para parámetros de búsqueda de pacientes.

    Define los campos permitidos para búsqueda avanzada.
    """

    # Campos de búsqueda de texto
    buscar = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Buscar por nombre, apellido, ID clínico o cédula"
    )

    # Filtros específicos
    id_clinico = serializers.CharField(required=False, allow_blank=True)
    cedula_identidad = serializers.CharField(required=False, allow_blank=True)

    # Filtros de edad
    edad_minima = serializers.IntegerField(required=False, min_value=0, max_value=150)
    edad_maxima = serializers.IntegerField(required=False, min_value=0, max_value=150)

    # Filtros de riesgo
    nivel_riesgo = serializers.ChoiceField(
        required=False,
        choices=[
            ('bajo', 'Riesgo Bajo'),
            ('moderado', 'Riesgo Moderado'),
            ('alto', 'Riesgo Alto'),
            ('muy_alto', 'Riesgo Muy Alto'),
        ]
    )

    # Filtros de estado
    activo = serializers.BooleanField(required=False)

    # Filtros de factores de riesgo
    con_diabetes = serializers.BooleanField(required=False)
    con_hipertension = serializers.BooleanField(required=False)
    con_preeclampsia_previa = serializers.BooleanField(required=False)

    # Ordenamiento
    orden = serializers.ChoiceField(
        required=False,
        choices=[
            ('nombre', 'Nombre A-Z'),
            ('-nombre', 'Nombre Z-A'),
            ('fecha_registro', 'Más antiguos primero'),
            ('-fecha_registro', 'Más recientes primero'),
            ('edad', 'Menor a mayor edad'),
            ('-edad', 'Mayor a menor edad'),
            ('indice_riesgo', 'Menor riesgo primero'),
            ('-indice_riesgo', 'Mayor riesgo primero'),
        ]
    )


# =============================================================================
# SERIALIZER PARA INACTIVACIÓN DE PACIENTE
# =============================================================================
class PacienteInactivacionSerializer(serializers.Serializer):
    """
    Serializer para el proceso de inactivación de pacientes.

    Requiere un motivo para la inactivación (soft delete).
    """

    motivo_inactivacion = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=500,
        help_text="Motivo de la inactivación del paciente"
    )

    def validate_motivo_inactivacion(self, value):
        """Valida que el motivo tenga al menos 10 caracteres."""
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "El motivo de inactivación debe tener al menos 10 caracteres."
            )
        return value.strip()


# =============================================================================
# SERIALIZER PARA REACTIVACIÓN DE PACIENTE
# =============================================================================
class PacienteReactivacionSerializer(serializers.Serializer):
    """
    Serializer para el proceso de reactivación de pacientes.

    Puede incluir notas sobre la reactivación.
    """

    notas_reactivacion = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text="Notas sobre la reactivación del paciente"
    )


# =============================================================================
# SERIALIZER PARA EXPORTACIÓN DE DATOS
# =============================================================================
class PacienteExportacionSerializer(serializers.ModelSerializer):
    """
    Serializer para exportación de datos de pacientes.

    Incluye todos los campos en formato plano para exportar a CSV/Excel.
    """

    edad = serializers.SerializerMethodField()
    nombre_completo = serializers.SerializerMethodField()
    gpac = serializers.SerializerMethodField()
    paridad = serializers.SerializerMethodField()
    indice_riesgo = serializers.SerializerMethodField()
    clasificacion_riesgo = serializers.SerializerMethodField()

    class Meta:
        model = Paciente
        fields = [
            # Identificación
            'id',
            'uuid',
            'id_clinico',
            'cedula_identidad',
            # Datos personales
            'nombre',
            'apellido_paterno',
            'apellido_materno',
            'nombre_completo',
            'fecha_nacimiento',
            'edad',
            'genero',
            # Contacto
            'telefono_principal',
            'telefono_secundario',
            'email',
            'direccion',
            'ciudad',
            'departamento',
            'codigo_postal',
            # Antecedentes obstétricos
            'gpac',
            'paridad',
            'gestas',
            'partos',
            'abortos',
            'cesareas',
            'ectopicos',
            'molas',
            'hijos_vivos',
            'hijos_muertos',
            # Factores de riesgo
            'diabetes_previa',
            'hipertension_previa',
            'preeclampsia_previa',
            'eclampsia_previa',
            'indice_riesgo',
            'clasificacion_riesgo',
            # Hábitos
            'fuma',
            'cigarrillos_dia',
            'consume_alcohol',
            'consume_drogas',
            # Socioeconómicos
            'nivel_educativo',
            'ocupacion',
            'estado_civil',
            'tiene_seguro',
            'tipo_seguro',
            # Estado
            'activo',
            'fecha_registro',
        ]

    def get_edad(self, obj):
        return obj.calcular_edad()

    def get_nombre_completo(self, obj):
        return obj.get_nombre_completo()

    def get_gpac(self, obj):
        return obj.get_gpac_formatted()

    def get_paridad(self, obj):
        return obj.get_paridad()

    def get_indice_riesgo(self, obj):
        return obj.get_indice_riesgo()

    def get_clasificacion_riesgo(self, obj):
        return obj.get_clasificacion_riesgo()


# =============================================================================
# FIN DEL ARCHIVO
# =============================================================================
