"""=============================================================================
COMANDO DE POBLADO DE VALORES DE REFERENCIA EXPANDIDO
=============================================================================
Hormonas reproductivas, marcadores tumorales, hepaticas, infecciosas extras.

Uso:
    python manage.py poblar_valores_referencia_expandido
=============================================================================
"""

from django.core.management.base import BaseCommand

from laboratorio.models import TipoExamen, ValorReferencia


class Command(BaseCommand):
    """Command"""
    help = "Poblar valores de referencia expandidos (hormonas, marcadores, hepaticas, etc.)"

    def handle(self, *_args, **_kwargs):
        """Handle"""
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 80))
        self.stdout.write(
            self.style.SUCCESS("POBLANDO VALORES DE REFERENCIA EXPANDIDOS"),
        )
        self.stdout.write(self.style.SUCCESS("=" * 80 + "\n"))

        count = 0

        count += self.crear_valores_hormonas_reproductivas()
        count += self.crear_valores_prolactina()
        count += self.crear_valores_amh()
        count += self.crear_valores_he4()
        count += self.crear_valores_cea()
        count += self.crear_valores_funcion_hepatica()
        count += self.crear_valores_hepatitis_c()
        count += self.crear_valores_chlamydia_gonorrea()
        count += self.crear_valores_dimero_d()

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(
            self.style.SUCCESS(
                f"TOTAL: {count} valores de referencia creados/verificados",
            ),
        )
        self.stdout.write(self.style.SUCCESS("=" * 80 + "\n"))

    def crear_valores_hormonas_reproductivas(self):
        """FSH, LH, Estradiol, Progesterona - Fertilidad"""
        count = 0
        self.stdout.write(self.style.SUCCESS("\nHORMONAS REPRODUCTIVAS"))

        # FSH
        try:
            tipo_fsh = TipoExamen.objects.get(codigo="HOR003")
            _valor, created = ValorReferencia.objects.get_or_create(
                tipo_examen=tipo_fsh,
                parametro="FSH",
                defaults={
                    "valor_minimo": 3.0,
                    "valor_maximo": 10.0,
                    "unidad": "mUI/mL",
                    "es_critico_alto": 25.0,
                    "condicion": "Fase folicular - Edad reproductiva",
                },
            )
            if created:
                count += 1
                self.stdout.write("  + FSH - Fase folicular")
        except TipoExamen.DoesNotExist:
            pass

        # LH
        try:
            tipo_lh = TipoExamen.objects.get(codigo="HOR004")
            parametros_lh = [
                {
                    "parametro": "LH Basal",
                    "valor_minimo": 2.0,
                    "valor_maximo": 15.0,
                    "unidad": "mUI/mL",
                    "condicion": "Fase folicular",
                },
                {
                    "parametro": "LH Pico Ovulatorio",
                    "valor_minimo": 20.0,
                    "valor_maximo": 100.0,
                    "unidad": "mUI/mL",
                    "condicion": "Momento ovulacion (>20 confirma)",
                },
            ]

            for param in parametros_lh:
                _valor, created = ValorReferencia.objects.get_or_create(
                    tipo_examen=tipo_lh, parametro=param["parametro"], defaults=param,
                )
                if created:
                    count += 1
                    self.stdout.write(f"  + {param['parametro']}")
        except TipoExamen.DoesNotExist:
            pass

        # Estradiol (E2)
        try:
            tipo_e2 = TipoExamen.objects.get(codigo="HOR005")
            parametros_e2 = [
                {
                    "parametro": "Estradiol Fase Folicular",
                    "valor_minimo": 27.0,
                    "valor_maximo": 161.0,
                    "unidad": "pg/mL",
                    "condicion": "Fase folicular",
                },
                {
                    "parametro": "Estradiol Fase Lutea",
                    "valor_minimo": 50.0,
                    "valor_maximo": 200.0,
                    "unidad": "pg/mL",
                    "condicion": "Fase lutea",
                },
            ]

            for param in parametros_e2:
                _valor, created = ValorReferencia.objects.get_or_create(
                    tipo_examen=tipo_e2, parametro=param["parametro"], defaults=param,
                )
                if created:
                    count += 1
                    self.stdout.write(f"  + {param['parametro']}")
        except TipoExamen.DoesNotExist:
            pass

        # Progesterona
        try:
            tipo_prog = TipoExamen.objects.get(codigo="HOR006")
            parametros_prog = [
                {
                    "parametro": "Progesterona Folicular",
                    "valor_minimo": 0.0,
                    "valor_maximo": 1.0,
                    "unidad": "ng/mL",
                    "condicion": "Fase folicular",
                },
                {
                    "parametro": "Progesterona Lutea (Dia 21)",
                    "valor_minimo": 5.0,
                    "valor_maximo": 20.0,
                    "unidad": "ng/mL",
                    "condicion": ">5 confirma ovulacion",
                },
                {
                    "parametro": "Progesterona Embarazo",
                    "valor_minimo": 10.0,
                    "valor_maximo": 999.0,
                    "unidad": "ng/mL",
                    "condicion": ">10 apoya embarazo",
                },
            ]

            for param in parametros_prog:
                _valor, created = ValorReferencia.objects.get_or_create(
                    tipo_examen=tipo_prog, parametro=param["parametro"], defaults=param,
                )
                if created:
                    count += 1
                    self.stdout.write(f"  + {param['parametro']}")
        except TipoExamen.DoesNotExist:
            pass

        return count

    def crear_valores_prolactina(self):
        """Prolactina - Fertilidad e hiperprolactinemia"""
        count = 0

        try:
            tipo = TipoExamen.objects.get(codigo="HOR007")
        except TipoExamen.DoesNotExist:
            return 0

        _valor, created = ValorReferencia.objects.get_or_create(
            tipo_examen=tipo,
            parametro="Prolactina",
            defaults={
                "valor_minimo": 0.0,
                "valor_maximo": 20.0,
                "unidad": "ng/mL",
                "es_critico_alto": 100.0,
                "condicion": "No embarazada - >30 hiperprolactinemia",
            },
        )
        if created:
            count += 1
            self.stdout.write(f"  + {tipo.nombre} - Prolactina")

        return count

    def crear_valores_amh(self):
        """AMH (Hormona Antimulleriana) - Reserva ovarica"""
        count = 0

        try:
            tipo = TipoExamen.objects.get(codigo="HOR008")
        except TipoExamen.DoesNotExist:
            return 0

        _valor, created = ValorReferencia.objects.get_or_create(
            tipo_examen=tipo,
            parametro="AMH",
            defaults={
                "valor_minimo": 0.7,
                "valor_maximo": 3.5,
                "unidad": "ng/mL",
                "es_critico_bajo": 0.5,
                "condicion": "<0.7 baja reserva, <0.5 muy baja",
            },
        )
        if created:
            count += 1
            self.stdout.write(f"  + {tipo.nombre} - AMH")

        return count

    def crear_valores_he4(self):
        """HE4 - Marcador tumoral ovarico"""
        count = 0

        try:
            tipo = TipoExamen.objects.get(codigo="SER008")
        except TipoExamen.DoesNotExist:
            return 0

        parametros = [
            {
                "parametro": "HE4 Premenopausica",
                "valor_minimo": 0.0,
                "valor_maximo": 150.0,
                "unidad": "pmol/L",
                "es_critico_alto": 200.0,
                "condicion": "Mujer premenopausica",
            },
            {
                "parametro": "HE4 Postmenopausica",
                "valor_minimo": 0.0,
                "valor_maximo": 90.0,
                "unidad": "pmol/L",
                "es_critico_alto": 150.0,
                "condicion": "Mujer postmenopausica",
            },
        ]

        for param in parametros:
            _valor, created = ValorReferencia.objects.get_or_create(
                tipo_examen=tipo, parametro=param["parametro"], defaults=param,
            )
            if created:
                count += 1
                self.stdout.write(f"  + {tipo.nombre} - {param['parametro']}")

        return count

    def crear_valores_cea(self):
        """CEA - Antigeno carcinoembrionario"""
        count = 0

        try:
            tipo = TipoExamen.objects.get(codigo="SER009")
        except TipoExamen.DoesNotExist:
            return 0

        _valor, created = ValorReferencia.objects.get_or_create(
            tipo_examen=tipo,
            parametro="CEA",
            defaults={
                "valor_minimo": 0.0,
                "valor_maximo": 5.0,
                "unidad": "ng/mL",
                "es_critico_alto": 20.0,
                "condicion": "CA-125/CEA >25: origen ovarico, <25: intestinal",
            },
        )
        if created:
            count += 1
            self.stdout.write(f"  + {tipo.nombre} - CEA")

        return count

    def crear_valores_funcion_hepatica(self):
        """AST, ALT, LDH, Bilirrubinas"""
        count = 0
        self.stdout.write(self.style.SUCCESS("\nFUNCION HEPATICA"))

        try:
            tipo = TipoExamen.objects.get(codigo="BIO006")
        except TipoExamen.DoesNotExist:
            return 0

        parametros = [
            {
                "parametro": "AST (TGO)",
                "valor_minimo": 0.0,
                "valor_maximo": 35.0,
                "unidad": "U/L",
                "es_critico_alto": 500.0,
                "condicion": ">500: HELLP, hepatitis aguda",
            },
            {
                "parametro": "ALT (TGP)",
                "valor_minimo": 0.0,
                "valor_maximo": 35.0,
                "unidad": "U/L",
                "es_critico_alto": 500.0,
                "condicion": ">500: HELLP, hepatitis aguda",
            },
            {
                "parametro": "LDH",
                "valor_minimo": 100.0,
                "valor_maximo": 250.0,
                "unidad": "U/L",
                "es_critico_alto": 1000.0,
                "condicion": ">600: HELLP/hemolisis, >1000: critico",
            },
            {
                "parametro": "Bilirrubina Total",
                "valor_minimo": 0.0,
                "valor_maximo": 1.2,
                "unidad": "mg/dL",
                "es_critico_alto": 5.0,
                "condicion": "Colestasis intrahepatica del embarazo",
            },
            {
                "parametro": "Bilirrubina Directa",
                "valor_minimo": 0.0,
                "valor_maximo": 0.3,
                "unidad": "mg/dL",
                "es_critico_alto": 2.0,
                "condicion": "Fraccion conjugada",
            },
        ]

        for param in parametros:
            _valor, created = ValorReferencia.objects.get_or_create(
                tipo_examen=tipo, parametro=param["parametro"], defaults=param,
            )
            if created:
                count += 1
                self.stdout.write(f"  + {tipo.nombre} - {param['parametro']}")

        return count

    def crear_valores_hepatitis_c(self):
        """Anti-HCV - Hepatitis C"""
        count = 0

        try:
            tipo = TipoExamen.objects.get(codigo="SER010")
        except TipoExamen.DoesNotExist:
            return 0

        _valor, created = ValorReferencia.objects.get_or_create(
            tipo_examen=tipo,
            parametro="Anti-HCV",
            defaults={
                "unidad": "cualitativo",
                "valor_normal": "Negativo",
                "condicion": "Si positivo: confirmar con PCR-ARN",
            },
        )
        if created:
            count += 1
            self.stdout.write(f"  + {tipo.nombre} - Anti-HCV")

        return count

    def crear_valores_chlamydia_gonorrea(self):
        """Chlamydia trachomatis y Neisseria gonorrhoeae por PCR/NAAT"""
        count = 0

        try:
            tipo = TipoExamen.objects.get(codigo="MIC002")
        except TipoExamen.DoesNotExist:
            return 0

        parametros = [
            {"parametro": "Chlamydia trachomatis (PCR)", "valor_normal": "Negativo"},
            {"parametro": "Neisseria gonorrhoeae (PCR)", "valor_normal": "Negativo"},
        ]

        for param in parametros:
            _valor, created = ValorReferencia.objects.get_or_create(
                tipo_examen=tipo,
                parametro=param["parametro"],
                defaults={
                    "unidad": "cualitativo",
                    "valor_normal": param["valor_normal"],
                    "condicion": "Muestra: orina o frotis cervical/vaginal",
                },
            )
            if created:
                count += 1
                self.stdout.write(f"  + {tipo.nombre} - {param['parametro']}")

        return count

    def crear_valores_dimero_d(self):
        """Dimero-D - Trombosis"""
        count = 0

        try:
            tipo = TipoExamen.objects.get(codigo="HEM002")
        except TipoExamen.DoesNotExist:
            return 0

        _valor, created = ValorReferencia.objects.get_or_create(
            tipo_examen=tipo,
            parametro="Dimero-D",
            defaults={
                "valor_minimo": 0.0,
                "valor_maximo": 500.0,
                "unidad": "ng/mL",
                "es_critico_alto": 5000.0,
                "condicion": "Elevado: TVP, embolia pulmonar, CID",
            },
        )
        if created:
            count += 1
            self.stdout.write("  + Coagulacion - Dimero-D")

        return count
