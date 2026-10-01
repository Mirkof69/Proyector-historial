"""Epicrisis (resumen de egreso) del parto y sus campos configurables.

Contenido tomado de lo que exige el expediente clínico en Bolivia (Norma
Técnica para el Manejo del Expediente Clínico del Ministerio de Salud; la
epicrisis es el resumen que acompaña el egreso) y de la sección de egreso de
la Historia Clínica Perinatal CLAP/SMR-OPS que usa el SUS:

- identificación y fechas de ingreso y egreso, días de internación;
- diagnósticos de ingreso y de egreso con su código CIE-10;
- resumen clínico, exámenes relevantes, tratamiento y procedimientos;
- complicaciones, condición de la madre al egreso y tipo de egreso
  (alta médica, solicitada, referencia, fuga, fallecimiento);
- anticoncepción post evento obstétrico (consejería y método elegido) y
  lactancia materna;
- indicaciones al alta, signos de alarma explicados y próximo control;
- médico responsable con su matrícula profesional (firma).

Abierta a cada hospital: el administrador añade campos propios en
`CampoAdicionalEpicrisis` (sin programar) y sus valores se guardan en
`campos_adicionales`, validados contra esa definición.

Una epicrisis FIRMADA ya no se edita: es un documento del expediente. Si hay
que corregirla, el administrador la reabre y queda auditado.
"""
from __future__ import annotations

import re
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

CIE10 = re.compile(r"^[A-TV-Z]\d{2}(\.\d{1,2})?$")


