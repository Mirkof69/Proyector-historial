from django.core.management.base import BaseCommand
from laboratorio.models import TipoExamen, ValorReferencia
from decimal import Decimal


class Command(BaseCommand):
    help = 'Crea datos iniciales de laboratorio (tipos de exámenes y valores de referencia)'
    
    def handle(self, *args, **kwargs):
        self.stdout.write('Creando datos de laboratorio...')
        
        # HEMOGRAMA COMPLETO
        hemograma, created = TipoExamen.objects.get_or_create(
            codigo='HEM001',
            defaults={
                'nombre': 'Hemograma Completo',
                'categoria': 'hematologia',
                'descripcion': 'Análisis completo de células sanguíneas',
                'preparacion': 'No requiere ayuno',
                'tiempo_resultado': 24,
                'precio': Decimal('50.00'),
                'activo': True,
            }
        )
        
        if created:
            # Valores de referencia para Hemograma
            ValorReferencia.objects.create(
                tipo_examen=hemograma,
                parametro='Hemoglobina',
                valor_minimo=Decimal('12.0'),
                valor_maximo=Decimal('16.0'),
                unidad='g/dL',
                condicion='Mujer embarazada',
                es_critico_bajo=Decimal('7.0'),
                es_critico_alto=Decimal('20.0'),
            )
            
            ValorReferencia.objects.create(
                tipo_examen=hemograma,
                parametro='Hematocrito',
                valor_minimo=Decimal('33.0'),
                valor_maximo=Decimal('44.0'),
                unidad='%',
                condicion='Mujer embarazada',
            )
            
            ValorReferencia.objects.create(
                tipo_examen=hemograma,
                parametro='Leucocitos',
                valor_minimo=Decimal('6.0'),
                valor_maximo=Decimal('17.0'),
                unidad='10³/µL',
                condicion='Mujer embarazada',
            )
            
            ValorReferencia.objects.create(
                tipo_examen=hemograma,
                parametro='Plaquetas',
                valor_minimo=Decimal('150'),
                valor_maximo=Decimal('400'),
                unidad='10³/µL',
                es_critico_bajo=Decimal('50'),
                es_critico_alto=Decimal('1000'),
            )
        
        # GLUCOSA EN AYUNAS
        glucosa, created = TipoExamen.objects.get_or_create(
            codigo='BIO001',
            defaults={
                'nombre': 'Glucosa en Ayunas',
                'categoria': 'bioquimica',
                'descripcion': 'Medición de glucosa en sangre',
                'preparacion': 'Ayuno de 8-12 horas',
                'tiempo_resultado': 12,
                'precio': Decimal('20.00'),
                'activo': True,
            }
        )
        
        if created:
            ValorReferencia.objects.create(
                tipo_examen=glucosa,
                parametro='Glucosa',
                valor_minimo=Decimal('70'),
                valor_maximo=Decimal('99'),
                unidad='mg/dL',
                condicion='En ayunas',
                es_critico_bajo=Decimal('40'),
                es_critico_alto=Decimal('400'),
            )
        
        # EXAMEN DE ORINA
        orina, created = TipoExamen.objects.get_or_create(
            codigo='URI001',
            defaults={
                'nombre': 'Examen General de Orina',
                'categoria': 'urinalisis',
                'descripcion': 'Análisis físico, químico y microscópico de orina',
                'preparacion': 'Primera orina de la mañana',
                'tiempo_resultado': 24,
                'precio': Decimal('30.00'),
                'activo': True,
            }
        )
        
        if created:
            ValorReferencia.objects.create(
                tipo_examen=orina,
                parametro='Proteínas',
                valor_normal='Negativo',
                unidad='cualitativo',
            )
            
            ValorReferencia.objects.create(
                tipo_examen=orina,
                parametro='Glucosa',
                valor_normal='Negativo',
                unidad='cualitativo',
            )
            
            ValorReferencia.objects.create(
                tipo_examen=orina,
                parametro='Leucocitos',
                valor_minimo=Decimal('0'),
                valor_maximo=Decimal('5'),
                unidad='células/campo',
            )
        
        # GRUPO SANGUÍNEO
        grupo, created = TipoExamen.objects.get_or_create(
            codigo='SER001',
            defaults={
                'nombre': 'Grupo Sanguíneo y Factor Rh',
                'categoria': 'serologia',
                'descripcion': 'Determinación de grupo ABO y factor Rh',
                'preparacion': 'No requiere ayuno',
                'tiempo_resultado': 12,
                'precio': Decimal('40.00'),
                'activo': True,
            }
        )
        
        # HIV
        hiv, created = TipoExamen.objects.get_or_create(
            codigo='SER002',
            defaults={
                'nombre': 'Prueba de VIH (ELISA)',
                'categoria': 'serologia',
                'descripcion': 'Detección de anticuerpos contra VIH',
                'preparacion': 'No requiere ayuno',
                'tiempo_resultado': 48,
                'precio': Decimal('80.00'),
                'activo': True,
            }
        )
        
        if created:
            ValorReferencia.objects.create(
                tipo_examen=hiv,
                parametro='Anti-VIH',
                valor_normal='No reactivo',
                unidad='cualitativo',
            )
        
        # VDRL (SÍFILIS)
        vdrl, created = TipoExamen.objects.get_or_create(
            codigo='SER003',
            defaults={
                'nombre': 'VDRL (Prueba de Sífilis)',
                'categoria': 'serologia',
                'descripcion': 'Detección de sífilis',
                'preparacion': 'No requiere ayuno',
                'tiempo_resultado': 24,
                'precio': Decimal('35.00'),
                'activo': True,
            }
        )
        
        if created:
            ValorReferencia.objects.create(
                tipo_examen=vdrl,
                parametro='VDRL',
                valor_normal='No reactivo',
                unidad='cualitativo',
            )
        
        self.stdout.write(self.style.SUCCESS('✅ Datos de laboratorio creados exitosamente'))