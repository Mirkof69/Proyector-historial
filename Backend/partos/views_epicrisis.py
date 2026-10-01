"""API de la epicrisis del parto, sus campos configurables y las tablas de Capurro/Ballard.

/api/partos/epicrisis/                 CRUD (médico y administrador escriben)
/api/partos/epicrisis/sugerencia/?parto=ID   borrador prellenado con los datos del parto
/api/partos/epicrisis/{id}/firmar/     la deja firmada (ya no se edita)
/api/partos/epicrisis/{id}/reabrir/    solo administrador, con motivo; auditado
/api/partos/epicrisis/{id}/pdf/        documento para el expediente
/api/partos/epicrisis-campos/          campos propios del hospital (escribe el administrador)
/api/partos/edad-gestacional-rn/       signos y puntos de Capurro y Ballard
"""
from __future__ import annotations

import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response

from core.permissions import EsSoloAdministrador, EsSoloMedico, FetalMedicalPermission

from .edad_gestacional_rn import tablas
from .models import Parto
from .models_epicrisis import CampoAdicionalEpicrisis, Epicrisis
from .serializers_epicrisis import CampoAdicionalEpicrisisSerializer, EpicrisisSerializer

logger = logging.getLogger(__name__)


def _auditar(request, accion: str, detalle: str) -> None:
    try:
        from auditoria.models import RegistroAuditoria

        RegistroAuditoria.registrar(usuario=request.user, accion=accion, modulo="Epicrisis",
                                    detalle=detalle, request=request)
    except Exception:
        logger.warning("No se pudo auditar la epicrisis", exc_info=True)