class CampoAdicionalEpicrisis(models.Model):
    """Un campo que el hospital agrega a su epicrisis sin tocar el código."""

    TIPOS = [
        ("texto", "Texto corto"),
        ("parrafo", "Párrafo"),
        ("numero", "Número"),
        ("fecha", "Fecha"),
        ("si_no", "Sí / No"),
        ("opcion", "Una opción de una lista"),
    ]
    clave = models.SlugField(max_length=60, unique=True, help_text="Nombre interno, sin espacios: p. ej. «grupo_sanguineo_rn»")
    etiqueta = models.CharField(max_length=120)
    tipo = models.CharField(max_length=10, choices=TIPOS, default="texto")
    opciones = models.JSONField(default=list, blank=True, help_text="Solo para «opción»: lista de textos")
    obligatorio = models.BooleanField(default=False)
    ayuda = models.CharField(max_length=200, blank=True)
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "partos_epicrisis_campos"
        ordering = ["orden", "id"]
        verbose_name = "Campo adicional de epicrisis"
        verbose_name_plural = "Campos adicionales de epicrisis"

    def __str__(self):
        return self.etiqueta

    def clean(self):
        if self.tipo == "opcion" and not (isinstance(self.opciones, list) and self.opciones):
            raise ValidationError({"opciones": "Un campo de tipo «opción» necesita al menos una opción."})

    def validar_valor(self, valor) -> str | None:
        """Mensaje de error, o None si el valor sirve para este campo."""
        vacio = valor in (None, "", [])
        if vacio:
            return f"«{self.etiqueta}» es obligatorio." if self.obligatorio else None
        if self.tipo == "numero":
            try:
                float(valor)
            except (TypeError, ValueError):
                return f"«{self.etiqueta}» tiene que ser un número."
        elif self.tipo == "si_no" and not isinstance(valor, bool):
            return f"«{self.etiqueta}» tiene que ser sí o no."
        elif self.tipo == "fecha" and not (isinstance(valor, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", valor)):
            return f"«{self.etiqueta}» tiene que ser una fecha AAAA-MM-DD."
        elif self.tipo == "opcion" and valor not in self.opciones:
            return f"«{self.etiqueta}» tiene que ser una de: {', '.join(map(str, self.opciones))}."
        elif self.tipo in ("texto", "parrafo") and not isinstance(valor, str):
            return f"«{self.etiqueta}» tiene que ser texto."
        return None


class Epicrisis(models.Model):
    CONDICION_MATERNA = [
        ("sana", "Sana"),
        ("con_patologia", "Con patología"),
        ("traslado", "Trasladada"),
        ("fallecida", "Fallecida"),
    ]
    TIPO_EGRESO = [
        ("alta_medica", "Alta médica"),
        ("alta_solicitada", "Alta solicitada"),
        ("referencia", "Referencia a otro establecimiento"),
        ("fuga", "Fuga"),
        ("fallecimiento", "Fallecimiento"),
    ]
    METODO_ANTICONCEPTIVO = [
        ("ninguno", "Ninguno"),
        ("diu_post_evento", "DIU post evento obstétrico"),
        ("diu", "DIU"),
        ("implante", "Implante subdérmico"),
        ("inyectable", "Inyectable"),
        ("oral", "Anticonceptivo oral"),
        ("barrera", "Barrera (condón)"),
        ("ligadura_tubaria", "Ligadura tubaria"),
        ("mela", "MELA (lactancia y amenorrea)"),
        ("otro", "Otro"),
    ]
    PRONOSTICO = [("bueno", "Bueno"), ("reservado", "Reservado"), ("malo", "Malo")]
    ESTADOS = [("borrador", "Borrador"), ("firmada", "Firmada")]

    parto = models.OneToOneField("partos.Parto", on_delete=models.CASCADE, related_name="epicrisis")

    fecha_egreso = models.DateTimeField(verbose_name="Fecha y hora de egreso")
    diagnostico_ingreso = models.TextField(verbose_name="Diagnóstico de ingreso")
    cie10_ingreso = models.CharField(max_length=7, blank=True, verbose_name="CIE-10 de ingreso")
    diagnostico_egreso = models.TextField(verbose_name="Diagnóstico de egreso")
    cie10_egreso = models.CharField(max_length=7, blank=True, verbose_name="CIE-10 de egreso")
    resumen_clinico = models.TextField(verbose_name="Resumen clínico (motivo de ingreso y evolución)")
    examenes_relevantes = models.TextField(blank=True, verbose_name="Exámenes complementarios relevantes")
    tratamiento_recibido = models.TextField(blank=True, verbose_name="Tratamiento recibido")
    procedimientos = models.TextField(blank=True, verbose_name="Procedimientos realizados")
    complicaciones = models.TextField(blank=True, verbose_name="Complicaciones")

    condicion_materna_egreso = models.CharField(max_length=15, choices=CONDICION_MATERNA, default="sana")
    tipo_egreso = models.CharField(max_length=20, choices=TIPO_EGRESO, default="alta_medica")
    establecimiento_referencia = models.CharField(max_length=200, blank=True)

    consejeria_anticoncepcion = models.BooleanField(default=False, verbose_name="Recibió consejería en anticoncepción")
    metodo_anticonceptivo = models.CharField(max_length=20, choices=METODO_ANTICONCEPTIVO, default="ninguno")
    lactancia_materna_exclusiva = models.BooleanField(default=True)

    indicaciones_alta = models.TextField(blank=True, verbose_name="Indicaciones al alta (medicación y cuidados)")
    signos_alarma_explicados = models.BooleanField(default=False, verbose_name="Se explicaron los signos de alarma")
    proximo_control = models.DateField(null=True, blank=True)
    lugar_proximo_control = models.CharField(max_length=200, blank=True)
    pronostico = models.CharField(max_length=10, choices=PRONOSTICO, default="bueno")

    medico = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="epicrisis_firmadas",
                               null=True, blank=True, verbose_name="Médico responsable")
    matricula_profesional = models.CharField(max_length=30, blank=True)
    campos_adicionales = models.JSONField(default=dict, blank=True)

    estado = models.CharField(max_length=10, choices=ESTADOS, default="borrador")
    fecha_firma = models.DateTimeField(null=True, blank=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="+")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "partos_epicrisis"
        verbose_name = "Epicrisis"
        verbose_name_plural = "Epicrisis"

    def __str__(self):
        return f"Epicrisis del parto {self.parto_id}"

    @property
    def dias_internacion(self) -> int | None:
        inicio = self.parto.fecha_ingreso or self.parto.fecha_parto
        if not (inicio and self.fecha_egreso):
            return None
        return max(0, (timezone.localdate(self.fecha_egreso) - timezone.localdate(inicio)).days)

    def clean(self):
        errores: dict[str, str | list[str]] = {}
        inicio = self.parto.fecha_parto if self.parto_id else None
        if self.fecha_egreso and inicio and self.fecha_egreso < inicio:
            errores["fecha_egreso"] = "El egreso no puede ser anterior al parto."
        if self.fecha_egreso and self.fecha_egreso > timezone.now() + timedelta(days=1):
            errores["fecha_egreso"] = "La fecha de egreso no puede estar en el futuro."
        for campo in ("cie10_ingreso", "cie10_egreso"):
            valor = (getattr(self, campo) or "").strip().upper()
            setattr(self, campo, valor)
            if valor and not CIE10.match(valor):
                errores[campo] = f"«{valor}» no es un código CIE-10 (p. ej. O80, O14.1, O72.0)."
        if self.tipo_egreso == "referencia" and not self.establecimiento_referencia.strip():
            errores["establecimiento_referencia"] = "Indique a qué establecimiento se refiere a la paciente."
        if (self.tipo_egreso == "fallecimiento") != (self.condicion_materna_egreso == "fallecida"):
            errores["condicion_materna_egreso"] = "El tipo de egreso «fallecimiento» y la condición «fallecida» van juntos."
        if self.metodo_anticonceptivo not in ("", "ninguno") and not self.consejeria_anticoncepcion:
            errores["consejeria_anticoncepcion"] = "Si eligió un método anticonceptivo, registre que recibió consejería."
        if self.proximo_control and self.fecha_egreso and self.proximo_control < timezone.localdate(self.fecha_egreso):
            errores["proximo_control"] = "El próximo control no puede ser antes del egreso."
        mensajes = self.validar_campos_adicionales()
        if mensajes:
            errores["campos_adicionales"] = mensajes
        if errores:
            raise ValidationError(errores)

    def validar_campos_adicionales(self) -> list[str]:
        valores = self.campos_adicionales or {}
        if not isinstance(valores, dict):
            return ["Los campos adicionales tienen que ser un objeto {clave: valor}."]
        definiciones = {c.clave: c for c in CampoAdicionalEpicrisis.objects.filter(activo=True)}
        mensajes = [m for c in definiciones.values() if (m := c.validar_valor(valores.get(c.clave)))]
        desconocidos = set(valores) - set(definiciones)
        if desconocidos:
            mensajes.append(f"Campos que este hospital no tiene definidos: {', '.join(sorted(desconocidos))}.")
        return mensajes

    def firmar(self, usuario) -> None:
        """Valida todo y la deja firmada. Exige matrícula: sin ella no es un documento válido."""
        if self.estado == "firmada":
            raise ValidationError("La epicrisis ya está firmada.")
        if not self.matricula_profesional.strip():
            raise ValidationError({"matricula_profesional": "Para firmar hace falta la matrícula profesional."})
        self.full_clean()
        self.estado = "firmada"
        self.medico = usuario
        self.fecha_firma = timezone.now()
        self.save()
