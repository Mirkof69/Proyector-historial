"""=============================================================================
COMANDO DE POBLADO DE VALORES DE REFERENCIA - LABORATORIO CLÍNICO
=============================================================================
Adaptado para condiciones de alta altitud (La Paz, Bolivia - 3600-4000m)

EXÁMENES INCLUIDOS:
    pass
1. Hematología: Hemograma completo (adaptado a altura)
2. Bioquímica: Glucosa, función renal, perfil lipídico, calcio
3. Hormonas: β-hCG, FSH, LH, Progesterona, Perfil Tiroideo (TSH, T3, T4)
4. Marcadores Tumorales: CA-125, AFP, CA 19-9
5. Infecciosas: VIH, VDRL, Hepatitis B, Panel TORCH, Cultivo GBS
6. Coagulación: PT/INR, aPTT, Fibrinógeno
7. Orina: EGO completo
8. Especiales: Grupo sanguíneo, Papanicolaou, Curva de tolerancia

VALORES ADAPTADOS A ALTURA:
    pass
- Hemoglobina: 12-16 g/dL (embarazadas) vs 14-20 g/dL (no embarazadas)
- Hematocrito: 32-44% (embarazadas) vs 43-55% (no embarazadas)
- Eritrocitos: Policitemia fisiológica de adaptación

Uso:
    python manage.py poblar_valores_referencia
=============================================================================
"""

from django.core.management.base import BaseCommand

from laboratorio.models import TipoExamen, ValorReferencia


