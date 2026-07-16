"""Serializers module."""
import re
from datetime import datetime

from django.core.validators import EmailValidator
from django.utils import timezone
from rest_framework import serializers

from .fields import compute_search_hash
from .models import Paciente


def _validar_ci_disponible(value, instancia=None):
    """Rechaza CI duplicado ANTES de llegar a la BD. La unicidad vive en
    ci_hash (el campo ci va cifrado con IV aleatorio); sin este chequeo un
    duplicado revienta con IntegrityError → 500 en vez de un 400 claro."""
    qs = Paciente.objects.filter(ci_hash=compute_search_hash(value))
    if instancia is not None:
        qs = qs.exclude(pk=instancia.pk)
    if qs.exists():
        raise serializers.ValidationError(
            "Ya existe un paciente registrado con esta cédula de identidad",
        )


class PacienteSerializer(serializers.ModelSerializer):
    """Serializer completo para el modelo Paciente"""

    # Campos calculados
    edad = serializers.SerializerMethodField()
    nombre_completo = serializers.SerializerMethodField()
    embarazos_activos = serializers.SerializerMethodField()
    imc = serializers.SerializerMethodField()

    # ✅ TRAZABILIDAD - Información del usuario
    created_by_display = serializers.SerializerMethodField()
    updated_by_display = serializers.SerializerMethodField()

    # ✅ DATOS RELACIONADOS - Para Historia Clínica
    embarazos = serializers.SerializerMethodField()
    controles_prenatales = serializers.SerializerMethodField()
    ecografias = serializers.SerializerMethodField()
    partos = serializers.SerializerMethodField()
    citas = serializers.SerializerMethodField()
    examenes_laboratorio = serializers.SerializerMethodField()
    antecedentes_gineco = serializers.SerializerMethodField()
    antecedentes_patologicos = serializers.SerializerMethodField()

    # Alias para compatibilidad con frontend
    grupo_sanguineo = serializers.CharField(
        source="tipo_sangre",
        required=False,
        allow_blank=True,
        allow_null=True,
        read_only=True,
    )

    class Meta:
        """Meta"""
        model = Paciente
        fields = [
            "id",
            "id_clinico",
            "nombre",
            "apellido_paterno",
            "apellido_materno",
            "nombre_completo",
            "fecha_nacimiento",
            "edad",
            "genero",
            "ci",  # CORREGIDO: era cedula_identidad
            "telefono",  # CORREGIDO: era telefono_principal
            "email",
            "direccion",
            "ciudad",
            "pais",
            "estado_civil",
            "ocupacion",
            "observaciones",
            "activo",
            "fecha_registro",
            "fecha_actualizacion",
            "embarazos_activos",
            # ✅ NUEVOS CAMPOS MÉDICOS - AGREGADOS
            "tipo_sangre",
            "grupo_sanguineo",  # Alias para frontend
            "factor_rh",
            "numero_seguro_social",
            "estado_paciente",
            "fecha_baja",
            # ✅ NUEVOS CAMPOS - CONTACTO DE EMERGENCIA
            "contacto_emergencia_nombre",
            "contacto_emergencia_telefono",
            "contacto_emergencia_relacion",
            # ✅ NUEVOS CAMPOS - DATOS ANTROPOMÉTRICOS
            "peso_kg",
            "altura_cm",
            "imc",
            # ✅ TRAZABILIDAD
            "created_by",
            "updated_by",
            "created_by_display",
            "updated_by_display",
            # ✅ DATOS RELACIONADOS
            "embarazos",
            "controles_prenatales",
            "ecografias",
            "partos",
            "citas",
            "examenes_laboratorio",
            "antecedentes_gineco",
            "antecedentes_patologicos",
        ]
        read_only_fields = [
            "id",
            "id_clinico",
            "fecha_registro",
            "fecha_actualizacion",
            "created_by",
            "updated_by",
        ]

    def get_nombre_completo(self, obj):
        """Retorna nombre completo del paciente"""
        apellido_materno = f" {obj.apellido_materno}" if obj.apellido_materno else ""
        return f"{obj.nombre} {obj.apellido_paterno}{apellido_materno}"

    def get_edad(self, obj):
        """Calcula edad del paciente"""

        today = timezone.localdate()
        edad = today.year - obj.fecha_nacimiento.year
        if today.month < obj.fecha_nacimiento.month or (
            today.month == obj.fecha_nacimiento.month
            and today.day < obj.fecha_nacimiento.day
        ):
            edad -= 1
        return edad

    def get_embarazos_activos(self, obj):
        """Cuenta embarazos activos"""
        return obj.embarazos.filter(estado="activo").count()

    def get_imc(self, obj):
        """Retorna el IMC calculado"""
        return obj.imc  # Usa la propiedad del modelo

    def get_created_by_display(self, obj):
        """✅ TRAZABILIDAD: Información del usuario que creó el registro"""
        if obj.created_by:
            return {
                "id": obj.created_by.id,
                "email": obj.created_by.email,
                "nombre_completo": obj.created_by.get_full_name()
                if hasattr(obj.created_by, "get_full_name")
                else obj.created_by.email,
                "fecha": obj.fecha_registro.isoformat() if obj.fecha_registro else None,
            }
        return None

    def get_updated_by_display(self, obj):
        """✅ TRAZABILIDAD: Información del usuario que actualizó el registro"""
        if obj.updated_by:
            return {
                "id": obj.updated_by.id,
                "email": obj.updated_by.email,
                "nombre_completo": obj.updated_by.get_full_name()
                if hasattr(obj.updated_by, "get_full_name")
                else obj.updated_by.email,
                "fecha": obj.fecha_actualizacion.isoformat()
                if obj.fecha_actualizacion
                else None,
            }
        return None

    def get_embarazos(self, obj):
        """✅ DATOS RELACIONADOS: Lista de embarazos del paciente"""
        from embarazos.serializers import EmbarazoListSerializer

        embarazos = obj.embarazos.all().order_by("-fecha_registro")
        return EmbarazoListSerializer(embarazos, many=True).data

    def get_controles_prenatales(self, obj):
        """✅ DATOS RELACIONADOS: Lista de controles prenatales del paciente"""
        from controles.serializers import ControlPrenatalListSerializer

        controles = obj.controles_prenatales.all().order_by("-fecha_control")
        return ControlPrenatalListSerializer(controles, many=True).data

    def get_ecografias(self, obj):
        """✅ DATOS RELACIONADOS: Lista de ecografías del paciente"""
        from ecografias.serializers import EcografiaSerializer

        ecografias = obj.ecografias.all().order_by("-fecha_ecografia")
        return EcografiaSerializer(ecografias, many=True).data

    def get_partos(self, obj):
        """✅ DATOS RELACIONADOS: Lista de partos del paciente"""
        from partos.serializers import PartoResumenSerializer

        partos = obj.partos.all().order_by("-fecha_parto")
        return PartoResumenSerializer(partos, many=True).data

    def get_citas(self, obj):
        """✅ DATOS RELACIONADOS: Lista de citas del paciente"""
        from citas.serializers import CitaListSerializer

        citas = obj.citas.all().order_by("-fecha_cita")
        return CitaListSerializer(citas, many=True).data

    def get_examenes_laboratorio(self, obj):
        """✅ DATOS RELACIONADOS: Lista de exámenes de laboratorio del paciente"""
        from laboratorio.serializers import ExamenLaboratorioListSerializer

        examenes = obj.examenes_laboratorio.all().order_by("-fecha_solicitud")
        return ExamenLaboratorioListSerializer(examenes, many=True).data

    def get_antecedentes_gineco(self, obj):
        """✅ DATOS RELACIONADOS: Antecedente gineco-obstétrico del paciente (OneToOne)"""
        from antecedentes.serializers import AntecedenteGinecoObstetricoSerializer

        try:
            if hasattr(obj, "antecedente_gineco") and obj.antecedente_gineco:
                return [
                    AntecedenteGinecoObstetricoSerializer(obj.antecedente_gineco).data,
                ]
        except Exception:
            pass
        return []

    def get_antecedentes_patologicos(self, obj):
        """✅ DATOS RELACIONADOS: Lista de antecedentes patológicos del paciente"""
        from antecedentes.serializers import AntecedentePatologicoSerializer

        antecedentes = obj.antecedentes_patologicos.all().order_by("-fecha_registro")
        return AntecedentePatologicoSerializer(antecedentes, many=True).data

    def validate_ci(self, value):
        """Valida formato de cédula boliviana"""
        if value:
            # Remover espacios y guiones
            ci = re.sub(r"[\s\-]", "", value)
            # Validar que sean solo números
            if not ci.isdigit():
                raise serializers.ValidationError(
                    "La cédula debe contener solo números",
                )
            # Validar longitud (5-10 dígitos en Bolivia)
            if len(ci) < 5 or len(ci) > 10:
                raise serializers.ValidationError(
                    "La cédula debe tener entre 5 y 10 dígitos",
                )
            _validar_ci_disponible(value, self.instance)
        return value

    def validate_telefono(self, value):
        """Valida formato de teléfono boliviano"""
        if value:
            # Remover espacios, guiones y paréntesis
            telefono = re.sub(r"[\s\-\(\)]", "", value)
            # Validar que sean solo números
            if not telefono.isdigit():
                raise serializers.ValidationError(
                    "El teléfono debe contener solo números",
                )
            # Validar longitud (7-8 dígitos)
            if len(telefono) < 7 or len(telefono) > 8:
                raise serializers.ValidationError(
                    "El teléfono debe tener 7 u 8 dígitos",
                )
        return value

    def validate_email(self, value):
        """Valida formato de email"""
        if value:
            validator = EmailValidator()
            validator(value)
        return value

    def validate(self, attrs):
        """Validaciones generales"""
        # Validar fecha de nacimiento no sea futura
        if "fecha_nacimiento" in attrs:
            if attrs["fecha_nacimiento"] > timezone.localdate():
                raise serializers.ValidationError(
                    {"fecha_nacimiento": "La fecha de nacimiento no puede ser futura"},
                )

            # Validar edad mínima (10 años) y máxima (100 años)
            edad = timezone.localdate().year - attrs["fecha_nacimiento"].year
            if edad < 10:
                raise serializers.ValidationError(
                    {"fecha_nacimiento": "El paciente debe tener al menos 10 años"},
                )
            if edad > 100:
                raise serializers.ValidationError(
                    {"fecha_nacimiento": "Fecha de nacimiento inválida"},
                )

        return attrs


class PacienteListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""

    nombre_completo = serializers.SerializerMethodField()
    edad = serializers.SerializerMethodField()
    embarazos_activos = serializers.SerializerMethodField()

    # ✅ NUEVOS CAMPOS OBSTÉTRICOS
    numero_gesta = serializers.SerializerMethodField()
    numero_para = serializers.SerializerMethodField()
    numero_abortos = serializers.SerializerMethodField()
    numero_cesareas = serializers.SerializerMethodField()
    ultimo_estado_obstetrico = serializers.SerializerMethodField()
    fecha_ultimo_evento = serializers.SerializerMethodField()

    # Alias para compatibilidad con frontend
    grupo_sanguineo = serializers.CharField(
        source="tipo_sangre",
        required=False,
        allow_blank=True,
        allow_null=True,
        read_only=True,
    )

    class Meta:
        """Meta"""
        model = Paciente
        fields = [
            "id",
            "id_clinico",
            "nombre",  # ✅ AGREGADO: Campo individual necesario para frontend
            "apellido_paterno",  # ✅ AGREGADO: Campo individual necesario para frontend
            "apellido_materno",  # ✅ AGREGADO: Campo individual necesario para frontend
            "nombre_completo",
            "fecha_nacimiento",  # ✅ AGREGADO: NECESARIO para editar paciente
            "edad",
            "genero",
            "telefono",  # CORREGIDO: era telefono_principal
            "ci",  # CORREGIDO: era uuid (que no existe)
            "email",  # ✅ AGREGADO: Para expediente rápido
            "direccion",  # ✅ AGREGADO: Para expediente rápido
            "ciudad",  # ✅ AGREGADO: Para expediente rápido
            "pais",  # ✅ AGREGADO: País del paciente
            "estado_civil",  # ✅ AGREGADO: Estado civil del paciente
            "ocupacion",  # ✅ AGREGADO: Ocupación del paciente
            "observaciones",  # ✅ AGREGADO: Observaciones del paciente
            "tipo_sangre",  # ✅ AGREGADO: Para expediente rápido
            "grupo_sanguineo",  # Alias para frontend
            "activo",
            "embarazos_activos",
            "fecha_registro",
            # ✅ NUEVOS CAMPOS OBSTÉTRICOS
            "numero_gesta",
            "numero_para",
            "numero_abortos",
            "numero_cesareas",
            "ultimo_estado_obstetrico",
            "fecha_ultimo_evento",
            # ✅ CAMPOS ANTROPOMÉTRICOS
            "peso_kg",
            "altura_cm",
            "imc",
            "factor_rh",
        ]

    def get_nombre_completo(self, obj):
        """Get nombre completo"""
        apellido_materno = f" {obj.apellido_materno}" if obj.apellido_materno else ""
        return f"{obj.nombre} {obj.apellido_paterno}{apellido_materno}"

    def get_edad(self, obj):
        """Get edad"""

        today = timezone.localdate()
        edad = today.year - obj.fecha_nacimiento.year
        if today.month < obj.fecha_nacimiento.month or (
            today.month == obj.fecha_nacimiento.month
            and today.day < obj.fecha_nacimiento.day
        ):
            edad -= 1
        return edad

    def get_embarazos_activos(self, obj):
        """Verifica si tiene embarazos activos"""
        return obj.embarazos.filter(estado="activo").exists()

    def _get_ultimo_embarazo(self, obj):
        """Cache del último embarazo para evitar 4 queries separadas por paciente (N+1)."""
        cache_attr = "_cached_ultimo_embarazo"
        if not hasattr(obj, cache_attr):
            setattr(obj, cache_attr, obj.embarazos.order_by("-fecha_registro").first())
        return getattr(obj, cache_attr)

    def get_numero_gesta(self, obj):
        """Obtiene el número de gesta del último embarazo"""
        ue = self._get_ultimo_embarazo(obj)
        return ue.numero_gesta if ue else 0

    def get_numero_para(self, obj):
        """Obtiene el número de para del último embarazo"""
        ue = self._get_ultimo_embarazo(obj)
        return ue.numero_para if ue else 0

    def get_numero_abortos(self, obj):
        """Obtiene el número de abortos del último embarazo"""
        ue = self._get_ultimo_embarazo(obj)
        return ue.numero_abortos if ue else 0

    def get_numero_cesareas(self, obj):
        """Obtiene el número de cesáreas del último embarazo"""
        ue = self._get_ultimo_embarazo(obj)
        return ue.numero_cesareas if ue else 0

    def get_ultimo_estado_obstetrico(self, obj):
        try:
            eventos = []

            for e in obj.embarazos.all():
                if not e.fecha_registro:
                    continue
                if e.estado == "activo":
                    eventos.append((e.fecha_registro, "GESTANDO"))
                elif e.estado == "perdida":
                    eventos.append((e.fecha_registro, "Último: Aborto"))

            ultimo_control = obj.controles_prenatales.order_by("-fecha_control").first()
            if ultimo_control and ultimo_control.fecha_control:
                eventos.append((
                    datetime.combine(ultimo_control.fecha_control, datetime.min.time()),
                    f"Último Control: {ultimo_control.fecha_control.strftime('%d/%m/%Y')}",
                ))

            for parto in obj.partos.all():
                if not parto.fecha_parto:
                    continue
                tipo = "Cesárea" if parto.tipo_parto and "cesarea" in parto.tipo_parto.lower() else "Parto Normal"
                eventos.append((
                    datetime.combine(parto.fecha_parto, datetime.min.time()),
                    f"Último: {tipo}",
                ))

            if not eventos:
                return None
            return max(eventos, key=lambda x: x[0])[1]

        except Exception:
            return None

    def get_fecha_ultimo_evento(self, obj):
        try:
            fechas: list[datetime] = []

            ultimo_embarazo = obj.embarazos.order_by("-fecha_registro").first()
            if ultimo_embarazo and ultimo_embarazo.fecha_registro:
                fechas.append(ultimo_embarazo.fecha_registro)

            ultimo_control = obj.controles_prenatales.order_by("-fecha_control").first()
            if ultimo_control and ultimo_control.fecha_control:
                fechas.append(datetime.combine(ultimo_control.fecha_control, datetime.min.time()))

            ultimo_parto = obj.partos.order_by("-fecha_parto").first()
            if ultimo_parto and ultimo_parto.fecha_parto:
                fechas.append(datetime.combine(ultimo_parto.fecha_parto, datetime.min.time()))

            if not fechas:
                return None

            fecha_max = max(fechas)
            return fecha_max.date().isoformat() if hasattr(fecha_max, "date") else str(fecha_max)

        except Exception:
            return None


class PacienteCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar pacientes"""

    # Alias para compatibilidad con frontend
    grupo_sanguineo = serializers.CharField(
        source="tipo_sangre", required=False, allow_blank=True, allow_null=True,
    )

    class Meta:
        """Meta"""
        model = Paciente
        fields = [
            "nombre",
            "apellido_paterno",
            "apellido_materno",
            "fecha_nacimiento",
            "genero",
            "ci",  # CORREGIDO: era cedula_identidad
            "telefono",  # CORREGIDO: era telefono_principal
            "email",
            "direccion",
            "ciudad",
            "pais",
            "estado_civil",
            "ocupacion",
            "observaciones",
            "activo",
            # ✅ NUEVOS CAMPOS MÉDICOS - AGREGADOS
            "tipo_sangre",
            "grupo_sanguineo",  # Alias para frontend
            "factor_rh",
            "numero_seguro_social",
            "estado_paciente",
            "fecha_baja",
            # ✅ NUEVOS CAMPOS - CONTACTO DE EMERGENCIA
            "contacto_emergencia_nombre",
            "contacto_emergencia_telefono",
            "contacto_emergencia_relacion",
            # ✅ NUEVOS CAMPOS - DATOS ANTROPOMÉTRICOS
            "peso_kg",
            "altura_cm",
            # Consentimiento de tratamiento de datos (Ley 164 Bolivia)
            "consentimiento_datos_aceptado",
            "consentimiento_datos_fecha",
            "consentimiento_datos_ip",
        ]
        read_only_fields = ["consentimiento_datos_fecha", "consentimiento_datos_ip"]

    def validate_consentimiento_datos_aceptado(self, value):
        """Ley 164 (Bolivia), Art. 22 y Reglamento DS 1793/2013 Art. 56-57:
        el tratamiento de datos personales requiere consentimiento expreso
        previo del titular. No se puede crear un paciente sin esto."""
        if not self.instance and not value:
            raise serializers.ValidationError(
                "Se requiere el consentimiento expreso del paciente (o su "
                "representante) para el tratamiento de sus datos personales, "
                "conforme a la Ley 164.",
            )
        return value

    def create(self, validated_data):
        """Registra fecha/IP del consentimiento server-side — nunca se
        confia en un timestamp/IP que mande el cliente."""
        if validated_data.get("consentimiento_datos_aceptado"):
            from django.utils import timezone as tz
            validated_data["consentimiento_datos_fecha"] = tz.now()
            request = self.context.get("request")
            if request:
                validated_data["consentimiento_datos_ip"] = request.META.get("REMOTE_ADDR")
        return super().create(validated_data)

    def validate_ci(self, value):
        """Valida formato de cédula boliviana"""
        if value:
            ci = re.sub(r"[\s\-]", "", value)
            if not ci.isdigit():
                raise serializers.ValidationError(
                    "La cédula debe contener solo números",
                )
            if len(ci) < 5 or len(ci) > 10:
                raise serializers.ValidationError(
                    "La cédula debe tener entre 5 y 10 dígitos",
                )
            _validar_ci_disponible(value, self.instance)
        return value

    def validate_telefono(self, value):
        """Valida formato de teléfono boliviano"""
        if value:
            telefono = re.sub(r"[\s\-\(\)]", "", value)
            if not telefono.isdigit():
                raise serializers.ValidationError(
                    "El teléfono debe contener solo números",
                )
            if len(telefono) < 7 or len(telefono) > 8:
                raise serializers.ValidationError(
                    "El teléfono debe tener 7 u 8 dígitos",
                )
        return value

    def validate_contacto_emergencia_telefono(self, value):
        """Valida formato de teléfono del contacto de emergencia"""
        if value:
            telefono = re.sub(r"[\s\-\(\)]", "", value)
            if not telefono.isdigit():
                raise serializers.ValidationError(
                    "El teléfono debe contener solo números",
                )
            if len(telefono) < 7 or len(telefono) > 8:
                raise serializers.ValidationError(
                    "El teléfono debe tener 7 u 8 dígitos",
                )
        return value

    def validate(self, attrs):
        """Validaciones generales"""
        # Validar que la fecha de nacimiento no sea null si se está enviando
        if "fecha_nacimiento" in attrs:
            if attrs["fecha_nacimiento"] is None:
                raise serializers.ValidationError(
                    {"fecha_nacimiento": "La fecha de nacimiento es obligatoria"},
                )

            if attrs["fecha_nacimiento"] > timezone.localdate():
                raise serializers.ValidationError(
                    {"fecha_nacimiento": "La fecha de nacimiento no puede ser futura"},
                )

            edad = timezone.localdate().year - attrs["fecha_nacimiento"].year
            if edad < 10:
                raise serializers.ValidationError(
                    {"fecha_nacimiento": "El paciente debe tener al menos 10 años"},
                )
            if edad > 100:
                raise serializers.ValidationError(
                    {"fecha_nacimiento": "Fecha de nacimiento inválida"},
                )

        return attrs
