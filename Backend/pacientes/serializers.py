"""Serializers module."""
import re
from datetime import date, datetime

from django.core.validators import EmailValidator
from rest_framework import serializers

from .models import Paciente


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

        today = date.today()
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
            if attrs["fecha_nacimiento"] > date.today():
                raise serializers.ValidationError(
                    {"fecha_nacimiento": "La fecha de nacimiento no puede ser futura"},
                )

            # Validar edad mínima (10 años) y máxima (100 años)
            edad = date.today().year - attrs["fecha_nacimiento"].year
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

        today = date.today()
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
        """Determina el ÚLTIMO ESTADO real del paciente mirando TODOS los eventos:
            pass
        - Embarazos (activo, finalizado, perdida)
        - Controles Prenatales
        - Partos
        """
        try:
            from partos.models import Parto

            # Recopilar TODOS los eventos con sus fechas
            eventos = []

            # 1. EMBARAZOS
            for embarazo in obj.embarazos.all():
                try:
                    fecha = embarazo.fecha_registro
                    if not fecha:
                        continue

                    if embarazo.estado == "activo":
                        eventos.append(
                            {
                                "tipo": "embarazo_activo",
                                "fecha": fecha,
                                "descripcion": "GESTANDO",
                                "embarazo": embarazo,
                            },
                        )
                    elif embarazo.estado == "perdida":
                        eventos.append(
                            {
                                "tipo": "aborto",
                                "fecha": fecha,
                                "descripcion": "Último: Aborto",
                                "embarazo": embarazo,
                            },
                        )
                except Exception:
                    # Log pero continuar con otros embarazos
                    continue

            # 2. CONTROLES PRENATALES
            try:
                ultimo_control = obj.controles_prenatales.order_by(
                    "-fecha_control",
                ).first()
                if ultimo_control and ultimo_control.fecha_control:
                    eventos.append(
                        {
                            "tipo": "control",
                            "fecha": datetime.combine(
                                ultimo_control.fecha_control, datetime.min.time(),
                            ),
                            "descripcion": f"Último Control: {ultimo_control.fecha_control.strftime('%d/%m/%Y')}",
                            "control": ultimo_control,
                        },
                    )
            except Exception:
                # Log pero continuar
                pass

            # 3. PARTOS
            try:
                for parto in Parto.objects.filter(paciente=obj).order_by(
                    "-fecha_parto",
                ):
                    try:
                        if not parto.fecha_parto:
                            continue

                        # ✅ Validación: Verificar que tipo_parto no sea None
                        if parto.tipo_parto:
                            tipo_parto_str = (
                                "Cesárea"
                                if "cesarea" in parto.tipo_parto.lower()
                                else "Parto Normal"
                            )
                        else:
                            tipo_parto_str = "Parto"  # Fallback si no hay tipo_parto

                        eventos.append(
                            {
                                "tipo": "parto",
                                "fecha": datetime.combine(
                                    parto.fecha_parto, datetime.min.time(),
                                ),
                                "descripcion": f"Último: {tipo_parto_str}",
                                "parto": parto,
                            },
                        )
                    except Exception:
                        # Log pero continuar con otros partos
                        continue
            except Exception:
                # Log pero continuar
                pass

            # Si no hay eventos, retornar None
            if not eventos:
                return None

            # Ordenar eventos por fecha (más reciente primero)
            eventos_ordenados = sorted(eventos, key=lambda x: x["fecha"], reverse=True)
            evento_mas_reciente = eventos_ordenados[0]

            # Retornar descripción del evento más reciente
            return evento_mas_reciente["descripcion"]

        except Exception:
            # Si hay cualquier error, retornar None en vez de fallar
            return None

    def get_fecha_ultimo_evento(self, obj):
        """Obtiene la fecha del ÚLTIMO EVENTO real (embarazo, control o parto)
        """
        try:

            fechas = []

            # Embarazos
            try:
                ultimo_embarazo = obj.embarazos.order_by("-fecha_registro").first()
                if ultimo_embarazo and ultimo_embarazo.fecha_registro:
                    fechas.append(ultimo_embarazo.fecha_registro)
            except Exception:
                pass

            # Controles
            try:
                ultimo_control = obj.controles_prenatales.order_by(
                    "-fecha_control",
                ).first()
                if ultimo_control and ultimo_control.fecha_control:
                    fechas.append(
                        datetime.combine(
                            ultimo_control.fecha_control, datetime.min.time(),
                        ),
                    )
            except Exception:
                pass

            # Partos
            try:
                from partos.models import Parto
                ultimo_parto = (
                    Parto.objects.filter(paciente=obj).order_by("-fecha_parto").first()
                )
                if ultimo_parto and ultimo_parto.fecha_parto:
                    fechas.append(
                        datetime.combine(ultimo_parto.fecha_parto, datetime.min.time()),
                    )
            except Exception:
                pass

            if not fechas:
                return None

            # Retornar la fecha más reciente
            fecha_mas_reciente = max(fechas)

            if hasattr(fecha_mas_reciente, "date"):
                return fecha_mas_reciente.date().isoformat()
            if hasattr(fecha_mas_reciente, "isoformat"):
                return fecha_mas_reciente.isoformat()
            return str(fecha_mas_reciente)

        except Exception:
            # Si hay cualquier error, retornar None
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
        ]

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

            if attrs["fecha_nacimiento"] > date.today():
                raise serializers.ValidationError(
                    {"fecha_nacimiento": "La fecha de nacimiento no puede ser futura"},
                )

            edad = date.today().year - attrs["fecha_nacimiento"].year
            if edad < 10:
                raise serializers.ValidationError(
                    {"fecha_nacimiento": "El paciente debe tener al menos 10 años"},
                )
            if edad > 100:
                raise serializers.ValidationError(
                    {"fecha_nacimiento": "Fecha de nacimiento inválida"},
                )

        return attrs