class EpicrisisViewSet(viewsets.ModelViewSet):
    serializer_class = EpicrisisSerializer
    filterset_fields = ["parto", "estado"]

    def get_permissions(self):
        if self.action == "reabrir":
            return [EsSoloAdministrador()]
        if self.request.method in SAFE_METHODS:
            return [FetalMedicalPermission()]
        return [FetalMedicalPermission(), EsSoloMedico()]

    def get_queryset(self):
        return Epicrisis.objects.select_related("parto__paciente", "medico").order_by("-fecha_creacion")

    def perform_create(self, serializer):
        epicrisis = serializer.save(creado_por=self.request.user)
        _auditar(self.request, "CREAR", f"Epicrisis {epicrisis.pk} del parto {epicrisis.parto_id}")

    def perform_update(self, serializer):
        epicrisis = serializer.save()
        _auditar(self.request, "ACTUALIZAR", f"Epicrisis {epicrisis.pk} del parto {epicrisis.parto_id}")

    def destroy(self, request, *args, **kwargs):
        epicrisis = self.get_object()
        if epicrisis.estado == "firmada":
            return Response({"error": "Una epicrisis firmada no se borra: es parte del expediente."},
                            status=status.HTTP_409_CONFLICT)
        _auditar(request, "ELIMINAR", f"Epicrisis {epicrisis.pk} (borrador) del parto {epicrisis.parto_id}")
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def sugerencia(self, request):
        """Borrador con lo que el sistema ya sabe del parto, para no volver a escribirlo."""
        try:
            parto = Parto.objects.select_related("paciente", "embarazo").get(pk=request.query_params.get("parto"))
        except (Parto.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Indique un parto existente (?parto=ID)."}, status=status.HTTP_400_BAD_REQUEST)
        if hasattr(parto, "epicrisis"):
            return Response({"error": "Este parto ya tiene epicrisis.", "id": parto.epicrisis.pk},
                            status=status.HTTP_409_CONFLICT)
        procedimientos = []
        tipo = (parto.tipo_parto or "").replace("_", " ")
        if tipo:
            procedimientos.append(f"Parto {tipo}")
        if parto.episiotomia:
            procedimientos.append("Episiotomía" + (f" {parto.tipo_episiotomia}" if parto.tipo_episiotomia else ""))
        if parto.desgarros:
            procedimientos.append("Reparación de desgarro" + (f" grado {parto.grado_desgarros}" if parto.grado_desgarros else ""))
        if parto.analgesia_utilizada:
            procedimientos.append("Analgesia" + (f" {parto.tipo_analgesia}" if parto.tipo_analgesia else ""))
        if parto.oxitocina_utilizada:
            procedimientos.append("Oxitocina" + (f" {parto.dosis_oxitocina}" if parto.dosis_oxitocina else ""))
        rns = list(parto.recien_nacidos.all())
        resumen_rn = "; ".join(
            f"RN {r.numero_gemelo or i + 1}: {r.get_sexo_display()}, {r.peso_nacimiento} g, Apgar "
            f"{r.apgar_1_minuto}/{r.apgar_5_minutos}" for i, r in enumerate(rns))
        eg = parto.edad_gestacional_parto or ""
        return Response({
            "parto": parto.pk,
            "fecha_egreso": timezone.localtime().replace(second=0, microsecond=0).isoformat(),
            "diagnostico_ingreso": f"Embarazo de {eg} semanas en trabajo de parto" if eg else "Embarazo en trabajo de parto",
            "diagnostico_egreso": f"Puerperio inmediato post parto {tipo}".strip(),
            "resumen_clinico": (f"Ingresa el {timezone.localtime(parto.fecha_ingreso or parto.fecha_parto):%d/%m/%Y %H:%M}. "
                                f"Parto {tipo} el {timezone.localtime(parto.fecha_parto):%d/%m/%Y %H:%M}. {resumen_rn}").strip(),
            "procedimientos": ". ".join(procedimientos),
            "complicaciones": parto.complicaciones_maternas or "",
            "condicion_materna_egreso": "con_patologia" if parto.hemorragia_postparto or parto.complicaciones_maternas else "sana",
        })

    @action(detail=True, methods=["post"])
    def firmar(self, request, pk=None):
        epicrisis = self.get_object()
        if request.data.get("matricula_profesional"):
            epicrisis.matricula_profesional = str(request.data["matricula_profesional"]).strip()
        try:
            epicrisis.firmar(request.user)
        except DjangoValidationError as e:
            detalle = e.message_dict if hasattr(e, "error_dict") else {"error": e.messages[0]}
            return Response(detalle, status=status.HTTP_400_BAD_REQUEST)
        _auditar(request, "FIRMAR", f"Epicrisis {epicrisis.pk} firmada (matrícula {epicrisis.matricula_profesional})")
        return Response(self.get_serializer(epicrisis).data)

    @action(detail=True, methods=["post"])
    def reabrir(self, request, pk=None):
        epicrisis = self.get_object()
        motivo = str(request.data.get("motivo", "")).strip()
        if len(motivo) < 10:
            return Response({"motivo": "Explique por qué se reabre (al menos 10 caracteres)."},
                            status=status.HTTP_400_BAD_REQUEST)
        if epicrisis.estado != "firmada":
            return Response({"error": "Solo se reabre una epicrisis firmada."}, status=status.HTTP_409_CONFLICT)
        epicrisis.estado = "borrador"
        epicrisis.fecha_firma = None
        epicrisis.save(update_fields=["estado", "fecha_firma", "fecha_modificacion"])
        _auditar(request, "REABRIR", f"Epicrisis {epicrisis.pk} reabierta: {motivo}")
        return Response(self.get_serializer(epicrisis).data)

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        from reportes.pdf_clinico import PdfClinico

        e = self.get_object()
        parto = e.parto
        pac = parto.paciente
        datos = self.get_serializer(e).data
        pdf = PdfClinico("Epicrisis obstétrica" + ("" if e.estado == "firmada" else " — BORRADOR (sin firma)"),
                         f"Paciente: {datos['paciente_nombre']} · CI {getattr(pac, 'ci', '') or '—'} · "
                         f"Historia {getattr(pac, 'id_clinico', '') or pac.pk}")
        pdf.seccion("Internación")
        pdf.ficha([
            ("Ingreso", timezone.localtime(parto.fecha_ingreso or parto.fecha_parto).strftime("%d/%m/%Y %H:%M")),
            ("Egreso", timezone.localtime(e.fecha_egreso).strftime("%d/%m/%Y %H:%M")),
            ("Días de internación", e.dias_internacion),
            ("Tipo de egreso", e.get_tipo_egreso_display()),
            ("Condición de la madre", e.get_condicion_materna_egreso_display()),
            ("Pronóstico", e.get_pronostico_display()),
        ])
        if e.tipo_egreso == "referencia":
            pdf.parrafo(f"<b>Referida a:</b> {e.establecimiento_referencia}")
        pdf.seccion("Diagnósticos")
        pdf.ficha([("De ingreso", f"{e.diagnostico_ingreso} {f'({e.cie10_ingreso})' if e.cie10_ingreso else ''}"),
                   ("De egreso", f"{e.diagnostico_egreso} {f'({e.cie10_egreso})' if e.cie10_egreso else ''}")], columnas=1)
        for titulo, texto in (("Resumen clínico", e.resumen_clinico), ("Exámenes relevantes", e.examenes_relevantes),
                              ("Tratamiento recibido", e.tratamiento_recibido), ("Procedimientos", e.procedimientos),
                              ("Complicaciones", e.complicaciones)):
            if texto:
                pdf.seccion(titulo)
                pdf.parrafo(texto)
        rns = list(parto.recien_nacidos.all())
        if rns:
            pdf.seccion("Recién nacidos")
            pdf.tabla(["N.º", "Sexo", "Peso (g)", "Talla (cm)", "Apgar 1/5", "EG por examen", "Destino"], [[
                r.numero_gemelo or i + 1, r.get_sexo_display(), r.peso_nacimiento, r.talla_nacimiento,
                f"{r.apgar_1_minuto}/{r.apgar_5_minutos}",
                f"{r.edad_gestacional_examen_semanas} s ({r.get_metodo_edad_gestacional_display()})"
                if r.edad_gestacional_examen_semanas else "No evaluada",
                (r.destino_rn or "").replace("_", " ")] for i, r in enumerate(rns)])
        pdf.seccion("Al egreso")
        pdf.ficha([
            ("Consejería en anticoncepción", "Sí" if e.consejeria_anticoncepcion else "No"),
            ("Método elegido", e.get_metodo_anticonceptivo_display()),
            ("Lactancia materna exclusiva", "Sí" if e.lactancia_materna_exclusiva else "No"),
            ("Signos de alarma explicados", "Sí" if e.signos_alarma_explicados else "No"),
            ("Próximo control", e.proximo_control.strftime("%d/%m/%Y") if e.proximo_control else "—"),
            ("Lugar", e.lugar_proximo_control or "—"),
        ])
        if e.indicaciones_alta:
            pdf.parrafo(f"<b>Indicaciones:</b> {e.indicaciones_alta}")
        campos = {c.clave: c for c in CampoAdicionalEpicrisis.objects.filter(activo=True)}
        extra = [(campos[k].etiqueta, ("Sí" if v is True else "No" if v is False else v))
                 for k, v in (e.campos_adicionales or {}).items() if k in campos]
        if extra:
            pdf.seccion("Datos adicionales del establecimiento")
            pdf.ficha(extra)
        pdf.seccion("Firma")
        if e.estado == "firmada":
            pdf.parrafo(f"Firmado por <b>{datos['medico_nombre']}</b> · Matrícula {e.matricula_profesional} · "
                        f"{timezone.localtime(e.fecha_firma):%d/%m/%Y %H:%M}")
        else:
            pdf.parrafo("Documento sin firmar: no tiene validez hasta que el médico responsable lo firme.")
        _auditar(request, "EXPORTAR", f"PDF de la epicrisis {e.pk}")
        respuesta = HttpResponse(pdf.generar().getvalue(), content_type="application/pdf")
        respuesta["Content-Disposition"] = f'attachment; filename="epicrisis_parto_{parto.pk}.pdf"'
        return respuesta


class CampoAdicionalEpicrisisViewSet(viewsets.ModelViewSet):
    """Todos los clínicos leen la definición (la necesita el formulario); solo el administrador la cambia."""

    serializer_class = CampoAdicionalEpicrisisSerializer
    queryset = CampoAdicionalEpicrisis.objects.all()

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [FetalMedicalPermission()]
        return [EsSoloAdministrador()]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def tablas_edad_gestacional_rn(_request):
    return Response(tablas())