class Command(BaseCommand):
    """Command"""
    help = "Poblar valores de referencia para exámenes de ginecología y obstetricia (altura)"

    def handle(self, *_args, **_kwargs):
        """Handle"""
        self.stdout.write(self.style.SUCCESS("\\n" + "=" * 80))
        self.stdout.write(
            self.style.SUCCESS("POBLANDO VALORES DE REFERENCIA - LABORATORIO CLÍNICO"),
        )
        self.stdout.write(
            self.style.SUCCESS("Adaptado para ALTA ALTITUD (La Paz, Bolivia)"),
        )
        self.stdout.write(self.style.SUCCESS("=" * 80 + "\\n"))

        count = 0

        # HEMATOLOGÍA
        count += self.crear_valores_hemograma()

        # BIOQUÍMICA
        count += self.crear_valores_glucosa()
        count += self.crear_valores_curva_glucosa()
        count += self.crear_valores_funcion_renal()
        count += self.crear_valores_perfil_lipidico()
        count += self.crear_valores_calcio()

        # HORMONAS
        count += self.crear_valores_beta_hcg()
        count += self.crear_valores_perfil_tiroideo()
        count += self.crear_valores_hormonas_reproductivas()
        count += getattr(self, 'crear_valores_prolactina')()
        count += getattr(self, 'crear_valores_amh')()

        # MARCADORES TUMORALES
        count += self.crear_valores_ca125()
        count += self.crear_valores_afp()
        count += getattr(self, 'crear_valores_he4')()
        count += getattr(self, 'crear_valores_cea')()

        # FUNCIÓN HEPÁTICA
        count += getattr(self, 'crear_valores_funcion_hepatica')()

        # INFECCIOSAS
        count += self.crear_valores_vih()
        count += self.crear_valores_vdrl()
        count += self.crear_valores_hepatitis_b()
        count += getattr(self, 'crear_valores_hepatitis_c')()
        count += getattr(self, 'crear_valores_torch')()
        count += getattr(self, 'crear_valores_cultivo_gbs')()
        count += getattr(self, 'crear_valores_chlamydia_gonorrea')()

        # COAGULACIÓN
        count += getattr(self, 'crear_valores_coagulacion')()
        count += getattr(self, 'crear_valores_dimero_d')()

        # ORINA
        count += self.crear_valores_orina()

        # ESPECIALES
        count += self.crear_valores_grupo_sanguineo()
        count += self.crear_valores_papanicolaou()

        self.stdout.write("\\n" + "=" * 80)
        self.stdout.write(
            self.style.SUCCESS(f"✅ {count} VALORES DE REFERENCIA CREADOS EXITOSAMENTE"),
        )
        self.stdout.write(self.style.SUCCESS("=" * 80 + "\\n"))

    # =========================================================================
    # HEMATOLOGÍA
    # =========================================================================
    def crear_valores_hemograma(self):
        """Hemograma completo adaptado a altura (La Paz, Bolivia)"""
        try:
            tipo = TipoExamen.objects.get(codigo="HEM001")
        except TipoExamen.DoesNotExist:
            self.stdout.write(
                self.style.WARNING("  ⚠ Hemograma Completo no encontrado"),
            )
            return 0

        count = 0
        self.stdout.write(self.style.SUCCESS("\\n HEMATOLOGÍA"))

        parametros = [
            {
                "parametro": "Hemoglobina",
                "valor_minimo": 12.0,
                "valor_maximo": 16.0,
                "unidad": "g/dL",
                "es_critico_bajo": 7.0,
                "es_critico_alto": 18.0,
                "condicion": "Mujer embarazada (altura)",
            },
            {
                "parametro": "Hematocrito",
                "valor_minimo": 33.0,
                "valor_maximo": 44.0,
                "unidad": "%",
                "es_critico_bajo": 20.0,
                "es_critico_alto": 60.0,
                "condicion": "Mujer embarazada (altura)",
            },
            {
                "parametro": "Leucocitos",
                "valor_minimo": 6.0,
                "valor_maximo": 17.0,
                "unidad": "10³/µL",
                "es_critico_bajo": 2.0,
                "es_critico_alto": 30.0,
                "condicion": "Mujer embarazada",
            },
            {
                "parametro": "Plaquetas",
                "valor_minimo": 150.0,
                "valor_maximo": 400.0,
                "unidad": "10³/µL",
                "es_critico_bajo": 50.0,
                "es_critico_alto": 1000.0,
                "condicion": "General",
            },
            {
                "parametro": "Neutrófilos",
                "valor_minimo": 40.0,
                "valor_maximo": 70.0,
                "unidad": "%",
                "condicion": "General",
            },
            {
                "parametro": "Linfocitos",
                "valor_minimo": 20.0,
                "valor_maximo": 45.0,
                "unidad": "%",
                "condicion": "General",
            },
            {
                "parametro": "Eosinófilos",
                "valor_minimo": 1.0,
                "valor_maximo": 4.0,
                "unidad": "%",
                "condicion": "General",
            },
            {
                "parametro": "Basófilos",
                "valor_minimo": 0.0,
                "valor_maximo": 1.0,
                "unidad": "%",
                "condicion": "General",
            },
        ]

        for param in parametros:
            _valor, created = ValorReferencia.objects.get_or_create(
                tipo_examen=tipo, parametro=param["parametro"], defaults=param,
            )
            if created:
                count += 1
                self.stdout.write(f"  ✓ {tipo.nombre} - {param['parametro']}")

        return count

    # =========================================================================
    # BIOQUÍMICA
    # =========================================================================
    def crear_valores_glucosa(self):
        """Glucosa en ayunas"""
        try:
            tipo = TipoExamen.objects.get(codigo="BIO001")
        except TipoExamen.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ Glucosa en Ayunas no encontrado"))
            return 0

        count = 0
        self.stdout.write(self.style.SUCCESS("\\n BIOQUÍMICA"))

        _valor, created = ValorReferencia.objects.get_or_create(
            tipo_examen=tipo,
            parametro="Glucosa",
            defaults={
                "valor_minimo": 70.0,
                "valor_maximo": 99.0,
                "unidad": "mg/dL",
                "es_critico_bajo": 50.0,
                "es_critico_alto": 200.0,
                "condicion": "En ayunas",
            },
        )
        if created:
            count += 1
            self.stdout.write(f"  ✓ {tipo.nombre} - Glucosa")

        return count

    def crear_valores_curva_glucosa(self):
        """Curva de tolerancia a la glucosa (CTG) - Diabetes Gestacional"""
        try:
            tipo = TipoExamen.objects.get(codigo="BIO002")
        except TipoExamen.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ CTG no encontrado"))
            return 0

        count = 0
        parametros = [
            {
                "parametro": "Glucosa basal",
                "valor_minimo": 70.0,
                "valor_maximo": 92.0,
                "unidad": "mg/dL",
                "es_critico_alto": 126.0,
                "condicion": "En ayunas",
            },
            {
                "parametro": "Glucosa 1 hora",
                "valor_minimo": 0.0,
                "valor_maximo": 180.0,
                "unidad": "mg/dL",
                "es_critico_alto": 200.0,
                "condicion": "1 hora post-carga",
            },
            {
                "parametro": "Glucosa 2 horas",
                "valor_minimo": 0.0,
                "valor_maximo": 153.0,
                "unidad": "mg/dL",
                "es_critico_alto": 200.0,
                "condicion": "2 horas post-carga",
            },
        ]

        for param in parametros:
            _valor, created = ValorReferencia.objects.get_or_create(
                tipo_examen=tipo, parametro=param["parametro"], defaults=param,
            )
            if created:
                count += 1
                self.stdout.write(f"  ✓ {tipo.nombre} - {param['parametro']}")

        return count

    def crear_valores_funcion_renal(self):
        """Función renal: Urea y Creatinina"""
        try:
            tipo = TipoExamen.objects.get(codigo="BIO004")
        except TipoExamen.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ Función Renal no encontrado"))
            return 0

        count = 0
        parametros = [
            {
                "parametro": "Urea",
                "valor_minimo": 15.0,
                "valor_maximo": 40.0,
                "unidad": "mg/dL",
                "es_critico_alto": 100.0,
                "condicion": "General",
            },
            {
                "parametro": "Creatinina",
                "valor_minimo": 0.50,
                "valor_maximo": 1.10,
                "unidad": "mg/dL",
                "es_critico_alto": 3.0,
                "condicion": "Mujer",
            },
        ]

        for param in parametros:
            _valor, created = ValorReferencia.objects.get_or_create(
                tipo_examen=tipo, parametro=param["parametro"], defaults=param,
            )
            if created:
                count += 1
                self.stdout.write(f"  ✓ {tipo.nombre} - {param['parametro']}")

        return count

    def crear_valores_perfil_lipidico(self):
        """Perfil lipídico completo"""
        try:
            tipo = TipoExamen.objects.get(codigo="BIO003")
        except TipoExamen.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ Perfil Lipídico no encontrado"))
            return 0

        count = 0
        parametros = [
            {
                "parametro": "Colesterol Total",
                "valor_minimo": 0.0,
                "valor_maximo": 200.0,
                "unidad": "mg/dL",
                "es_critico_alto": 300.0,
                "condicion": "Ayunas",
            },
            {
                "parametro": "HDL Colesterol",
                "valor_minimo": 40.0,
                "valor_maximo": 200.0,
                "unidad": "mg/dL",
                "es_critico_bajo": 25.0,
                "condicion": "Mayor es mejor",
            },
            {
                "parametro": "LDL Colesterol",
                "valor_minimo": 0.0,
                "valor_maximo": 100.0,
                "unidad": "mg/dL",
                "es_critico_alto": 190.0,
                "condicion": "Ayunas",
            },
            {
                "parametro": "Triglicéridos",
                "valor_minimo": 0.0,
                "valor_maximo": 150.0,
                "unidad": "mg/dL",
                "es_critico_alto": 500.0,
                "condicion": "Ayunas 12 horas",
            },
        ]

        for param in parametros:
            _valor, created = ValorReferencia.objects.get_or_create(
                tipo_examen=tipo, parametro=param["parametro"], defaults=param,
            )
            if created:
                count += 1
                self.stdout.write(f"  ✓ {tipo.nombre} - {param['parametro']}")

        return count

    def crear_valores_calcio(self):
        """Calcio sérico"""
        try:
            tipo = TipoExamen.objects.get(codigo="BIO005")
        except TipoExamen.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ Calcio Sérico no encontrado"))
            return 0

        count = 0
        _valor, created = ValorReferencia.objects.get_or_create(
            tipo_examen=tipo,
            parametro="Calcio Total",
            defaults={
                "valor_minimo": 8.8,
                "valor_maximo": 10.4,
                "unidad": "mg/dL",
                "es_critico_bajo": 7.0,
                "es_critico_alto": 13.0,
                "condicion": "General",
            },
        )
        if created:
            count += 1
            self.stdout.write(f"  ✓ {tipo.nombre} - Calcio Total")

        return count

    # =========================================================================
    # HORMONAS
    # =========================================================================
    def crear_valores_beta_hcg(self):
        """Beta hCG - Prueba de embarazo cuantitativa"""
        try:
            tipo = TipoExamen.objects.get(codigo="HOR001")
        except TipoExamen.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ Beta hCG no encontrado"))
            return 0

        count = 0
        self.stdout.write(self.style.SUCCESS("\\n HORMONAS"))

        _valor, created = ValorReferencia.objects.get_or_create(
            tipo_examen=tipo,
            parametro="Beta hCG",
            defaults={
                "valor_minimo": 5.0,
                "valor_maximo": 25.0,
                "unidad": "mUI/mL",
                "condicion": "No embarazada (<5 negativo, ≥25 positivo)",
            },
        )
        if created:
            count += 1
            self.stdout.write(f"  ✓ {tipo.nombre} - Beta hCG")

        return count

    def crear_valores_perfil_tiroideo(self):
        """Perfil tiroideo: TSH, T3, T4"""
        try:
            tipo = TipoExamen.objects.get(codigo="HOR002")
        except TipoExamen.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ Perfil Tiroideo no encontrado"))
            return 0

        count = 0
        parametros = [
            {
                "parametro": "TSH",
                "valor_minimo": 0.5,
                "valor_maximo": 2.5,
                "unidad": "μUI/mL",
                "es_critico_bajo": 0.1,
                "es_critico_alto": 10.0,
                "condicion": "Primer trimestre embarazo",
            },
            {
                "parametro": "T3 Total",
                "valor_minimo": 80.0,
                "valor_maximo": 200.0,
                "unidad": "ng/dL",
                "condicion": "General",
            },
            {
                "parametro": "T4 Total",
                "valor_minimo": 5.0,
                "valor_maximo": 12.0,
                "unidad": "µg/dL",
                "condicion": "General",
            },
            {
                "parametro": "T4 Libre",
                "valor_minimo": 0.8,
                "valor_maximo": 1.5,
                "unidad": "ng/dL",
                "condicion": "Embarazo",
            },
        ]

        for param in parametros:
            _valor, created = ValorReferencia.objects.get_or_create(
                tipo_examen=tipo, parametro=param["parametro"], defaults=param,
            )
            if created:
                count += 1
                self.stdout.write(f"  ✓ {tipo.nombre} - {param['parametro']}")

        return count

    def crear_valores_hormonas_reproductivas(self):
        """FSH, LH, Progesterona, Estradiol"""
        count = 0

        # FSH y LH
        try:
            tipo_fsh = TipoExamen.objects.get(codigo="HOR003")
            _valor, created = ValorReferencia.objects.get_or_create(
                tipo_examen=tipo_fsh,
                parametro="FSH",
                defaults={
                    "valor_minimo": 3.0,
                    "valor_maximo": 10.0,
                    "unidad": "mUI/mL",
                    "condicion": "Fase folicular",
                },
            )
            if created:
                count += 1
                self.stdout.write(f"  ✓ {tipo_fsh.nombre} - FSH")
        except TipoExamen.DoesNotExist:
            pass

        return count

    # =========================================================================
    # MARCADORES TUMORALES
    # =========================================================================
    def crear_valores_ca125(self):
        """CA-125 - Marcador tumoral ovárico"""
        count = 0
        self.stdout.write(self.style.SUCCESS("\\n️ MARCADORES TUMORALES"))

        try:
            tipo = TipoExamen.objects.get(codigo="SER005")
        except TipoExamen.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ CA-125 no encontrado"))
            return 0

        _valor, created = ValorReferencia.objects.get_or_create(
            tipo_examen=tipo,
            parametro="CA-125",
            defaults={
                "valor_minimo": 0.0,
                "valor_maximo": 35.0,
                "unidad": "U/mL",
                "es_critico_alto": 100.0,
                "condicion": "General",
            },
        )
        if created:
            count += 1
            self.stdout.write(f"  ✓ {tipo.nombre} - CA-125")

        return count

    def crear_valores_afp(self):
        """AFP - Alfafetoproteína"""
        count = 0
        try:
            tipo = TipoExamen.objects.get(codigo="SER006")
        except TipoExamen.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ AFP no encontrado"))
            return 0

        _valor, created = ValorReferencia.objects.get_or_create(
            tipo_examen=tipo,
            parametro="AFP",
            defaults={
                "valor_minimo": 0.0,
                "valor_maximo": 10.0,
                "unidad": "ng/mL",
                "es_critico_alto": 40.0,
                "condicion": "No embarazada",
            },
        )
        if created:
            count += 1
            self.stdout.write(f"  ✓ {tipo.nombre} - AFP")

        return count

    # =========================================================================
    # INFECCIOSAS
    # =========================================================================
    def crear_valores_vih(self):
        """VIH - Prueba de ELISA"""
        count = 0
        self.stdout.write(self.style.SUCCESS("\\n ENFERMEDADES INFECCIOSAS"))

        tipos = TipoExamen.objects.filter(codigo__in=["SER002", "hiv"])
        for tipo in tipos:
            _valor, created = ValorReferencia.objects.get_or_create(
                tipo_examen=tipo,
                parametro="Anti-VIH",
                defaults={
                    "unidad": "cualitativo",
                    "valor_normal": "No reactivo",
                    "condicion": "General",
                },
            )
            if created:
                count += 1
                self.stdout.write(f"  ✓ {tipo.nombre} - Anti-VIH")

        return count

    def crear_valores_vdrl(self):
        """VDRL - Prueba de sífilis"""
        count = 0
        tipos = TipoExamen.objects.filter(codigo__in=["SER003", "vdrl"])
        for tipo in tipos:
            _valor, created = ValorReferencia.objects.get_or_create(
                tipo_examen=tipo,
                parametro="VDRL",
                defaults={
                    "unidad": "cualitativo",
                    "valor_normal": "No reactivo",
                    "condicion": "General",
                },
            )
            if created:
                count += 1
                self.stdout.write(f"  ✓ {tipo.nombre} - VDRL")

        return count

    def crear_valores_hepatitis_b(self):
        """Hepatitis B - HBsAg"""
        count = 0
        try:
            tipo = TipoExamen.objects.get(codigo="SER007")
        except TipoExamen.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ Hepatitis B no encontrado"))
            return 0

        _valor, created = ValorReferencia.objects.get_or_create(
            tipo_examen=tipo,
            parametro="HBsAg",
            defaults={
                "unidad": "cualitativo",
                "valor_normal": "No reactivo",
                "condicion": "General",
            },
        )
        if created:
            count += 1
            self.stdout.write(f"  ✓ {tipo.nombre} - HBsAg")

        return count

    def crear_valores_torch(self):
        """Panel TORCH - Toxoplasma, Rubéola, CMV, Herpes"""
        try:
            tipo = TipoExamen.objects.get(codigo="SER004")
        except TipoExamen.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ Panel TORCH no encontrado"))
            return 0

        count = 0
        parametros = [
            {
                "parametro": "Toxoplasma IgG",
                "unidad": "cualitativo",
                "valor_normal": "Negativo o < 1.0 IU/mL",
            },
            {
                "parametro": "Toxoplasma IgM",
                "unidad": "cualitativo",
                "valor_normal": "Negativo",
            },
            {
                "parametro": "Rubéola IgG",
                "unidad": "cualitativo",
                "valor_normal": "> 10 IU/mL (Inmune)",
            },
            {
                "parametro": "Rubéola IgM",
                "unidad": "cualitativo",
                "valor_normal": "Negativo",
            },
            {
                "parametro": "Citomegalovirus IgG",
                "unidad": "cualitativo",
                "valor_normal": "Negativo",
            },
            {
                "parametro": "Citomegalovirus IgM",
                "unidad": "cualitativo",
                "valor_normal": "Negativo",
            },
            {
                "parametro": "Herpes Simple IgG",
                "unidad": "cualitativo",
                "valor_normal": "Negativo",
            },
            {
                "parametro": "Herpes Simple IgM",
                "unidad": "cualitativo",
                "valor_normal": "Negativo",
            },
        ]

        for param in parametros:
            _valor, created = ValorReferencia.objects.get_or_create(
                tipo_examen=tipo,
                parametro=param["parametro"],
                defaults={**param, "condicion": "Embarazo"},
            )
            if created:
                count += 1
                self.stdout.write(f"  ✓ {tipo.nombre} - {param['parametro']}")

        return count

    def crear_valores_cultivo_gbs(self):
        """Cultivo para Estreptococo Grupo B"""
        count = 0
        try:
            tipo = TipoExamen.objects.get(codigo="MIC001")
        except TipoExamen.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ Cultivo GBS no encontrado"))
            return 0

        _valor, created = ValorReferencia.objects.get_or_create(
            tipo_examen=tipo,
            parametro="Estreptococo Grupo B",
            defaults={
                "unidad": "cualitativo",
                "valor_normal": "Negativo",
                "condicion": "35-37 semanas gestación",
            },
        )
        if created:
            count += 1
            self.stdout.write(f"  ✓ {tipo.nombre} - Estreptococo Grupo B")

        return count

    # =========================================================================
    # COAGULACIÓN
    # =========================================================================
    def crear_valores_coagulacion(self):
        """Pruebas de coagulación"""
        count = 0
        self.stdout.write(self.style.SUCCESS("\\n COAGULACIÓN"))

        try:
            tipo = TipoExamen.objects.get(codigo="HEM002")
        except TipoExamen.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ Coagulación no encontrado"))
            return 0

        parametros = [
            {
                "parametro": "PT (Tiempo de Protrombina)",
                "valor_minimo": 11.0,
                "valor_maximo": 13.0,
                "unidad": "segundos",
                "es_critico_alto": 20.0,
                "condicion": "General",
            },
            {
                "parametro": "INR",
                "valor_minimo": 0.8,
                "valor_maximo": 1.2,
                "unidad": "ratio",
                "es_critico_alto": 3.0,
                "condicion": "General",
            },
            {
                "parametro": "aPTT",
                "valor_minimo": 25.0,
                "valor_maximo": 35.0,
                "unidad": "segundos",
                "es_critico_alto": 60.0,
                "condicion": "General",
            },
            {
                "parametro": "Fibrinógeno",
                "valor_minimo": 200.0,
                "valor_maximo": 400.0,
                "unidad": "mg/dL",
                "es_critico_bajo": 100.0,
                "es_critico_alto": 600.0,
                "condicion": "General",
            },
        ]

        for param in parametros:
            _valor, created = ValorReferencia.objects.get_or_create(
                tipo_examen=tipo, parametro=param["parametro"], defaults=param,
            )
            if created:
                count += 1
                self.stdout.write(f"  ✓ {tipo.nombre} - {param['parametro']}")

        return count

    # =========================================================================
    # ORINA
    # =========================================================================
    def crear_valores_orina(self):
        """Examen General de Orina"""
        try:
            tipo = TipoExamen.objects.get(codigo="URI001")
        except TipoExamen.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ Examen de Orina no encontrado"))
            return 0

        count = 0
        self.stdout.write(self.style.SUCCESS("\\n ORINA"))

        parametros = [
            {
                "parametro": "Color",
                "unidad": "cualitativo",
                "valor_normal": "Amarillo claro",
            },
            {
                "parametro": "Aspecto",
                "unidad": "cualitativo",
                "valor_normal": "Transparente",
            },
            {
                "parametro": "pH",
                "valor_minimo": 4.5,
                "valor_maximo": 8.0,
                "unidad": "pH",
                "condicion": "General",
            },
            {
                "parametro": "Densidad",
                "valor_minimo": 1.005,
                "valor_maximo": 1.030,
                "unidad": "g/mL",
                "condicion": "General",
            },
            {
                "parametro": "Proteínas",
                "unidad": "cualitativo",
                "valor_normal": "Negativo",
            },
            {
                "parametro": "Glucosa",
                "unidad": "cualitativo",
                "valor_normal": "Negativo",
            },
            {
                "parametro": "Cetonas",
                "unidad": "cualitativo",
                "valor_normal": "Negativo",
            },
            {
                "parametro": "Sangre",
                "unidad": "cualitativo",
                "valor_normal": "Negativo",
            },
            {
                "parametro": "Bilirrubina",
                "unidad": "cualitativo",
                "valor_normal": "Negativo",
            },
            {
                "parametro": "Nitritos",
                "unidad": "cualitativo",
                "valor_normal": "Negativo",
            },
            {
                "parametro": "Leucocitos",
                "valor_minimo": 0.0,
                "valor_maximo": 5.0,
                "unidad": "por campo",
                "es_critico_alto": 10.0,
                "condicion": "Sedimento microscópico",
            },
            {
                "parametro": "Hematíes",
                "valor_minimo": 0.0,
                "valor_maximo": 3.0,
                "unidad": "por campo",
                "es_critico_alto": 10.0,
                "condicion": "Sedimento microscópico",
            },
        ]

        for param in parametros:
            _valor, created = ValorReferencia.objects.get_or_create(
                tipo_examen=tipo, parametro=param["parametro"], defaults=param,
            )
            if created:
                count += 1
                self.stdout.write(f"  ✓ {tipo.nombre} - {param['parametro']}")

        return count

    # =========================================================================
    # ESPECIALES
    # =========================================================================
    def crear_valores_grupo_sanguineo(self):
        """Grupo sanguíneo y Factor Rh"""
        try:
            tipo = TipoExamen.objects.get(codigo="SER001")
        except TipoExamen.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ Grupo Sanguíneo no encontrado"))
            return 0

        count = 0
        self.stdout.write(self.style.SUCCESS("\\n ESPECIALES"))

        parametros = [
            {
                "parametro": "Grupo Sanguíneo",
                "unidad": "cualitativo",
                "valor_normal": "A/B/AB/O",
            },
            {
                "parametro": "Factor Rh",
                "unidad": "cualitativo",
                "valor_normal": "Positivo/Negativo",
            },
        ]

        for param in parametros:
            _valor, created = ValorReferencia.objects.get_or_create(
                tipo_examen=tipo, parametro=param["parametro"], defaults=param,
            )
            if created:
                count += 1
                self.stdout.write(f"  ✓ {tipo.nombre} - {param['parametro']}")

        return count

    def crear_valores_papanicolaou(self):
        """Papanicolaou - Citología cervical"""
        try:
            tipo = TipoExamen.objects.get(codigo="CIT001")
        except TipoExamen.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠ Papanicolaou no encontrado"))
            return 0

        count = 0
        _valor, created = ValorReferencia.objects.get_or_create(
            tipo_examen=tipo,
            parametro="Resultado",
            defaults={
                "unidad": "cualitativo",
                "valor_normal": "Negativo para lesión intraepitelial",
                "condicion": "Clasificación Bethesda",
            },
        )
        if created:
            count += 1
            self.stdout.write(f"  ✓ {tipo.nombre} - Resultado")

        return count
